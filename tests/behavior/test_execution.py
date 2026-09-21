"""Given a target and pack, observe outcomes, evidence, and cleanup."""
from dataclasses import asdict
from pathlib import Path

import pytest

from kst.adapters import Capture, MockAdapter, Registry
from kst.analysis import summarize
from kst.core import Invalid
from kst.engine import execute
from kst.telemetry import Ledger

pytestmark = pytest.mark.behavior


def endings(directory):
    return [e["payload"] for e in Ledger(directory / "events.jsonl").read()
            if e["event_type"] == "trial.finished"]


@pytest.mark.parametrize("fault,status,count", [
    (None, "completed", 3), ("unsupported", "unsupported", 3),
    ("start", "error", 3), ("submit", "error", 3), ("timeout", "timeout", 3),
    ("empty", "error", 3), ("close", "error", 3), ("cancel", "cancelled", 1),
])
def test_failures_remain_evidence_not_recall_scores(pack, one_target, tmp_path, fault, status, count):
    made = []
    def factory(target):
        adapter = MockAdapter(fault=fault)
        made.append(adapter)
        return adapter
    registry = Registry()
    registry.register("mock", factory)
    directory = tmp_path / "run"
    result = execute(pack, one_target, directory, 1, registry=registry)
    assert result["trial_count"] == count
    assert {e["status"] for e in endings(directory)} == {status}
    assert all(a.closed for a in made)
    assert all(g["scored"] == 0 for g in summarize(Ledger(directory / "events.jsonl"))["groups"])
    if fault == "close":
        assert all(e["capture"]["raw_text"] and e["cleanup_error"] for e in endings(directory))


def test_fresh_sessions_and_clean_owned_workspace(pack, one_target, tmp_path):
    workspaces, received = [], []
    class Spy(MockAdapter):
        def start(self, target, workspace):
            workspaces.append(workspace)
            return super().start(target, workspace)
        def submit(self, session, request):
            received.append(asdict(request))
            return super().submit(session, request)
    registry = Registry()
    registry.register("mock", lambda _: Spy())
    execute(pack, one_target, tmp_path / "run", 2, registry=registry)
    records = endings(tmp_path / "run")
    assert len({r["capture"]["session_id"] for r in records}) == 6
    assert len(set(workspaces)) == 6
    assert not any(path.exists() for path in workspaces)
    assert all(set(request) == {"trial_id", "prompt", "timeout_seconds"} for request in received)
    assert all("DEMO-LAYER" not in str(request) and "paper boats" not in str(request)
               for request in received)


def test_observed_identity_does_not_inherit_request(pack, one_target, tmp_path):
    target = one_target["targets"][0]
    target["model"]["requested_model_id"] = "requested-x"
    target["runtime"]["mock"]["observed"] = {"model_id": "observed-y", "reasoning": "high"}
    execute(pack, one_target, tmp_path / "run", 1)
    assert all(r["capture"]["observed"]["model_id"] == "observed-y" for r in endings(tmp_path / "run"))
    target["runtime"]["mock"]["observed"] = {}
    execute(pack, one_target, tmp_path / "other", 1)
    assert all("model_id" not in r["capture"]["observed"] for r in endings(tmp_path / "other"))


def test_unknown_adapter_is_reported_without_fallback(pack, one_target, tmp_path):
    one_target["targets"][0]["runtime"]["adapter"] = "not-implemented"
    execute(pack, one_target, tmp_path / "run", 1)
    assert {r["status"] for r in endings(tmp_path / "run")} == {"unsupported"}


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf")])
def test_bad_timeout_leaves_no_run(pack, targets, tmp_path, timeout):
    with pytest.raises(Invalid, match="positive and finite"):
        execute(pack, targets, tmp_path / "run", timeout_seconds=timeout)
    assert not (tmp_path / "run").exists()


def test_existing_run_is_never_overwritten(pack, targets, tmp_path):
    (tmp_path / "keep").write_text("original")
    with pytest.raises(FileExistsError):
        execute(pack, targets, tmp_path)
    assert (tmp_path / "keep").read_text() == "original"


@pytest.mark.parametrize("case", ["not-capture", "bad-text", "bad-mode", "bad-session", "nan"])
def test_malformed_adapter_output_fails_loudly(pack, one_target, tmp_path, case):
    class Bad(MockAdapter):
        def submit(self, session, request):
            if case == "not-capture":
                return {"raw_text": "wrong type"}
            result = super().submit(session, request)
            if case == "bad-text": result.raw_text = ["wrong type"]
            if case == "bad-mode": result.mode = "live"
            if case == "bad-session": result.session_id = "other-session"
            if case == "nan": result.latency_ms = float("nan")
            return result
    registry = Registry()
    registry.register("mock", lambda _: Bad())
    execute(pack, one_target, tmp_path / "run", 1, registry=registry)
    assert {r["status"] for r in endings(tmp_path / "run")} == {"error"}


def test_reused_session_is_not_a_cold_trial(pack, one_target, tmp_path):
    class Reused(MockAdapter):
        def start(self, target, workspace): return "same-session"
    registry = Registry()
    registry.register("mock", lambda _: Reused())
    execute(pack, one_target, tmp_path / "run", 1, registry=registry)
    assert [r["status"] for r in endings(tmp_path / "run")] == ["completed", "error", "error"]


def test_workspace_under_framework_is_rejected(pack, one_target, tmp_path, monkeypatch):
    from contextlib import contextmanager
    import kst.engine
    @contextmanager
    def unsafe_workspace(**kwargs):
        yield str(Path(kst.engine.__file__).resolve().parent / "scratch")
    monkeypatch.setattr(kst.engine.tempfile, "TemporaryDirectory", unsafe_workspace)
    execute(pack, one_target, tmp_path / "run", 1)
    assert all("outside" in r["error"]["message"] for r in endings(tmp_path / "run"))

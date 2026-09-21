import json

import pytest

from kst.analysis import summarize
from kst.core import Invalid, canonical, digest
from kst.engine import execute
from kst.telemetry import Ledger, score

pytestmark = pytest.mark.unit


@pytest.fixture
def completed(pack, one_target, tmp_path):
    execute(pack, one_target, tmp_path / "run", 1)
    ledger = Ledger(tmp_path / "run" / "events.jsonl")
    start = next(e["payload"] for e in ledger.read() if e["event_type"] == "trial.started"
                 and e["payload"]["pack"]["kind"] == "positive")
    return ledger, start["trial_id"]


def test_rescoring_is_append_only_and_projection_uses_latest(completed):
    ledger, tid = completed
    original = ledger.path.read_bytes()
    score(ledger, tid, 2, "human-a", "rubric-1", "recognized")
    after_first = ledger.path.read_bytes()
    score(ledger, tid, 0, "human-b", "rubric-2", "unknown", "Revised after review")
    assert ledger.path.read_bytes().startswith(after_first)
    assert after_first.startswith(original)
    scores = [e for e in ledger.read() if e["event_type"] == "score.recorded"]
    assert [e["payload"]["score"] for e in scores] == [2, 0]
    row = next(g for g in summarize(ledger)["groups"] if g["scored"])
    assert row["full_recognition_rate"] == 0
    assert row["mean_score"] == 0
    assert row["unknown"] == 1


def test_unscored_is_not_zero(completed):
    ledger, _ = completed
    for row in summarize(ledger)["groups"]:
        assert row["mean_score"] is None
        assert row["scored"] == 0
        assert "score_sum" not in row


def test_control_rejection_is_not_recall(completed):
    ledger, _ = completed
    tid = next(e["payload"]["trial_id"] for e in ledger.read()
               if e["event_type"] == "trial.started" and e["payload"]["pack"]["kind"] == "negative_control")
    score(ledger, tid, 2, "human", "1", "rejected")
    row = next(g for g in summarize(ledger)["groups"] if g["kind"] == "negative_control")
    assert row["control_rejection_rate"] == 1
    assert "full_recognition_rate" not in row
    with pytest.raises(Invalid, match="contradict"):
        score(ledger, tid, 2, "human", "1", "recognized")


@pytest.mark.parametrize("value,assessment", [(3, "recognized"), (-1, "wrong"),
                                               (True, "partial"), (2, "wrong")])
def test_invalid_scores_do_not_change_history(completed, value, assessment):
    ledger, tid = completed
    before = ledger.path.read_bytes()
    with pytest.raises(Invalid):
        score(ledger, tid, value, "human", "1", assessment)
    assert ledger.path.read_bytes() == before


def test_unknown_trial_cannot_be_scored(completed):
    with pytest.raises(Invalid, match="completed trial"):
        score(completed[0], "missing", 0, "human", "1", "unknown")


def test_failed_execution_cannot_be_scored(pack, one_target, tmp_path):
    one_target["targets"][0]["runtime"]["mock"]["fault"] = "timeout"
    execute(pack, one_target, tmp_path / "run", 1)
    ledger = Ledger(tmp_path / "run" / "events.jsonl")
    tid = next(e["payload"]["trial_id"] for e in ledger.read() if e["event_type"] == "trial.finished")
    with pytest.raises(Invalid, match="completed trial"):
        score(ledger, tid, 0, "human", "1", "unknown")


@pytest.mark.parametrize("damage", ["truncated", "json", "hash", "sequence", "schema"])
def test_corrupt_ledger_is_never_silently_repaired(completed, damage):
    ledger, _ = completed
    data = ledger.path.read_bytes()
    if damage == "truncated":
        broken = data[:-1]
    elif damage == "json":
        broken = b"not-json\n"
    else:
        events = [json.loads(line) for line in data.splitlines()]
        if damage == "hash": events[0]["hash"] = "0" * 64
        if damage == "sequence": events[0]["sequence"] = 12
        if damage == "schema": events[0]["schema_version"] = "999"
        broken = ("\n".join(canonical(e) for e in events) + "\n").encode()
    ledger.path.write_bytes(broken)
    with pytest.raises(Invalid):
        ledger.read()
    with pytest.raises(Invalid):
        ledger.append("run.finished", {"run_id": "r", "status": "incomplete", "trial_count": 0})
    assert ledger.path.read_bytes() == broken
    assert not ledger.path.with_suffix(".jsonl.lock").exists()


def test_existing_writer_lock_is_not_broken(tmp_path):
    ledger = Ledger(tmp_path / "events.jsonl")
    lock = tmp_path / "events.jsonl.lock"
    lock.write_text("another writer")
    with pytest.raises(Invalid, match="another writer"):
        ledger.append("anything", {})
    assert lock.read_text() == "another writer"
    assert not ledger.path.exists()


def test_bad_event_never_creates_ledger(tmp_path):
    ledger = Ledger(tmp_path / "events.jsonl")
    with pytest.raises(Invalid):
        ledger.append("nonexistent-event", {})
    assert not ledger.path.exists()


def test_storage_failure_is_loud_and_releases_lock(tmp_path, monkeypatch):
    ledger = Ledger(tmp_path / "events.jsonl")
    def fail(_): raise OSError("simulated disk failure")
    monkeypatch.setattr("kst.telemetry.os.fsync", fail)
    with pytest.raises(OSError, match="disk failure"):
        ledger.append("run.finished", {"run_id": "r", "status": "incomplete", "trial_count": 0})
    assert not (tmp_path / "events.jsonl.lock").exists()


def test_projection_reports_unfinished_trials(completed):
    ledger, tid = completed
    events = ledger.read()
    first_start = next(e for e in events if e["event_type"] == "trial.started")
    ledger.path.write_text("\n".join(canonical(e) for e in events[:first_start["sequence"]]) + "\n")
    report = summarize(ledger)
    assert report["groups"][0]["unfinished"] == 1


def test_projection_rejects_duplicate_start(completed):
    ledger, _ = completed
    start = next(e["payload"] for e in ledger.read() if e["event_type"] == "trial.started")
    ledger.append("trial.started", start)
    with pytest.raises(Invalid, match="Duplicate"):
        summarize(ledger)


def test_projection_rejects_orphan_score(completed):
    ledger, _ = completed
    ledger.append("score.recorded", {"trial_id": "missing", "score": 0,
                  "scorer": "test", "rubric_version": "1", "assessment": "unknown", "note": ""})
    with pytest.raises(Invalid, match="Orphan"):
        summarize(ledger)


def test_failed_trial_with_injected_score_is_rejected(pack, one_target, tmp_path):
    one_target["targets"][0]["runtime"]["mock"]["fault"] = "timeout"
    execute(pack, one_target, tmp_path / "run", 1)
    ledger = Ledger(tmp_path / "run" / "events.jsonl")
    tid = next(e["payload"]["trial_id"] for e in ledger.read() if e["event_type"] == "trial.finished")
    ledger.append("score.recorded", {"trial_id": tid, "score": 0, "scorer": "test",
                  "rubric_version": "1", "assessment": "unknown", "note": ""})
    with pytest.raises(Invalid, match="failed execution"):
        summarize(ledger)


def test_score_requires_a_start_even_with_a_completion(tmp_path):
    ledger = Ledger(tmp_path / "events.jsonl")
    ledger.append("trial.finished", {"run_id": "r", "trial_id": "t", "status": "completed",
                  "capture": {"raw_text": "answer", "mode": "mock", "isolation": {}, "observed": {}},
                  "error": None, "cleanup_error": None})
    with pytest.raises(Invalid, match="trial start"):
        score(ledger, "t", 2, "test", "1", "recognized")


def test_unicode_line_separators_round_trip_as_response_data(tmp_path):
    ledger = Ledger(tmp_path / "events.jsonl")
    texts = ["left\u2028right", "left\u2029right", "left\u0085right", "λ\n\r\n\t\x00"]
    for index, text in enumerate(texts):
        ledger.append("trial.finished", {"run_id": "unicode", "trial_id": str(index),
                      "status": "completed", "capture": {"raw_text": text, "mode": "mock",
                      "observed": {}, "isolation": {}}, "error": None, "cleanup_error": None})
        assert ledger.read()[-1]["payload"]["capture"]["raw_text"] == text

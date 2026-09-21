"""Reusable conformance checks: extend adapter_factory with offline native shims."""
from dataclasses import asdict

import pytest

from kst.adapters import Capture, MockAdapter, ProbeRequest, Registry, Unsupported
from kst.core import Invalid, validate

pytestmark = pytest.mark.contract


@pytest.fixture(params=[MockAdapter], ids=["mock"])
def adapter_factory(request):
    return request.param


def test_adapter_lifecycle_contract(adapter_factory, one_target, tmp_path):
    adapter = adapter_factory()
    target = one_target["targets"][0]
    capabilities = adapter.preflight(target)
    assert capabilities.mode in ("mock", "manual", "live")
    session = adapter.start(target, tmp_path)
    assert isinstance(session, str) and session
    result = adapter.submit(session, ProbeRequest("opaque-trial", "A blind question"))
    assert isinstance(result, Capture)
    validate(asdict(result), "capture")
    assert result.session_id == session
    adapter.close(session)
    assert adapter.closed
    assert adapter.calls == ["preflight", "start", "submit", "close"]


def test_registry_never_silently_replaces_an_adapter(one_target):
    registry = Registry()
    target = one_target["targets"][0]
    with pytest.raises(Unsupported):
        registry.create(target)
    registry.register("mock", lambda _: MockAdapter())
    with pytest.raises(Invalid, match="registered"):
        registry.register("mock", lambda _: MockAdapter())
    with pytest.raises(Invalid):
        registry.register("", lambda _: MockAdapter())
    assert isinstance(registry.create(target), MockAdapter)


def test_mock_requires_empty_workspace(one_target, tmp_path):
    (tmp_path / "answer-key.txt").write_text("not blind")
    with pytest.raises(Invalid, match="empty"):
        MockAdapter().start(one_target["targets"][0], tmp_path)


def test_protocol_request_has_no_grading_fields():
    assert set(asdict(ProbeRequest("opaque", "question"))) == {
        "trial_id", "prompt", "timeout_seconds"}

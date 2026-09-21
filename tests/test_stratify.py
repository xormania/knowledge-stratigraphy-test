"""Compatibility and user-named target examples; names never become enums."""
import pytest

import stratify
from kst.core import plan

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("harness,model", [
    ("Claude Code", "Fable"), ("Claude Code", "Opus"),
    ("Codex", "ChatGPT"), ("Grok Build", "Grok"),
    ("Future Harness", "Future Model"),
])
def test_model_and_harness_are_independent_data(pack, one_target, harness, model):
    target = one_target["targets"][0]
    target["harness"]["name"] = harness
    target["model"]["requested_label"] = model
    target["runtime"] = {"adapter": "manual"}
    result = stratify.requested_target_record(target)
    assert result["harness_requested"]["name"] == harness
    assert result["model_requested"]["label"] == model
    assert len(plan(pack, one_target, 1)["trials"]) == 3

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("stratify", ROOT / "stratify.py")
stratify = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(stratify)


class TargetTests(unittest.TestCase):
    def test_example_targets_are_independent_dimensions(self):
        data = stratify.load_targets(ROOT / "targets.example.json")
        targets = {t["id"]: t for t in data["targets"]}

        self.assertEqual(targets["claude-code-fable"]["harness"]["name"], "Claude Code")
        self.assertEqual(targets["claude-code-fable"]["model"]["family"], "Fable")
        self.assertEqual(targets["claude-code-opus"]["harness"]["name"], "Claude Code")
        self.assertEqual(targets["claude-code-opus"]["model"]["family"], "Opus")
        self.assertEqual(targets["codex-chatgpt"]["model"]["family"], "ChatGPT")
        self.assertEqual(targets["grok-build-grok"]["model"]["family"], "Grok")

    def test_future_harness_and_model_require_no_enum_change(self):
        target = {
            "id": "future",
            "label": "Future Harness / Future Model",
            "harness": {
                "name": "Future Harness",
                "mode": "other",
                "requested_version": None,
                "executable": None,
            },
            "model": {
                "provider": "Future Provider",
                "family": "Future Family",
                "requested_label": "Future Model 99",
                "requested_model_id": "future-99",
                "requested_reasoning": "novel",
            },
            "runtime": {"adapter": "manual", "transport": "manual"},
        }

        record = stratify.requested_target_record(target)
        self.assertEqual(record["harness_requested"]["name"], "Future Harness")
        self.assertEqual(record["model_requested"]["label"], "Future Model 99")
        self.assertEqual(record["model_requested"]["reasoning"], "novel")

    def test_requested_record_contains_no_observed_identity(self):
        data = stratify.load_targets(ROOT / "targets.example.json")
        target = stratify.find_target(data, "grok-build-grok")
        record = stratify.requested_target_record(target)

        self.assertIn("model_requested", record)
        self.assertNotIn("observed", record)
        self.assertNotIn("effective_model", json.dumps(record))

    def test_probe_pack_is_target_agnostic(self):
        pack = stratify.load_pack(ROOT / "examples" / "codex-reset-2026-v0.1.json")
        encoded = json.dumps(pack).lower()

        self.assertNotIn('"target_id"', encoded)
        self.assertNotIn('"harness"', encoded)

    def test_enabled_targets_filters_without_model_logic(self):
        data = {
            "targets": [
                {"id": "a", "enabled": True},
                {"id": "b", "enabled": False},
                {"id": "c"},
            ]
        }
        self.assertEqual([t["id"] for t in stratify.enabled_targets(data)], ["a", "c"])


if __name__ == "__main__":
    unittest.main()

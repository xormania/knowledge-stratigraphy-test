"""Offline behavior and abuse-regression tests for the trusted metadata gate."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("contribution_gate", ROOT / "scripts/contribution_gate.py")
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)
HEAD = "a" * 40
REPO = "xormania/knowledge-stratigraphy-test"


def proof(kind="bugfix"):
    return {"kind": kind, "tested_commit": HEAD,
            "baseline": "An empty adapter response was treated as a recall failure.",
            "change": "Reuse the execution-result classifier; add an empty-answer regression.",
            "verification": [
                {"command": "python scripts/check.py", "result": "99 tests passed; coverage above the unchanged threshold.",
                 "evidence": "tests/behavior/test_engine.py::test_empty_response"},
                {"command": "python scripts/package_smoke.py", "result": "Installed wheel completed the six-trial mock run.",
                 "evidence": "CI artifact and installed-package command output"}],
            "limitations": "Mock evidence only; no live backend compatibility claim."}


def body(value=None):
    return gate.START + "\n```json\n" + json.dumps(value or proof()) + "\n```\n" + gate.END


def files(*paths):
    return [{"filename": p, "status": "modified"} for p in paths]


def evaluate(value=None, changed=None, raw=None):
    changed = changed if changed is not None else files("kst/engine.py", "tests/behavior/test_engine.py")
    return gate.validate_proof({"body": raw if raw is not None else body(value), "head": {"sha": HEAD},
                                "changed_files": len(changed)}, changed, REPO)


class ProofTests(unittest.TestCase):
    def test_valid_runtime_proof(self):
        self.assertEqual([], evaluate())

    def test_stale_head_fails(self):
        value = proof(); value["tested_commit"] = "b" * 40
        self.assertTrue(any("current full PR head" in e for e in evaluate(value)))

    def test_abbreviated_commit_fails(self):
        value = proof(); value["tested_commit"] = "aaaaaaa"
        self.assertTrue(evaluate(value))

    def test_docs_have_lightweight_manual_proof(self):
        value = proof("docs")
        value["verification"] = [{"command": "Manual: render Markdown", "result": "Checked all six relative links and the corrected command.",
                                  "evidence": "README.md quick-start section, rendered Files changed view"}]
        self.assertEqual([], evaluate(value, files("README.md")))

    def test_docs_cannot_hide_code(self):
        self.assertTrue(any("docs is only" in e for e in evaluate(proof("docs"))))

    def test_renaming_code_into_docs_does_not_hide_scope(self):
        changed = files("docs/example.md")
        changed[0]["previous_filename"] = "kst/engine.py"
        self.assertTrue(evaluate(proof("docs"), changed))

    def test_runtime_needs_changed_tests(self):
        self.assertTrue(any("regression tests" in e for e in evaluate(changed=files("kst/engine.py"))))

    def test_deleted_test_does_not_count(self):
        changed = files("kst/engine.py", "tests/test_old.py"); changed[1]["status"] = "removed"
        self.assertTrue(evaluate(changed=changed))

    def test_adapter_needs_both_contract_and_behavior(self):
        self.assertTrue(evaluate(proof("adapter")))
        self.assertEqual([], evaluate(proof("adapter"), files("kst/adapters.py", "tests/contracts/test_new.py", "tests/behavior/test_new.py")))

    def test_placeholders_fail(self):
        for text in ("REPLACE with your output", "TODO: investigate later", "TBD", "N/A", "..."):
            value = proof(); value["baseline"] = text
            with self.subTest(text=text): self.assertTrue(evaluate(value))

    def test_missing_block_fails(self):
        self.assertTrue(evaluate(raw="Looks good. All tests pass."))

    def test_two_blocks_fail(self):
        self.assertTrue(evaluate(raw=body() + body()))

    def test_invalid_json_fails(self):
        self.assertTrue(evaluate(raw=gate.START + '\n```json\n{broken}\n```\n' + gate.END))

    def test_duplicate_json_key_fails(self):
        text = body().replace('"kind": "bugfix"', '"kind": "docs", "kind": "bugfix"')
        self.assertTrue(evaluate(raw=text))

    def test_unknown_field_fails(self):
        value = proof(); value["auto_approve"] = True
        self.assertTrue(evaluate(value))

    def test_wrong_typed_fields_fail_without_crashing(self):
        for field in ("kind", "tested_commit", "baseline", "verification"):
            for wrong in (None, 1, [], {}):
                value = proof(); value[field] = wrong
                with self.subTest(field=field, wrong=wrong): self.assertTrue(evaluate(value))
        value = proof(); value["verification"][0]["command"] = 42
        self.assertTrue(evaluate(value))

    def test_shell_expression_does_not_count_as_standard_check(self):
        value = proof(); value["verification"][0]["command"] = "echo python scripts/check.py"
        self.assertTrue(evaluate(value))

    def test_proof_commands_are_never_executed(self):
        value = proof("docs")
        value["verification"][0]["command"] = "$(touch /tmp/should-not-exist)"
        with patch("subprocess.run", side_effect=AssertionError("execution")):
            self.assertEqual([], evaluate(value, files("README.md")))

    def test_raw_runs_and_credentials_rejected(self):
        for path in ("runs/a/events.jsonl", "results/private.zip", ".env", "secrets/private.pem"):
            with self.subTest(path=path):
                self.assertTrue(any("credentials" in e for e in evaluate(proof("ci"), files(path))))

    def test_removing_sensitive_file_is_allowed(self):
        changed = files(".env"); changed[0]["status"] = "removed"
        self.assertEqual([], evaluate(proof("ci"), changed))

    def test_probe_requires_provenance(self):
        self.assertTrue(evaluate(proof("probe"), files("examples/new.json")))
        value = proof("probe"); value["sources"] = [{"url": "https://example.org/source", "observed_date": "2026-09-01"}]
        self.assertEqual([], evaluate(value, files("examples/new.json")))

    def test_probe_accepts_declared_synthetic_fixture(self):
        value = proof("probe"); value["sources"] = [{"synthetic": True, "reason": "Invented fixture; no empirical knowledge claim."}]
        self.assertEqual([], evaluate(value, files("examples/new.json")))

    def test_source_credentials_invalid_date_and_bad_shape_fail(self):
        for source in ({"url": "https://secret@example.org", "observed_date": "2026-09-01"},
                       {"url": "https://example.org", "observed_date": "yesterday"}, 2):
            value = proof("probe"); value["sources"] = [source]
            with self.subTest(source=source): self.assertTrue(evaluate(value, files("examples/new.json")))

    def test_incomplete_file_listing_fails(self):
        self.assertTrue(gate.validate_proof({"changed_files": 2}, files("README.md"), REPO))

    def test_invalid_path_and_empty_diff_fail(self):
        self.assertTrue(evaluate(changed=files("../outside.py")))
        self.assertTrue(evaluate(changed=[]))

    def test_real_dependabot_pin_exception(self):
        changed = files("requirements-test.txt")
        changed[0]["patch"] = "@@ -1 +1 @@\n-pytest==9.0.2\n+pytest==9.1.1"
        pr = {"changed_files": 1, "user": {"login": "dependabot[bot]", "id": 49699333, "type": "Bot"},
              "head": {"ref": "dependabot/pip/group", "repo": {"full_name": REPO}}}
        self.assertEqual([], gate.validate_proof(pr, changed, REPO))
        pr["user"]["id"] = 123
        self.assertTrue(gate.validate_proof(pr, changed, REPO))

    def test_bot_has_no_arbitrary_workflow_exemption(self):
        changed = files(".github/workflows/test.yml")
        changed[0]["patch"] = "@@ -1 +1 @@\n-  run: python scripts/check.py\n+  run: echo passed"
        pr = {"changed_files": 1, "user": {"login": "dependabot[bot]", "id": 49699333, "type": "Bot"},
              "head": {"ref": "dependabot/github-actions/group", "repo": {"full_name": REPO}}}
        self.assertTrue(gate.validate_proof(pr, changed, REPO))
        changed[0]["patch"] = "@@ -1 +1 @@\n- uses: actions/checkout@" + "a" * 40 + "\n+ uses: actions/checkout@" + "b" * 40
        self.assertEqual([], gate.validate_proof(pr, changed, REPO))

    def test_local_cli_exit_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "body.md").write_text(body(), encoding="utf-8")
            (root / "files.json").write_text(json.dumps(files("kst/engine.py", "tests/test_new.py")), encoding="utf-8")
            argv = ["--body-file", str(root / "body.md"), "--files-file", str(root / "files.json"), "--head-sha", HEAD]
            self.assertEqual(0, gate.main(argv))
            (root / "body.md").write_text("spam", encoding="utf-8")
            self.assertEqual(1, gate.main(argv))


class FakeAPI:
    def __init__(self, change=False, invalid=False):
        self.calls = []
        self.reads = 0
        self.change = change
        self.invalid = invalid

    def call(self, path, data=None):
        self.calls.append((path, data))
        if data is not None: return {}
        if "/files?" in path:
            if self.invalid: raise ValueError("simulated malformed transport")
            return files("kst/engine.py", "tests/test_new.py")
        self.reads += 1
        result = {"state": "open", "head": {"sha": HEAD}, "body": body(), "changed_files": 2}
        if self.change and self.reads > 1: result["head"]["sha"] = "b" * 40
        return result


class LiveBoundaryTests(unittest.TestCase):
    def test_status_bound_to_head_and_success(self):
        api = FakeAPI()
        errors, checked = gate.check_live(api, REPO, 8, "https://example.org/run")
        self.assertEqual([], errors); self.assertTrue(checked)
        writes = [(path, data) for path, data in api.calls if data is not None]
        self.assertEqual(["pending", "success"], [x[1]["state"] for x in writes])
        self.assertTrue(all(path.endswith(HEAD) for path, _ in writes))

    def test_race_does_not_publish_success(self):
        api = FakeAPI(change=True)
        self.assertTrue(gate.check_live(api, REPO, 8, "https://example.org/run")[0])
        self.assertEqual("failure", api.calls[-1][1]["state"])

    def test_api_failure_is_not_a_pass(self):
        api = FakeAPI(invalid=True)
        with self.assertRaises(ValueError): gate.check_live(api, REPO, 8, "https://example.org/run")
        self.assertEqual("error", api.calls[-1][1]["state"])

    def test_token_and_private_error_body_not_printed(self):
        with patch.dict("os.environ", {"PR_NUMBER": "bad", "GH_TOKEN": "never-print-this"}):
            self.assertEqual(2, gate.main(["--live"]))

    def test_repository_path_validation(self):
        with self.assertRaises(ValueError): gate.GitHubAPI("../secrets", "token")
        api = gate.GitHubAPI(REPO, "token")
        with self.assertRaises(ValueError): api.call("https://external.invalid")


if __name__ == "__main__":
    unittest.main()

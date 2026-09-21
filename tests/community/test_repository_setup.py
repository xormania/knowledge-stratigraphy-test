"""No-account tests for the owner-side activation plan."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("configure_repository", ROOT / "scripts/configure_repository.py")
setup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(setup)


class FakeAdmin:
    def __init__(self, existing=False, admin=True, failure=False):
        self.calls = []
        self.existing, self.admin, self.failure = existing, admin, failure

    def __call__(self, method, path="", payload=None):
        self.calls.append((method, path, payload))
        if method == "GET" and not path:
            return {"full_name": setup.REPO, "permissions": {"admin": self.admin}}
        if method == "GET" and "rulesets?" in path:
            return [{"id": 42, "name": "kst-contribution-proof"}] if self.existing else []
        if path.startswith("/rulesets"):
            return {"id": 42, "enforcement": "active"}
        if self.failure and path == "/private-vulnerability-reporting":
            raise RuntimeError("simulated administration denial")
        return {}


class SetupTests(unittest.TestCase):
    def test_default_preview_never_calls_github(self):
        def forbidden(*args): raise AssertionError("network")
        self.assertEqual("preview", setup.configure(api=forbidden)["mode"])

    def test_admin_required_before_any_write(self):
        api = FakeAdmin(admin=False)
        with self.assertRaises(RuntimeError): setup.configure(True, api)
        self.assertTrue(all(c[0] == "GET" for c in api.calls))

    def test_create_requires_both_checks_and_owner_only_bypass(self):
        api = FakeAdmin()
        result = setup.configure(True, api)
        self.assertEqual([], result["failures"])
        rule = next(c[2] for c in api.calls if c[0] == "POST")
        self.assertEqual([127287135], [a["actor_id"] for a in rule["bypass_actors"]])
        checks = next(r for r in rule["rules"] if r["type"] == "required_status_checks")
        self.assertEqual({"Contribution proof", "Framework CI"}, {x["context"] for x in checks["parameters"]["required_status_checks"]})

    def test_rerun_updates_only_the_named_ruleset(self):
        api = FakeAdmin(existing=True)
        setup.configure(True, api)
        self.assertFalse(any(c[0] == "POST" for c in api.calls))
        self.assertTrue(any(c[0] == "PUT" and c[1] == "/rulesets/42" for c in api.calls))

    def test_partial_failure_is_visible(self):
        result = setup.configure(True, FakeAdmin(failure=True))
        self.assertEqual("/private-vulnerability-reporting", result["failures"][0]["operation"])


if __name__ == "__main__":
    unittest.main()

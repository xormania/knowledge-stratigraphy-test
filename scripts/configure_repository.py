#!/usr/bin/env python3
"""Preview/apply the personal-repository settings using an existing gh login.

No tokens are read or printed by this script. Nothing is changed without --apply.
Other rulesets are left alone. API failures are reported, never treated as success.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REPO = "xormania/knowledge-stratigraphy-test"


def gh(method, suffix="", payload=None):
    argv = ["gh", "api", "--method", method, f"repos/{REPO}{suffix}"]
    if payload is not None:
        argv += ["--input", "-"]
    result = subprocess.run(argv, input=None if payload is None else json.dumps(payload),
                            text=True, capture_output=True, timeout=60, check=False)
    if result.returncode:
        raise RuntimeError(f"GitHub rejected {method} {suffix or '/repository'}; inspect repository administration permissions.")
    return json.loads(result.stdout) if result.stdout.strip() else None


def configure(apply=False, api=gh):
    rules = json.loads((ROOT / ".github/repository-ruleset.json").read_text(encoding="utf-8"))
    settings = {"allow_squash_merge": True, "allow_merge_commit": False,
                "allow_rebase_merge": False, "delete_branch_on_merge": True, "has_issues": True}
    operations = [("PATCH", "", settings),
                  ("PUT", "/actions/permissions/workflow", {"default_workflow_permissions": "read", "can_approve_pull_request_reviews": False}),
                  ("PUT", "/actions/permissions/fork-pr-contributor-approval", {"approval_policy": "all_external_contributors"}),
                  ("PUT", "/private-vulnerability-reporting", None)]
    if not apply:
        return {"mode": "preview", "repository": REPO, "ruleset": rules, "settings": operations,
                "note": "No changes made. --apply requires existing gh authentication with repository administration access."}
    meta = api("GET")
    if meta.get("full_name") != REPO or not meta.get("permissions", {}).get("admin"):
        raise RuntimeError("The existing gh identity must administer this exact repository.")
    existing = []
    for page in range(1, 101):
        chunk = api("GET", f"/rulesets?includes_parents=false&per_page=100&page={page}")
        existing.extend(chunk)
        if len(chunk) < 100:
            break
    else:
        raise RuntimeError("Ruleset listing exceeded the safety limit; no writes performed.")
    matching = [r for r in existing if r["name"] == rules["name"]]
    if len(matching) > 1:
        raise RuntimeError("Duplicate project rulesets require owner reconciliation; no writes performed.")
    suffix = f'/rulesets/{matching[0]["id"]}' if matching else "/rulesets"
    rule_result = api("PUT" if matching else "POST", suffix, rules)
    results = [{"operation": "ruleset", "id": rule_result["id"], "enforcement": rule_result.get("enforcement")}]
    failures = []
    for method, path, payload in operations:
        try:
            api(method, path, payload)
            results.append({"operation": path or "repository merge settings", "status": "applied"})
        except (RuntimeError, OSError, ValueError, subprocess.TimeoutExpired) as error:
            failures.append({"operation": path, "error": str(error)})
    installed = api("GET", f'/rulesets/{rule_result["id"]}')
    if installed.get("enforcement") != "active":
        failures.append({"operation": "ruleset verification", "error": "Ruleset not active"})
    return {"mode": "applied", "repository": REPO, "results": results, "failures": failures,
            "note": "Verify a real PR shows both required checks. Actions event policies and security scanning are separate owner checks; no policy was weakened."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = configure(args.apply)
        print(json.dumps(result, indent=2))
        return 1 if result.get("failures") else 0
    except (RuntimeError, OSError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

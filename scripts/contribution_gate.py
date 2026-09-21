#!/usr/bin/env python3
"""Trusted, metadata-only PR proof gate. Never executes submitted commands/code."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import PurePosixPath, Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

CONTEXT = "Contribution proof"
KINDS = {"bugfix", "feature", "refactor", "tests", "docs", "probe", "adapter", "dependency", "ci"}
START, END = "<!-- kst-proof -->", "<!-- /kst-proof -->"
SHA = re.compile(r"[0-9a-f]{40}\Z")
PLACEHOLDER = re.compile(r"^(?:replace\b|todo\b|tbd\b|insert\b|your .* here|n/?a\Z|\.\.\.\Z)", re.I)


def substantive(value: object, minimum: int = 12) -> bool:
    return isinstance(value, str) and len(value.strip()) >= minimum and not PLACEHOLDER.match(value.strip())


def dependency_only(pr: dict, files: list[dict], repository: str) -> bool:
    """Narrow exemption for real Dependabot pin updates, not arbitrary bot code."""
    user = pr.get("user", {})
    head = pr.get("head", {})
    if not (user.get("login") == "dependabot[bot]" and user.get("id") == 49699333
            and user.get("type") == "Bot" and head.get("repo", {}).get("full_name") == repository
            and head.get("ref", "").startswith("dependabot/") and files):
        return False
    for file in files:
        path, patch = file["filename"], file.get("patch")
        if file.get("status") != "modified" or not isinstance(patch, str):
            return False
        minus = [s[1:].strip() for s in patch.splitlines() if s.startswith("-") and not s.startswith("---")]
        plus = [s[1:].strip() for s in patch.splitlines() if s.startswith("+") and not s.startswith("+++")]
        if not minus or len(minus) != len(plus):
            return False
        if path == "requirements-test.txt":
            pattern = r"([A-Za-z0-9_.-]+)==[0-9]+(?:\.[0-9]+)*(?:[a-z0-9.]*)"
        elif path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml")):
            pattern = r"-?\s*uses:\s*(actions/(?:checkout|setup-python|upload-artifact))@[0-9a-f]{40}(?:\s+#.*)?"
        else:
            return False
        for old, new in zip(minus, plus):
            a, b = re.fullmatch(pattern, old), re.fullmatch(pattern, new)
            if not a or not b or a.group(1) != b.group(1) or old == new:
                return False
    return True


def validate_proof(pr: dict, files: list[dict], repository: str) -> list[str]:
    """Validate declarations and file scope, not the truth of prose or test output."""
    errors: list[str] = []
    if len(files) != pr.get("changed_files") or not files:
        return ["Complete, nonempty changed-file metadata is required."]
    paths: set[str] = set()
    for file in files:
        name = file.get("filename")
        if not isinstance(name, str) or name.startswith("/") or ".." in PurePosixPath(name).parts:
            return ["Invalid changed-file metadata."]
        paths.add(name)
        if file.get("previous_filename"):
            paths.add(file["previous_filename"])
        if file.get("status") != "removed" and (
            name.startswith(("runs/", "results/")) and name.endswith((".jsonl", ".zip", ".log"))
            or PurePosixPath(name).name == ".env" or name.endswith((".pem", ".key", ".p12", ".pfx"))
        ):
            errors.append("Do not commit credentials or raw run artifacts; use sanitized test fixtures.")
    if dependency_only(pr, files, repository):
        return errors
    body = pr.get("body") or ""
    if not isinstance(body, str) or len(body) > 100000 or body.count(START) != 1 or body.count(END) != 1 or body.find(END) < body.find(START):
        return errors + ["Provide exactly one kst-proof JSON block from the PR template."]
    fragment = body.split(START, 1)[1].split(END, 1)[0].strip()
    match = re.fullmatch(r"```json\s*\n(.*?)\n```", fragment, re.S)
    if not match:
        return errors + ["The kst-proof block must contain one fenced JSON object."]
    try:
        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError("duplicate JSON key")
                result[key] = value
            return result
        proof = json.loads(match.group(1), object_pairs_hook=unique)
    except (ValueError, RecursionError):
        return errors + ["Proof JSON is invalid or contains duplicate keys."]
    if not isinstance(proof, dict):
        return errors + ["Proof must be a JSON object."]
    required = {"kind", "tested_commit", "baseline", "change", "verification", "limitations"}
    if set(proof) - required - {"sources"} or required - set(proof):
        errors.append("Use the required proof fields; only sources is optional.")
    kind = proof.get("kind")
    if not isinstance(kind, str) or kind not in KINDS:
        errors.append("Choose a documented contribution kind.")
    tested = proof.get("tested_commit")
    if not isinstance(tested, str) or not SHA.fullmatch(tested) or tested != pr.get("head", {}).get("sha"):
        errors.append("tested_commit must equal the current full PR head SHA; refresh evidence after new commits.")
    for key in ("baseline", "change", "limitations"):
        if not substantive(proof.get(key)):
            errors.append(f"{key} needs a concrete, non-placeholder explanation.")
    verification = proof.get("verification")
    if not isinstance(verification, list) or not 1 <= len(verification) <= 20:
        errors.append("verification needs 1–20 command/result/evidence records.")
        verification = []
    for item in verification:
        if not isinstance(item, dict) or set(item) != {"command", "result", "evidence"} or not all(
            substantive(item.get(k), 4 if k == "command" else 12) for k in ("command", "result", "evidence")
        ):
            errors.append("Each verification needs a specific command, actual result, and inspectable evidence reference.")
    docs_only = all(PurePosixPath(p).suffix.lower() in {".md", ".rst"} for p in paths)
    if kind == "docs" and not docs_only:
        errors.append("docs is only valid for Markdown/reStructuredText-only changes.")
    if not docs_only:
        commands = [v.get("command", "") for v in verification if isinstance(v, dict) and isinstance(v.get("command"), str)]
        for script in ("scripts/check.py", "scripts/package_smoke.py"):
            if not any(re.fullmatch(r"python(?:3(?:\.\d+)?)?\s+" + re.escape(script), c.strip()) for c in commands):
                errors.append(f"Non-documentation changes must report the standard command: python {script}")
    runtime = any(p.startswith("kst/") or p == "stratify.py" for p in paths)
    changed_tests = [f["filename"] for f in files if f.get("status") != "removed"
                     and f["filename"].startswith("tests/") and f["filename"].endswith(".py")]
    if runtime and not changed_tests:
        errors.append("Runtime/schema changes must include added or updated regression tests.")
    if kind == "adapter" and not all(any(p.startswith(folder) for p in changed_tests)
                                     for folder in ("tests/contracts/", "tests/behavior/")):
        errors.append("Adapter contributions need contract and failure-path behavior tests.")
    probe_change = kind == "probe" or any(p.startswith(("packs/", "examples/")) and p.endswith(".json") for p in paths)
    if probe_change:
        sources = proof.get("sources", [])
        if not isinstance(sources, list) or not sources:
            errors.append("Probe changes need dated public sources, or explicit synthetic-fixture provenance.")
        else:
            for source in sources:
                if isinstance(source, dict) and source.get("synthetic") is True and substantive(source.get("reason")):
                    continue
                try:
                    url = urlparse(source["url"])
                    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", source["observed_date"]):
                        raise ValueError("Invalid date format")
                    date.fromisoformat(source["observed_date"])
                    valid = url.scheme == "https" and bool(url.netloc) and not url.username and not url.password
                except (TypeError, KeyError, ValueError):
                    valid = False
                if not valid:
                    errors.append("Each source needs an HTTPS URL and YYYY-MM-DD observed_date, or a synthetic reason.")
    return errors


class GitHubAPI:
    def __init__(self, repository: str, token: str):
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9_.-]+", repository) or any(p in {".", ".."} for p in repository.split("/")):
            raise ValueError("Invalid repository identifier")
        self.root = f"https://api.github.com/repos/{repository}"
        self.token = token

    def call(self, path: str, data=None):
        if not path.startswith("/") or ".." in path or "://" in path:
            raise ValueError("Invalid API path")
        payload = None if data is None else json.dumps(data).encode()
        request = Request(self.root + path, data=payload, headers={
            "Authorization": "Bearer " + self.token, "Accept": "application/vnd.github+json",
            "Content-Type": "application/json", "User-Agent": "kst-contribution-proof",
        })
        with urlopen(request, timeout=20) as response:
            raw = response.read(4_000_001)
        if len(raw) > 4_000_000:
            raise ValueError("Oversized API response")
        return json.loads(raw)


def check_live(api, repository: str, number: int, run_url: str) -> tuple[list[str], bool]:
    pr = api.call(f"/pulls/{number}")
    if pr.get("state") != "open":
        return [], False
    sha = pr["head"]["sha"]
    if not SHA.fullmatch(sha):
        raise ValueError("Invalid head SHA")
    def publish(state, description):
        api.call(f"/statuses/{sha}", {"state": state, "context": CONTEXT,
                 "description": description[:140], "target_url": run_url})
    publish("pending", "Checking current-head proof and changed-file scope")
    files = []
    try:
        for page in range(1, 31):
            chunk = api.call(f"/pulls/{number}/files?per_page=100&page={page}")
            if not isinstance(chunk, list):
                raise ValueError("Invalid file list")
            files.extend(chunk)
            if len(chunk) < 100:
                break
        errors = validate_proof(pr, files, repository)
        fresh = api.call(f"/pulls/{number}")
        if fresh.get("head", {}).get("sha") != sha or fresh.get("body") != pr.get("body"):
            publish("failure", "PR changed during validation; rerun contribution-policy")
            return ["PR changed during validation; rerun contribution-policy."], True
        publish("failure" if errors else "success", "Proof incomplete: inspect workflow summary" if errors
                else "Proof declarations valid; CI and maintainer review remain required")
        return errors, True
    except (ValueError, KeyError, TypeError, HTTPError, URLError, TimeoutError):
        publish("error", "Proof validation failed to complete; rerun contribution-policy")
        raise


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--body-file", type=Path)
    parser.add_argument("--files-file", type=Path)
    parser.add_argument("--head-sha")
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", "xormania/knowledge-stratigraphy-test"))
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.live:
            number = int(os.environ["PR_NUMBER"])
            if number < 1:
                raise ValueError("Invalid PR number")
            run_id = os.environ["GITHUB_RUN_ID"]
            if not run_id.isdigit():
                raise ValueError("Invalid run ID")
            api = GitHubAPI(args.repository, os.environ["GH_TOKEN"])
            errors, _ = check_live(api, args.repository, number,
                                  f"https://github.com/{args.repository}/actions/runs/{run_id}")
        else:
            if not args.body_file or not args.files_file or not args.head_sha:
                parser.error("local checks need --body-file, --files-file, and --head-sha")
            files = json.loads(args.files_file.read_text(encoding="utf-8"))
            pr = {"body": args.body_file.read_text(encoding="utf-8"), "head": {"sha": args.head_sha},
                  "changed_files": len(files)}
            errors = validate_proof(pr, files, args.repository)
    except (OSError, ValueError, KeyError, TypeError) as error:
        # Do not print HTTP bodies, tokens, raw PR prose, or submitted commands.
        print("Contribution proof could not be checked: " + type(error).__name__, file=sys.stderr)
        return 2
    report = "Contribution proof: " + ("FAIL\n" + "\n".join("- " + e for e in errors) if errors else "PASS")
    print(report)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as stream:
            stream.write(report + "\n\nThis checks declarations, not their truth. CI and owner review are separate.\n")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

# Contributing

Useful contributions are welcome: reproducible bugs, good tests, clearer documentation,
well-sourced probes, and harness integrations with evidence. You do not need an invitation,
a particular model subscription, a public real name, or a long GitHub history.

This is a personally maintained project. **xor (`@xormania`) makes scope and merge
decisions.** Passing checks makes a contribution reviewable, not automatically accepted.

## Start small, reuse what exists

For small fixes, send a focused PR directly. Discuss a new dependency, major redesign,
new native adapter, public interface change, or broad probe corpus in an issue before
investing heavily. This avoids competing implementations and wasted work, not contribution.

Keep knowledge content in packs, selection in targets, native I/O in adapters, and
interpretation in reports. Do not add vendor-specific rules to the planner or model-name
enums. Historical documents are source material; current owner direction controls scope.

## Evidence, not assurances

The PR template contains one `kst-proof` JSON block. Keep its markers and provide:

| Field | What belongs here |
| --- | --- |
| `kind` | `bugfix`, `feature`, `refactor`, `tests`, `docs`, `probe`, `adapter`, `dependency`, or `ci` |
| `tested_commit` | Full current PR head SHA from `git rev-parse HEAD` |
| `baseline` | Reproduction and prior outcome, missing behavior, or the exact documentation error |
| `change` | What changes and what existing capability is reused; explain a new dependency |
| `verification` | Command, actual result, and an inspectable test/log/CI reference for each check |
| `limitations` | Risks, untested cases, and mock-versus-live boundaries; be specific even when none are known |
| `sources` | Required for probe changes: dated source records or declared synthetic provenance |

Non-documentation changes report both standard commands:

```bash
python -m pip install -r requirements-test.txt -e .
python scripts/check.py
python scripts/package_smoke.py
```

For runtime/schema changes, include added or updated regression tests. A bugfix should
show the failing behavior before the fix and passing behavior afterward. A feature
should test its acceptance behavior. Native adapters need offline transport doubles,
contract tests under `tests/contracts/`, and failure-path tests under `tests/behavior/`.
A new event shape needs versioning and migration notes; never rewrite old evidence.

Markdown/reStructuredText-only fixes may use `kind: docs` and a short manual verification
record instead of pretending to have run code. Say what you rendered, compared, or checked.
Do not use `docs` to conceal executable or configuration changes.

Probe `sources` use records like:

```json
{"url":"https://example.org/dated-primary-source","observed_date":"2026-09-01"}
```

For invented fixtures, use `{"synthetic":true,"reason":"Invented fixture; no empirical knowledge claim."}`.
Distinguish event date from publication/observation date, document contamination and
licensing, and avoid leaking answer keys into target prompts. Sources need maintainer
review; the gate does not fetch or certify them.

## What the checks enforce

`Contribution proof` rejects missing/placeholder proof, stale commit binding, incomplete
file metadata, misleading docs scope, missing runtime regressions, and missing adapter
or probe evidence. It also rejects obvious credential/raw-run artifact paths. Its errors
explain how to repair a PR; it does not automatically close contributions.

`Framework CI` aggregates the complete offline OS/Python matrix and packaging checks.
The metadata gate runs trusted default-branch code and treats PR text/diffs only as data.
**Neither a JSON declaration nor a green build proves that prose is true or a feature is
useful.** The maintainer checks relevance, reproduces important claims, and reviews changes.
Repository settings must require these checks to make them merge-blocking; see
[activation and verification](docs/REPOSITORY-SETUP.md).

Real Dependabot version-pin-only updates have a narrow metadata exemption; CI and review
still apply. Arbitrary bot code, changed shell steps, and names imitating Dependabot do not.

## Keep evidence honest and safe

Default tests must stay synthetic/offline and require no account, paid model, global
harness changes, credentials, or permission bypass. Live acceptance is separate and opt-in.
Requested identity is not observed identity. Missing evidence stays unknown. Do not present
an empty working directory or read-only sandbox as proof of complete isolation.

Preserve useful sanitized evidence, not secrets or other people's conversations. Put small
sanitized fixtures under `tests/`; do not upload raw `runs/` or `results/` archives. This
filename check is not a secret scanner, so inspect every diff yourself.

AI assistance is allowed. Submitters must understand the changes, reproduce the claims,
and identify borrowed material and its license. We do not require a CLA or real-name
sign-off; contributions are offered under the repository's existing MIT license, with
third-party notices retained where required.

## What gets declined

Unrelated promotion, copied issues, fabricated results, bulk cosmetic churn, untested
code dumps, and repetitive off-scope PRs may be closed with a reason. Small legitimate
fixes and first-time contributors are welcome. Repairable omissions get actionable
feedback; repeated abuse can be moderated under the [Code of Conduct](CODE_OF_CONDUCT.md).
There is no automatic stale bot closing useful work merely because the maintainer is busy.

See [support](SUPPORT.md), [security reporting](SECURITY.md), and [governance](GOVERNANCE.md).

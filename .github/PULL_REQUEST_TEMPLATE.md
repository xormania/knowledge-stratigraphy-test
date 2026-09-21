## Problem and scope

Explain the observable problem and the smallest useful change. Link an issue when one
exists; a separate issue is not required for a small bug or documentation fix.

## Proof

Replace every `REPLACE` value. See [CONTRIBUTING.md](../CONTRIBUTING.md).
`tested_commit` is the full output of `git rev-parse HEAD`; update proof after pushing
new commits. Provide real commands, actual outcomes, and test paths or CI/log references.
Do not paste secrets, private conversations, raw run archives, or invented results.

<!-- kst-proof -->
```json
{
  "kind": "bugfix",
  "tested_commit": "REPLACE with the full current PR head SHA",
  "baseline": "REPLACE with the failing reproduction, missing behavior, or documented error",
  "change": "REPLACE with what changed and which existing capability you reused",
  "verification": [
    {
      "command": "python scripts/check.py",
      "result": "REPLACE with the actual outcome",
      "evidence": "REPLACE with a relevant test path, CI run, or sanitized log reference"
    },
    {
      "command": "python scripts/package_smoke.py",
      "result": "REPLACE with the actual outcome",
      "evidence": "REPLACE with an inspectable result reference"
    }
  ],
  "limitations": "REPLACE with known risks, untested cases, and mock-versus-live boundaries"
}
```
<!-- /kst-proof -->

## Review notes

Flag schema/API changes, new dependencies, attribution/licensing, and any changes to
workflows, permissions, or this contribution policy. AI-assisted work is welcome;
the submitting person remains responsible for understanding and verifying the result.

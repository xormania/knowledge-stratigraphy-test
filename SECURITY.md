# Security policy

## Supported scope

Report reproducible security defects in the current default branch or latest release.
Older versions do not have a separate maintenance commitment. A missing knowledge answer,
unverified model identity, or low benchmark score is not itself a vulnerability.

Relevant concerns include credential leakage, unsafe harness invocation, answer-key or
private-data exposure, untrusted workflow execution, and evidence-integrity failures.
Test only systems and accounts you own or are authorized to assess. Never attack hosted
providers, other contributors, or production data to demonstrate a defect here.

## Private reporting

Use **Security → Advisories → Report a vulnerability** when the repository's private
reporting feature is enabled. Give affected versions/commits, a minimal reproduction,
impact, and a sanitized proof. Do not put exploit details or credentials in public issues.

If that button is absent, open a minimal issue asking `@xormania` to enable a private
reporting channel, without vulnerability details. The repository setup procedure enables
the feature, but the presence of this file alone does not prove it is active.

No bounty, fixed response deadline, or remediation SLA is promised. Disclose responsibly
and coordinate a fix before public technical details where practical.

## Operational boundaries

Mock CI does not validate native harness security or sandbox isolation. Do not expose
live provider credentials to PRs. Never run fork code or commands copied from a PR body
in a privileged workflow. The contribution gate is metadata-only; code tests have a
read-only token and no provider secrets. Raw transcripts and archives can contain private
content even after automatic redaction; review them before sharing.

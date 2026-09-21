# Owner activation and verification

## What is installed versus what needs administration access

The repository contains contribution/community files, structured issue forms, a PR proof
template, a trusted metadata validator, offline tests, grouped Dependabot updates, and
CI checks. **Those files alone do not make checks merge-blocking.**

On 2026-09-21 the ChatGPT GitHub integration returned HTTP 403 for branch-administration
access. Required-check enforcement and private vulnerability reporting were therefore
not activated or claimed active by that session.

## Apply the prepared personal-repository settings

From a trusted checkout and an existing GitHub CLI login that administers this repo:

```bash
python scripts/configure_repository.py          # local preview; no network or changes
python scripts/configure_repository.py --apply  # explicit owner-side activation
```

The script creates or updates only the named `kst-contribution-proof` ruleset; unrelated
rulesets stay untouched. Existing rules can still impose additional restrictions. The
plan targets the default branch, requires `Contribution proof` and `Framework CI` from
GitHub Actions, requires PRs and code-owner review, resolves review threads, and prevents
ordinary force pushes/deletion. It selects squash-only merges and deletes merged branches.
Only `@xormania` is explicitly exempted, preserving owner maintenance authority without
an artificial second reviewer. The generic approving-review count stays zero; outside
changes still require the designated code owner's approval.

It also requests read-only default workflow permissions, disables Actions approving PRs,
requires approval before external fork workflows run, and enables private vulnerability
reporting. Each failure is reported. It does not upload credentials, install apps, alter
authentication, change repository visibility, or weaken any Actions event policy.
Review the JSON plan before applying; this script was unit-tested with mocked API calls,
not exercised with repository-administration credentials in the authoring session.

## Verify the actual merge gate

Open a legitimate test PR from a non-owner account or use the next real contribution.
A missing proof block should produce a failing `Contribution proof` status on the PR
head. Fill it with current-head evidence: the metadata status should pass, but merging
should still need green `Framework CI` and owner review. Push another commit: the stale
`tested_commit` must fail until updated. A body-only edit must rerun the policy check.
Confirm both checks appear as **required** in GitHub; a green optional check is not a gate.
Do not approve or merge a deliberately invalid contribution to test this.

## Trusted workflow boundary

`contribution-policy.yml` uses `pull_request_target` solely to run the trusted default-
branch validator, fetch PR metadata, and post a head-bound status. It never checks out
fork/head code, installs PR dependencies, runs submitted commands, imports artifacts,
or injects PR text into a shell. The only write permission is commit statuses.

`framework-ci` runs untrusted candidate code separately with a read-only token and no
provider secrets. Its aggregate `Framework CI` job fails unless the whole matrix passes.
Workflow/policy changes still need careful owner review; status checks are not substitutes
for examining a change that modifies its own testing rules.

GitHub's documented default policy for public `pull_request_target` workflows is under
rollout, with enforcement announced for November 2, 2026. Check repository Actions policy
insights. If this trusted metadata-only workflow is blocked, explicitly allow the intended
policy or leave PRs blocked pending a replacement; do not enable fork code in privileged
runs or disable the proof requirement to make the error disappear. The setup script
intentionally does not relax event policies automatically.

## Community and security checklist

| Item | Repository support / owner verification |
| --- | --- |
| README and MIT license | Existing files retained |
| Contribution instructions and PR template | `CONTRIBUTING.md`, `.github/PULL_REQUEST_TEMPLATE.md` |
| Conduct, support, governance | Root policy files; no fake private contact or support SLA |
| Structured issues | Bug, proposal, probe, and question forms; blank issues disabled |
| Ownership | `.github/CODEOWNERS` routes review to `@xormania` |
| Proof and CI | Workflows installed; make checks required using the activation plan |
| Dependency maintenance | Weekly grouped minor/patch tool updates; majors still reviewed separately |
| Vulnerability reports | `SECURITY.md`; verify **Report a vulnerability** actually appears |
| Fork safety | Verify external workflow approval and read-only default tokens |
| Secret protection | Enable/verify secret scanning and push protection in repository Security settings |
| Code scanning | Consider GitHub default CodeQL setup for Python and Actions; not enabled by these files |
| Discussions | Optional; issue question form works without another community surface |
| Moderation | No bulk auto-closing of old or first-time contributions; owner handles repeated spam |

No funding link, chat server, new maintainer, CLA, paid service, or auto-merge bot is created.

## Primary references

- https://docs.github.com/en/rest/repos/rules
- https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target
- https://docs.github.com/en/rest/actions/permissions
- https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository
- https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/about-community-profiles-for-public-repositories

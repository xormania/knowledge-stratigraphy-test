# Validation record — foundation 0.2.0

Local validation performed on 2026-09-21 using Python 3.13.5 on Linux.

| Check | Observed outcome |
| --- | --- |
| `python scripts/check.py` | 99 tests passed |
| Coverage with branch measurement enabled | 99.41%; required threshold 90% |
| JSON Schema validation and synthetic example validation | Passed |
| `python scripts/package_smoke.py` | Wheel built, installed into a separate directory, validated and completed a six-trial mock run outside the source checkout |
| Real model or native harness sessions | Not run; no empirical model claim |

The committed CI workflow runs the same checks on its declared OS/Python matrix.
This local record does not assert that hosted jobs have already passed; use the
workflow run associated with the final commit for that evidence.

Mock failures are deliberately simulated. The test suite does not yet certify native
transport compatibility, hard preemption of a hung adapter, OS-enforced isolation,
model identity, or empirical knowledge-frontier validity.

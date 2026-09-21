# Testing the framework

## Run the same gate locally and in CI

```bash
python -m pip install -r requirements-test.txt -e .
python scripts/check.py
python scripts/package_smoke.py
```

The first command installs the pinned direct test toolchain. Installation may use the
network. The actual tests are offline and require no account, harness installation,
model SDK, provider credential, or paid inference call.

## Test layers

| Layer | Location | Main assertions |
| --- | --- | --- |
| Unit | `tests/unit/` | Real schema validation, identifiers, deterministic plans, target independence, ledger integrity, rescoring, metric denominators |
| Behavior | `tests/behavior/` | Public CLI, blind export, exact manual capture, complete mock runs, timeouts, failures, cancellation, cleanup, honest unknowns |
| Adapter contract | `tests/contracts/` | Lifecycle contract, narrow target payload, schema-valid captures, registry behavior |
| Compatibility | `tests/test_stratify.py` | Named and future harness/model combinations remain data |
| Packaging | `scripts/package_smoke.py` | Installed wheel finds its bundled schemas/fixtures and runs outside the source tree |

Pytest markers allow focused runs: `python -m pytest -m unit`, `-m behavior`, or
`-m contract`. The full gate remains authoritative for a change.

## Deterministic doubles, not real-model assertions

Synthetic fixture content has no empirical cutoff meaning. Mock responses are configured
independently of answer keys. Faults cover unsupported configuration, startup, submission,
timeout, empty output, cleanup, and cancellation. Behavior tests also inject malformed
captures, mismatched sessions/modes, reused session IDs, corrupt telemetry, and storage
failures. They check resulting state and evidence, not only that a function was called.

The test process blocks normal socket connection calls. Real subprocess entry-point
smokes only execute the mock-only validation path. This is an offline test safeguard,
not a security sandbox; native transport integrations need their own offline process
fixtures before being added to the default suite.

## Coverage and CI

Branch measurement is enabled and combined coverage must stay at or above 90%.
Coverage is a regression signal, not proof of correctness. Assertions around blinding,
identity provenance, failed-vs-unknown outcomes, and append-only scoring are mandatory
even when a numerical gate passes.

CI runs Linux/Python 3.10, 3.12, 3.13, 3.14 and Windows/macOS with Python 3.13.
Every job runs the checks and installed-wheel smoke. Jobs retain JUnit/coverage XML on
success or failure. Actions are SHA-pinned, checkout credentials are not persisted,
workflow permissions are read-only, and no provider secrets are requested.

Live native acceptance tests will remain explicit, separate, and opt-in. Passing mocks
does not certify a vendor interface or prove that a particular model was selected.

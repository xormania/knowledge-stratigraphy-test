# Knowledge Stratigraphy Test

**A reusable measurement framework, independent of today's models and harnesses.**

```text
Probe pack × Target set × Repetitions
                 │
          Harness × Model × Runtime
                 │
       Blinded execution through an adapter
                 │
      Append-only observations and scores
                 │
       Rebuildable comparison reports
```

The project investigates effective knowledge differences and possible routing changes.
It does not identify a backend or infer a training cutoff from a single answer.

## Foundation status — 0.2.0

The reusable Python package, deterministic planner, adapter protocol, fault-injectable
mock, manual capture workflow, validated event ledger, scoring, and reporting are
implemented. Defaults use **synthetic probes and mock targets**, with no model calls.

**Native Codex, Claude Code, and Grok Build automation is not implemented here yet.**
All can be measured through manual prompt export and capture now. The adapter boundary
is ready for native implementations without changing probe or scoring semantics.
The [multi-harness proof](https://github.com/xormania/multi-harness-proof) remains the
reference for native transport and identity-observation mechanics.

## Install and verify

Python 3.10 or later:

```bash
python -m venv .venv
# Activate .venv using your shell's normal activation command.
python -m pip install -r requirements-test.txt -e .
python scripts/check.py
python scripts/package_smoke.py
```

`check.py` runs compilation, unit tests, behavior tests, adapter-contract tests,
branch-enabled coverage with a **90% gate**, and example validation. The packaging
check builds a wheel and executes it from outside the source tree.

For runtime use without test dependencies: `python -m pip install -e .`.
The runtime uses `jsonschema` for Draft 2020-12 validation; no model SDK is required.

## Run the complete mock pipeline

```bash
python stratify.py validate
python stratify.py matrix --repetitions 2 --seed 42
python stratify.py run --output runs/demo --repetitions 2 --seed 42
python stratify.py report runs/demo/events.jsonl
```

The installed `kst` command and `python -m kst` expose the same CLI.
Every run directory must be new. A mock answer is labeled `mock`, never a model result.
Execution success is not a knowledge score: observations remain unscored until reviewed.

## Use any harness and model

Targets are data, not an allowlist. `targets.example.json` retains the initial manual
examples for Claude Code/Fable, Claude Code/Opus, Codex/ChatGPT, and Grok Build/Grok.
Those are descriptive labels, not promises that a particular native model ID exists.
Add another target with the model identifier supported by its actual runtime.

```bash
python stratify.py --targets targets.example.json targets
python stratify.py --pack path/to/pack.json --targets targets.example.json \
  export --output runs/blind-battery --repetitions 3 --seed 42
```

`blind/` contains prompts with opaque filenames. `manifest.json` is controller-only
mapping data. Give the target **one prompt in one fresh session**, not the manifest,
answer keys, source pack, previous answers, or telemetry. This protects the payload;
it is not an operating-system sandbox around a future native harness.

Capture an answer using the pack/probe and target IDs from your private manifest:

```bash
python stratify.py --pack path/to/pack.json --targets targets.example.json \
  record PROBE_ID --target-id TARGET_ID --run-id RUN_ID \
  --output results/RUN_ID.jsonl < response.txt
```

Use `--prompt-file actual-prompt.txt` when the submitted wording differs. Responses
are preserved exactly, including whitespace. Omitted isolation observations remain
`unknown`; configured intent is never promoted to observed isolation.

The command prints a trial ID. Record or revise its assessment separately:

```bash
python stratify.py score results/RUN_ID.jsonl TRIAL_ID 2 \
  --scorer xor --rubric-version manual-v1 --assessment recognized
python stratify.py report results/RUN_ID.jsonl
```

That example is for a positive probe. A fully rejected negative control uses
`--assessment rejected`. Score revisions append events and retain earlier judgments.
See `python stratify.py record --help` for explicit native identity, token, latency,
and isolation fields.

## What is separated

| Concern | Implementation |
| --- | --- |
| Validation, identities, reproducible experiment plans | `kst/core.py` |
| Narrow target-facing request and adapter contract | `kst/adapters.py` |
| Fresh-trial orchestration, failure classification, cleanup | `kst/engine.py` |
| Append-only, hash-linked events and score revisions | `kst/telemetry.py` |
| Per-probe reports without mixing mock/manual/live observations | `kst/analysis.py` |
| CLI and manual import/export | `kst/cli.py` |
| Machine-enforced JSON Schemas and synthetic fixtures | `kst/data/` |

## Testing and CI

The default suite is offline. Unit tests cover validation, identity, planning, and
storage. Behavior tests exercise CLI capture, export, full mock runs, scoring, reports,
and failure recovery. Adapter-contract tests specify the boundary future integrations
must satisfy using offline doubles.

GitHub Actions runs Python 3.10, 3.12, 3.13, and 3.14 on Linux, plus Python 3.13 on
Windows and macOS. It checks coverage and packaging and retains JUnit/coverage reports,
including failures. Action revisions and direct test dependencies are pinned.
No native harness, provider credentials, or paid calls are needed by CI.

[Testing](TESTING.md) · [Architecture](ARCHITECTURE.md) · [Adapter contract](ADAPTERS.md) ·
[Telemetry](TELEMETRY.md) · [Contributing](CONTRIBUTING.md) ·
[Migration notes](docs/MIGRATION-0.2.md) · [Validation record](VALIDATION.md)

## Historical probe material

The original Codex-reset pack and `EVIDENCE.md` are retained as historical construction
material. Their source claims and dates have **not been reverified in this framework
refactor**. They are not the default fixtures and do not establish empirical results.
Future empirical packs need their own evidence review and contamination tracking.

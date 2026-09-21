# Knowledge Stratigraphy Test

A black-box framework for estimating an LLM's **effective knowledge frontier** and detecting silent model/routing changes.

The framework is intentionally independent of both **harness** and **model**.

```text
Probe Pack × Target Set × Repetitions
```

where:

```text
Target = Harness × Requested Model × Runtime
```

So the same pack can be tested through Claude Code, Codex, Grok Build, a web app, an API client, or a future harness, using ChatGPT, Grok, Fable, Opus, or future models.

This is not an intelligence benchmark and cannot prove backend identity. It is a behavioral fingerprinting and measurement method.

## Core concept

Instead of asking whether a model knows one obscure fact, test a sequence of **dated, obscure, relational facts from a constrained domain**.

A useful probe tends to be:

- **recent** enough to separate knowledge frontiers;
- **obscure** enough that recognition is informative;
- **relational** enough that guessing one entity name is insufficient;
- **source-grounded** so the stratum date can be justified;
- paired with **negative controls** to detect confabulation.

The output is a profile across strata, not a binary pass/fail.

## Harnesses and models are independent

Do not collapse "Claude Code/Fable" or "Codex/ChatGPT" into one identity.

The framework records separately:

- harness requested;
- harness version/build;
- model requested;
- reasoning/effort requested;
- model actually observed, when native evidence exists;
- reasoning/effort actually observed;
- route/backend identity if exposed.

**Requested is not observed.**

The confirmed [multi-harness proof](https://github.com/xormania/multi-harness-proof) demonstrated why this matters: native telemetry can expose settings different from the launch request.

See [TARGETS.md](TARGETS.md).

## Universal execution

The baseline adapter is **manual**.

That is intentional: any new harness/model combination can be tested immediately without framework code changes.

Optional native adapters can later automate session creation, model selection, clean workspaces, prompt delivery, response capture, and native identity evidence for specific harnesses.

Probe packs do not depend on adapters.

## Repository structure

- `ARCHITECTURE.md` — framework layers and improvement loop.
- `TARGETS.md` — harness × model × runtime abstraction.
- `PROTOCOL.md` — controlled execution and scoring.
- `TELEMETRY.md` — requested-vs-observed telemetry and analysis dimensions.
- `schemas/probe-pack.schema.example.json` — generic pack structure.
- `schemas/target.schema.example.json` — generic target structure.
- `schemas/telemetry.schema.example.json` — append-only trial telemetry.
- `targets.example.json` — example targets for current harness/model combinations.
- `examples/` — worked probe packs.
- `results/` — optional raw JSONL run records.
- `stratify.py` — zero-dependency prompt, matrix, target, and telemetry helper.
- `EVIDENCE.md` — source evidence for the first worked pack.

## Quick start

List probes:

```bash
python3 stratify.py list
```

List enabled targets:

```bash
python3 stratify.py targets
```

Inspect one target:

```bash
python3 stratify.py target claude-code-fable
```

Expand a randomized experiment matrix:

```bash
python3 stratify.py matrix --repetitions 3 --seed 42
```

Print one blinded probe:

```bash
python3 stratify.py prompt KST-CODEX-2026-07-PUSHED
```

Create run metadata for one target:

```bash
python3 stratify.py new-run --target-id claude-code-fable
```

Record a response append-only:

```bash
printf '%s' 'MODEL RESPONSE HERE' | \
python3 stratify.py record KST-CODEX-2026-07-PUSHED \
  --target-id claude-code-fable \
  --run-id RUN_ID \
  --output results/RUN_ID.jsonl
```

If native evidence exposes the actual backend, record it separately:

```bash
printf '%s' 'MODEL RESPONSE HERE' | \
python3 stratify.py record KST-CODEX-2026-07-PUSHED \
  --target-id grok-build-grok \
  --run-id RUN_ID \
  --output results/RUN_ID.jsonl \
  --observed-model grok-4.6 \
  --observed-reasoning xhigh \
  --observed-source native_telemetry
```

## Critical isolation rule

**Do not run the target model from inside this repository.**

Agentic harnesses may inspect local files and silently read answer keys.

Generate/copy blinded prompts, then execute them in a clean environment with web/search/tools/files/project context disabled as far as the target permits.

## Telemetry first

Each probe trial should emit one append-only record preserving:

- exact prompt and response;
- probe pack/version;
- target ID;
- harness requested;
- model/reasoning requested;
- harness/model/reasoning actually observed, if exposed;
- evidence source for observed identity;
- isolation state;
- latency/token data when available;
- score/calibration;
- comparison group/change event.

Preserve raw responses and raw identity evidence so future analysis can rescore old runs.

## Probe lifecycle

```text
draft → experimental → active → contaminated → retired
```

Probe content is disposable. The measurement framework and telemetry are durable.

## First worked example

The first pack grew from community use of **"Tibo the reset guy"** as an accidental routing fingerprint.

That material is only a worked example. It does not define the framework or restrict future domains.

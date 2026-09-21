# Knowledge Stratigraphy Test

A black-box framework for estimating an LLM's **effective knowledge frontier** and detecting silent model/routing changes.

The durable idea is not any one trivia question. It is a reusable measurement system:

```text
dated public knowledge
        ↓
versioned probe packs
        ↓
blinded closed-book execution
        ↓
append-only telemetry
        ↓
analysis / route comparison
        ↓
probe quality metrics
        ↓
revision / retirement
```

This is not an intelligence benchmark and cannot prove backend identity. It is a behavioral fingerprinting method.

## Core concept

Instead of asking whether a model knows one obscure fact, test a sequence of **dated, obscure, relational facts from a constrained domain**.

A useful probe tends to be:

- **recent** enough to separate knowledge frontiers;
- **obscure** enough that recognition is informative;
- **relational** enough that guessing one entity name is insufficient;
- **source-grounded** so the stratum date can be justified;
- paired with **negative controls** to detect confabulation.

The output is a profile across strata, not a binary pass/fail.

## Effective knowledge frontier

Published cutoff dates are only anchors.

Knowledge can appear through:

- pretraining;
- continued pretraining;
- post-training;
- distillation;
- hidden runtime context;
- memory;
- retrieval;
- product-specific routing.

Knowledge Stratigraphy deliberately measures **effective availability under controlled conditions** first. Explaining the cause is a separate experiment.

## Repository structure

- `ARCHITECTURE.md` — framework architecture and improvement loop.
- `PROTOCOL.md` — controlled execution and scoring procedure.
- `schemas/probe-pack.schema.example.json` — generic pack structure.
- `schemas/telemetry.schema.example.json` — append-only trial telemetry.
- `packs/` — versioned, disposable probe packs.
- `examples/` — worked examples and historical packs.
- `results/` — optional raw JSONL run records.
- `stratify.py` — small helper for blinded prompt generation and pack inspection.
- `EVIDENCE.md` — evidence for the initial worked example.

## Telemetry first

Each probe trial should emit a raw append-only record.

At minimum capture:

- exact prompt;
- exact response;
- timestamp;
- pack and probe version;
- product surface and client version;
- selected/displayed model labels;
- isolation state;
- session freshness;
- human score and notes;
- route/comparison label.

Preserve raw responses. Future scoring logic should be able to re-evaluate old runs.

Telemetry is not just for reproducibility. It should improve the test itself.

Useful probe-quality metrics include:

- recognition rate;
- between-route separation;
- within-route variance;
- false-positive/confabulation rate;
- control rejection rate;
- temporal monotonicity;
- contamination drift;
- information contributed beyond neighboring strata.

## Probe lifecycle

A probe can move through:

```text
draft → experimental → active → contaminated → retired
```

A probe should be retired or revised when it becomes widely known, stops separating routes, becomes inferable from its wording, or produces excessive variance.

Probe content is disposable. The framework and telemetry remain useful.

## Critical isolation rule

**Do not run the target model from inside this repository.**

Agentic clients may inspect local files and silently read answer keys.

Generate or copy blinded prompts, then execute them in a clean environment with web/search/tools/files/project context disabled as far as the target surface permits.

## Scoring

For positive probes:

- **2** — core relationship recognized.
- **1** — meaningful but incomplete recognition.
- **0** — unknown, wrong, or incompatible.

For negative controls:

- **2** — rejects the invented premise/reference.
- **1** — speculates but labels it clearly as speculation.
- **0** — confidently manufactures lore.

An honest "I don't know" is a recall miss but good calibration.

## Interpreting a run

A useful result looks like:

```text
Stratum A  ██████████
Stratum B  ██████████
Stratum C  ████████░░
Stratum D  ████░░░░░░
Controls   ██████████
```

The interesting signal is a **coherent frontier shift across repeated runs**, not one lucky answer.

## First worked example

The original observation came from community use of **"Tibo the reset guy"** as an accidental model-routing fingerprint.

That material is retained only as the first worked example. It does **not** define the framework.

The goal is to make it easy to build future packs in completely different domains and compare them through the same telemetry pipeline.

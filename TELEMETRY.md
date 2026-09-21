# Telemetry

Telemetry is a first-class part of the test.

## Principle

Store **raw trial events append-only**. Preserve enough identity to separate the harness from the requested model and from the model/runtime actually observed.

The most important rule is:

> **requested is not observed**

A launch argument, UI selection, alias, or configuration file says what was requested. It is not proof of what backend actually answered.

When native evidence exists, store it separately.

## Target identity

Every trial should preserve three layers:

```text
HARNESS REQUESTED
  name / version / mode / executable

MODEL REQUESTED
  provider / family / label / model ID / reasoning

OBSERVED
  native harness version / build
  effective model label / ID
  effective reasoning
  route/backend if exposed
  evidence source + raw evidence
```

Unknown stays unknown.

This is essential for silent-routing experiments.

## Why

Repeated use should answer questions such as:

- Which probes actually separate models?
- Which probes separate harness routes even when the selected model label is the same?
- Does one client version produce a different frontier?
- Does requested model X sometimes expose different native model IDs?
- Which controls trigger confabulation?
- Does a probe's usefulness decay after publication?
- Does the apparent frontier move after a harness update?
- Do old responses score differently under improved rubrics?

## Raw format

Use JSONL: one trial per line.

Suggested path:

`results/<run-id>.jsonl`

See `schemas/telemetry.schema.example.json`.

## Comparison dimensions

Do not flatten everything into a single route label. Derive views by:

- model;
- harness;
- model × harness;
- model × harness × client version;
- requested model vs observed model;
- reasoning/effort;
- before/after change event;
- provider surface.

## Probe-level derived metrics

For each probe and comparison group, derive:

- attempts;
- mean score;
- full-recognition rate;
- honest-unknown rate;
- confabulation rate;
- negative-control rejection rate;
- within-target variance;
- between-target separation;
- score drift over time;
- contamination state.

## Pack-level derived metrics

Useful pack diagnostics:

- latest consistently recognized stratum;
- frontier confidence;
- temporal monotonicity;
- control performance;
- harness disagreement;
- model disagreement;
- requested-vs-observed identity disagreement;
- target separation;
- fraction of probes still clean;
- effective information per probe.

## Improvement heuristic

A strong probe has:

```text
high between-target separation
+ low within-target variance
+ low inference leakage
+ low confabulation
+ low contamination
```

A weak probe has the opposite profile.

Raw responses and raw identity evidence should remain available so later analysis can improve without rerunning old experiments.

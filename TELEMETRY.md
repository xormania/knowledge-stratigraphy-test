# Telemetry

Telemetry is a first-class part of the test.

## Principle

Store **raw trial events append-only**. Do not replace old scores or responses when the scoring method changes.

If a score is corrected later, append a new scoring/review event in a future schema revision rather than erasing the original observation.

## Why

The interesting questions emerge only after repeated use:

- Which probes actually separate routes?
- Which probes are noisy?
- Which controls trigger confabulation?
- Does one client surface behave differently from another?
- Does a probe's usefulness decay after publication?
- Does the apparent frontier move after a product update?
- Do old responses score differently under improved rubrics?

Without raw telemetry, those questions cannot be answered retroactively.

## Raw format

Use JSONL: one trial per line.

Suggested path:

`results/<run-id>.jsonl`

See `schemas/telemetry.schema.example.json`.

## Probe-level derived metrics

For each probe and comparison group, derive:

- attempts;
- mean score;
- full-recognition rate;
- honest-unknown rate;
- confabulation rate;
- negative-control rejection rate;
- within-route variance;
- between-route separation;
- score drift over time;
- contamination state.

## Pack-level derived metrics

Useful pack diagnostics:

- latest consistently recognized stratum;
- frontier confidence;
- temporal monotonicity;
- control performance;
- surface disagreement;
- route separation;
- fraction of probes still clean;
- effective information per probe.

## Improvement heuristic

A strong probe has:

```text
high between-route separation
+ low within-route variance
+ low inference leakage
+ low confabulation
+ low contamination
```

A weak probe has the opposite profile.

That lets future pack maintenance be evidence-driven instead of intuition-driven.

# Architecture

Knowledge Stratigraphy Test is organized around **four independent layers**.

## 1. Method

The method defines how to infer an effective knowledge frontier from repeated closed-book probes.

It is domain-agnostic.

A probe pack can target:

- developer culture;
- scientific discoveries;
- niche software releases;
- legal/regulatory changes;
- obscure product behavior;
- community terminology;
- any other dated body of public knowledge.

The framework does not assume that "knowledge" came from pretraining. It measures effective availability under controlled conditions.

## 2. Probe packs

A probe pack is disposable experimental content.

Each pack should:

- hold its subject domain as constant as practical;
- contain multiple dated strata;
- prefer relational knowledge over trivia;
- include negative controls;
- record source evidence separately from prompts;
- carry explicit contamination state;
- be versioned.

The current Codex/Tibo material belongs here, not in the core design.

## 3. Telemetry

Every probe execution should emit one append-only trial record.

Telemetry exists for two reasons:

1. **experimental reproducibility** — reconstruct exactly what was tested, where, when, and under what isolation conditions;
2. **test improvement** — identify which probes discriminate routes, which are noisy, which hallucination controls are weak, and which have become contaminated.

The canonical telemetry shape is in:

`schemas/telemetry.schema.example.json`

JSONL is recommended for raw run capture because it is append-only, diffable, streamable, and easy to ingest into SQLite later.

## 4. Analysis

Analysis should operate on telemetry rather than hand-written conclusions.

Useful derived metrics include:

- recognition rate by stratum;
- negative-control rejection rate;
- variance across cold sessions;
- surface/client disagreement;
- route separation score;
- temporal monotonicity;
- probe discrimination;
- contamination drift;
- calibration quality.

The framework should preserve raw responses so future scoring methods can be applied retroactively.

# Improvement loop

A pack should improve from its own telemetry.

For each probe, track:

- recognition rate by route;
- between-route separation;
- within-route variance;
- false-positive/confabulation rate;
- average confidence;
- contamination status;
- age of probe;
- source quality;
- number of repetitions.

A probe is valuable when it produces a stable difference between comparison groups without encouraging confabulation.

A probe should be revised or retired when it:

- becomes famous;
- is recognized equally by all routes;
- produces high within-route variance;
- is easy to infer from wording;
- depends on ambiguous naming;
- creates frequent false positives;
- no longer contributes information beyond neighboring strata.

# Future direction

The long-term artifact should look less like a benchmark and more like a **measurement system**:

```text
probe sources
    ↓
pack builder
    ↓
blinded execution
    ↓
append-only telemetry
    ↓
scoring / analysis
    ↓
probe quality metrics
    ↓
pack revision / retirement
```

That allows new domains and new time periods to be added without changing the underlying method.

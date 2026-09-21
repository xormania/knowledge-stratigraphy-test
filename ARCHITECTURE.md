# Architecture

Knowledge Stratigraphy Test is organized around **six independent layers**.

## 1. Method

Defines how to estimate an effective knowledge frontier from repeated closed-book probes.

It is domain-, harness-, provider-, and model-agnostic.

## 2. Probe packs

A probe pack is disposable experimental content.

Each pack should:

- keep its subject domain as constant as practical;
- contain multiple dated strata;
- prefer relational knowledge over trivia;
- include negative controls;
- preserve source evidence separately from prompts;
- carry contamination state;
- be versioned.

A probe pack must not depend on a particular harness or model.

## 3. Targets

A target describes where a pack is tested:

```text
Target = Harness × Requested Model × Runtime
```

Harness and model are free-form dimensions.

A target set enumerates valid combinations for one experiment. It is not assumed that every harness supports every model.

Target configuration records **requested** identity only.

## 4. Adapters

Adapters execute a target.

The universal baseline is `manual`, which works with any harness/model immediately.

Optional adapters can automate harness-specific mechanics such as:

- clean session creation;
- model/reasoning selection;
- prompt injection;
- response capture;
- native version/model metadata;
- latency and token capture.

Adapter capability must not leak into probe semantics.

The confirmed `xormania/multi-harness-proof` repository is the reference for proven Codex, Claude Code, and Grok Build execution mechanics. Its lessons are reused without coupling this framework to its coordination objective.

## 5. Telemetry

Every probe execution emits one append-only trial record.

Telemetry preserves separately:

```text
requested harness/model/runtime
observed harness/model/runtime evidence
isolation state
prompt/response
score/calibration
comparison metadata
```

Unknown observations stay unknown.

JSONL is recommended for raw trial capture.

## 6. Analysis

Analysis operates on telemetry, not hand-written conclusions.

Useful derived metrics include:

- recognition rate by stratum;
- negative-control rejection;
- within-target variance;
- between-target separation;
- harness effects;
- model effects;
- harness × model interaction;
- requested-vs-observed disagreement;
- client-version effects;
- reasoning/effort effects;
- temporal monotonicity;
- contamination drift;
- calibration quality.

# Experiment shape

```text
sources
   ↓
probe pack
   ↓
target set ── harness × model × runtime
   ↓
repetitions
   ↓
blinded execution
   ↓
append-only telemetry
   ↓
analysis
   ↓
probe + target quality metrics
   ↓
pack revision / adapter improvement
```

# Improvement loop

For each probe, track:

- recognition rate by target;
- between-target separation;
- within-target variance;
- confabulation rate;
- control rejection;
- contamination;
- age/source quality;
- repetitions.

For each adapter/target, track:

- successful executions;
- isolation failures;
- native identity coverage;
- requested-vs-observed mismatches;
- version compatibility;
- capture completeness.

This allows both the **questions** and the **execution machinery** to improve from telemetry.

# Invariants

1. Harness identity is not model identity.
2. Requested identity is not observed identity.
3. Unknown is not inferred.
4. Probe packs do not encode harness assumptions.
5. Raw responses are retained.
6. Raw identity evidence is retained when available.
7. New harnesses and models must not require schema redesign.

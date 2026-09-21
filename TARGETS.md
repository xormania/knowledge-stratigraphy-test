# Targets and Harnesses

Knowledge Stratigraphy treats **harness**, **model**, and **runtime observation** as separate dimensions.

## Core abstraction

```text
Experiment = Probe Pack × Target Set × Repetitions

Target = Harness × Requested Model × Runtime
```

A target is one concrete combination to test. Examples:

```text
Claude Code × Fable
Claude Code × Opus
Codex       × ChatGPT
Grok Build  × Grok
```

Nothing in the schema restricts those names. Future harnesses and future models are ordinary strings, not enum changes.

Not every harness must support every model. The target set enumerates combinations that are valid for the experiment.

## Keep harness and model independent

A harness is the execution shell around a model.

Examples:

- Claude Code
- Codex
- Grok Build
- a web application
- an API client
- a future agent harness

A model is the requested reasoning system.

Examples:

- ChatGPT
- Grok
- Fable
- Opus
- a future model or alias

This distinction matters because a result can change when either side changes.

## Requested is not observed

A target records what the experiment **requested**.

Telemetry separately records what the harness/vendor **actually exposed as effective**.

```text
requested:
  harness = Grok Build
  model = grok-4.5
  reasoning = low

observed:
  harness version = ...
  model = grok-4.6
  reasoning = xhigh
  evidence source = native telemetry
```

The framework must never silently convert a request into an observation.

This rule comes directly from the confirmed multi-harness proof, where native telemetry sometimes differed from requested settings.

## Adapter model

Adapters are execution mechanisms, not model definitions.

The minimum adapter is **manual**:

1. generate a blinded prompt;
2. run it in any harness/model;
3. paste/capture the response;
4. record the target metadata and response.

Because manual execution has no harness dependency, a new harness or model can be tested immediately.

Optional native adapters can automate:

- session creation;
- clean working directories;
- model selection;
- prompt delivery;
- response capture;
- native model/version metadata;
- reasoning/effort metadata;
- latency/token metadata.

The experiment and telemetry schema must not depend on those adapters existing.

## Lessons reused from multi-harness-proof

The separate project at:

https://github.com/xormania/multi-harness-proof

proved useful cross-harness mechanics for Codex, Claude Code, and Grok Build. Knowledge Stratigraphy reuses the general lessons rather than coupling to that repository:

- adapter-per-harness execution;
- fresh run/session identity;
- run-local evidence;
- requested settings preserved separately from native observations;
- native telemetry preferred over launch arguments as evidence;
- version-sensitive compatibility recorded rather than hidden;
- incomplete observations remain unknown, not inferred;
- append-only events are more useful than terminal output alone.

Its native mechanisms are also useful references for future adapters:

- Codex app-server;
- Claude Code native CLI/session instrumentation;
- Grok Build ACP / `agent stdio`.

## Target file

Targets are defined outside probe packs.

See:

- `schemas/target.schema.example.json`
- `targets.example.json`

Probe packs should never say "run this on Claude" or "this is a Grok probe." A pack describes knowledge. A target describes where that knowledge is tested.

## Comparison axes

Because dimensions remain separate, telemetry can support comparisons such as:

```text
same harness, different model
same model, different harness
same harness + model, different client version
same target, before/after suspected routing change
same target, different reasoning effort
same model family, different provider surface
```

That is the point of the abstraction: the framework should survive today's products.

# Adapter Contract

Adapters automate execution without defining the experiment.

## Universal baseline: manual

Every target is testable through the manual adapter.

That guarantees that support for a new harness or model never depends on implementation work.

## Native adapter responsibilities

A native adapter may provide:

1. preflight/version detection;
2. fresh native session creation;
3. clean working-directory setup;
4. requested model/reasoning selection;
5. blinded prompt delivery;
6. raw response capture;
7. native effective-model/version evidence;
8. latency/token capture;
9. isolation-state observation;
10. orderly session cleanup.

It must not:

- alter probe wording;
- read answer keys into the target context;
- infer an effective model from a requested model;
- silently substitute a model;
- convert missing evidence into a claim.

## Minimal interface

Conceptually:

```text
preflight(target) -> capabilities
start(target, isolation) -> session
submit(session, prompt) -> response
observe(session) -> native identity + usage evidence
close(session) -> lifecycle evidence
```

The exact implementation can be CLI, RPC, API, browser, or manual.

## Capability negotiation

Adapters should report capabilities rather than forcing a lowest common denominator.

Example:

```json
{
  "fresh_session": true,
  "model_select": true,
  "reasoning_select": true,
  "effective_model_observation": true,
  "token_usage": false,
  "web_disable": true,
  "tool_disable": true
}
```

This lets telemetry distinguish "not supported" from "not measured."

## Current harness references

The confirmed multi-harness proof contains working, version-sensitive mechanics for:

### Codex

- app-server over stdio;
- explicit model and reasoning request;
- native turn lifecycle;
- native metadata where exposed.

### Claude Code

- explicit native session ID;
- CLI model/effort request;
- run-local settings/hooks;
- native transcript/debug evidence.

### Grok Build

- ACP / `agent stdio`;
- explicit model/effort request;
- native session lifecycle;
- native completion/update events.

Reference:

https://github.com/xormania/multi-harness-proof

Knowledge Stratigraphy should borrow these mechanics only inside harness adapters. The core method, packs, targets, and telemetry remain independent.

## Clean-room requirement

Automated adapters must execute the target outside the Knowledge Stratigraphy repository and outside any directory containing the selected pack's answer keys.

A useful adapter should create a fresh scratch directory and record its isolation state.

## Requested vs effective identity

Adapters may request:

```text
model = X
reasoning = low
```

They may only populate observed identity when supported by native evidence:

```text
observed.model = Y
observed.reasoning = high
observed.evidence_source = native_telemetry
```

Mismatch is data, not an error to normalize away.

## Future adapters

Adding a harness should require only:

- one adapter implementation;
- capability metadata;
- tests/fixtures for its invocation and observation behavior.

It must not require changes to probe-pack schema or scoring semantics.

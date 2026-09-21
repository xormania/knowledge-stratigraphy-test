# Framework architecture

## Current implementation

`kst.core` owns validation, canonical hashes, target selection, and deterministic plans.
`kst.adapters` defines the provider boundary. `kst.engine` orchestrates trials against
that boundary. `kst.telemetry` stores observations and score revisions. `kst.analysis`
builds projections. `kst.cli` is an interface, not the location of domain behavior.

Dependencies point toward the core, not toward a vendor SDK. Harness names, providers,
model families, aliases, and reasoning labels remain ordinary target data.

## Boundary objects

**Probe pack:** knowledge content, source/contamination metadata, and scoring signals.
It describes neither an executor nor a required model.

**Target:** harness, requested model, runtime adapter, and configured isolation intent.
The target snapshot is separate from whatever identity the runtime exposes.

**Plan:** pack/target content hashes, seed, repetitions, ordered slots, and opaque IDs.
The plan is controller-side data. Dates, probe IDs, answers, and grading metadata do
not cross into `ProbeRequest`.

**Adapter:** owns native I/O, session creation, timeout enforcement, response capture,
and cleanup. The engine depends on a protocol, not a vendor-specific implementation.
A registry supplies a new adapter instance for each trial. An unknown adapter produces
an explicit unsupported result, never a silent substitution.

**Capture:** exact answer, execution mode, observed identity, isolation observations,
optional token/latency fields, and native session identity. Requested identity is
never copied into observed fields.

**Event:** validated immutable observation. Scoring is another event, not a mutation
of the response. Reports can be reconstructed from the event stream.

## Lifecycle

```text
validate → plan → run.started
                    │
              trial.started
                    │
         preflight → start → submit → close
                    │
              trial.finished
                    │
               run.finished
                    │
           score.recorded (zero or more revisions)
                    │
              rebuild report
```

A timeout, empty output, startup failure, unavailable adapter, or cleanup failure is
an execution outcome, not a wrong answer. Cancelled runs retain evidence for completed
work and stop scheduling new trials. A hard kill can leave a started trial unfinished;
reports expose that state rather than inventing a completion.

## Reuse from the proof project

The [multi-harness proof](https://github.com/xormania/multi-harness-proof) informs the
separation of native session identity, requested settings, observed metadata, and
lifecycle evidence. Its coordination protocol is not imported into this framework.
Knowledge trials normally need fresh independent sessions, unlike that proof's
persistent-session coordination objective.

## Extension points

New domains require packs. New model names require target data. Automated support for
a new harness requires an adapter plus conformance and failure tests. New scoring
methods append versioned assessments. New analyses consume events rather than changing
historical observations.

## Deliberate current boundaries

The shipped executor automates mocks; manual export/capture covers other surfaces.
Native adapters and native process/transport simulators are subsequent integrations.
The JSONL ledger is a small-run reference implementation with sequential writes; a
SQLite store can implement the same event semantics later. It is not a high-throughput
distributed store. The report provides descriptive rates, not statistical proof of a
cutoff, route identity, or model ranking.

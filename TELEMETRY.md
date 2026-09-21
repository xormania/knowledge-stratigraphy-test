# Telemetry and improvement

## Version 2 event stream

Each append records `schema_version`, an event UUID, ordered sequence, UTC timestamp,
event type, payload, previous hash, and current hash. The machine-enforced contract
is `kst/data/event.schema.json`, validated with JSON Schema Draft 2020-12.

Event types are `run.started`, `trial.started`, `trial.finished`, `run.finished`, and
`score.recorded`. A planned run snapshots the source pack and targets. Each trial
also carries pack, probe, target, and exact-prompt hashes. Hashes use canonical JSON
(sorted keys, compact separators, UTF-8, non-finite numbers rejected).

## Separate facts from intent

Requested harness/model/runtime and configured isolation intent belong to the trial
start. The finish carries exact response text and separately observed model, reasoning,
session, usage, and isolation metadata. CLI defaults for isolation are `unknown`.
Manual observations without an explicit evidence source are `operator_unverified`.

A selected model label is not an observed backend ID. Mock metadata is explicitly
synthetic. No requested value is promoted into observed identity as a fallback.

## Append-only storage

The JSONL ledger uses an exclusive lock file to reject concurrent writers. Entries are
flushed and fsynced. Existing content is validated before an append. Broken JSON,
missing final newline, invalid schemas, and hash/sequence mismatches fail explicitly.
The application never silently truncates corrupt data or breaks a stale lock.

This protects application-level history and detects accidental changes. It is **not**
cryptographic authentication, an immutable filesystem, or a distributed transaction
system. A party with write access could rewrite and rehash the whole ledger. A reader
racing an active write may see an incomplete tail; retry after the writer completes.
Each append reads prior events, so this implementation favors small experiments.

After a crash, preserve the original before any repair. A leftover lock must only be
removed after establishing that its writer has stopped. Recovery tooling must produce
new evidence rather than silently rewriting history.

## Scoring and projections

`score` accepts only a completed trial. The score/assessment pairing is checked against
positive/control semantics. Each correction adds a new scorer/rubric-versioned event.
The report uses the latest assessment while retaining every earlier assessment.

Execution failures and unfinished trials remain separate counts. Unscored completions
are not zeros. Recognition and negative-control rejection have separate metric names.
Reports group by pack hash, target hash, probe, and execution mode, so mock, manual,
and live captures are not silently pooled. Rates use scored completions as their
explicit denominator; show the attempt/completion/scored counts alongside them.

## Improving the system

Use accumulated per-probe observations to investigate discrimination, variance,
unknowns, fabrication, contamination, and scoring disagreements. Use lifecycle evidence
to investigate adapter failures and identity-observation gaps. The current reporter
provides descriptive counts/rates; temporal aggregation, statistical uncertainty,
contamination drift, and automated probe selection remain extensions, not claimed
implemented metrics.

## Privacy

Runs and result data are ignored by Git. Capture is local; nothing is automatically
uploaded. Exact responses, target snapshots, pack keys, and operator-supplied metadata
may be sensitive. Do not put credentials in target definitions. Review any logs before
sharing, and do not give a tested agent access to the controller's logs or answer keys.
The CI artifact upload contains only synthetic-test JUnit and coverage output.

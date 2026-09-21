# Adapter contract

The executable contract is in `kst/adapters.py`.

```python
preflight(target) -> Capabilities
start(target, workspace) -> native_session_id
submit(native_session_id, ProbeRequest) -> Capture
close(native_session_id_or_none) -> None
```

An adapter may use CLI, RPC, HTTP, or another transport. Model names are not adapter
names. Selection is through `Registry.register(name, factory)`; a factory returns a
new instance for each cold trial. The shipped default registry registers only `mock`.
Manual export/capture is a CLI workflow, not an automatically launched native session.

## Responsibilities

Preflight reports capabilities and rejects unsupported operations without substituting
another model or harness. Startup creates a native session in the supplied empty
scratch directory. Submission returns raw text and evidence. Cleanup releases only
owned resources and must tolerate a `None` session after partial startup.

`ProbeRequest` contains only an opaque trial ID, prompt, and timeout budget. It carries
no answer key, source links, probe dates, stratum labels, or expected signals.

The native adapter must enforce the timeout using its process/RPC/HTTP mechanism and
raise `TimeoutError`. The synchronous engine classifies that error; it cannot preempt
an arbitrary adapter that ignores the budget. The mock simulates timeouts immediately,
without sleeps or live calls.

A capture's mode must match preflight. Session identities must agree, and the engine
rejects reuse within a run. Omitted model identity and isolation observations stay
unknown. Adapter-reported isolation is evidence of what the adapter observed, not an
OS-level guarantee against all access to local files or runtime-injected context.

## Mock scenarios

`MockAdapter` supports normal responses and deterministic faults:
`unsupported`, `start`, `submit`, `timeout`, `empty`, `close`, and `cancel`.
Observed model metadata can deliberately differ from the requested model. Every mock
capture is labeled `mock`, and its identity evidence source is also `mock`.

## Acceptance path for a native adapter

Implement the protocol, register its factory, and add an offline fixture-backed
contract case in `tests/contracts/test_adapters.py`. Add transport/process doubles
for that native interface and behavior cases for startup, malformed messages, timeout,
permission denial, cancellation, identity mismatch, and cleanup. Networked acceptance
checks must be explicitly opt-in and must not replace the offline CI suite.

The reusable native references are in
[`xormania/multi-harness-proof`](https://github.com/xormania/multi-harness-proof):
Codex app-server, Claude Code session/CLI instrumentation, and Grok Build ACP.
Do not copy the proof's persistent-session objective into independent knowledge trials.

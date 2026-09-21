"""Cold-trial orchestration. All model I/O lives behind the adapter protocol."""
from __future__ import annotations

import math
import tempfile
import uuid
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .adapters import Capture, ProbeRequest, Registry, Unsupported, default_registry
from .core import Invalid, blinded_prompt, canonical, digest, find_probe, find_target, plan
from .core import requested_target_record, validate
from .telemetry import Ledger


def trial_start(run_id: str, trial_id: str, pack: dict[str, Any], probe: dict[str, Any],
                target: dict[str, Any], prompt: str, **metadata: Any) -> dict[str, Any]:
    return {"run_id": run_id, "trial_id": trial_id,
            "target": requested_target_record(target), "target_hash": digest(target),
            "pack": {"id": pack["pack"]["id"], "version": pack["pack"]["version"],
                     "hash": digest(pack), "probe_id": probe["id"],
                     "probe_hash": digest(probe), "stratum": probe["stratum"],
                     "kind": probe["kind"]},
            "prompt": {"exact_text": prompt, "sha256": digest(prompt)},
            "isolation_requested": deepcopy(target.get("isolation_defaults", {})),
            **metadata}


def execute(pack: dict[str, Any], targets: dict[str, Any], directory: Path,
            repetitions: int = 3, seed: int = 0, timeout_seconds: float = 60,
            registry: Registry | None = None) -> dict[str, Any]:
    schedule = plan(pack, targets, repetitions, seed)
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise Invalid("Timeout must be positive and finite")
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    ledger = Ledger(directory / "events.jsonl")
    registry = registry or default_registry()
    run_id = str(uuid.uuid4())
    ledger.append("run.started", {"run_id": run_id, "plan": schedule,
                  "pack_snapshot": deepcopy(pack), "targets_snapshot": deepcopy(targets)})
    statuses: list[str] = []
    sessions: set[str] = set()
    for slot in schedule["trials"]:
        trial_id = str(uuid.uuid4())
        target = find_target(targets, slot["target_id"])
        probe = find_probe(pack, slot["probe_id"])
        request = ProbeRequest(trial_id, blinded_prompt(pack, probe), timeout_seconds)
        ledger.append("trial.started", trial_start(run_id, trial_id, pack, probe, target,
                      request.prompt, slot=slot))
        adapter = None
        session = None
        capture = None
        error = None
        cleanup_error = None
        status = "completed"
        try:
            # No source files, answer keys, or controller manifests are copied here.
            with tempfile.TemporaryDirectory(prefix="kst-trial-") as scratch:
                workspace = Path(scratch).resolve()
                if Path(__file__).resolve().parents[1] in workspace.parents:
                    raise Invalid("Trial workspace must be outside the framework checkout")
                try:
                    adapter = registry.create(deepcopy(target))
                    capabilities = adapter.preflight(deepcopy(target))
                    session = adapter.start(deepcopy(target), workspace)
                    if not session or session in sessions:
                        raise Invalid("Missing or reused native session identity")
                    sessions.add(session)
                    result = adapter.submit(session, request)
                    if not isinstance(result, Capture):
                        raise Invalid("Adapter must return Capture")
                    capture = asdict(result)
                    validate(capture, "capture")
                    canonical(capture)
                    if capture["mode"] != capabilities.mode:
                        raise Invalid("Capture mode differs from adapter preflight")
                    if capture.get("session_id") not in (None, session):
                        raise Invalid("Capture belongs to a different session")
                    if not capture["raw_text"].strip():
                        raise Invalid("Empty output is an execution failure, not a recall miss")
                finally:
                    if adapter is not None:
                        try:
                            adapter.close(session)
                        except Exception as exc:
                            cleanup_error = f"{type(exc).__name__}: {exc}"
        except KeyboardInterrupt:
            status, error = "cancelled", {"type": "KeyboardInterrupt", "message": "Cancelled"}
        except Exception as exc:
            status = ("unsupported" if isinstance(exc, Unsupported) else
                      "timeout" if isinstance(exc, TimeoutError) else "error")
            error = {"type": type(exc).__name__, "message": str(exc)}
            if capture is not None:
                try:
                    validate(capture, "capture")
                    canonical(capture)
                except (Invalid, ValueError, TypeError):
                    error["invalid_capture"] = repr(capture)
                    capture = None
        if cleanup_error and status == "completed":
            status = "error"
        ledger.append("trial.finished", {"run_id": run_id, "trial_id": trial_id,
                      "status": status, "capture": capture, "error": error,
                      "cleanup_error": cleanup_error})
        statuses.append(status)
        if status == "cancelled":
            break
    result = {"run_id": run_id, "status": "cancelled" if "cancelled" in statuses else
              "completed" if all(s == "completed" for s in statuses) else "incomplete",
              "trial_count": len(statuses)}
    ledger.append("run.finished", result)
    return result

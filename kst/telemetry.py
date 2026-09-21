"""Local append-only JSONL ledger. Sequential writers; no destructive recovery."""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .core import Invalid, canonical, digest, validate


class Ledger:
    def __init__(self, path: Path):
        self.path = Path(path)

    def read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        raw = self.path.read_text(encoding="utf-8")
        if raw and not raw.endswith("\n"):
            raise Invalid("Incomplete ledger tail; preserve the file and recover explicitly")
        result: list[dict[str, Any]] = []
        previous = None
        for line in raw.split("\n")[:-1]:
            try:
                event = json.loads(line)
                validate(event, "event")
                body = {key: value for key, value in event.items() if key != "hash"}
                if (event["sequence"] != len(result) + 1 or event["previous_hash"] != previous
                        or event["hash"] != digest(body)):
                    raise Invalid("Ledger hash/sequence mismatch")
            except (ValueError, TypeError) as exc:
                raise Invalid(f"Invalid ledger line {len(result) + 1}: {exc}") from exc
            result.append(event)
            previous = event["hash"]
        return result

    def append(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock = self.path.with_name(self.path.name + ".lock")
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise Invalid("Ledger has another writer or a stale lock; never break it automatically") from exc
        os.close(descriptor)
        try:
            history = self.read()
            event = {"schema_version": "2.0.0", "event_id": str(uuid.uuid4()),
                     "sequence": len(history) + 1,
                     "timestamp": datetime.now(timezone.utc).isoformat(),
                     "event_type": event_type, "payload": payload,
                     "previous_hash": history[-1]["hash"] if history else None}
            event["hash"] = digest(event)
            validate(event, "event")
            encoded = (canonical(event) + "\n").encode("utf-8")
            with self.path.open("ab") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            return event
        finally:
            lock.unlink()


def score(ledger: Ledger, trial_id: str, value: int, scorer: str, rubric_version: str,
          assessment: str, note: str = "") -> dict[str, Any]:
    history = ledger.read()
    finished = [e["payload"] for e in history if e["event_type"] == "trial.finished"
                and e["payload"]["trial_id"] == trial_id]
    if len(finished) != 1 or finished[0]["status"] != "completed":
        raise Invalid("Score requires one completed trial, not a failed or missing execution")
    starts = [e["payload"] for e in history if e["event_type"] == "trial.started"
              and e["payload"]["trial_id"] == trial_id]
    if len(starts) != 1:
        raise Invalid("Score requires one trial start")
    allowed = {
        "positive": {(2, "recognized"), (1, "partial"), (0, "unknown"),
                     (0, "wrong"), (0, "fabricated")},
        "negative_control": {(2, "rejected"), (1, "speculative"), (0, "fabricated")},
    }
    kind = starts[0]["pack"]["kind"]
    if kind in allowed and (value, assessment) not in allowed[kind]:
        raise Invalid("Score and assessment contradict the probe kind")
    return ledger.append("score.recorded", {"trial_id": trial_id, "score": value,
                         "scorer": scorer, "rubric_version": rubric_version,
                         "assessment": assessment, "note": note})

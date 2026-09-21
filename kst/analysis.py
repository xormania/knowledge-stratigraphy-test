"""Descriptive projections from evidence; never guess a cutoff or backend ID."""
from __future__ import annotations

from typing import Any

from .core import Invalid
from .telemetry import Ledger


def summarize(ledger: Ledger) -> dict[str, Any]:
    starts: dict[str, Any] = {}
    finishes: dict[str, Any] = {}
    scores: dict[str, Any] = {}
    for event in ledger.read():
        payload = event["payload"]
        tid = payload.get("trial_id")
        kind = event["event_type"]
        if kind in ("trial.started", "trial.finished"):
            collection = starts if kind == "trial.started" else finishes
            if tid in collection:
                raise Invalid(f"Duplicate {kind}: {tid}")
            collection[tid] = payload
        elif kind == "score.recorded":
            scores[tid] = payload  # New projection; historical scores stay in the ledger.
    if set(finishes) - set(starts) or set(scores) - set(finishes):
        raise Invalid("Orphan completion or score event")
    if any(finishes[tid]["status"] != "completed" for tid in scores):
        raise Invalid("A failed execution cannot carry a knowledge score")
    groups: dict[tuple[str, ...], dict[str, Any]] = {}
    for tid, start in starts.items():
        finish = finishes.get(tid)
        capture = finish.get("capture") if finish else None
        pack = start["pack"]
        mode = capture["mode"] if capture else "unobserved"
        key = (pack["hash"], start["target_hash"], pack["probe_id"], mode)
        if key not in groups:
            groups[key] = {"pack_hash": pack["hash"], "target_hash": start["target_hash"],
                           "target_id": start["target"]["target_id"],
                           "probe_id": pack["probe_id"], "stratum": pack["stratum"],
                           "kind": pack["kind"], "mode": mode, "attempts": 0,
                           "completed": 0, "failed": 0, "unfinished": 0,
                           "scored": 0, "full_score": 0, "score_sum": 0,
                           "unknown": 0, "fabricated": 0, "observed_model_ids": []}
        row = groups[key]
        row["attempts"] += 1
        if not finish:
            row["unfinished"] += 1
            continue
        if finish["status"] != "completed":
            row["failed"] += 1
            continue
        row["completed"] += 1
        observed = capture["observed"].get("model_id") if capture else None
        if observed and observed not in row["observed_model_ids"]:
            row["observed_model_ids"].append(observed)
        scored = scores.get(tid)
        if scored:
            row["scored"] += 1
            row["score_sum"] += scored["score"]
            row["full_score"] += int(scored["score"] == 2)
            row["unknown"] += int(scored["assessment"] == "unknown")
            row["fabricated"] += int(scored["assessment"] == "fabricated")
    rows = list(groups.values())
    for row in rows:
        n = row["scored"]
        total = row.pop("score_sum")
        row["mean_score"] = total / n if n else None
        rate_name = ("control_rejection_rate" if row["kind"] == "negative_control"
                     else "full_recognition_rate" if row["kind"] == "positive"
                     else "calibration_full_score_rate")
        row[rate_name] = row["full_score"] / n if n else None
    return {"trial_count": len(starts), "groups": rows,
            "interpretation": "Descriptive per-probe rates over scored completions only. "
            "Mock, manual, and live captures remain separate; no cutoff is inferred."}

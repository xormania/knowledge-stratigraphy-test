#!/usr/bin/env python3
"""Minimal helper for Knowledge Stratigraphy Test.

Zero dependencies. It does not call models. Its job is to blind prompts,
record telemetry, and keep raw experimental data append-only.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_PACK = ROOT / "examples" / "codex-reset-2026-v0.1.json"


def load_pack(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def find_probe(pack: dict, probe_id: str) -> dict:
    for probe in pack["probes"]:
        if probe["id"] == probe_id:
            return probe
    raise SystemExit(f"unknown probe: {probe_id}")


def blinded_prompt(pack: dict, probe: dict) -> str:
    return f'{pack["pack"]["standard_preamble"]}\n\n{probe["prompt"]}'


def cmd_list(args: argparse.Namespace) -> None:
    pack = load_pack(args.pack)
    for probe in pack["probes"]:
        print(f'{probe["id"]}\t{probe["stratum"]}\t{probe["kind"]}')


def cmd_prompt(args: argparse.Namespace) -> None:
    pack = load_pack(args.pack)
    print(blinded_prompt(pack, find_probe(pack, args.probe_id)))


def cmd_batch(args: argparse.Namespace) -> None:
    pack = load_pack(args.pack)
    probes = list(pack["probes"])
    random.Random(args.seed).shuffle(probes)
    for i, probe in enumerate(probes, 1):
        print(f"--- probe {i} ---")
        print(blinded_prompt(pack, probe))
        print()


def cmd_reveal(args: argparse.Namespace) -> None:
    pack = load_pack(args.pack)
    probe = find_probe(pack, args.probe_id)
    print(json.dumps(probe, indent=2))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def cmd_new_run(args: argparse.Namespace) -> None:
    run = {
        "run_id": args.run_id or str(uuid.uuid4()),
        "started_at": now_iso(),
        "pack_path": str(args.pack),
        "pack_id": load_pack(args.pack)["pack"]["id"],
        "pack_version": load_pack(args.pack)["pack"]["version"],
        "route_label": args.route_label,
        "provider": args.provider,
        "surface": args.surface,
        "client": args.client,
        "client_version": args.client_version,
        "selected_model_label": args.model,
        "notes": args.notes or [],
    }
    print(json.dumps(run, indent=2))


def cmd_record(args: argparse.Namespace) -> None:
    pack = load_pack(args.pack)
    probe = find_probe(pack, args.probe_id)

    response = args.response
    if response is None:
        response = sys.stdin.read()

    trial = {
        "schema_version": "1.0.0",
        "trial_id": str(uuid.uuid4()),
        "run_id": args.run_id,
        "timestamp": now_iso(),
        "pack_id": pack["pack"]["id"],
        "pack_version": pack["pack"]["version"],
        "probe_id": probe["id"],
        "probe_order": args.order,
        "session_fresh": args.session_fresh,
        "environment": {
            "provider": args.provider,
            "surface": args.surface,
            "client": args.client,
            "client_version": args.client_version,
            "selected_model_label": args.model,
            "displayed_model_id": args.model_id,
            "account_class": args.account_class,
            "region": None,
        },
        "isolation": {
            "web_enabled": args.web_enabled,
            "tools_enabled": args.tools_enabled,
            "files_available": args.files_available,
            "project_context_available": args.project_context_available,
            "persistent_memory_enabled": args.memory,
            "system_context_known": args.system_context,
            "notes": args.isolation_note or [],
        },
        "prompt": {
            "exact_text": blinded_prompt(pack, probe),
            "preamble_id": "pack-default",
        },
        "response": {
            "raw_text": response.rstrip("\n"),
            "latency_ms": args.latency_ms,
            "stop_reason": None,
            "token_usage": {"input": None, "output": None},
        },
        "scoring": {
            "score": args.score,
            "confidence": args.confidence,
            "recognized_signals": [],
            "missing_signals": [],
            "disqualifiers_hit": [],
            "calibration_quality": args.calibration,
            "scorer": "human" if args.score is not None else None,
            "notes": args.score_note or [],
        },
        "routing_fingerprint": {
            "route_label": args.route_label,
            "comparison_group": args.comparison_group,
            "suspected_change_event": args.change_event,
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(trial, ensure_ascii=False) + "\n")
    print(trial["trial_id"])


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--pack", type=Path, default=DEFAULT_PACK)
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("list")

    q = sub.add_parser("prompt")
    q.add_argument("probe_id")

    q = sub.add_parser("batch")
    q.add_argument("--seed", type=int, default=0)

    q = sub.add_parser("reveal")
    q.add_argument("probe_id")

    q = sub.add_parser("new-run")
    q.add_argument("--run-id")
    q.add_argument("--route-label")
    q.add_argument("--provider")
    q.add_argument("--surface")
    q.add_argument("--client")
    q.add_argument("--client-version")
    q.add_argument("--model")
    q.add_argument("--notes", action="append")

    q = sub.add_parser("record")
    q.add_argument("probe_id")
    q.add_argument("--run-id", required=True)
    q.add_argument("--output", type=Path, required=True)
    q.add_argument("--order", type=int)
    q.add_argument("--provider")
    q.add_argument("--surface")
    q.add_argument("--client")
    q.add_argument("--client-version")
    q.add_argument("--model")
    q.add_argument("--model-id")
    q.add_argument("--account-class")
    q.add_argument("--route-label")
    q.add_argument("--comparison-group")
    q.add_argument("--change-event")
    q.add_argument("--response")
    q.add_argument("--latency-ms", type=int)
    q.add_argument("--score", type=int, choices=(0, 1, 2))
    q.add_argument("--confidence", choices=("low", "medium", "high"))
    q.add_argument("--calibration", choices=("poor", "mixed", "good"))
    q.add_argument("--score-note", action="append")
    q.add_argument("--isolation-note", action="append")
    q.add_argument("--session-fresh", action=argparse.BooleanOptionalAction, default=True)
    q.add_argument("--web-enabled", action=argparse.BooleanOptionalAction, default=False)
    q.add_argument("--tools-enabled", action=argparse.BooleanOptionalAction, default=False)
    q.add_argument("--files-available", action=argparse.BooleanOptionalAction, default=False)
    q.add_argument("--project-context-available", action=argparse.BooleanOptionalAction, default=False)
    q.add_argument("--memory", choices=("true", "false", "unknown"), default="unknown")
    q.add_argument("--system-context", choices=("true", "false", "unknown"), default="unknown")

    return p


def main() -> None:
    args = parser().parse_args()
    {
        "list": cmd_list,
        "prompt": cmd_prompt,
        "batch": cmd_batch,
        "reveal": cmd_reveal,
        "new-run": cmd_new_run,
        "record": cmd_record,
    }[args.command](args)


if __name__ == "__main__":
    main()

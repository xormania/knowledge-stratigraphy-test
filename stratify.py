#!/usr/bin/env python3
"""Knowledge Stratigraphy helper.

Zero dependencies. The core stays harness/model agnostic.

The tool:
- reads versioned probe packs;
- reads arbitrary harness × model target definitions;
- emits blinded prompts and experiment matrices;
- records append-only JSONL telemetry;
- never assumes requested model identity equals observed runtime identity.

It intentionally does not require native harness automation. Manual execution is
the universal adapter; native adapters can be added without changing pack or
telemetry semantics.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_PACK = ROOT / "examples" / "codex-reset-2026-v0.1.json"
DEFAULT_TARGETS = ROOT / "targets.example.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_pack(path: Path) -> dict[str, Any]:
    data = load_json(path)
    if "pack" not in data or "probes" not in data:
        raise SystemExit(f"invalid probe pack: {path}")
    return data


def load_targets(path: Path) -> dict[str, Any]:
    data = load_json(path)
    if "targets" not in data:
        raise SystemExit(f"invalid target file: {path}")
    return data


def find_probe(pack: dict[str, Any], probe_id: str) -> dict[str, Any]:
    for probe in pack["probes"]:
        if probe["id"] == probe_id:
            return probe
    raise SystemExit(f"unknown probe: {probe_id}")


def find_target(targets: dict[str, Any], target_id: str) -> dict[str, Any]:
    for target in targets["targets"]:
        if target["id"] == target_id:
            return target
    raise SystemExit(f"unknown target: {target_id}")


def enabled_targets(targets: dict[str, Any]) -> list[dict[str, Any]]:
    return [t for t in targets["targets"] if t.get("enabled", True)]


def blinded_prompt(pack: dict[str, Any], probe: dict[str, Any]) -> str:
    return f'{pack["pack"]["standard_preamble"]}\n\n{probe["prompt"]}'


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def tri(value: str | bool | None) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value in ("true", "false", "unknown"):
        return value
    return "unknown"


def target_summary(target: dict[str, Any]) -> str:
    h = target.get("harness", {})
    m = target.get("model", {})
    r = target.get("runtime", {})
    return (
        f'{target["id"]}\t'
        f'{h.get("name", "?")}\t'
        f'{m.get("requested_label", "?")}\t'
        f'{r.get("adapter", "manual")}'
    )


def requested_target_record(target: dict[str, Any]) -> dict[str, Any]:
    harness = target.get("harness", {})
    model = target.get("model", {})
    runtime = target.get("runtime", {})
    return {
        "target_id": target.get("id"),
        "harness_requested": {
            "name": harness.get("name"),
            "mode": harness.get("mode"),
            "version": harness.get("requested_version"),
            "executable": harness.get("executable"),
        },
        "model_requested": {
            "provider": model.get("provider"),
            "family": model.get("family"),
            "label": model.get("requested_label"),
            "model_id": model.get("requested_model_id"),
            "reasoning": model.get("requested_reasoning"),
        },
        "runtime": {
            "adapter": runtime.get("adapter", "manual"),
            "transport": runtime.get("transport", "manual"),
        },
    }


def isolation_record(target: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    defaults = target.get("isolation_defaults", {})
    def choose(name: str) -> str:
        explicit = getattr(args, name, None)
        if explicit is not None:
            return tri(explicit)
        return tri(defaults.get(name))

    return {
        "session_fresh": tri(args.session_fresh),
        "clean_working_directory": tri(args.clean_working_directory),
        "web_enabled": choose("web_enabled"),
        "tools_enabled": choose("tools_enabled"),
        "files_available": choose("files_available"),
        "project_context_available": choose("project_context_available"),
        "persistent_memory_enabled": choose("persistent_memory_enabled"),
        "system_context_known": tri(args.system_context_known),
        "notes": args.isolation_note or [],
    }


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
        print(f"--- probe {i}: {probe['id']} ---")
        print(blinded_prompt(pack, probe))
        print()


def cmd_reveal(args: argparse.Namespace) -> None:
    pack = load_pack(args.pack)
    print(json.dumps(find_probe(pack, args.probe_id), indent=2))


def cmd_targets(args: argparse.Namespace) -> None:
    targets = load_targets(args.targets)
    for target in enabled_targets(targets):
        print(target_summary(target))


def cmd_target(args: argparse.Namespace) -> None:
    targets = load_targets(args.targets)
    print(json.dumps(find_target(targets, args.target_id), indent=2))


def cmd_matrix(args: argparse.Namespace) -> None:
    pack = load_pack(args.pack)
    targets = enabled_targets(load_targets(args.targets))
    rows: list[dict[str, Any]] = []

    for target in targets:
        for probe in pack["probes"]:
            for repetition in range(1, args.repetitions + 1):
                rows.append({
                    "target_id": target["id"],
                    "probe_id": probe["id"],
                    "stratum": probe["stratum"],
                    "kind": probe["kind"],
                    "repetition": repetition,
                })

    random.Random(args.seed).shuffle(rows)

    if args.json:
        print(json.dumps({
            "pack_id": pack["pack"]["id"],
            "pack_version": pack["pack"]["version"],
            "targets": [t["id"] for t in targets],
            "repetitions": args.repetitions,
            "trials": rows,
        }, indent=2))
        return

    for i, row in enumerate(rows, 1):
        print(
            f"{i}\t{row['target_id']}\t{row['probe_id']}\t"
            f"rep={row['repetition']}\t{row['stratum']}\t{row['kind']}"
        )


def cmd_new_run(args: argparse.Namespace) -> None:
    pack = load_pack(args.pack)
    target = find_target(load_targets(args.targets), args.target_id)
    run = {
        "schema_version": "1.1.0",
        "run_id": args.run_id or str(uuid.uuid4()),
        "started_at": now_iso(),
        "pack": {
            "path": str(args.pack),
            "id": pack["pack"]["id"],
            "version": pack["pack"]["version"],
        },
        "target": requested_target_record(target),
        "comparison_group": args.comparison_group,
        "suspected_change_event": args.change_event,
        "notes": args.note or [],
    }
    print(json.dumps(run, indent=2))


def cmd_record(args: argparse.Namespace) -> None:
    pack = load_pack(args.pack)
    probe = find_probe(pack, args.probe_id)
    target = find_target(load_targets(args.targets), args.target_id)

    response = args.response
    if response is None:
        response = sys.stdin.read()

    trial = {
        "schema_version": "1.1.0",
        "trial_id": str(uuid.uuid4()),
        "run_id": args.run_id,
        "timestamp": now_iso(),
        "pack": {
            "id": pack["pack"]["id"],
            "version": pack["pack"]["version"],
            "probe_id": probe["id"],
            "probe_order": args.order,
        },
        "target": requested_target_record(target),
        "observed": {
            "harness_version": args.observed_harness_version,
            "harness_build": args.observed_harness_build,
            "model_label": args.observed_model,
            "model_id": args.observed_model_id,
            "reasoning": args.observed_reasoning,
            "route_or_backend": args.observed_route,
            "evidence_source": args.observed_source,
            "evidence_raw": args.observed_evidence,
        },
        "isolation": isolation_record(target, args),
        "prompt": {
            "exact_text": blinded_prompt(pack, probe),
            "preamble_id": "pack-default",
        },
        "response": {
            "raw_text": response.rstrip("\n"),
            "latency_ms": args.latency_ms,
            "stop_reason": args.stop_reason,
            "token_usage": {
                "input": args.input_tokens,
                "output": args.output_tokens,
            },
        },
        "scoring": {
            "score": args.score,
            "confidence": args.confidence,
            "recognized_signals": args.recognized_signal or [],
            "missing_signals": args.missing_signal or [],
            "disqualifiers_hit": args.disqualifier or [],
            "calibration_quality": args.calibration,
            "scorer": "human" if args.score is not None else None,
            "notes": args.score_note or [],
        },
        "comparison": {
            "group": args.comparison_group,
            "suspected_change_event": args.change_event,
            "notes": args.comparison_note or [],
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(trial, ensure_ascii=False) + "\n")
    print(trial["trial_id"])


def add_isolation_args(q: argparse.ArgumentParser) -> None:
    state = ("true", "false", "unknown")
    q.add_argument("--session-fresh", choices=state, default="true")
    q.add_argument("--clean-working-directory", choices=state, default="true")
    q.add_argument("--web-enabled", choices=state)
    q.add_argument("--tools-enabled", choices=state)
    q.add_argument("--files-available", choices=state)
    q.add_argument("--project-context-available", choices=state)
    q.add_argument("--persistent-memory-enabled", choices=state)
    q.add_argument("--system-context-known", choices=state, default="unknown")
    q.add_argument("--isolation-note", action="append")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Harness/model-agnostic knowledge stratigraphy helper"
    )
    p.add_argument("--pack", type=Path, default=DEFAULT_PACK)
    p.add_argument("--targets", type=Path, default=DEFAULT_TARGETS)
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="list probes")

    q = sub.add_parser("prompt", help="print one blinded probe")
    q.add_argument("probe_id")

    q = sub.add_parser("batch", help="print a randomized blinded probe batch")
    q.add_argument("--seed", type=int, default=0)

    q = sub.add_parser("reveal", help="show answer-key metadata for one probe")
    q.add_argument("probe_id")

    sub.add_parser("targets", help="list enabled harness × model targets")

    q = sub.add_parser("target", help="show one target definition")
    q.add_argument("target_id")

    q = sub.add_parser("matrix", help="expand targets × probes × repetitions")
    q.add_argument("--repetitions", type=int, default=3)
    q.add_argument("--seed", type=int, default=0)
    q.add_argument("--json", action="store_true")

    q = sub.add_parser("new-run", help="create run metadata for one target")
    q.add_argument("--target-id", required=True)
    q.add_argument("--run-id")
    q.add_argument("--comparison-group")
    q.add_argument("--change-event")
    q.add_argument("--note", action="append")

    q = sub.add_parser("record", help="append one trial record to JSONL")
    q.add_argument("probe_id")
    q.add_argument("--target-id", required=True)
    q.add_argument("--run-id", required=True)
    q.add_argument("--output", type=Path, required=True)
    q.add_argument("--order", type=int)
    q.add_argument("--response")
    q.add_argument("--latency-ms", type=int)
    q.add_argument("--stop-reason")
    q.add_argument("--input-tokens", type=int)
    q.add_argument("--output-tokens", type=int)

    q.add_argument("--observed-harness-version")
    q.add_argument("--observed-harness-build")
    q.add_argument("--observed-model")
    q.add_argument("--observed-model-id")
    q.add_argument("--observed-reasoning")
    q.add_argument("--observed-route")
    q.add_argument(
        "--observed-source",
        choices=("native_telemetry", "transcript", "api", "harness_output", "manual", "unknown"),
    )
    q.add_argument("--observed-evidence")

    q.add_argument("--score", type=int, choices=(0, 1, 2))
    q.add_argument("--confidence", choices=("low", "medium", "high"))
    q.add_argument("--calibration", choices=("poor", "mixed", "good"))
    q.add_argument("--recognized-signal", action="append")
    q.add_argument("--missing-signal", action="append")
    q.add_argument("--disqualifier", action="append")
    q.add_argument("--score-note", action="append")

    q.add_argument("--comparison-group")
    q.add_argument("--change-event")
    q.add_argument("--comparison-note", action="append")
    add_isolation_args(q)

    return p


def main() -> None:
    args = parser().parse_args()
    handlers = {
        "list": cmd_list,
        "prompt": cmd_prompt,
        "batch": cmd_batch,
        "reveal": cmd_reveal,
        "targets": cmd_targets,
        "target": cmd_target,
        "matrix": cmd_matrix,
        "new-run": cmd_new_run,
        "record": cmd_record,
    }
    handlers[args.command](args)


if __name__ == "__main__":
    main()

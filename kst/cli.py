"""CLI boundary. Defaults exercise mocks, never paid/native model sessions."""
from __future__ import annotations

import argparse
import json
import random
import sys
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .adapters import Capture
from .analysis import summarize
from .core import DATA, Invalid, blinded_prompt, digest, enabled_targets, find_probe
from .core import find_target, load_pack, load_targets, plan, requested_target_record
from .engine import execute, trial_start
from .telemetry import Ledger, score


def emit(value: Any) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False))


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Knowledge stratigraphy framework")
    parser.add_argument("--pack", type=Path, default=DATA / "demo-pack.json")
    parser.add_argument("--targets", type=Path, default=DATA / "demo-targets.json")
    subs = parser.add_subparsers(dest="command", required=True)
    for command in ("list", "targets", "validate"):
        subs.add_parser(command)
    for command, parameter in (("prompt", "probe_id"), ("reveal", "probe_id"),
                               ("target", "target_id")):
        subs.add_parser(command).add_argument(parameter)
    for command in ("matrix", "batch", "export", "run"):
        sub = subs.add_parser(command)
        sub.add_argument("--seed", type=int, default=0)
        sub.add_argument("--repetitions", type=int, default=3 if command != "batch" else 1)
        if command == "matrix":
            sub.add_argument("--json", action="store_true", help="JSON is already the default")
        if command in ("export", "run"):
            sub.add_argument("--output", type=Path, required=True)
        if command == "run":
            sub.add_argument("--timeout", type=float, default=60)
    sub = subs.add_parser("new-run")
    sub.add_argument("--target-id", required=True)
    sub.add_argument("--run-id")
    sub.add_argument("--comparison-group")
    sub.add_argument("--change-event")
    sub = subs.add_parser("record")
    sub.add_argument("probe_id")
    sub.add_argument("--target-id", required=True)
    sub.add_argument("--run-id", required=True)
    sub.add_argument("--output", type=Path, required=True)
    sub.add_argument("--response")
    sub.add_argument("--prompt-file", type=Path, help="Capture the actual prompt when wording differs")
    sub.add_argument("--order", type=int)
    sub.add_argument("--repetition", type=int, default=1)
    sub.add_argument("--comparison-group")
    sub.add_argument("--change-event")
    sub.add_argument("--latency-ms", type=float)
    sub.add_argument("--input-tokens", type=int)
    sub.add_argument("--output-tokens", type=int)
    for field in ("harness-version", "harness-build", "model", "model-id", "reasoning", "route",
                  "source", "evidence"):
        sub.add_argument("--observed-" + field)
    for field in ("session-fresh", "clean-working-directory", "web-enabled", "tools-enabled",
                  "files-available", "project-context-available", "persistent-memory-enabled",
                  "system-context-known"):
        sub.add_argument("--" + field, choices=("true", "false", "unknown"), default="unknown")
    sub = subs.add_parser("score")
    sub.add_argument("ledger", type=Path)
    sub.add_argument("trial_id")
    sub.add_argument("value", type=int, choices=(0, 1, 2))
    sub.add_argument("--scorer", required=True)
    sub.add_argument("--rubric-version", required=True)
    sub.add_argument("--assessment", required=True, choices=("recognized", "partial", "unknown",
                     "wrong", "rejected", "speculative", "fabricated"))
    sub.add_argument("--note", default="")
    subs.add_parser("report").add_argument("ledger", type=Path)
    return parser


def record(args: argparse.Namespace, pack: dict[str, Any], targets: dict[str, Any]) -> None:
    from .core import validate
    target = find_target(targets, args.target_id)
    probe = find_probe(pack, args.probe_id)
    if args.repetition < 1:
        raise Invalid("Repetition must be positive")
    response = args.response if args.response is not None else sys.stdin.read()
    if not response.strip():
        raise Invalid("A manual capture must contain a response")
    prompt = (args.prompt_file.read_text(encoding="utf-8") if args.prompt_file
              else blinded_prompt(pack, probe))
    observed = {"harness_version": args.observed_harness_version,
                "harness_build": args.observed_harness_build, "model_label": args.observed_model,
                "model_id": args.observed_model_id, "reasoning": args.observed_reasoning,
                "route_or_backend": args.observed_route,
                "evidence_source": args.observed_source or "operator_unverified",
                "evidence_raw": args.observed_evidence}
    fields = ("session_fresh", "clean_working_directory", "web_enabled", "tools_enabled",
              "files_available", "project_context_available", "persistent_memory_enabled",
              "system_context_known")
    capture = asdict(Capture(response, "manual", observed,
                    {name: getattr(args, name) for name in fields},
                    latency_ms=args.latency_ms,
                    token_usage={"input": args.input_tokens, "output": args.output_tokens}))
    validate(capture, "capture")
    trial_id = str(uuid.uuid4())
    ledger = Ledger(args.output)
    ledger.append("trial.started", trial_start(args.run_id, trial_id, pack, probe, target, prompt,
                  order=args.order, repetition=args.repetition,
                  prompt_source="operator_file" if args.prompt_file else "pack_rendered",
                  comparison_group=args.comparison_group, change_event=args.change_event))
    ledger.append("trial.finished", {"run_id": args.run_id, "trial_id": trial_id,
                  "status": "completed", "capture": capture, "error": None, "cleanup_error": None})
    print(trial_id)


def dispatch(args: argparse.Namespace) -> int:
    command = args.command
    if command == "report":
        emit(summarize(Ledger(args.ledger)))
        return 0
    if command == "score":
        emit(score(Ledger(args.ledger), args.trial_id, args.value, args.scorer,
                   args.rubric_version, args.assessment, args.note))
        return 0
    if command in ("targets", "target"):
        targets = load_targets(args.targets)
        if command == "target":
            emit(find_target(targets, args.target_id))
        else:
            for target in enabled_targets(targets):
                print(f'{target["id"]}\t{target["harness"]["name"]}\t{target["model"]["requested_label"]}')
        return 0
    pack = load_pack(args.pack)
    if command == "list":
        for probe in pack["probes"]:
            print(f'{probe["id"]}\t{probe["stratum"]}\t{probe["kind"]}')
        return 0
    if command in ("prompt", "reveal"):
        probe = find_probe(pack, args.probe_id)
        if command == "prompt":
            print(blinded_prompt(pack, probe))
        else:
            emit(probe)
        return 0
    if command == "batch":
        if args.repetitions < 1:
            raise Invalid("Repetitions must be positive")
        probes = list(pack["probes"]) * args.repetitions
        random.Random(args.seed).shuffle(probes)
        for index, probe in enumerate(probes, 1):
            print(f"--- prompt {index} ---")
            print(blinded_prompt(pack, probe))
        return 0
    targets = load_targets(args.targets)
    if command == "validate":
        emit({"valid": True, "pack_hash": digest(pack), "targets_hash": digest(targets)})
    elif command == "new-run":
        emit({"schema_version": "2.0.0", "run_id": args.run_id or str(uuid.uuid4()),
              "target": requested_target_record(find_target(targets, args.target_id)),
              "pack_hash": digest(pack), "comparison_group": args.comparison_group,
              "change_event": args.change_event})
    elif command == "record":
        record(args, pack, targets)
    elif command == "run":
        result = execute(pack, targets, args.output, args.repetitions, args.seed, args.timeout)
        emit(result)
        return 0 if result["status"] == "completed" else 1
    else:
        schedule = plan(pack, targets, args.repetitions, args.seed)
        if command == "matrix":
            emit(schedule)  # Controller-only: never paste this mapping into a target.
        elif command == "export":
            args.output.mkdir(parents=True, exist_ok=False)
            blind = args.output / "blind"
            blind.mkdir()
            for row in schedule["trials"]:
                (blind / f'{row["slot_id"]}.txt').write_text(
                    blinded_prompt(pack, find_probe(pack, row["probe_id"])), encoding="utf-8")
            (args.output / "manifest.json").write_text(json.dumps(schedule, indent=2), encoding="utf-8")
            emit({"trials": len(schedule["trials"]), "directory": str(args.output)})
    return 0


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    try:
        return dispatch(args)
    except (Invalid, OSError, ValueError, TypeError) as exc:
        print(f"kst: {exc}", file=sys.stderr)
        return 2

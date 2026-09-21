"""Validation, identity, and deterministic planning. No adapter side effects."""
from __future__ import annotations

import hashlib
import json
import random
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

DATA = Path(__file__).parent / "data"


class Invalid(ValueError):
    """Invalid experiment input or inconsistent evidence."""


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise Invalid(f"Cannot read JSON {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise Invalid(f"Expected an object in {path}")
    return data


@lru_cache(maxsize=8)
def validator_for(schema_name: str) -> Draft202012Validator:
    schema = load_json(DATA / f"{schema_name}.schema.json")
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def validate(data: Any, schema_name: str) -> None:
    errors = sorted(validator_for(schema_name).iter_errors(data), key=lambda e: str(list(e.path)))
    if errors:
        error = errors[0]
        location = "/".join(str(p) for p in error.path) or "<root>"
        raise Invalid(f"{schema_name} at {location}: {error.message}")


def unique(items: list[dict[str, Any]]) -> None:
    ids = [item["id"] for item in items]
    if len(ids) != len(set(ids)):
        raise Invalid("Duplicate IDs are not allowed")


def load_pack(path: Path) -> dict[str, Any]:
    data = load_json(path)
    validate(data, "pack")
    unique(data["probes"])
    return data


def load_targets(path: Path) -> dict[str, Any]:
    data = load_json(path)
    validate(data, "targets")
    unique(data["targets"])
    return data


def find_probe(pack: dict[str, Any], probe_id: str) -> dict[str, Any]:
    return find(pack["probes"], probe_id)


def find_target(targets: dict[str, Any], target_id: str) -> dict[str, Any]:
    return find(targets["targets"], target_id)


def find(items: list[dict[str, Any]], item_id: str) -> dict[str, Any]:
    for item in items:
        if item["id"] == item_id:
            return item
    raise Invalid(f"Unknown ID: {item_id}")


def enabled_targets(targets: dict[str, Any]) -> list[dict[str, Any]]:
    return [target for target in targets["targets"] if target.get("enabled", True)]


def blinded_prompt(pack: dict[str, Any], probe: dict[str, Any]) -> str:
    return pack["pack"]["standard_preamble"] + "\n\n" + probe["prompt"]


def requested_target_record(target: dict[str, Any]) -> dict[str, Any]:
    h, m = target["harness"], target["model"]
    return {
        "target_id": target["id"],
        "harness_requested": {"name": h["name"], "mode": h.get("mode"),
                              "version": h.get("requested_version"),
                              "executable": h.get("executable")},
        "model_requested": {"provider": m.get("provider"), "family": m.get("family"),
                            "label": m["requested_label"],
                            "model_id": m.get("requested_model_id"),
                            "reasoning": m.get("requested_reasoning")},
        "runtime": deepcopy(target.get("runtime", {"adapter": "manual"})),
    }


def plan(pack: dict[str, Any], targets: dict[str, Any], repetitions: int = 3,
         seed: int = 0) -> dict[str, Any]:
    validate(pack, "pack")
    validate(targets, "targets")
    unique(pack["probes"])
    unique(targets["targets"])
    if type(repetitions) is not int or repetitions < 1:
        raise Invalid("Repetitions must be a positive integer")
    selected = sorted(enabled_targets(targets), key=lambda t: t["id"])
    if not selected:
        raise Invalid("No enabled targets")
    rows = [{"target_id": t["id"], "probe_id": p["id"], "repetition": r}
            for t in selected for p in sorted(pack["probes"], key=lambda p: p["id"])
            for r in range(1, repetitions + 1)]
    random.Random(seed).shuffle(rows)
    for index, row in enumerate(rows, 1):
        row["order"] = index
        row["slot_id"] = digest([digest(pack), digest(targets), seed, row])[:24]
    return {"schema_version": "2.0.0", "pack_hash": digest(pack),
            "targets_hash": digest(targets), "seed": seed,
            "repetitions": repetitions, "trials": rows}

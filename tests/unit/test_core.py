import json
import socket
from copy import deepcopy

import pytest
from jsonschema import Draft202012Validator

from kst.core import (DATA, Invalid, blinded_prompt, canonical, digest, enabled_targets,
                      find_probe, find_target, load_json, load_pack, load_targets,
                      plan, requested_target_record, validate)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("schema", sorted(DATA.glob("*.schema.json")), ids=lambda p: p.stem)
def test_schemas_are_real_draft_2020_12(schema):
    Draft202012Validator.check_schema(load_json(schema))


@pytest.mark.parametrize("repetitions", [0, -1, True, 1.5, "3"])
def test_invalid_repetition_count(pack, targets, repetitions):
    with pytest.raises(Invalid, match="positive integer"):
        plan(pack, targets, repetitions)


def test_planning_is_reproducible_without_mutating_inputs(pack, targets):
    before = deepcopy((pack, targets))
    a = plan(pack, targets, 4, 17)
    assert a == plan(pack, targets, 4, 17)
    b = plan(pack, targets, 4, 18)
    assert a["trials"] != b["trials"]
    assert len(a["trials"]) == 24
    assert len({r["slot_id"] for r in a["trials"]}) == 24
    assert (pack, targets) == before
    for target in targets["targets"]:
        for probe in pack["probes"]:
            assert sum(r["target_id"] == target["id"] and r["probe_id"] == probe["id"]
                       for r in a["trials"]) == 4


def test_disabled_targets_are_not_scheduled(pack, targets):
    targets["targets"][1]["enabled"] = False
    assert len(plan(pack, targets, 1)["trials"]) == 3
    targets["targets"][0]["enabled"] = False
    with pytest.raises(Invalid, match="No enabled"):
        plan(pack, targets)


def test_duplicate_ids_rejected(pack, targets, tmp_path):
    pack["probes"].append(deepcopy(pack["probes"][0]))
    path = tmp_path / "pack.json"
    path.write_text(json.dumps(pack))
    with pytest.raises(Invalid, match="Duplicate"):
        load_pack(path)
    targets["targets"].append(deepcopy(targets["targets"][0]))
    path.write_text(json.dumps(targets))
    with pytest.raises(Invalid, match="Duplicate"):
        load_targets(path)


@pytest.mark.parametrize("value", [[], {}, {"pack": {}}, {"pack": {}, "probes": []}])
def test_invalid_pack_shape(value):
    with pytest.raises(Invalid):
        validate(value, "pack")


def test_invalid_dates_and_target_booleans_rejected(pack, targets):
    pack["probes"][0]["observed_date"] = "2026-02-30"
    with pytest.raises(Invalid, match="date"):
        validate(pack, "pack")
    targets["targets"][0]["enabled"] = "false"
    with pytest.raises(Invalid, match="boolean"):
        validate(targets, "targets")


def test_unknown_ids_are_errors(pack, targets):
    assert find_probe(pack, "DEMO-CONTROL")["kind"] == "negative_control"
    assert find_target(targets, "mock-a")["harness"]["name"] == "Mock Harness"
    for function, data in ((find_probe, pack), (find_target, targets)):
        with pytest.raises(Invalid, match="Unknown ID"):
            function(data, "absent")


def test_load_errors_have_context(tmp_path):
    path = tmp_path / "input.json"
    with pytest.raises(Invalid, match="Cannot read"):
        load_json(path)
    path.write_text("{broken")
    with pytest.raises(Invalid, match="Cannot read"):
        load_json(path)
    path.write_text("[]")
    with pytest.raises(Invalid, match="Expected an object"):
        load_json(path)


def test_future_harness_and_model_are_data_not_enums(pack, one_target):
    target = one_target["targets"][0]
    target["harness"]["name"] = "Uninvented Harness"
    target["model"].update(requested_label="Future Model 99", requested_reasoning="novel")
    target["runtime"]["adapter"] = "future-protocol"
    assert len(plan(pack, one_target, 1)["trials"]) == 3
    requested = requested_target_record(target)
    assert requested["model_requested"]["reasoning"] == "novel"
    assert "observed" not in requested
    requested["runtime"]["adapter"] = "changed"
    assert target["runtime"]["adapter"] == "future-protocol"


def test_blind_prompt_contains_no_answer_key_or_metadata(pack):
    probe = pack["probes"][0]
    output = blinded_prompt(pack, probe)
    assert probe["prompt"] in output
    assert all(value not in output for value in (probe["id"], probe["stratum"],
                                                 probe["expected_signals"][0]))


def test_hashes_ignore_object_key_order_but_notice_prompt_changes(pack):
    assert digest({"b": 2, "a": 1}) == digest({"a": 1, "b": 2})
    before = digest(pack)
    pack["probes"][0]["prompt"] += " "
    assert digest(pack) != before
    assert "λ" in canonical({"text": "λ"})
    with pytest.raises(ValueError):
        canonical(float("nan"))


def test_offline_guard_is_active():
    with pytest.raises(AssertionError, match="Network"):
        socket.create_connection(("example.com", 443))


def test_legacy_compatibility_exports(pack, targets):
    import stratify
    assert stratify.enabled_targets(targets) == enabled_targets(targets)
    assert stratify.blinded_prompt(pack, pack["probes"][0]) == blinded_prompt(pack, pack["probes"][0])

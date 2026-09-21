import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from kst.cli import main
from kst.core import DATA, digest, load_json
from kst.telemetry import Ledger

pytestmark = pytest.mark.behavior
ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("argv", [
    ["list"], ["targets"], ["validate"], ["target", "mock-a"],
    ["prompt", "DEMO-LAYER-1"], ["reveal", "DEMO-LAYER-1"],
    ["matrix", "--repetitions", "2", "--seed", "7", "--json"],
    ["new-run", "--target-id", "mock-a", "--comparison-group", "ab"],
])
def test_public_cli_commands(argv, capsys):
    assert main(argv) == 0
    assert capsys.readouterr().out


def test_pack_and_target_inspection_are_independent(capsys):
    assert main(["--targets", "missing.json", "prompt", "DEMO-LAYER-1"]) == 0
    assert main(["--pack", "missing.json", "target", "mock-a"]) == 0


def test_blind_export_has_opaque_names_and_no_keys(tmp_path, pack, capsys):
    out = tmp_path / "export"
    assert main(["export", "--output", str(out), "--repetitions", "2"]) == 0
    manifest = load_json(out / "manifest.json")
    prompts = list((out / "blind").glob("*.txt"))
    assert len(prompts) == len(manifest["trials"]) == 12
    for path in prompts:
        assert len(path.stem) == 24
        assert not any(p["id"] in path.name or p["id"] in path.read_text() for p in pack["probes"])
        assert "expected_signals" not in path.read_text()
        assert "paper boats" not in path.read_text()
    assert main(["export", "--output", str(out)]) == 2
    assert len(list((out / "blind").glob("*.txt"))) == 12


def test_batch_is_one_pack_not_a_target_cross_product(capsys):
    assert main(["batch", "--seed", "3"]) == 0
    result = capsys.readouterr().out
    assert result.count("--- prompt") == 3
    assert "DEMO-" not in result
    assert main(["batch", "--repetitions", "0"]) == 2


def test_manual_capture_preserves_exact_text_and_unknowns(tmp_path, monkeypatch, capsys):
    ledger_path = tmp_path / "events.jsonl"
    prompt = tmp_path / "actual.txt"
    prompt.write_text("Actual prompt with trailing space. \n", encoding="utf-8")
    response = "λ answer with spacing \n\n"
    monkeypatch.setattr(sys, "stdin", io.StringIO(response))
    assert main(["record", "DEMO-LAYER-1", "--target-id", "mock-a", "--run-id", "manual-1",
                 "--output", str(ledger_path), "--prompt-file", str(prompt),
                 "--observed-model-id", "native-y", "--observed-source", "harness_output"]) == 0
    tid = capsys.readouterr().out.strip()
    history = Ledger(ledger_path).read()
    assert history[0]["payload"]["prompt"]["exact_text"] == prompt.read_text()
    capture = history[1]["payload"]["capture"]
    assert capture["raw_text"] == response
    assert capture["mode"] == "manual"
    assert all(state == "unknown" for state in capture["isolation"].values())
    assert capture["observed"]["model_id"] == "native-y"
    assert main(["score", str(ledger_path), tid, "2", "--scorer", "xor",
                 "--rubric-version", "1", "--assessment", "recognized"]) == 0
    capsys.readouterr()
    assert main(["report", str(ledger_path)]) == 0
    assert json.loads(capsys.readouterr().out)["groups"][0]["full_recognition_rate"] == 1


def test_manual_capture_accepts_explicit_response_and_isolation(tmp_path, capsys):
    out = tmp_path / "events.jsonl"
    assert main(["record", "DEMO-CONTROL", "--target-id", "mock-a", "--run-id", "manual",
                 "--output", str(out), "--response", "I do not recognize that.",
                 "--session-fresh", "true", "--web-enabled", "false"]) == 0
    capture = Ledger(out).read()[-1]["payload"]["capture"]
    assert capture["isolation"]["session_fresh"] == "true"
    assert capture["observed"]["model_id"] is None
    assert capture["observed"]["evidence_source"] == "operator_unverified"


@pytest.mark.parametrize("extra", [
    ["--response", ""], ["--response", "ok", "--latency-ms", "-3"],
    ["--response", "ok", "--repetition", "0"],
])
def test_invalid_manual_capture_writes_nothing(tmp_path, extra, capsys):
    out = tmp_path / "events.jsonl"
    assert main(["record", "DEMO-LAYER-1", "--target-id", "mock-a", "--run-id", "manual",
                 "--output", str(out), *extra]) == 2
    assert not out.exists()


def test_cli_mock_run_produces_report(tmp_path, capsys):
    out = tmp_path / "run"
    assert main(["run", "--output", str(out), "--repetitions", "1"]) == 0
    assert json.loads(capsys.readouterr().out)["trial_count"] == 6
    assert main(["report", str(out / "events.jsonl")]) == 0
    assert {r["mode"] for r in json.loads(capsys.readouterr().out)["groups"]} == {"mock"}


def test_invalid_cli_input_is_clear_without_traceback(capsys):
    assert main(["prompt", "no-such-probe"]) == 2
    assert "Unknown ID" in capsys.readouterr().err
    assert main(["matrix", "--repetitions", "0"]) == 2


@pytest.mark.parametrize("entry", [["stratify.py"], ["-m", "kst"]])
def test_real_process_entrypoints(entry):
    result = subprocess.run([sys.executable, *entry, "validate"], cwd=ROOT,
                            capture_output=True, text=True, timeout=15, check=False)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["valid"] is True

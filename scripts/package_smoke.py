#!/usr/bin/env python3
"""Build a wheel and exercise its installed data outside the source checkout."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix="kst-wheel-") as directory:
    temp = Path(directory)
    wheels, install = temp / "wheels", temp / "installed"
    subprocess.run([sys.executable, "-m", "pip", "wheel", ".", "--no-deps",
                    "--no-build-isolation", "--wheel-dir", str(wheels)], cwd=root, check=True)
    wheel = next(wheels.glob("*.whl"))
    subprocess.run([sys.executable, "-m", "pip", "install", "--no-deps", "--target",
                    str(install), str(wheel)], cwd=temp, check=True)
    env = {**os.environ, "PYTHONPATH": str(install), "PYTHONNOUSERSITE": "1"}
    for command in (["validate"], ["run", "--output", str(temp / "run"), "--repetitions", "1"]):
        subprocess.run([sys.executable, "-m", "kst", *command], cwd=temp, env=env, check=True)

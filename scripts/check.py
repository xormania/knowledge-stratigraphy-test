#!/usr/bin/env python3
"""The same offline checks run locally and in CI after dependency installation."""
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
commands = [
    [sys.executable, "-m", "compileall", "-q", "kst", "stratify.py"],
    [sys.executable, "-m", "pytest", "--cov=kst", "--cov-branch",
     "--cov-report=term-missing", "--cov-report=xml", "--junitxml=junit.xml"],
    [sys.executable, "stratify.py", "validate"],
]
for command in commands:
    result = subprocess.run(command, cwd=root, check=False)
    if result.returncode:
        raise SystemExit(result.returncode)

#!/usr/bin/env python3
"""Compatibility entry point; implementation lives in the reusable kst package."""
from kst.cli import main
from kst.core import (blinded_prompt, enabled_targets, find_probe, find_target,
                      load_json, load_pack, load_targets, requested_target_record)

if __name__ == "__main__":
    raise SystemExit(main())

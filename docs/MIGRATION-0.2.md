# Moving from the original helper to 0.2

The single-file helper is now a `kst` package. `stratify.py` remains a compatibility
entry point and exports the original loading/lookup/prompt helpers. Install the runtime
first; the framework now uses `jsonschema` rather than handwritten schema checks.

Default packs/targets are synthetic and mock-only. Select the old worked example and
manual target file explicitly to use them. Their contents remain in the repository.

The files named `schemas/*.schema.example.json` are historical descriptive examples,
not executable JSON Schemas. Active validators live in `kst/data/*.schema.json`.

Telemetry is now event schema **2.0.0**, not the earlier one-object-per-trial 1.x shape.
New logs contain lifecycle events and independent score revisions. Existing 1.x logs
are preserved and are not silently rewritten or accepted as 2.0. An explicit importer
can be added later without inventing missing observations.

`record` captures a raw answer. Inline `--score`, `--confidence`, and `--calibration`
from older iterations are replaced by the separate `score` command with a scorer,
rubric version, and assessment. Run `record --help` and `score --help` for supported
arguments. Manual isolation defaults changed from assumed fresh/clean to `unknown`.

`matrix` emits controller-side JSON by default; `--json` remains accepted.
`batch` prints each probe without semantic IDs and does not multiply it by target count.
`export` writes opaque prompt filenames plus a separate private mapping manifest.
Neither the old semantic probe IDs nor answer keys belong in the target's prompt.

This release supplies an executable adapter boundary and mock implementation, not native
Claude Code/Codex/Grok Build automation. Existing manual capture remains universal.

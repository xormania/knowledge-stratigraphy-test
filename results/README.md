# Local results

Use `results/<run-id>.jsonl` for manual captures and `runs/<run-name>/events.jsonl`
for planned mock/native runs. Both locations are ignored by Git except this guide.

The current format is the version 2 event stream described in `TELEMETRY.md`.
A response is not automatically scored. Append an assessment with `kst score` and
rebuild a report with `kst report`. Do not edit earlier events to revise a score.

Exact responses and controller snapshots may contain sensitive material and answer
keys. Review evidence before sharing. Nothing is uploaded automatically.

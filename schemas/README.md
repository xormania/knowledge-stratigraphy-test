# Schema locations

The `*.schema.example.json` files in this directory describe the early 0.1 designs.
They are retained for history and are not JSON Schema validators.

Machine-enforced Draft 2020-12 contracts now live in `kst/data/`:
`pack.schema.json`, `targets.schema.json`, `capture.schema.json`, and `event.schema.json`.
They ship in the Python wheel and are exercised by the offline suite.

See [migration notes](../docs/MIGRATION-0.2.md) before importing earlier trial logs.

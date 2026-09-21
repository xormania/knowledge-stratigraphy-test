# Working from this foundation

Begin with a behavior the framework should exhibit. Add the regression test at the
appropriate boundary, implement the smallest reusable change, and run both check scripts.

Keep knowledge content in packs, model/harness selection in targets, native I/O in
adapters, and interpretation in reports. Do not add vendor-specific rules to the planner
or encode today's model names as schema enums.

A new native adapter needs an offline transport double, protocol conformance tests,
and failure-path behavior tests. A new event shape needs a schema version and migration
notes. Never rewrite old response or scoring evidence to make a new interpretation fit.

Defaults and CI must stay synthetic and offline. Do not add live model calls, global
harness configuration changes, credential reads, or permission bypasses to a normal test.
Do not treat a read-only sandbox or an empty working directory as proof that all context
and retrieval are disabled. Preserve unknowns and their measurement limitations.

Use the current directions from xor when scope changes. Historical examples and design
notes are source material, not authority against later project direction.

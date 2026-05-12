# Lane: benchmark-harness-schema-parity-test-fix

## Goal

Repair the focused schema/parity benchmark-harness tests committed in
`8a7d44f` so they actually run under pytest. Planner review reproduced the
failure with:

```bash
rtk python -m pytest benchmarks/harness/tests/test_schema_parity.py -q
```

Both tests error during setup because they request a fixture named `tmp`, which
is not a pytest fixture in this environment. The available temporary-path
fixture is `tmp_path`.

## Required reading

1. `docs/parallel-sessions.md`
2. `docs/parallel-sessions/MASTER_PLAN.md`
3. `docs/specs/benchmark-harness.md`
4. `benchmarks/harness/tests/test_schema_parity.py`

## Writable scope

- `benchmarks/harness/tests/test_schema_parity.py`
- `docs/parallel-sessions/MASTER_PLAN.md` row note only, if status changes
- the matching `codex-tasks/g4gpu/worker-1.txt` queue file to pop/claim this task

Do not refactor production harness modules in this lane unless the fixture fix
exposes a separate reproducible failure. Do not run or submit SLURM jobs.

## One compact-safe iteration

1. Reproduce the error:
   ```bash
   rtk python -m pytest benchmarks/harness/tests/test_schema_parity.py -q
   ```
2. Make the smallest test fix so the temporary directory fixture resolves and
   still passes `Path` objects to the helpers.
3. Run the focused schema/parity tests and the builder/runner tests:
   ```bash
   rtk python -m pytest benchmarks/harness/tests/test_schema_parity.py -q
   rtk python -m pytest tests/test_benchmark_harness_builder_runner.py -q
   ```
4. If both pass, update `MASTER_PLAN.md` to `DONE` for this row with the exact
   commands and counts. If another failure appears, leave the row `BLOCKED` with
   the new error and stop.

## Verification

```bash
rtk wc -l benchmarks/harness/tests/test_schema_parity.py docs/parallel-sessions/MASTER_PLAN.md
rtk bash scripts/validate-csup-queues.sh
```

## Stop condition

Commit the focused test fix and status update, then stop. Do not broaden into
new harness features.

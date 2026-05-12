# Lane: benchmark-harness-reference-flag-guard

## Goal

Make the benchmark harness CLI fail closed when `--generate-reference` is used
before the dedicated reference-generation lane exists. Planner review of commit
`ed9544a` found that the flag is accepted by `python -m benchmarks.harness.run`
but currently renders an ordinary `benchmarks/raw/...` comparison job instead of
writing `benchmarks/reference/` and `MANIFEST.sha256` as required by
`docs/specs/benchmark-harness.md`.

## Files to edit

- `benchmarks/harness/run.py`
- `tests/test_benchmark_harness_builder_runner.py`

Do not submit SLURM jobs. Do not implement full reference generation in this
compact task; only make the unsupported flag safe and tested.

## Implementation steps

1. Add a guard near CLI argument validation: if `args.generate_reference` is set,
   exit nonzero with a clear message that reference generation is deferred to
   implementation task 7.
2. Keep existing `--help`, ordinary dry-run, `--submit`, and fail-closed
   `--collect` behavior unchanged.
3. Add a focused regression test proving
   `python -m benchmarks.harness.run --generate-reference ...` exits nonzero and
   mentions the deferred reference-generation task instead of printing an sbatch.
4. Re-run the focused benchmark-harness tests.

## Test command

```bash
rtk proxy python -m pytest tests/test_benchmark_harness_builder_runner.py -q
```

## Stop condition

Stop when the unsupported `--generate-reference` path fails closed, the focused
test suite passes, touched files remain under 500 lines, and `MASTER_PLAN.md` can
be updated from `NEXT` to `DONE` with the verification evidence.

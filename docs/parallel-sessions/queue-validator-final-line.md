# Lane: queue-validator-final-line

## Goal

Repair the codex-supervisor queue validator so it checks non-blank prompt or
queue entries even when a file lacks a trailing newline. This is a coordination
bugfix only; do not touch production simulation or reconstruction code.

## Why this exists

Planner review of commit `fcf5fe6` found a validator coverage gap while checking
the new meta DEBUGGER/VALIDATOR role guard:

- `bash scripts/validate-csup-queues.sh` reported `prompt lines checked: 28`.
- A robust Python `splitlines()` scan over `codex-prompts-*.txt` plus
  `codex-tasks/<session>/*.txt`, excluding `._*` AppleDouble files, counted 38
  non-comment prompt lines in the same checkout.
- Many active prompt/queue files are one-line or multi-line files without a
  final newline, so the shell `read` loop can undercount or skip final entries.

## Writable scope

You may edit only:

- `scripts/validate-csup-queues.sh`
- `tests/test_validate_csup_queues.py`
- `docs/parallel-sessions/MASTER_PLAN.md` for this lane row status/evidence
- `codex-tasks/meta/worker-0.txt` only to pop your claimed queue line, if needed

## Files you must NOT touch

- Production simulation or reconstruction code
- SLURM scripts, macros, Parquet outputs, or benchmark results
- Other queue files, except read-only inspection
- `codex-prompts-*.txt` and existing prompt contents, except read-only evidence

## Required reading

1. `docs/parallel-sessions.md`
2. `docs/parallel-sessions/MASTER_PLAN.md`
3. This file
4. `scripts/validate-csup-queues.sh`
5. `tests/test_validate_csup_queues.py`

## One compact-safe iteration

1. Reproduce the coverage gap with a small throwaway command or by reading the
   current line-count evidence above.
2. Add a RED pytest regression using a temporary repo fixture where the only
   invalid prompt/queue line is the final line and has no trailing newline.
3. Fix `scan_file()` so it processes the final unterminated line, e.g. by using
   a `read` loop that continues when `line` is non-empty at EOF.
4. Preserve existing behavior for comments, blank lines, `--fix`, AppleDouble
   `._*` files, word/character caps, lane-token validation, and meta role guards.
5. Run the verification commands below.
6. Update the `Queue validator final-line scan regression` row in
   `MASTER_PLAN.md` from `NEXT` to `DONE` with exact test and validator output.
7. Stop after the compact fix; do not launch supervisor sessions or submit jobs.

## Verification commands

```bash
rtk python -m pytest tests/test_validate_csup_queues.py -q
rtk bash -n scripts/validate-csup-queues.sh
rtk bash scripts/validate-csup-queues.sh
```

The validator should report zero failures. If prompt files change before your
run, record both the validator-reported prompt-line count and a robust expected
count from `splitlines()` in the MASTER_PLAN evidence.

## Stop condition

Stop when the regression test fails before the fix, passes after the fix, the
validator scans the final unterminated lines, and the MASTER_PLAN row is updated.
If the current queue contains invalid prompt lines once final-line scanning is
fixed, do not auto-comment them; record the failures and queue precise follow-up
repairs instead.

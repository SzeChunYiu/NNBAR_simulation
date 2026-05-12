# Lane: coordinate-utilities-file-cap-split

## Goal

Restore the full test suite by splitting `nnbar_reconstruction/utils/coordinates.py`
below the pre-addition guard without changing public coordinate/math behavior.

## Background

Planner verification on 2026-05-12 failed:

```text
FAILED tests/test_file_caps.py::test_coordinate_utilities_stay_below_pre_addition_guard
AssertionError: nnbar_reconstruction/utils/coordinates.py has 496 lines
```

`tests/test_file_caps.py` now requires both
`nnbar_reconstruction/utils/coordinates.py` and
`nnbar_reconstruction/utils/event_quantities.py` to stay at or below 450 lines.
`event_quantities.py` is currently 133 lines; `coordinates.py` must be split
before further utility additions.

## Writable files

- `nnbar_reconstruction/utils/coordinates.py`
- New helper module(s) under `nnbar_reconstruction/utils/`
- `nnbar_reconstruction/utils/__init__.py` only if exports must be preserved
- Tests only if import-surface regressions are needed
- `docs/parallel-sessions/MASTER_PLAN.md`

Do not edit simulation C++, SLURM scripts, data outputs, or unrelated
reconstruction subsystems.

## Required reading

- `docs/parallel-sessions.md`
- `docs/parallel-sessions/MASTER_PLAN.md`
- `CODING_STANDARDS.md` §1
- `tests/test_file_caps.py`

## Implementation steps

1. Run the failing focused test first and capture the failure:
   `rtk python -m pytest tests/test_file_caps.py::test_coordinate_utilities_stay_below_pre_addition_guard -q`.
2. Split a coherent responsibility from `coordinates.py` into one or more
   sibling modules (for example momentum/invariant-mass helpers or cone
   geometry helpers). Keep backward-compatible imports from `coordinates.py`
   so existing callers do not change.
3. Keep every touched Python/test file under 450 lines when possible and under
   the hard 500-line cap.
4. Add or adjust a focused import-surface regression only if the split changes
   module exports.
5. Update the MASTER_PLAN row for this lane to `DONE` with exact verification.

## Verification commands

```bash
rtk python -m pytest tests/test_file_caps.py::test_coordinate_utilities_stay_below_pre_addition_guard -q
rtk proxy bash -lc 'python -m pytest tests/ -x -q 2>&1 | tail -20'
rtk proxy bash -lc 'wc -l nnbar_reconstruction/utils/coordinates.py nnbar_reconstruction/utils/event_quantities.py nnbar_reconstruction/utils/*.py | sort -n'
rtk bash scripts/validate-csup-queues.sh
```

## Stop condition

Stop after focused/full tests pass, touched files satisfy the line caps, and
MASTER_PLAN marks this task `DONE`.

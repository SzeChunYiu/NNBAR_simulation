# Lane: hibeam-acts-metric-shape-fix

## Goal

Tighten the HIBEAM ACTS/Kalman evidence audit so `sigma_r` and `epsilon`
metric fields fail closed when they are non-empty dictionaries but do not carry
an actual metric value. Planner review of commit `c52583d` reproduced that
`{"definition": "no numeric value"}` currently satisfies both metric fields,
which is weaker than the thesis-readiness row claim that σ_r and ε evidence are
required before use.

## Files

- Edit: `nnbar_reconstruction/analysis/hibeam_acts_audit.py`
- Test: `tests/test_hibeam_acts_audit.py`
- Update: `docs/parallel-sessions/MASTER_PLAN.md` status/notes only after
  verification passes.

Do not edit `acts_tracking/`, run training, promote HIBEAM performance numbers,
submit SLURM jobs, or change any simulation/G4GPU files.

## Implementation steps

1. Re-read `docs/parallel-sessions.md`, this spec, `CODING_STANDARDS.md`, and
   the existing HIBEAM ACTS audit tests.
2. Add a failing regression in `tests/test_hibeam_acts_audit.py` showing that a
   complete evidence manifest whose `sigma_r` or `epsilon` field is a dictionary
   without a concrete `value` (for example only a `definition`) is not ready and
   emits stable blockers.
3. Implement the minimal fix in `hibeam_acts_audit.py`: metric dictionaries must
   contain a non-placeholder `value`; keep scalar numeric/string metrics working
   if they are non-placeholder.
4. Preserve the existing complete-manifest happy path and all existing
   fail-closed missing/TODO/status blockers.
5. Run focused tests, the full test suite, file-cap checks, and an import grep.
6. Mark this row `DONE` in `MASTER_PLAN.md` only after verification passes and
   include the new blocker names plus focused/full test results.

## Verification

```bash
rtk python -m pytest tests/test_hibeam_acts_audit.py -q
rtk proxy python -m pytest tests/ -x -q
rtk wc -l nnbar_reconstruction/analysis/hibeam_acts_audit.py \
          tests/test_hibeam_acts_audit.py \
          docs/parallel-sessions/MASTER_PLAN.md
rtk proxy bash -lc 'grep -RIn "import acts_tracking\\|from acts_tracking" nnbar_reconstruction/analysis/hibeam_acts_audit.py tests/test_hibeam_acts_audit.py || echo OK_NO_PRODUCTION_IMPORT'
```

Expected: focused/full tests pass, touched files stay under 500 lines, and the
import grep prints `OK_NO_PRODUCTION_IMPORT`.

## Stop condition

Stop after one compact test-first fix, verification evidence, and
`MASTER_PLAN.md` row update are committed. Do not start broader HIBEAM evidence
manifest design in this lane.

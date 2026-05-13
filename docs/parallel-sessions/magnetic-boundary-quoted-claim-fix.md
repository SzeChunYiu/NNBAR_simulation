# Lane: magnetic-boundary-quoted-claim-fix

## Goal

Patch the no-B-field boundary audit so a positive statement such as
"charge sign may be quoted from curvature" fails closed. The current
`magnetic_field_boundary.py` helper correctly blocks direct charge-sign and
momentum-from-curvature claims, but planner review found that the broad
`may be quoted` safe/deferred pattern incorrectly treats a positive quotation
claim as acceptable.

## Files

- Edit: `nnbar_reconstruction/analysis/magnetic_field_boundary.py`
- Test: `tests/test_magnetic_field_boundary.py`
- Update: `docs/parallel-sessions/MASTER_PLAN.md` status/notes only after
  verification passes.

Do not edit thesis plan documents, C++ simulation code, queue tooling, or submit
SLURM jobs.

## Implementation steps

1. Re-read `docs/parallel-sessions.md`, this spec, `CODING_STANDARDS.md`, and
   the existing magnetic-boundary tests.
2. Add a regression test proving that a no-B-field surface with
   "charge sign may be quoted from curvature" or equivalent positive
   quotation language emits `forbidden_magnetic_claim`.
3. Preserve the intended safe case: "charge sign may not be quoted" remains a
   deferred/negated no-blocker statement.
4. Fix the safe/deferred pattern logic without broadening the audit to accept
   positive charge-sign or curvature-momentum claims.
5. Run focused and full pytest, plus file-cap checks.
6. Mark the MASTER_PLAN row for this lane `DONE` only after verification passes
   and notes include the regression coverage.

## Verification

Run:

```bash
rtk python -m pytest tests/test_magnetic_field_boundary.py -q
rtk proxy python -m pytest tests/ -x -q
rtk wc -l nnbar_reconstruction/analysis/magnetic_field_boundary.py tests/test_magnetic_field_boundary.py docs/parallel-sessions/MASTER_PLAN.md
```

Expected: focused/full tests pass; touched files remain under 500 lines; the
new positive `may be quoted` regression fails closed while `may not be quoted`
stays accepted.

## Stop condition

Stop after one compact fix, tests, and MASTER_PLAN row update are committed.

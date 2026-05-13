# Lane: magnetic-field-boundary

## Goal

Add a compact no-B-field boundary closure so detector reconstruction cannot
quietly claim charge-sign or momentum-from-curvature information. The output may
be a fail-closed audit helper/report if the current evidence is only a documented
scope boundary.

## Files

- Create: `nnbar_reconstruction/analysis/magnetic_field_boundary.py`
- Test: `tests/test_magnetic_field_boundary.py`
- Read-only references:
  - `docs/rebuild_plans/07_simulation_atomic_walkthrough/07_12_field_model.md`
  - `docs/rebuild_plans/25_subsystem_tpc_hits_to_tracks.md`
  - `docs/rebuild_plans/26_subsystem_track_fit_and_pulls.md`
  - `docs/rebuild_plans/45_systematics_taxonomy.md`
- Update: `docs/parallel-sessions/MASTER_PLAN.md` status/notes only

Do not edit detector simulation, tracking production code, C++, or SLURM jobs.

## Implementation steps

1. Re-read `docs/parallel-sessions.md`, this spec, and `CODING_STANDARDS.md`.
2. Write failing tests for a boundary audit that distinguishes:
   - allowed straight-line/no-curvature statements;
   - forbidden charge-sign or momentum-from-curvature claims in the no-B-field
     baseline;
   - explicit systematics/deferred-scenario language as acceptable provenance;
   - missing boundary documentation as a blocker.
3. Implement a small immutable audit module that scans supplied text surfaces and
   returns blockers with the needed evidence, observable, and figure of merit.
4. Run the audit on the read-only plan documents above in a smoke test, but do
   not rewrite those plans in this lane.
5. Update this lane's `MASTER_PLAN.md` row to `DONE` only for the audit helper
   and tests; leave any future magnetic-field scenario implementation out of
   scope.

## Verification

Run:

```bash
rtk python -m pytest tests/test_magnetic_field_boundary.py -q
rtk zsh -lc 'python -m pytest tests/ -x -q 2>&1 | tail -20'
rtk wc -l nnbar_reconstruction/analysis/magnetic_field_boundary.py tests/test_magnetic_field_boundary.py docs/parallel-sessions/MASTER_PLAN.md
```

Expected: focused tests pass; full test command exits 0; every touched file is
<=500 lines.

## Stop condition

Stop after the compact audit helper/tests and `MASTER_PLAN.md` status update are
committed. Do not implement magnetic-field tracking or alter physics constants.

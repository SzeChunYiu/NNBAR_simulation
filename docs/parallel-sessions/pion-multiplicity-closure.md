# Lane: pion-multiplicity-closure

## Goal

Add a fail-closed audit for the thesis Ch. 9 truth-vs-reconstruction pion
multiplicity closure. The compact unit should not run simulations; it should
make the missing sample/artifact requirements explicit and verify that the
Table 9.1 `MIN_PION_COUNT` selection uses a provenance-checked multiplicity.

## Files

- Create: `nnbar_reconstruction/analysis/pion_multiplicity_closure.py`
- Test: `tests/test_pion_multiplicity_closure.py`
- Read-only references:
  - `nnbar_reconstruction/analysis/event_variables.py`
  - `nnbar_reconstruction/reconstruction/cutflow.py`
  - `docs/rebuild_plans/36_subsystem_event_variables.md`
- Update: `docs/parallel-sessions/MASTER_PLAN.md` status/notes only

Do not edit C++ or run simulations/SLURM jobs.

## Implementation steps

1. Re-read `docs/parallel-sessions.md`, this spec, and `CODING_STANDARDS.md`.
2. Write failing tests for an immutable closure audit that distinguishes:
   - source-backed truth and reconstructed charged/neutral/total pion counts;
   - missing truth multiplicity columns or missing reconstruction count columns;
   - a documented `MIN_PION_COUNT == 1` Table 9.1 gate;
   - absent `sig_foil_v3`/truth-vs-reco heatmap artifacts as blockers.
3. Implement a small audit module that accepts in-memory `pandas.DataFrame`
   inputs and optional artifact/provenance paths, returning `ready=False` unless
   truth counts, reco counts, and provenance are all present.
4. The blocker messages must name the needed sample, observable, and figure of
   merit: charged/neutral/total pion multiplicity truth-vs-reco confusion
   matrix or heatmap residuals.
5. Do not change cut constants or production selection behavior in this lane.
6. Update this lane's `MASTER_PLAN.md` row to `DONE` only for the audit helper
   and tests; leave physics closure blocked until real artifacts exist.

## Verification

Run:

```bash
rtk python -m pytest tests/test_pion_multiplicity_closure.py -q
rtk zsh -lc 'python -m pytest tests/ -x -q 2>&1 | tail -20'
rtk wc -l nnbar_reconstruction/analysis/pion_multiplicity_closure.py tests/test_pion_multiplicity_closure.py docs/parallel-sessions/MASTER_PLAN.md
```

Expected: focused tests pass; full test command exits 0; every touched file is
<=500 lines.

## Stop condition

Stop after the compact audit helper/tests and `MASTER_PLAN.md` status update are
committed. Do not stage or generate new physics samples in this iteration.

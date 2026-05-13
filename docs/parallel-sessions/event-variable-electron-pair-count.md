# Lane: event-variable-electron-pair-count

## Goal

Wire the completed electron-pair topology helper into event-variable output
without violating the 500-line rule. `analysis/event_variables.py` is already
555 lines, so the compact unit starts by splitting a coherent helper out before
adding `n_electron_pairs` and blocker fields.

## Files

- Modify/split first: `nnbar_reconstruction/analysis/event_variables.py`
- Prefer creating: `nnbar_reconstruction/analysis/event_particle_counts.py`
- Read-only unless a focused regression requires otherwise:
  `nnbar_reconstruction/reconstruction/electron_pair.py`
- Test: `tests/test_event_variables.py`
- Update: `docs/parallel-sessions/MASTER_PLAN.md` status/notes only

Do not edit C++ or run simulations/SLURM jobs.

## Implementation steps

1. Re-read `docs/parallel-sessions.md`, this spec, and `CODING_STANDARDS.md`.
2. Confirm `nnbar_reconstruction/analysis/event_variables.py` is over cap with
   `rtk wc -l`; do not add net lines to it until a split reduces it below 500.
3. Write failing tests showing `compute_event_variables(...).to_dict()` exposes:
   - `n_electron_pairs == 1` for an `ELECTRON_PAIR`/`ELECTRON_PAIR_MEMBER` pair;
   - `electron_pair_count_blocked is False` and an empty reason when TPC entries exist;
   - `electron_pair_count_blocked is True` with reason `missing_tpc_entry` when
     the count cannot be computed safely.
4. Extract particle-counting responsibilities into a small helper module, keeping
   existing `count_particles` import behavior compatible if possible.
5. Use `electron_pair_event_counts` from `nnbar_reconstruction/reconstruction/electron_pair.py`
   to populate new `EventVariables` dataclass fields and `to_dict()` keys.
6. Keep the Ch. 9 cutflow observable conversion unchanged unless a focused test
   proves a necessary adjustment.
7. Update this lane's `MASTER_PLAN.md` row to `DONE` only after tests pass and
   every touched source/test file is <=500 lines.

## Verification

Run:

```bash
rtk python -m pytest tests/test_event_variables.py tests/test_electron_pair_integration.py -q
rtk zsh -lc 'python -m pytest tests/ -x -q 2>&1 | tail -20'
rtk wc -l nnbar_reconstruction/analysis/event_variables.py nnbar_reconstruction/analysis/event_particle_counts.py tests/test_event_variables.py docs/parallel-sessions/MASTER_PLAN.md
```

Expected: focused tests pass; full test command exits 0; `event_variables.py`
is below 500 lines after the split.

## Stop condition

Stop after one split-and-wiring unit plus the `MASTER_PLAN.md` status update is
committed. If the split grows beyond this compact unit, commit only the split and
leave a blocker note instead of adding event-pair fields.

# Lane: electron-pair-integration

## Goal

Close the gap between the existing `identify_electron_pair` helper and the
thesis Ch. 8 requirement that e+/e- conversion pairs with TPC entry points
within 5 cm are represented consistently in object lists, pion searches, and
event-variable counts.

## Files

- Modify or split as needed: `nnbar_reconstruction/reconstruction/object_identification.py`
- Prefer creating helper files if integration would push a file over 500 lines,
  e.g. `nnbar_reconstruction/reconstruction/electron_pair.py`
- Test: `tests/test_electron_pair_integration.py`
- Update: `docs/parallel-sessions/MASTER_PLAN.md` status/notes only
- Read-only references:
  - `nnbar_reconstruction/analysis/event_variables.py`
  - `docs/rebuild_plans/24_reconstruction_question_tree/24_3_charged.md`
  - `docs/rebuild_plans/36_subsystem_event_variables.md`

## Implementation steps

1. Re-read `docs/parallel-sessions.md`, this spec, and `CODING_STANDARDS.md`.
2. Check file sizes first. `event_variables.py` is known to be near/over the
   cap in some branches; do not add lines to an over-cap file unless you split
   a coherent helper out first.
3. Write failing tests for:
   - two TPC entry points at exactly/just below/just above 5 cm;
   - pair rows counted once, not as two independent charged pions;
   - object/event variable output exposes an electron-pair count or explicit
     blocker state;
   - downstream pion-count logic cannot accidentally count the pair as a pion.
4. Implement the minimal integration in a small helper module, then wire it into
   existing object construction only if the file-cap rule remains satisfied.
5. If full event-variable integration requires a larger refactor, commit the
   helper/tests plus a blocker note and queue the split explicitly.
6. Update `MASTER_PLAN.md` with DONE only for the completed compact unit and
   name any remaining integration blocker.

## Verification

Run:

```bash
rtk python -m pytest tests/test_electron_pair_integration.py -q
rtk zsh -lc 'python -m pytest tests/ -x -q 2>&1 | tail -20'
rtk wc -l nnbar_reconstruction/reconstruction/object_identification.py nnbar_reconstruction/reconstruction/electron_pair.py nnbar_reconstruction/analysis/event_variables.py tests/test_electron_pair_integration.py docs/parallel-sessions/MASTER_PLAN.md
```

Expected: focused tests pass; full test command exits 0; touched files comply
with the 500-line cap or the commit stops with a documented blocker instead of
adding to an over-cap file.

## Stop condition

Stop after one compact integration/split unit and MASTER_PLAN status update.
Do not bundle broad event-variable refactors with this task.

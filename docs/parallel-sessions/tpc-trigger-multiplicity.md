# Lane: tpc-trigger-multiplicity

## Goal

Align the rolling event pre-selection trigger with thesis Chapter 7:
the trigger activates when **more than one TPC track** is detected and/or
calorimeter energy exceeds 100 MeV. The implementation must count TPC
tracks, not raw TPC hits, and keep the 50 ns window / 10 ns step behavior.

## Repo command rule

`AGENTS.md` imports `/Users/billy/.codex/RTK.md`: prefix shell commands
with `rtk` or wrap compound commands with `rtk proxy ...`.

## Read first

- `docs/parallel-sessions.md`
- `docs/parallel-sessions/MASTER_PLAN.md`
- this file
- `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/7_Reconstruction.tex`
  (verify the Chapter 7 event pre-selection wording before changing code)

## Writable targets

- `nnbar_reconstruction/reconstruction/event_preselection.py`
- `nnbar_reconstruction/config/nnbar_geometry.yaml`
- a focused test file under `tests/`

Do not change the Chapter 9 final cutflow threshold unless the thesis
evidence explicitly requires it; this lane is about the rolling trigger.

## Required work

1. Add failing regression tests showing:
   - one TPC track represented by many hits does **not** satisfy the TPC-only
     trigger;
   - two distinct TPC tracks in the same rolling window do satisfy it;
   - calorimeter energy at/above 100 MeV still triggers even with fewer than
     two TPC tracks;
   - both `track_id` and `Track_ID` column spellings are handled if practical.
2. Update the rolling trigger to count unique track identifiers when a track
   column is present. Ignore negative/noise track IDs if present.
3. Change the reconstruction trigger default from one TPC track to the thesis
   "more than one" requirement.
4. Keep backward-compatible behavior explicit for callers that pass only
   `tpc_times`; document whether that path counts hits or requires an added
   track-ID argument.
5. Run focused tests, then the full pytest suite if focused tests pass.

## Verification

```bash
rtk pytest -q tests/<new-or-updated-trigger-test>.py
rtk pytest -q
rtk proxy sh -c 'wc -l nnbar_reconstruction/reconstruction/event_preselection.py tests/<new-or-updated-trigger-test>.py'
```

All touched files must stay at or below 500 lines.

## Commit message

```text
fix(tpc-trigger): count tracks in rolling preselection

Plan: rolling-trigger-tpc-track-multiplicity
Lane: tpc-trigger-multiplicity
```

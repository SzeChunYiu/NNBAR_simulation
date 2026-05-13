# Lane: tpc-dedx-electrons

## Goal

Align the tracked-particle TPC dE/dx observable with the thesis Chapter 7
definition: per TPC layer, use ionization electrons divided by track length in
that layer, then take the lower-60% truncated mean.

## Scope

Pane 1 / Python reconstruction only.

Writable files:
- `nnbar_reconstruction/tracking/track_fitting.py`
- `nnbar_reconstruction/reconstruction/charged_reconstruction.py` only if the
  wrapper/docstring must clarify units
- focused tests under `tests/`
- `docs/parallel-sessions/MASTER_PLAN.md` only for final status

Do not change C++, CUDA, SLURM, LUNARC job state, cosmic queues, or the
charged pion/proton PID threshold formula in this lane. The optimized
`t(n)` calibration is a separate planned task.

## Required reading

- `docs/parallel-sessions.md`
- `docs/parallel-sessions/MASTER_PLAN.md`
- `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/7_Reconstruction.tex`
  subsection "TPC dE/dx calculation"
- `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/8_Object_Definition.tex`
  charged pion/proton dE/dx-vs-range definition
- `nnbar_reconstruction/tracking/track_fitting.py`
- `nnbar_reconstruction/reconstruction/charged_reconstruction.py`
- `nnbar_reconstruction/calibration/tpc_calibration.py`

## Verified current surfaces

- `nnbar_reconstruction/tracking/track_fitting.py` defines
  `compute_track_dedx`.
- `nnbar_reconstruction/reconstruction/charged_reconstruction.py` defines
  `calculate_truncated_dedx`.
- `nnbar_reconstruction/calibration/tpc_calibration.py` already has a separate
  `calculate_track_dedx` path that consumes `electrons`, useful for comparison
  but not automatically wired into charged reconstruction.

## Required changes

1. Add focused regressions for `compute_track_dedx` that fail under the current
   energy-deposit path:
   - when `electrons` and `eDep` are both present, the layer values must be
     derived from `electrons / layer_path_length`, not `eDep / layer_path_length`;
   - the returned layer array must preserve one value per valid TPC layer;
   - the truncated mean must use the lower 60% of layer values with
     `max(1, int(n_layers * 0.6))`;
   - missing `electrons` should either fall back to the documented legacy energy
     path or return zero, but the behavior must be explicit in tests/docstrings.
2. Update `compute_track_dedx` so the thesis electron-count convention is used
   whenever an `electrons` column is available.
3. Clarify units in docstrings/comments. The thesis observable is in e-/cm; do
   not silently describe it as MeV/cm after switching the source column.
4. Keep PID threshold constants unchanged. If the unit change exposes that
   `identify_pion_proton` is still uncalibrated, leave the existing
   MASTER_PLAN proposed task for `t(n)` calibration in place.
5. Mark this lane `DONE` in `MASTER_PLAN.md` after verification passes.

## Verification

Run:

```bash
rtk proxy python -m pytest tests/test_tpc_dedx.py -q
rtk proxy python -m pytest tests/ -x -q
rtk proxy sh -c 'wc -l nnbar_reconstruction/tracking/track_fitting.py nnbar_reconstruction/reconstruction/charged_reconstruction.py tests/test_tpc_dedx.py'
```

All touched files must stay at or below 500 lines.

## Commit message

```text
fix(tpc-dedx): use electron counts per layer

Plan: tpc-dedx-electrons
Lane: tpc-dedx-electrons
```

## Stop condition

Stop when the thesis electron-count dE/dx convention is pinned by focused
regressions, the full pytest suite passes, `MASTER_PLAN.md` marks this lane
`DONE`, and the changes are committed.

Handoff format:

```text
DONE: tpc-dedx-electrons
Files changed: ...
Verification: ...
Notes/blockers: ...
```

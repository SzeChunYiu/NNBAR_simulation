# Lane: scintillator-layer-count

## Goal

Align the Python reconstruction scintillator range convention with the thesis
10-layer scintillator module. The range observable should not silently use a
5-layer configuration when Chapter 4 and Chapter 7 describe 10 layers and range
examples that count all 10 layers.

## Scope

Pane 1 / Python reconstruction only.

Writable files:
- `nnbar_reconstruction/config/nnbar_geometry.yaml`
- `nnbar_reconstruction/reconstruction/charged_reconstruction.py`
- `nnbar_reconstruction/reconstruction/object_identification.py` only if the
  hardcoded range maximum must be centralized
- focused tests under `tests/`
- `docs/parallel-sessions/MASTER_PLAN.md` only for final status

Do not change C++, CUDA, SLURM jobs, LUNARC job state, cosmic queues, or charged
PID threshold values unless the thesis evidence requires it and the change is
pinned by tests.

## Required reading

- `docs/parallel-sessions.md`
- `docs/parallel-sessions/MASTER_PLAN.md`
- `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/4_HIBEAM_NNBAR_detector_setup.tex`
  scintillator-module paragraph: full detector modules contain 10 layers
- `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/7_Reconstruction.tex`
  scintillator-range subsection: range is the number of scintillator layers with
  signal; examples count 10 layers and 8 layers
- `nnbar_reconstruction/config/nnbar_geometry.yaml`
- `nnbar_reconstruction/reconstruction/charged_reconstruction.py`
- `nnbar_reconstruction/reconstruction/object_identification.py`

## Verified current surfaces

- `nnbar_reconstruction/config/nnbar_geometry.yaml` currently defines
  `scintillator.n_layers`.
- `nnbar_reconstruction/reconstruction/charged_reconstruction.py` defines
  `count_scintillator_layers`.
- `nnbar_reconstruction/reconstruction/object_identification.py` defines
  `expected_scintillator_range` and `identify_pion_proton`.

## Required changes

1. Add focused regressions showing the configured scintillator layer count is
   the thesis value 10 and that charged-object range reconstruction can count
   a particle with signals in all 10 layers.
2. Update `nnbar_geometry.yaml` so the scintillator layer count and nearby
   comments use the thesis 10-layer convention.
3. Ensure reconstructed scintillator range cannot exceed the configured layer
   count. Prefer deriving the maximum from config over duplicating a magic
   number; if invalid `Layer_ID` values appear, document and test the chosen
   ignore-or-clamp behavior.
4. Keep the existing charged pion/proton PID threshold formula unchanged unless
   a separate thesis calibration task is created.
5. Mark this lane `DONE` in `MASTER_PLAN.md` after verification passes.

## Verification

Run:

```bash
rtk proxy python -m pytest tests/test_config.py tests/test_scintillator_range.py -q
rtk proxy python -m pytest tests/ -x -q
rtk proxy sh -c 'wc -l nnbar_reconstruction/config/nnbar_geometry.yaml nnbar_reconstruction/reconstruction/charged_reconstruction.py nnbar_reconstruction/reconstruction/object_identification.py tests/test_scintillator_range.py'
```

All touched files must stay at or below 500 lines.

## Stop condition

Stop when the thesis 10-layer convention is reflected in config/range behavior,
focused and full pytest pass, `MASTER_PLAN.md` marks this lane `DONE`, and the
changes are committed.

Handoff format:

```text
DONE: scintillator-layer-count
Files changed: ...
Verification: ...
Notes/blockers: ...
```

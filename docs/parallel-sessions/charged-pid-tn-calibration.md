# Lane: charged-pid-tn-calibration

## Goal

Align charged pion/proton identification with the thesis Chapter 8
range-dependent threshold \(t(n)\) and the Chapter 7 TPC dE/dx convention
(electrons per centimeter). The current implementation still compares the new
TPC `electrons / layer_path_length` observable against a generic legacy
MeV/cm line (`2.5 + 0.1n`).

## Scope

Pane 1 / Python reconstruction only.

Writable files:
- `nnbar_reconstruction/reconstruction/object_identification.py` only to wire a
  helper and shrink the file below the 500-line cap if touched.
- New small helper module(s) under `nnbar_reconstruction/reconstruction/`, for
  example `charged_pid.py`, for the calibrated \(t(n)\) surface.
- `nnbar_reconstruction/config/nnbar_geometry.yaml` only for charged-PID
  threshold/config keys.
- Focused tests under `tests/`.
- `docs/parallel-sessions/MASTER_PLAN.md` only for final status/blocker notes.

Do not change C++, CUDA, SLURM/LUNARC job state, pi0 constants, cosmic weights,
or G4GPU files in this lane.

## Required reading

- `docs/parallel-sessions.md`
- `docs/parallel-sessions/MASTER_PLAN.md`
- `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/7_Reconstruction.tex`
  subsection `TPC dE/dx calculation`
- `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/8_Object_Definition.tex`
  section `Charged Pion and Proton`
- `nnbar_reconstruction/tracking/track_quantities.py`
- `nnbar_reconstruction/reconstruction/charged_reconstruction.py`
- `nnbar_reconstruction/reconstruction/object_identification.py`
- `nnbar_reconstruction/config/nnbar_geometry.yaml`

## Verified current surfaces

- `compute_track_dedx` now returns e-/cm when an `electrons` column is present.
- `identify_pion_proton` still uses `dedx_threshold_a=2.5` and
  `dedx_threshold_b=0.1` from `particle_id` config and documents MeV/cm.
- `object_identification.py` is currently 527 lines, so any edit must split or
  remove enough code to satisfy the 500-line cap.
- Thesis Ch.8 states the classification rule:
  proton if `TPC dE/dx >= t(n)`, charged pion if `TPC dE/dx < t(n)`, with
  optimized range-dependent cut values and reported efficiencies of 90.8% pion
  and 98.0% proton identification.
- Extracted thesis plots are available under
  `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/plots/Detector_Simulation/`
  as `TPC_dedx_vs_range_layer_*.jpg` and may be needed if no numeric table is
  present.

## Required changes

1. Evidence first: locate the numeric \(t(n)\) thresholds from thesis source,
   source data, committed notebooks/scripts, or a reproducible digitization of
   the extracted Ch.8 plot. Do **not** invent threshold numbers.
2. Add focused failing tests for the charged-PID threshold surface:
   - thresholds are keyed by scintillator range `n=1..10` and use e-/cm units;
   - values just below/above a selected threshold classify as pion/proton;
   - invalid or out-of-range scintillator labels are handled explicitly;
   - legacy MeV/cm config keys no longer drive the electron-count path.
3. Implement the smallest code change that passes the tests. Prefer a new
   `charged_pid.py` helper and keep `object_identification.py` as a thin wrapper
   to stay under 500 lines.
4. Update docstrings/comments so charged PID says e-/cm for the electron-count
   path. If a legacy MeV/cm fallback remains, label it explicitly.
5. If exact \(t(n)\) values cannot be recovered in one compact iteration, stop
   safely: leave production behavior unchanged, add a `BLOCKED` note to
   `MASTER_PLAN.md` with the exact missing artifact, and do not mark DONE.
6. Mark this lane `DONE` in `MASTER_PLAN.md` only after focused and full tests
   pass and the file-cap check is clean.

## Verification

Run:

```bash
rtk proxy python -m pytest tests/test_charged_pid.py -q
rtk proxy python -m pytest tests/ -x -q
rtk proxy sh -c 'wc -l nnbar_reconstruction/reconstruction/object_identification.py nnbar_reconstruction/reconstruction/charged_pid.py tests/test_charged_pid.py 2>/dev/null'
```

All touched files must stay at or below 500 lines.

## Commit message

```text
fix(charged-pid): calibrate t(n) threshold units

Plan: charged-pid-tn-calibration
Lane: charged-pid-tn-calibration
```

## Stop condition

Stop after one compact-safe iteration: either committed `DONE` with verification
output, or `BLOCKED` with the exact missing thesis/source artifact and no
invented threshold values.

Handoff format:

```text
DONE/BLOCKED: charged-pid-tn-calibration
Files changed: ...
Verification: ...
Notes/blockers: ...
```

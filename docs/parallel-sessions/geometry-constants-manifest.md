# Lane: geometry-constants-manifest

## Goal

Create a compact Python-side detector-constant manifest and audit that compares
thesis Chapter 4/5 detector constants with the reconstruction configuration. The
first iteration should make mismatches visible and tested without editing C++ or
inventing constants that were not verified from the thesis text.

## Writable scope

- `nnbar_reconstruction/analysis/geometry_constants.py` (new, or a smaller
  module under `nnbar_reconstruction/analysis/` if the worker finds a better
  name)
- `tests/test_geometry_constants_manifest.py`
- `docs/parallel-sessions/MASTER_PLAN.md` only for final lane-status notes

Do not edit C++ simulation, CUDA/G4GPU files, SLURM files, queues, or unrelated
reconstruction modules in this lane.

## Required reading

1. `docs/parallel-sessions.md`
2. `docs/parallel-sessions/MASTER_PLAN.md`
3. `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/4_HIBEAM_NNBAR_detector_setup.tex`
4. `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/5_Detector_simulation.tex`
5. `nnbar_reconstruction/config/nnbar_geometry.yaml`
6. `CODING_STANDARDS.md` for the 500-line cap

Before committing any file/function/path claim, re-run the verifier rule in
`docs/parallel-sessions.md`; do not trust this handoff for line numbers.

## One compact-safe iteration

Implement one tested audit unit:

1. Add a small manifest data structure for thesis detector constants that the
   worker verifies directly from the required reading. Candidate constants from
   the planner row include scintillator layer count, SF5 lead-glass block size,
   target/foil radius, TPC dimensions, and cosmic-veto/passive-shield envelope;
   include only values whose source text was checked.
2. Add a loader/auditor that reads `nnbar_geometry.yaml`, normalizes units, and
   returns structured `match`, `mismatch`, or `missing` results per constant.
3. Add tests with toy inputs for unit conversion and mismatch reporting.
4. Add one integration-style test against the current reconstruction config that
   asserts the audit report is deterministic and exposes known mismatches as
   data, not as an unhandled failure.
5. Treat C++ geometry as read-only. If the C++ source path is not available in
   this worktree, record a `missing` audit item or MASTER_PLAN blocker instead
   of inventing a path.

## Verification command

```bash
python -m pytest tests/test_geometry_constants_manifest.py -q
python -m pytest tests/ -x -q
wc -l nnbar_reconstruction/analysis/geometry_constants.py tests/test_geometry_constants_manifest.py
```

## Stop condition

Stop after the manifest/audit test passes, full tests pass, touched files remain
under 500 lines, and `MASTER_PLAN.md` says which constants are now audited and
which cross-repo geometry comparisons remain open.

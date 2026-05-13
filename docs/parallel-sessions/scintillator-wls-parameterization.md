# Lane: scintillator-wls-parameterization

## Goal

Audit whether the scintillator response implements the thesis Ch. 5 WLS SiPM
light-collection parameterization functions `f(r)` and `f(z)`. The expected
outcome may be a fail-closed blocker report if only simple light yield or
attenuation is implemented today.

## Files

- Create: `nnbar_reconstruction/analysis/scintillator_wls_contract.py`
- Test: `tests/test_scintillator_wls_contract.py`
- Update: `docs/parallel-sessions/MASTER_PLAN.md` status/notes only
- Read-only references:
  - `nnbar_reconstruction/analysis/geometry_constants.py`
  - `nnbar_reconstruction/analysis/timing_windows.py`
  - `NNBAR_Detector/` scintillator sensitive-detector/source files, if present
  - `docs/rebuild_plans/18_intercalibration.md`
  - `docs/rebuild_plans/24_reconstruction_question_tree/24_2_calorimetry.md`

Do not edit C++ or run simulations/SLURM jobs.

## Implementation steps

1. Re-read `docs/parallel-sessions.md`, this spec, and `CODING_STANDARDS.md`.
2. Write failing tests for a WLS contract audit that distinguishes:
   - explicit radial function evidence `f(r)`;
   - explicit longitudinal function evidence `f(z)`;
   - simple scalar light yield / attenuation evidence;
   - missing source/config surfaces.
3. Implement an immutable audit module that returns `ready=False` unless both
   `f(r)` and `f(z)` evidence are source-backed and tied to a DEC or closure
   artifact.
4. Add robust text scanners for current repo files; scanners must be diagnostic
   only and must not assume the C++ mirror exists.
5. If the current implementation lacks WLS functions, record precise blockers:
   needed sample, observable, and figure of merit for a future closure study.
6. Update `MASTER_PLAN.md` with DONE if the audit helper exists and blockers are
   explicit; do not mark the physics closure itself complete unless evidence is
   actually present.

## Verification

Run:

```bash
rtk python -m pytest tests/test_scintillator_wls_contract.py -q
rtk zsh -lc 'python -m pytest tests/ -x -q 2>&1 | tail -20'
rtk wc -l nnbar_reconstruction/analysis/scintillator_wls_contract.py tests/test_scintillator_wls_contract.py docs/parallel-sessions/MASTER_PLAN.md
```

Expected: focused tests pass; full test command exits 0; every touched file is
<= 500 lines.

## Stop condition

Stop after the compact audit helper/tests and MASTER_PLAN update are committed.
Do not launch production closure jobs in this iteration.

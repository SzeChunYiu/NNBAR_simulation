# Lane: leadglass-pmt-calibration

## Goal

Audit the thesis Ch. 5 lead-glass PMT calibration contract
`E_gamma = 0.46 N_PMT + 8.02` for `N_PMT > 0` against current Python and C++
surfaces. Do not silently retune production constants; report mismatches and
blockers unless the evidence is source-backed.

## Files

- Create: `nnbar_reconstruction/analysis/leadglass_pmt_calibration.py`
- Test: `tests/test_leadglass_pmt_calibration.py`
- Update: `docs/parallel-sessions/MASTER_PLAN.md` status/notes only
- Read-only references:
  - `nnbar_reconstruction/analysis/geometry_constants.py`
  - `nnbar_reconstruction/ml/feature_extraction.py`
  - `NNBAR_Detector/` lead-glass material/sensitive-detector files, if present
  - `docs/rebuild_plans/18_intercalibration.md`
  - `docs/rebuild_plans/24_reconstruction_question_tree/24_4_photon_pi0.md`

Do not edit C++ or LUNARC infrastructure.

## Implementation steps

1. Re-read `docs/parallel-sessions.md`, this spec, and `CODING_STANDARDS.md`.
2. Write failing tests for a pure calibration helper:
   - `N_PMT <= 0` is blocked/invalid;
   - `N_PMT=100` maps to `54.02 MeV` with slope 0.46 and intercept 8.02;
   - generic `photons_per_mev=200` style evidence is reported as non-thesis;
   - C++ reflectivity evidence of 95% vs thesis 90% is a mismatch, not a
     silently accepted value.
3. Implement a small audit module with immutable records for expected thesis
   constants, observed current constants, and blocker messages.
4. Add text scanners only for diagnostics; keep them robust to missing files and
   return `missing_surface:<path>` blockers instead of failing with traceback.
5. Do not change calibration values in production reconstruction unless a DEC and
   source-backed closure artifact already exist.
6. Update `MASTER_PLAN.md` with the exact audit result and remaining blockers.

## Verification

Run:

```bash
rtk python -m pytest tests/test_leadglass_pmt_calibration.py -q
rtk zsh -lc 'python -m pytest tests/ -x -q 2>&1 | tail -20'
rtk wc -l nnbar_reconstruction/analysis/leadglass_pmt_calibration.py tests/test_leadglass_pmt_calibration.py docs/parallel-sessions/MASTER_PLAN.md
```

Expected: focused tests pass; full test command exits 0; every touched file is
<= 500 lines.

## Stop condition

Stop after the audit helper/tests and MASTER_PLAN status update are committed.
If real Ch. 5 source artifacts are absent, leave fail-closed blockers rather
than changing production calibration.

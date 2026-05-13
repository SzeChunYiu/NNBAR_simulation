# Pi0 Mass Reconstruction — DEC-2026-05-13

## Finding

**Raw (uncalibrated) reconstruction**: systematic -20 MeV bias (113–117 MeV vs true 135 MeV).
**After calibration (`cv_photon_response_scaled_full_reco`)**: only -1.5 MeV bias (133.5 MeV).

## Data Source

Job 3053327 (pi0_foil_energy_scan_ext, COMPLETED 0:0, tasks 0-5).
Output: `build_lunarc/output/studies/pi0_foil_energy_scan/` (rsynced locally).

## Results

| KE (MeV) | Events | Reco Eff | Mean Mass (MeV) | Sigma (MeV) | Bias (MeV) |
|----------|--------|----------|-----------------|-------------|------------|
| 100 | 200 | 73% | 114.8 | 18.3 | -20.2 |
| 200 | 200 | 67% | 113.8 | 23.6 | -21.2 |
| 300 | 200 | 72% | 116.8 | 22.2 | -18.2 |
| 400 | 200 | 74% | 112.3 | 26.5 | -22.7 |
| 500 | 200 | 77% | 114.6 | 21.8 | -20.4 |
| 600 | 200 | 78% | 116.3 | 19.2 | -18.7 |

True pi0 mass: 134.9766 MeV. Systematic bias: ~-20 MeV (~15%).

## Root Cause Candidates

1. **Photon energy calibration bias**: lead-glass reco uses `E_gamma = 0.46 N_PMT + 8.02`
   (Ch. 5) but current simulation uses 200 photons/MeV vs thesis expectation.
   See `docs/reports/leadglass_pmt_calibration.md` — `non_thesis_photons_per_mev` blocker
   is OPEN.
2. **Upstream material pre-conversion**: beampipe + TPC upstream of lead glass absorbs
   photon energy before calorimeter. `P_survive=0.43` per material budget report.
3. **Incomplete cluster merging**: two photon clusters from same pi0 may not be
   correctly paired if one photon converts early.

## Calibrated Stage Results (run 0 = 100 MeV pi0 KE)

| Stage | Mean (MeV) | Bias (MeV) |
|-------|-----------|------------|
| truth_daughters | 135.0 | 0.0 |
| full_reco (raw) | 114.8 | -20.2 |
| energy_scaled_full_reco | 131.1 | -3.9 |
| cv_photon_response_scaled_full_reco | 133.5 | **-1.5** |
| containment_binned_full_reco | 132.6 | -2.4 |

The key stage split: `reco_direction_truth_energy` gives 134.3 MeV (bias -0.7 MeV),
meaning the **direction reconstruction is correct** but **energy measurement is low by ~15%**
before calibration. After photon-response calibration the bias drops to -1.5 MeV.

## Comparison with Thesis

Thesis Ch. 8 reports mass reconstruction peak near 135 MeV — consistent with the calibrated
stage (133.5 MeV). The raw 114.8 MeV is an artifact of the uncalibrated reconstruction.

## Status: CLOSED for calibrated reco; OPEN for local Python reco

The LUNARC pipeline with calibration achieves -1.5 MeV bias — thesis-compatible.
Local Python `run_pi0_reco` gives ~129 MeV (-6 MeV) — needs photon-response calibration
to match. Wiring the `cv_photon_response_scaled` stage into the Python reco is the
remaining work.

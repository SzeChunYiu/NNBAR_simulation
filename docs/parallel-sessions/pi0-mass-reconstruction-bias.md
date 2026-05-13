# Pi0 Mass Reconstruction Bias — DEC-2026-05-13

## Finding

The pi0 invariant-mass reconstruction has a systematic **-20 MeV bias** across the full
100–600 MeV kinetic-energy range. Reconstructed mass is ~113–117 MeV vs the true pi0
mass of 135.0 MeV.

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

## Comparison with Thesis

Thesis Ch. 8 reports mass reconstruction peak near 135 MeV with good sigma resolution.
The current -20 MeV bias indicates the reconstruction chain is not thesis-equivalent.
The most likely culprit is the `non_thesis_photons_per_mev` blocker (200 vs thesis value).

## Status: OPEN

Resolving this requires:
1. Closing `non_thesis_photons_per_mev` calibration blocker
2. Verifying lead-glass reflectivity (95% simulated vs 90% thesis)
3. Possibly applying an energy correction factor

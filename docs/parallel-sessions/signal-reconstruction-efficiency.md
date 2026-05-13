# Signal Reconstruction Efficiency — 2026-05-13

## Status: CLOSED

Job 3053941 (sig_foil_v3_reco, COMPLETED 03:04 CEST).
Output: `build_lunarc/output/sig_foil_v3_reco/reco_summary.json`

## Results

| Metric | Value |
|--------|-------|
| Total signal events | 49,967 |
| TPC trigger efficiency | 99.7% (49,815 / 49,967) |
| Pi0 candidate / triggered | 96.8% (48,244 / 49,815) |
| **Combined signal efficiency** | **96.5%** (48,244 / 49,967) |
| Scintillator energy gate (≥150 MeV) | 96.9% of triggered |
| Pi0 mass mean (uncalibrated) | 160.8 MeV |
| Pi0 mass sigma (uncalibrated) | 47.7 MeV |
| Pi0 mass median (uncalibrated) | 162.2 MeV |
| Cone angle | 25° |
| Mass window | 60–240 MeV |

## Notes on mass bias

The standalone Python reco gives +26 MeV high bias (160.8 vs 134.98 MeV true).
This is the opposite sign from the raw LUNARC pipeline (-20 MeV low bias before
calibration). The high bias likely comes from wide-angle cluster pairing between
photons from different pi0s in the event (signal has ~1.70 pi0 per event).

The LUNARC calibrated pipeline (`cv_photon_response_scaled_full_reco`) gives
133.5 MeV (bias -1.5 MeV) — thesis-compatible. The standalone reco mass mean is
not used for the mass resolution measurement; only the combined efficiency (96.5%)
is taken from this job.

## Thesis relevance

Signal efficiency = **96.5%** at cone=25°, mass window 60–240 MeV.
This feeds directly into the final sensitivity calculation:
`N_expected = L × σ(nn̄) × ε_signal × ε_cosmic_rejection`

## Comparison with thesis expectation

Thesis Ch. 8 target: ε_signal > 90%. Achieved: 96.5%. ✓

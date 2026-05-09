---
id: 23_sample_calibration_aux
title: Auxiliary calibration samples — single-particle anchors
version: 0.1
status: draft
owner: Sim Production
depends_on: [00_README, 03_dataset_registry, 17_field_calibration, 18_intercalibration]
inputs:
  - {path: NNBAR_Detector/macro/calibration/, schema: existing macros}
outputs:
  - {path: data/registry/cal_*/manifest.yml, schema: registered samples}
acceptance:
  - {test: e±, μ±, π±, p, γ samples at fixed energies registered, method: registry coverage, pass_when: ≥ 6 species samples}
  - {test: each sample has 100 000 events for calibration precision, method: row count, pass_when: ≥ 100k}
  - {test: every existing macro under macro/calibration/ is either promoted to registry or retired with DEC, method: §3 status, pass_when: zero unstatussed}
risks:
  - {risk: calibration sample list mismatched with downstream consumers (plan 18, 27, 28), mitigation: §2 consumer cross-reference}
estimated_effort: M
last_updated: 2026-05-09
---

# Auxiliary calibration samples — single-particle anchors

*Charter.* Produce, register, and freeze the single-particle samples
that anchor every calibration in the rebuild. Plans 17 (TPC field /
W-value), 18 (intercalibration), 24 (charged PID likelihood, plan
57), 27 (dE/dx), 28 (range/stopping) all consume these.

## 1. Sample matrix

| Species | Energy points | Origin | Sample ID | Statistics |
|---|---|---|---|---|
| e- | 50, 100, 200, 500, 1000 MeV | foil | `cal_singleelectron_v1` | 100k each |
| e+ | same | foil | `cal_singlepositron_v1` | 100k each |
| μ- | 50, 100, 200 MeV | foil | `cal_singlemuon_v1` | 100k each |
| μ+ | same | foil | `cal_singleantimuon_v1` | 100k each |
| π+ | 50, 100, 200, 400, 600 MeV | foil | `cal_singlepionplus_v1` | 100k each |
| π- | same | foil | `cal_singlepionminus_v1` | 100k each |
| p | 50, 100, 200, 300, 500 MeV | foil | `cal_singleproton_v1` | 100k each |
| γ | 50, 100, 200, 500, 1000 MeV | foil | `cal_singlegamma_v1` | 100k each |
| MIP π+ | momentum tuned to MIP | foil | `cal_singlepion_mip_v1` | 100k |

Each origin "foil" is shorthand for emission from the foil center,
isotropic direction. Specific energy / direction grids per species
are encoded in the macro.

## 2. Consumer cross-reference

| Consumer plan | Uses |
|---|---|
| plan 17 (TPC field) | `cal_singlepion_mip_v1` for W-value MIP cross-check |
| plan 18 (intercalibration) | `cal_singleelectron_v1`, `cal_singlepion_mip_v1` |
| plan 27 (dE/dx) | all charged-particle samples |
| plan 28 (range/stopping) | `cal_singleproton_v1`, `cal_singlepion*_v1` |
| plan 29 (charged PID) | all charged-particle samples for training likelihoods |
| plan 32 (event selection) | per-species samples for N-1 / ROC studies |
| plan 57 (MVA protocol) | charged PID likelihood / BDT training |

## 3. Existing-macro disposition

Every macro under `NNBAR_Detector/macro/calibration/` (plan 10 §1.4)
is either:

- *Promoted* to a registered sample manifest above (preserving the
  invocation), or
- *Retired* with a DEC entry stating the reason.

| Macro | Disposition |
|---|---|
| `calib_quick_leadglass.mac` | retire (smoke); replaced by sanity test |
| `calib_quick_scintillator.mac` | retire (smoke) |
| `gamma_energy_scan_full.mac` | promote → `cal_singlegamma_v1` |
| `leadglass/calib_electron_validation.mac` | promote → `cal_singleelectron_v1` |
| `leadglass/calib_gamma_all_surfaces.mac` | promote → acceptance-map auxiliary sample |
| `leadglass/calib_gamma_energy_scan.mac` | promote → `cal_singlegamma_v1` |
| `pi0_calib.mac` | promote → π⁰ calibration auxiliary |
| `run_all_calibrations.mac` | retire (orchestration; replaced by plan 52 batch system) |
| `scintillator/calib_pion_energy_scan.mac` | promote → `cal_singlepionplus_v1` / `cal_singlepionminus_v1` |
| `scintillator/calib_pion_minus.mac` | retire (subset of above) |
| `scintillator/calib_pion_mip.mac` | promote → `cal_singlepion_mip_v1` |

## 4. Acceptance criteria

- §1 registry entries created and frozen.
- §2 every consumer has at least one sample available.
- §3 every existing calibration macro has a status.
- Sanity plots per sample (plan 19 §2) green.

## 5. Risks

- *Risk:* energy grid coverage too coarse for non-linearity studies.
  *Mitigation:* §1 grid density chosen per consumer plan; finer
  binning added on demand.
- *Risk:* foil-only origin misses geometric effects elsewhere.
  *Mitigation:* §2 acceptance-map auxiliary uses
  `calib_gamma_all_surfaces.mac` style emission from many surfaces.

## 6. Dependencies

- **03** — registry.
- **17, 18** — calibration consumers.
- *Consumed by:* plans 27, 28, 29, 32, 57.

## 7. References

- Existing `macro/calibration/` macros for invocation patterns.
- Plan 10 §1.4 macro inventory.

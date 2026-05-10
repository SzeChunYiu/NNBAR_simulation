# Thesis reproduction ledger

Living ledger instantiated from plan 47 §1. Wave 2 status is `not-attempted`: rows inventory thesis claims and bind each claim to a planned sample/command, but no sample regeneration or comparison has been run.

## Row schema

| Field | Meaning |
|---|---|
| `id` | Stable ledger row id (`LIC-CH05-FIG-1`, `PHD-CH05-NUM-1`, ...). |
| `source` | Document, chapter, section, figure/table label or caption. |
| `thesis_value` | Exact number/string from the thesis or `figure` placeholder. |
| `reproducing.sample` | Plan 03 dataset id or plan 20-23 stub sample id. |
| `reproducing.command` | CLI/macro invocation pattern from plan 10. |
| `reproduced_value` | Number or artifact path after a future run. |
| `uncertainty` | Plan 04 statistical convention and plan 45 systematic convention. |
| `status` | `green`, `yellow`, `red`, or `not-attempted`. |
| `decision_log` | DEC entries governing the row, if any. |
| `leaf` | Plan 24 reconstruction leaf exercised by the row. |
| `notes` | Caveats, cross-checks, or source-version comments. |

## Rows seeded in Wave 2

Current row count: **20** (Chapter 5 seed).

| id | source | thesis_value | sample | reproducing.command | status | leaf | decision_log | notes |
|---|---|---|---|---|---|---|---|---|
| LIC-CH05-FIG-1 | licentiate+phd Ch5 Time Projection Chamber — fig:TPC_simulation_layout — TPC module segmentation in x-y plane | figure | sig_foil_v3 | `python3 -m nnbar_reconstruction.cli geometry-audit . --json output/ledger/LIC-CH05-FIG-1.json --fail-on-mismatch` | not-attempted | V.1 |  | PhD and licentiate Ch5 share the figure label/caption. |
| LIC-CH05-FIG-2 | licentiate+phd Ch5 Scintillator — fig:fits — WLS fibre photon absorption and trapping-efficiency fits | figure | sig_foil_optical_v1 | `python3 -m nnbar_reconstruction.cli summarize NNBAR_Detector/output/sig_foil_optical_v1 --run 0 --tables-dir output/ledger/LIC-CH05-FIG-2` | not-attempted | C.4 |  | Requires optical-mode sample because the plotted observable is photon transport. |
| LIC-CH05-NUM-1 | licentiate+phd Ch5 Lead Glass and PMT — Virtual PMT/light-guide volume dimensions | 8 cm × 8 cm × 0.1 cm | cal_singlegamma_v1 | `python3 -m nnbar_reconstruction.cli geometry-audit . --json output/ledger/LIC-CH05-NUM-1.json --fail-on-mismatch` | not-attempted | P.1 |  | Line appears in both thesis versions in the lead-glass/PMT subsection. |
| LIC-CH05-FIG-3 | licentiate+phd Ch5 Lead Glass and PMT — fig:top_layer_block — top-layer lead-glass block cross-section along z | figure | cal_singlegamma_v1 | `python3 -m nnbar_reconstruction.cli geometry-audit . --json output/ledger/LIC-CH05-FIG-3.json --fail-on-mismatch` | not-attempted | P.1 |  | Geometry-row reproduction uses the geometry audit path from plan 10. |
| LIC-CH05-FIG-4 | licentiate+phd Ch5 Lead Glass and PMT — fig:sub1 — lead-glass modules on top, bottom, and side surfaces | figure | cal_singlegamma_v1 | `python3 -m nnbar_reconstruction.cli geometry-audit . --json output/ledger/LIC-CH05-FIG-4.json --fail-on-mismatch` | not-attempted | P.1 |  | Subfigure of fig:leadglass_arrangement. |
| LIC-CH05-FIG-5 | licentiate+phd Ch5 Lead Glass and PMT — fig:sub2 — lead-glass modules on front and back surfaces | figure | cal_singlegamma_v1 | `python3 -m nnbar_reconstruction.cli geometry-audit . --json output/ledger/LIC-CH05-FIG-5.json --fail-on-mismatch` | not-attempted | P.1 |  | Subfigure of fig:leadglass_arrangement. |
| LIC-CH05-FIG-6 | licentiate+phd Ch5 Lead Glass and PMT — fig:leadglass_arrangement — lead-glass module arrangement on detector surfaces | figure | cal_singlegamma_v1 | `python3 -m nnbar_reconstruction.cli geometry-audit . --json output/ledger/LIC-CH05-FIG-6.json --fail-on-mismatch` | not-attempted | P.1 |  | Combined module-arrangement figure. |
| LIC-CH05-NUM-2 | licentiate+phd Ch5 Lead Glass and PMT — Lead-glass calibration equation | E_γ = 0.46 N_PMT + 8.02 | cal_singlegamma_v1 | `./nnbar-detector-simulation -m macro/calibration/leadglass/calib_gamma_energy_scan.mac && python3 -m nnbar_reconstruction.cli summarize NNBAR_Detector/output/cal_singlegamma_v1 --run 0 --tables-dir output/ledger/LIC-CH05-NUM-2` | not-attempted | P.4 |  | Equation label eqt:lead_glass_calibration in both thesis versions. |
| LIC-CH05-NUM-3 | licentiate+phd Ch5 Lead Glass and PMT — Lead-glass calibration slope | 0.46 MeV per PMT photon | cal_singlegamma_v1 | `./nnbar-detector-simulation -m macro/calibration/leadglass/calib_gamma_energy_scan.mac && python3 -m nnbar_reconstruction.cli summarize NNBAR_Detector/output/cal_singlegamma_v1 --run 0 --tables-dir output/ledger/LIC-CH05-NUM-3` | not-attempted | P.4 |  | Numerical coefficient from eqt:lead_glass_calibration. |
| LIC-CH05-NUM-4 | licentiate+phd Ch5 Lead Glass and PMT — Lead-glass calibration intercept | 8.02 MeV | cal_singlegamma_v1 | `./nnbar-detector-simulation -m macro/calibration/leadglass/calib_gamma_energy_scan.mac && python3 -m nnbar_reconstruction.cli summarize NNBAR_Detector/output/cal_singlegamma_v1 --run 0 --tables-dir output/ledger/LIC-CH05-NUM-4` | not-attempted | P.4 |  | Numerical coefficient from eqt:lead_glass_calibration. |
| LIC-CH05-NUM-5 | licentiate+phd Ch5 Lead Glass and PMT — Lead-glass calibration validity condition | N_PMT > 0 | cal_singlegamma_v1 | `./nnbar-detector-simulation -m macro/calibration/leadglass/calib_gamma_energy_scan.mac && python3 -m nnbar_reconstruction.cli validate-reco NNBAR_Detector/output/cal_singlegamma_v1 --run 0 --json output/ledger/LIC-CH05-NUM-5.json` | not-attempted | P.4 |  | The row checks the zero-photon guard in the calibration response. |
| LIC-CH05-FIG-7 | licentiate+phd Ch5 Lead Glass and PMT — fig:lead_glass_calibration — incident photon energy vs PMT photons | figure | cal_singlegamma_v1 | `./nnbar-detector-simulation -m macro/calibration/leadglass/calib_gamma_energy_scan.mac && python3 -m nnbar_reconstruction.cli summarize NNBAR_Detector/output/cal_singlegamma_v1 --run 0 --tables-dir output/ledger/LIC-CH05-FIG-7` | not-attempted | P.4 |  | Figure counterpart of eqt:lead_glass_calibration. |
| LIC-CH05-FIG-8 | licentiate+phd Ch5 NNBAR Detector Material Budget — fig:radiation_length_box — component radiation-length contribution vs pseudorapidity | figure | sig_foil_v3 | `python3 -m nnbar_reconstruction.cli geometry-audit . --json output/ledger/LIC-CH05-FIG-8.json --fail-on-mismatch` | not-attempted | E.1 |  | Material-budget reproduction is not yet implemented; geometry audit is the current command pattern. |
| LIC-CH05-FIG-9 | licentiate+phd Ch5 NNBAR Detector Material Budget — fig:interaction_length_box — component interaction-length contribution vs pseudorapidity | figure | sig_foil_v3 | `python3 -m nnbar_reconstruction.cli geometry-audit . --json output/ledger/LIC-CH05-FIG-9.json --fail-on-mismatch` | not-attempted | E.1 |  | Material-budget reproduction is not yet implemented; geometry audit is the current command pattern. |
| LIC-CH05-NUM-6 | licentiate+phd Ch5 Map of photon interaction — Gamma-conversion-map photon sample size | 100,000 photons | cal_singlegamma_v1 | `./nnbar-detector-simulation -m macro/calibration/leadglass/calib_gamma_all_surfaces.mac && python3 -m nnbar_reconstruction.cli summarize NNBAR_Detector/output/cal_singlegamma_v1 --run 0 --tables-dir output/ledger/LIC-CH05-NUM-6` | not-attempted | P.2 |  | Caption states photons are emitted from the carbon foil with random directions. |
| LIC-CH05-FIG-10 | licentiate+phd Ch5 Map of photon interaction — fig:gamma_conv_map_xy — x-y locations of gamma conversions | figure | cal_singlegamma_v1 | `./nnbar-detector-simulation -m macro/calibration/leadglass/calib_gamma_all_surfaces.mac && python3 -m nnbar_reconstruction.cli summarize NNBAR_Detector/output/cal_singlegamma_v1 --run 0 --tables-dir output/ledger/LIC-CH05-FIG-10` | not-attempted | P.2 |  | Subfigure of fig:gamma_conversion_map. |
| LIC-CH05-FIG-11 | licentiate+phd Ch5 Map of photon interaction — fig:gamma_conv_map_yz — y-z locations of gamma conversions | figure | cal_singlegamma_v1 | `./nnbar-detector-simulation -m macro/calibration/leadglass/calib_gamma_all_surfaces.mac && python3 -m nnbar_reconstruction.cli summarize NNBAR_Detector/output/cal_singlegamma_v1 --run 0 --tables-dir output/ledger/LIC-CH05-FIG-11` | not-attempted | P.2 |  | Subfigure of fig:gamma_conversion_map. |
| LIC-CH05-FIG-12 | licentiate+phd Ch5 Map of photon interaction — fig:gamma_conversion_map — combined gamma-conversion location maps | figure | cal_singlegamma_v1 | `./nnbar-detector-simulation -m macro/calibration/leadglass/calib_gamma_all_surfaces.mac && python3 -m nnbar_reconstruction.cli summarize NNBAR_Detector/output/cal_singlegamma_v1 --run 0 --tables-dir output/ledger/LIC-CH05-FIG-12` | not-attempted | P.2 |  | Combined caption states the 100,000-photon sampling condition. |
| PHD-CH05-NUM-1 | phd Ch5 Simulation Data Products for the HIBEAM TPC Study — GEANT4 internal length unit stated for CSV boundary | millimetres | sig_foil_v3 | `python3 -m nnbar_reconstruction.cli geometry-audit . --json output/ledger/PHD-CH05-NUM-1.json --fail-on-mismatch` | not-attempted | V.1 |  | PhD-only reproducibility/data-products section; not present in the frozen licentiate chapter. |
| PHD-CH05-DEC-1 | phd Ch5 Simulation Data Products for the HIBEAM TPC Study — Decision-log reference for corrected April 2026 CSV files | DEC-2026-04-24-3 | sig_foil_v3 | `python3 -m nnbar_reconstruction.cli geometry-audit . --json output/ledger/PHD-CH05-DEC-1.json --fail-on-mismatch` | not-attempted | V.1 | DEC-2026-04-24-3 | PhD-only provenance row for the April 2026 CSV correction boundary. |

## Source scan notes

- Chapter 5 rows were scanned from both `/Users/billy/Desktop/projects/overleaf-hibeam-thesis/5_Detector_simulation.tex` and `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/5_Detector_simulation.tex`.
- PhD-only rows are marked with `PHD-` ids and come from the PhD chapter section `Simulation Data Products for the HIBEAM TPC Study`.
- Figure rows intentionally keep `thesis_value: figure`; future execution applies the plan 47 §3 visual/bin/K-S comparison protocol.

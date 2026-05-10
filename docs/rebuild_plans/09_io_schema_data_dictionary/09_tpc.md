---
id: 09_tpc
title: IO schema — TPC_output_<run>.parquet
parent: 09_io_schema_data_dictionary
source_section: "§8"
---

## 8. TPC table — full column listing (canonical example)

The TPCSD writer (plan 07 §6.1) produces one row per recorded step
(first/last in volume only). The columns reflect the `NNbarHit`
fields written by `EventAction.cc`.

| Column | Dtype | Units | Semantics | Class | Rule | Notes |
|---|---|---|---|---|---|---|
| `Event_ID` | int64 | — | event index | A | §3.7 | |
| `Track_ID` | int64 | — | Geant4 track identifier | B | §3.4 | |
| `Parent_ID` | int64 | — | parent track identifier | B | §3.4 | |
| `Name` | string | — | particle PDG name | B | §3.5 | |
| `Process` | string | — | creator process | B | §3.5 | "primary" if Parent_ID == 0 |
| `vol_name` | string | — | current volume name | A | §3.7 | sensor-equivalent (volume ID) |
| `origin_vol_name` | string | — | track origin volume | B | §3.5 | track ancestry — Class B |
| `x`, `y`, `z` | float64 | mm | hit position (midpoint of pre/post-step) | A | §3.1 | limitation L1 (no smearing yet) |
| `t` | float64 | ns | hit global time | A | §3.2 | limitation L2 (no jitter) |
| `eDep` | float64 | MeV | step energy deposit | A | §3.3 | limitation L3 (no noise/threshold) |
| `kinEnergy` | float64 | MeV | step-mean kinetic energy | A | §3.3 | derived from pre/post-step KE |
| `px`, `py`, `pz` | float64 | — | pre-step momentum unit vector | A | §3.3 | direction only; magnitude = 1 |
| `TrackLength` | float64 | mm | step length | A | §3.3 | |
| `photons` | int32 | electrons | Poisson-distributed electron count from `eDep / 23.6 eV` | A+C | §3.3 + §3.8 | **field name reused** (TPCSD.cc:149); the **23.6 eV W-value** is Class C with calibration source `TPCSD.cc:102`. Plan 17 audits the value. |
| `xHitID` | int32 | — | TPC layer index (`replicaNumber(0)`) | A | §3.7 | |
| `module_ID` | int32 | — | TPC module index 0–11 (`replicaNumber(1)`) | A | §3.7 | per `DetectorConstruction.cc:273–300` |
| `step_info` | int32 | — | step provenance flag | A | §3.7 | 1 = first step from outside; 0 = last step from outside; 999 = origin inside TPC layer |
| `particle_x/y/z` | float64 | mm | particle production vertex | B | §3.5 | propagated from primary |

`TPC_output_*.parquet` is loaded by:
- `nnbar_reconstruction.cli.summarize` → `reconstruct_run`
- `nnbar_reconstruction.cli.scan-pid` → `reconstruct_charged_objects`
- `nnbar_reconstruction.cli.validate-reco`
- `pi0_study.evaluate_pi0_mass_ladder`
- `charged_study.evaluate_charged_stress`
- `pi0_fake_study.evaluate_pi0_fake_background`

Truth columns currently consumed by the reconstruction decision path
(flagged for migration per plan 08 §3.7): `Name`, `Track_ID`
(sparse-table fallback only), `origin_vol_name` (diagnostic).

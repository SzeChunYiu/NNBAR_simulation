---
id: 09_scintillator
title: IO schema — Scintillator_output_<run>.parquet
parent: 09_io_schema_data_dictionary
source_section: "§9"
---

## 9. Scintillator table

Rows are produced by `ScintillatorSD` for non-optical tracks and are
written only when the photon-equivalent count is positive. Positions
are persisted in **cm** by `NNbarRun::RecordEvent`.

| Column | Dtype | Units | Semantics | Class | Rule | Notes |
|---|---|---|---|---|---|---|
| `Event_ID` | int32 | dimensionless | Geant4 event id within the run | A | §3.7 | produced_by=`NNbarRun.cc:342`; consumed_by=charged reconstruction and event summaries |
| `Track_ID` | int32 | dimensionless | Geant4 track identifier | B | §3.4 | produced_by=`ScintillatorSD.cc:70,168` → `NNbarRun.cc:308,342`; consumed_by=diagnostic joins only |
| `Parent_ID` | int32 | dimensionless | parent Geant4 track id | B | §3.4 | produced_by=`ScintillatorSD.cc:129-138,164` → `NNbarRun.cc:309,342`; consumed_by=diagnostic ancestry only |
| `Name` | string | dimensionless | particle PDG name | B | §3.5 | produced_by=`ScintillatorSD.cc:122-123,167` → `NNbarRun.cc:310,342`; consumed_by=validation/diagnostics |
| `Proc` | string | dimensionless | creator process name, or `primary` | B | §3.5 | produced_by=`ScintillatorSD.cc:130-138,165` → `NNbarRun.cc:311,343`; consumed_by=diagnostic process studies |
| `Step_info` | int32 | dimensionless | first-step flag (`1` first in volume, `0` otherwise) | A | §3.7 | produced_by=`ScintillatorSD.cc:191-192` → `NNbarRun.cc:312,343`; consumed_by=scintillator-hit diagnostics |
| `Origin` | string | dimensionless | origin touchable volume name for the track | B | §3.5 | produced_by=`ScintillatorSD.cc:189-190` → `NNbarRun.cc:314,343`; consumed_by=truth-leak audit and diagnostics; source warns origin volume can be stale |
| `Volume` | string | dimensionless | current scintillator physical-volume name | A | §3.7 | produced_by=`ScintillatorSD.cc:96,187` → `NNbarRun.cc:313,343`; consumed_by=geometry diagnostics |
| `Module_ID` | int32 | dimensionless | scintillator module id from `replicaNumber(2)` | A | §3.7 | produced_by=`ScintillatorSD.cc:90-94,172` → `NNbarRun.cc:328,344`; consumed_by=charged matching and hemisphere sums |
| `Layer_ID` | int32 | dimensionless | scintillator layer id from `replicaNumber(1)` | A | §3.7 | produced_by=`ScintillatorSD.cc:90-94,171` → `NNbarRun.cc:327,344`; consumed_by=geometry diagnostics |
| `Stave_ID` | int32 | dimensionless | scintillator stave id from `replicaNumber(0)` | A | §3.7 | produced_by=`ScintillatorSD.cc:90-94,170` → `NNbarRun.cc:326,344`; consumed_by=geometry diagnostics |
| `x`, `y`, `z` | float64 | cm | scintillator module translation coordinates | A | §3.1 | produced_by=`ScintillatorSD.cc:100-105,175-177` → `NNbarRun.cc:329-344`; consumed_by=charged matching and event geometry |
| `particle_x`, `particle_y`, `particle_z` | float64 | cm | pre-step hit position in global coordinates | A | §3.1 | produced_by=`ScintillatorSD.cc:79-83,183-185` → `NNbarRun.cc:315-345`; consumed_by=hit-position diagnostics |
| `x_local`, `y_local`, `z_local` | float64 | cm | pre-step hit position transformed into module-local coordinates | A | §3.1 | produced_by=`ScintillatorSD.cc:108-111,179-181` → `NNbarRun.cc:333-346`; consumed_by=module-local diagnostics |
| `t` | float64 | ns | global track time at the scintillator hit | A | §3.2 | produced_by=`ScintillatorSD.cc:116-117,166` → `NNbarRun.cc:321,347`; consumed_by=timing/event summaries |
| `KE` | float64 | MeV | post-step kinetic energy | A | §3.3 | produced_by=`ScintillatorSD.cc:153-156,196` → `NNbarRun.cc:322,347`; consumed_by=energy-spectrum diagnostics |
| `eDep` | float64 | MeV | step total energy deposit in scintillator | A | §3.3 | produced_by=`ScintillatorSD.cc:72-73,195` → `NNbarRun.cc:323,347`; consumed_by=charged matching and event energy sums |
| `photons` | int32 | photons | photon-equivalent count using `11136 photons/MeV` | A+C | §3.3 + §3.8 | produced_by=`ScintillatorSD.cc:141-142,197` → `NNbarRun.cc:337,347`; consumed_by=plan 18 intercalibration and event energy summaries |

Decision-path consumers: `reconstruct_charged_objects` (matches
scintillator hits to TPC tracks); event-variable functions (per-
hemisphere energy sums).

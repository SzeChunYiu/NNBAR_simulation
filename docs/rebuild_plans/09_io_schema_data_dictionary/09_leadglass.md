---
id: 09_leadglass
title: IO schema — LeadGlass_output_<run>.parquet
parent: 09_io_schema_data_dictionary
source_section: "§10"
---

## 10. LeadGlass table

Rows are produced by `LeadGlassSD` only for non-optical tracks that
create at least one Cerenkov optical photon in `LeadGlassPV`. The
writer stores lead-glass block translations in **cm** and filters out
zero-photon rows.

| Column | Dtype | Units | Semantics | Class | Rule | Notes |
|---|---|---|---|---|---|---|
| `Event_ID` | int32 | dimensionless | Geant4 event id within the run | A | §3.7 | produced_by=`NNbarRun.cc:391`; consumed_by=photon reconstruction and event summaries |
| `Track_ID` | int32 | dimensionless | Geant4 track identifier | B | §3.4 | produced_by=`LeadGlassSD.cc:72,162` → `NNbarRun.cc:370,391`; consumed_by=diagnostic/ancestry paths |
| `Parent_ID` | int32 | dimensionless | parent Geant4 track id | B | §3.4 | produced_by=`LeadGlassSD.cc:133-145,158` → `NNbarRun.cc:371,391`; consumed_by=truth grouping until plan 26 replaces ancestry |
| `Name` | string | dimensionless | particle PDG name | B | §3.5 | produced_by=`LeadGlassSD.cc:113-114,161` → `NNbarRun.cc:372,391`; consumed_by=validation/diagnostics |
| `Proc` | string | dimensionless | creator process name, or `primary` | B | §3.5 | produced_by=`LeadGlassSD.cc:132-145,159` → `NNbarRun.cc:373,392`; consumed_by=diagnostic process studies |
| `Step_info` | int32 | dimensionless | first-step flag (`1` first in volume, `0` otherwise) | A | §3.7 | produced_by=`LeadGlassSD.cc:173-174` → `NNbarRun.cc:374,393`; consumed_by=calorimeter-hit diagnostics |
| `Origin` | string | dimensionless | origin touchable volume name for the track | B | §3.5 | produced_by=`LeadGlassSD.cc:171-172` → `NNbarRun.cc:375,394`; consumed_by=truth-leak audit and diagnostics |
| `Module_ID` | int32 | dimensionless | lead-glass block index from `replicaNumber(1)` | A | §3.7 | produced_by=`LeadGlassSD.cc:92-94,163` → `NNbarRun.cc:386,395`; consumed_by=photon clustering/block mapping |
| `x`, `y`, `z` | float64 | cm | lead-glass block translation coordinates | A | §3.1 | produced_by=`LeadGlassSD.cc:99-102,164-166` → `NNbarRun.cc:377-395`; consumed_by=photon-object geometry |
| `t` | float64 | ns | global track time at the lead-glass hit | A | §3.2 | produced_by=`LeadGlassSD.cc:107-108,160` → `NNbarRun.cc:380,396`; consumed_by=timing/event summaries |
| `KE` | float64 | MeV | post-step kinetic energy | A | §3.3 | produced_by=`LeadGlassSD.cc:148-151,169` → `NNbarRun.cc:381,396`; consumed_by=energy-spectrum diagnostics |
| `eDep` | float64 | MeV | step total energy deposit in lead glass | A | §3.3 | produced_by=`LeadGlassSD.cc:74-75,168` → `NNbarRun.cc:382,396`; consumed_by=photon energy reconstruction |
| `photons` | int32 | photons | Cerenkov photons produced in the step | A+C | §3.3 + §3.8 | produced_by=`LeadGlassSD.cc:120-130,170` → `NNbarRun.cc:387,396`; consumed_by=plan 18 intercalibration and photon-object studies |

Decision-path consumers: photon-object reconstruction (plan 08 §3.5).

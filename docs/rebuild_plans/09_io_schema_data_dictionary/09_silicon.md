---
id: 09_silicon
title: IO schema — Silicon_output_<run>.parquet
parent: 09_io_schema_data_dictionary
source_section: "§6"
---

## 6. Silicon table

Per-step records from SiliconSD. The writer stores only silicon hits
with positive `eDep`, and positions are persisted in **cm** via
`NNbarRun::RecordEvent`.

| Column | Dtype | Units | Semantics | Class | Rule | Notes |
|---|---|---|---|---|---|---|
| `Event_ID` | int32 | dimensionless | Geant4 event id within the run | A | §3.7 | produced_by=`NNbarRun.cc:230`; consumed_by=`io.load_run`, silicon diagnostics |
| `Track_ID` | int32 | dimensionless | Geant4 track identifier | B | §3.4 | produced_by=`SiliconSD.cc:71,145` → `NNbarRun.cc:208,230`; consumed_by=diagnostic joins only |
| `Parent_ID` | int32 | dimensionless | parent Geant4 track id | B | §3.4 | produced_by=`SiliconSD.cc:109-116,140` → `NNbarRun.cc:209,230`; consumed_by=diagnostic ancestry only |
| `Name` | string | dimensionless | particle PDG name | B | §3.5 | produced_by=`SiliconSD.cc:102-103,143` → `NNbarRun.cc:210,230`; consumed_by=validation/diagnostics |
| `Proc` | string | dimensionless | creator process name, or `primary` | B | §3.5 | produced_by=`SiliconSD.cc:112-117,141` → `NNbarRun.cc:211,231`; consumed_by=diagnostic process studies |
| `Step_info` | int32 | dimensionless | first-step flag (`1` first in volume, `0` otherwise) | A | §3.7 | produced_by=`SiliconSD.cc:134-136` → `NNbarRun.cc:212,231`; consumed_by=silicon-hit diagnostics |
| `Origin` | string | dimensionless | origin touchable volume name for the track | B | §3.5 | produced_by=`SiliconSD.cc:128,134` → `NNbarRun.cc:213,231`; consumed_by=truth-leak audit and diagnostics |
| `Layer_ID` | int32 | dimensionless | silicon replica/layer id from `replicaNumber(0)` | A | §3.7 | produced_by=`SiliconSD.cc:92-94,146` → `NNbarRun.cc:214,231`; consumed_by=geometry and material diagnostics |
| `x`, `y`, `z` | float64 | cm | midpoint of pre/post step in silicon | A | §3.1 | produced_by=`SiliconSD.cc:81-86,153-155` → `NNbarRun.cc:216-232`; consumed_by=plan 14/16 diagnostics |
| `px`, `py`, `pz` | float64 | dimensionless | pre-step momentum unit-vector components | A | §3.3 | produced_by=`SiliconSD.cc:127,150-152` → `NNbarRun.cc:219-233`; consumed_by=angular diagnostics |
| `t` | float64 | ns | global track time at the silicon hit | A | §3.2 | produced_by=`SiliconSD.cc:96-97,142` → `NNbarRun.cc:222,234`; consumed_by=timing diagnostics |
| `KE` | float64 | MeV | post-step kinetic energy | A | §3.3 | produced_by=`SiliconSD.cc:121-123,149` → `NNbarRun.cc:223,234`; consumed_by=energy-spectrum diagnostics |
| `eDep` | float64 | MeV | step total energy deposit in silicon | A | §3.3 | produced_by=`SiliconSD.cc:73-74,148` → `NNbarRun.cc:224,234`; consumed_by=material/energy-loss diagnostics |

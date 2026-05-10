---
id: 09_beampipe
title: IO schema — Beampipe_output_<run>.parquet
parent: 09_io_schema_data_dictionary
source_section: "§7"
---

## 7. Beampipe table

Per-step records from TubeSD inside any Beampipe LV. Used to study
beampipe-origin secondaries (plan 14 validation suite). Positions are
stored in **cm** by `NNbarRun::RecordEvent`.

| Column | Dtype | Units | Semantics | Class | Rule | Notes |
|---|---|---|---|---|---|---|
| `Event_ID` | int32 | dimensionless | Geant4 event id within the run | A | §3.7 | produced_by=`NNbarRun.cc:188`; consumed_by=`io.load_run`, plan 14 diagnostics |
| `Track_ID` | int32 | dimensionless | Geant4 track identifier | B | §3.4 | produced_by=`TubeSD.cc:51,85` → `NNbarRun.cc:170,188`; consumed_by=diagnostic joins only |
| `Parent_ID` | int32 | dimensionless | parent Geant4 track id | B | §3.4 | produced_by=`TubeSD.cc:52,86` → `NNbarRun.cc:171,188`; consumed_by=diagnostic ancestry only |
| `Name` | string | dimensionless | particle PDG name | B | §3.5 | produced_by=`TubeSD.cc:49-50,84` → `NNbarRun.cc:172,188`; consumed_by=validation/diagnostics |
| `Proc` | string | dimensionless | creator process name, or `primary` | B | §3.5 | produced_by=`TubeSD.cc:53-54,87` → `NNbarRun.cc:173,189`; consumed_by=diagnostic process studies |
| `Step_info` | int32 | dimensionless | first/last-in-volume flag (`2` both, `0` first, `1` last) | A | §3.7 | produced_by=`TubeSD.cc:100-114` → `NNbarRun.cc:174,189`; consumed_by=beampipe-hit diagnostics |
| `Current_Vol` | string | dimensionless | current beampipe physical-volume name | A | §3.7 | produced_by=`TubeSD.cc:80,88` → `NNbarRun.cc:176,189`; consumed_by=geometry/material diagnostics |
| `Origin` | string | dimensionless | origin touchable volume name for the track | B | §3.5 | produced_by=`TubeSD.cc:79,89` → `NNbarRun.cc:175,189`; consumed_by=truth-leak audit and diagnostics |
| `x`, `y`, `z` | float64 | cm | midpoint of pre/post step in the beampipe | A | §3.1 | produced_by=`TubeSD.cc:59-66,90-92` → `NNbarRun.cc:178-190`; consumed_by=plan 14/16 diagnostics |
| `px`, `py`, `pz` | float64 | dimensionless | pre-step momentum unit-vector components | A | §3.3 | produced_by=`TubeSD.cc:78,95-97` → `NNbarRun.cc:181-191`; consumed_by=angular diagnostics |
| `t` | float64 | ns | global track time at the beampipe hit | A | §3.2 | produced_by=`TubeSD.cc:68-69,93` → `NNbarRun.cc:184,192`; consumed_by=timing diagnostics |
| `KE` | float64 | MeV | mean of pre/post-step kinetic energy | A | §3.3 | produced_by=`TubeSD.cc:71-76,94` → `NNbarRun.cc:185,192`; consumed_by=energy-spectrum diagnostics |
| `eDep` | float64 | MeV | step total energy deposit in the beampipe | A | §3.3 | produced_by=`TubeSD.cc:56-57,98` → `NNbarRun.cc:186,192`; consumed_by=material/energy-loss diagnostics |

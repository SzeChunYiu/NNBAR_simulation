---
id: 09_carbon
title: IO schema — Carbon_output_<run>.parquet
parent: 09_io_schema_data_dictionary
source_section: "§5"
---

## 5. Carbon table

Per-step records from CarbonSD inside the foil. Used by
`reconstruction.py` only for diagnostics
(`@diagnostic_only` once plan 01 audit lands). Plan 13 (signal model)
consumes this to study annihilation-product distributions inside the
foil.

The active Parquet writer persists this table from `CarbonSD` hits via
`NNbarRun::RecordEvent`. Positions are stored in **cm** because the
writer divides hit coordinates by `CLHEP::cm` before filling Parquet.

| Column | Dtype | Units | Semantics | Class | Rule | Notes |
|---|---|---|---|---|---|---|
| `Event_ID` | int32 | dimensionless | Geant4 event id within the run | A | §3.7 | produced_by=`NNbarRun.cc:147`; consumed_by=`io.load_run`, plan 13 diagnostics |
| `Track_ID` | int32 | dimensionless | Geant4 track identifier | B | §3.4 | produced_by=`CarbonSD.cc:58,91` → `NNbarRun.cc:130,147`; consumed_by=diagnostic joins only |
| `Parent_ID` | int32 | dimensionless | parent Geant4 track id | B | §3.4 | produced_by=`CarbonSD.cc:59,92` → `NNbarRun.cc:131,147`; consumed_by=diagnostic ancestry only |
| `Name` | string | dimensionless | particle PDG name | B | §3.5 | produced_by=`CarbonSD.cc:56-57,90` → `NNbarRun.cc:132,147`; consumed_by=validation/diagnostics |
| `Proc` | string | dimensionless | creator process name, or `primary` | B | §3.5 | produced_by=`CarbonSD.cc:60-61,93` → `NNbarRun.cc:133,148`; consumed_by=diagnostic process studies |
| `Step_info` | int32 | dimensionless | first/last-in-volume flag (`2` both, `0` first, `1` last) | A | §3.7 | produced_by=`CarbonSD.cc:106-120` → `NNbarRun.cc:134,148`; consumed_by=foil-hit diagnostics |
| `Origin` | string | dimensionless | origin touchable volume name for the track | B | §3.5 | produced_by=`CarbonSD.cc:86,94` → `NNbarRun.cc:135,148`; consumed_by=truth-leak audit and diagnostics |
| `x`, `y`, `z` | float64 | cm | midpoint of pre/post step in the carbon foil | A | §3.1 | produced_by=`CarbonSD.cc:66-73,96-98` → `NNbarRun.cc:137-149`; consumed_by=plan 13 distributions |
| `px`, `py`, `pz` | float64 | dimensionless | pre-step momentum unit-vector components | A | §3.3 | produced_by=`CarbonSD.cc:85,101-103` → `NNbarRun.cc:140-150`; consumed_by=plan 13 angular diagnostics |
| `t` | float64 | ns | global track time at the carbon hit | A | §3.2 | produced_by=`CarbonSD.cc:75-76,99` → `NNbarRun.cc:143,151`; consumed_by=timing diagnostics |
| `KE` | float64 | MeV | mean of pre/post-step kinetic energy | A | §3.3 | produced_by=`CarbonSD.cc:78-83,100` → `NNbarRun.cc:144,151`; consumed_by=plan 13 spectra |
| `eDep` | float64 | MeV | step total energy deposit in carbon | A | §3.3 | produced_by=`CarbonSD.cc:63-64,104` → `NNbarRun.cc:145,151`; consumed_by=plan 13 energy-loss studies |

---
id: 09_interaction
title: IO schema — Interaction_output_<run>.parquet
parent: 09_io_schema_data_dictionary
source_section: "§4"
---

## 4. Interaction table (decay/process tree)

Sparse ancestry table written for non-primary tracks that first enter
their origin volume with kinetic energy above 1 MeV. It records Geant4
process/volume provenance for validation and truth-leak audits; plan 01
classifies Interaction-table entries as Class B truth-only ancestry.
Positions are stored in **cm** and global time is stored in **ns**.

| Column | Dtype | Units | Semantics | Class | Rule | Notes |
|---|---|---|---|---|---|---|
| `Event_ID` | int32 | dimensionless | Geant4 event id within the run | A | §3.7 | produced_by=`SteppingAction.cc:100`; consumed_by=truth-table joins |
| `Track_ID` | int32 | dimensionless | Geant4 track identifier for the secondary/descendant | B | §3.4 | produced_by=`RunAction.cc:151` schema; `SteppingAction.cc:86,100`; consumed_by=diagnostic ancestry only |
| `Parent_ID` | int32 | dimensionless | parent Geant4 track identifier | B | §3.4 | produced_by=`RunAction.cc:152` schema; `SteppingAction.cc:100`; consumed_by=diagnostic ancestry only |
| `Name` | string | dimensionless | particle PDG name of the recorded track | B | §3.6 | produced_by=`RunAction.cc:153` schema; `SteppingAction.cc:100`; consumed_by=validation/diagnostics |
| `Proc` | string | dimensionless | creator process name for the recorded track | B | §3.6 | produced_by=`RunAction.cc:154` schema; `SteppingAction.cc:89,100`; consumed_by=truth-leak and process diagnostics |
| `Current_Vol` | string | dimensionless | current Geant4 physical-volume name at first origin-volume step | B | §3.7 | produced_by=`RunAction.cc:155` schema; `SteppingAction.cc:84,100-101`; consumed_by=diagnostic ancestry only |
| `Origin` | string | dimensionless | origin touchable volume name for the track | B | §3.7 | produced_by=`RunAction.cc:156` schema; `SteppingAction.cc:84,101`; consumed_by=diagnostic ancestry only |
| `m` | float64 | MeV | PDG mass of the recorded track | B | §3.6 | produced_by=`RunAction.cc:157` schema; `SteppingAction.cc:88,101`; consumed_by=validation/diagnostics |
| `KE` | float64 | MeV | kinetic energy of the recorded track at the interaction row | B | §3.6 | produced_by=`RunAction.cc:158` schema; `SteppingAction.cc:84,101`; consumed_by=validation/diagnostics |
| `t` | float64 | ns | global time of the recorded track | B | §3.6 | produced_by=`RunAction.cc:159` schema; `SteppingAction.cc:90,102`; consumed_by=validation/diagnostics |
| `x`, `y`, `z` | float64 | cm | production vertex position of the recorded track | B | §3.6 | produced_by=`RunAction.cc:160-162` schema; `SteppingAction.cc:91,102`; consumed_by=validation/diagnostics |
| `px`, `py`, `pz` | float64 | dimensionless | momentum-direction unit vector of the recorded track | B | §3.6 | produced_by=`RunAction.cc:163-165` schema; `SteppingAction.cc:87,103`; consumed_by=validation/diagnostics |

The schema is exactly the active `Interaction_output_<run>.parquet`
layout from `RunAction.cc:150-165`; there are no optional
`secondary_pdg`, `Process`, `Vx`, `Vy`, `Vz`, or `Time` columns in the
current writer.

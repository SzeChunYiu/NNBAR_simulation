---
id: 09_particle
title: IO schema — Particle_output_<run>.parquet
parent: 09_io_schema_data_dictionary
source_section: "§3"
---

## 3. Particle table (truth primaries)

Truth-primary rows written by `PrimaryGeneratorAction` for particle-gun
runs and by `G4MCPLGenerator` for MCPL-driven samples. Positions are
stored in **cm** and primary time is stored in **ms**.

| Column | Dtype | Units | Semantics | Class | Rule | Notes |
|---|---|---|---|---|---|---|
| `Event_ID` | int32 | dimensionless | Geant4 event id within the run | A | §3.7 | produced_by=`PrimaryGeneratorAction.cc:169`; `G4MCPLGenerator.cc:113,153,199`; consumed_by=truth table joins |
| `PID` | int32 | dimensionless | PDG particle id for the generated primary | B | §3.5 | produced_by=`RunAction.cc:130` schema and generator writes; consumed_by=validation/labels only |
| `Mass` | float64 | MeV | PDG mass of the generated primary | B | §3.5 | produced_by=`G4MCPLGenerator.cc:113,153,199`; particle-gun path writes `0.0`; consumed_by=validation/labels only |
| `Name` | string | dimensionless | PDG particle name | B | §3.5 | produced_by=`PrimaryGeneratorAction.cc:170`; `G4MCPLGenerator.cc:114,154,200`; consumed_by=validation/labels only |
| `Charge` | float64 | e | PDG electric charge | B | §3.5 | produced_by=`G4MCPLGenerator.cc:114,154,200`; particle-gun path writes `0.0`; consumed_by=validation/labels only |
| `KE` | float64 | MeV | generated primary kinetic energy | B | §3.5 | produced_by=`PrimaryGeneratorAction.cc:154,172`; `G4MCPLGenerator.cc:115,155,201`; consumed_by=validation/labels only |
| `angle` | float64 | dimensionless | generator angle placeholder | B | §3.5 | produced_by=generator writes currently `0.0`; consumed_by=validation/diagnostics only |
| `x`, `y`, `z` | float64 | cm | generated primary vertex position | B | §3.5 | produced_by=`PrimaryGeneratorAction.cc:151-153,173`; `G4MCPLGenerator.cc:116,156,202`; consumed_by=validation/diagnostics only |
| `t` | float64 | ms | generated primary time | B | §3.5 | produced_by=`PrimaryGeneratorAction.cc:159,173`; `G4MCPLGenerator.cc:116,156,202`; consumed_by=validation/diagnostics only |
| `u`, `v`, `w` | float64 | dimensionless | generated primary momentum-direction unit vector | B | §3.5 | produced_by=`PrimaryGeneratorAction.cc:155-157,174`; `G4MCPLGenerator.cc:117,157,203`; consumed_by=validation/diagnostics only |
| `weight` | float64 | dimensionless | MCPL/generator event weight | B | §3.5 | produced_by=`PrimaryGeneratorAction.cc:160,174`; `G4MCPLGenerator.cc:117,157,203`; consumed_by=weighted validation/ledger studies |

This table is truth-only except for the event key. It is loaded by
validation and ledger code, never by the production reconstruction
decision path.

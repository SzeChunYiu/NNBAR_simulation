---
id: 07_9_output_management
title: Simulation atomic walkthrough §9 — output management
version: 0.1
status: draft
owner: Sim Production
depends_on: [07_simulation_atomic_walkthrough]
---

## 9. Output management (src/output/ParquetOutputManager.cc)

The parquet writer is the surface where Geant4 hits become offline
data. Each SD has a corresponding output stream:

| Output file pattern | Producer | Schema documented in |
|---|---|---|
| `Particle_output_<run>.parquet` | EventAction (truth primaries) | plan 09 |
| `Interaction_output_<run>.parquet` | EventAction (decay/process tree) | plan 09 |
| `Carbon_output_<run>.parquet` | CarbonSD via EventAction | plan 09 |
| `Silicon_output_<run>.parquet` | SiliconSD | plan 09 |
| `Beampipe_output_<run>.parquet` | TubeSD | plan 09 |
| `TPC_output_<run>.parquet` | TPCSD | plan 09 |
| `Scintillator_output_<run>.parquet` | ScintillatorSD | plan 09 |
| `LeadGlass_output_<run>.parquet` | LeadGlassSD | plan 09 |
| `PMT_output_<run>.parquet` | PMTSD | plan 09 |
| `GPUEnergy_output_<run>.parquet` | Celeritas calorimeters (`CeleritasCalorimeter`) | plan 09 |
| `Scintillator_Module_Position.txt` | Scintillator builder (per-module geometry) | plan 09 |

Schema discipline: every writer is configured at the top of
`ParquetOutputManager` against an explicit field list. Plan 09 freezes
the list. The writer wraps the vendored `parquet_writer` library at
`external/parquet-writer/src/cpp/`.

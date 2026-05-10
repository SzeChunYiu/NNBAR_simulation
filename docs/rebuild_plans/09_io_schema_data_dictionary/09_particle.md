---
id: 09_particle
title: IO schema — Particle_output_<run>.parquet
parent: 09_io_schema_data_dictionary
source_section: "§3"
---

## 3. Particle table (truth primaries)

Inferred from plan 07 §8.2 (EventAction primary recording) and
`reconstruction.py` cross-references (`Particle` is loaded by
`cli._add_truth_tables`):

| Column | Dtype | Units | Semantics | Class | Rule | Notes |
|---|---|---|---|---|---|---|
| `Event_ID` | int64 | — | per-run event index | A | §3.7 (sensor-equivalent identifier) | offsetable across runs by `EVENT_ID_OFFSET` (cli.py:27) |
| `Track_ID` | int64 | — | Geant4 internal track identifier | B | §3.4 | every primary has a Track_ID; secondaries inherit |
| `Parent_ID` | int64 | — | parent track identifier (0 = primary) | B | §3.4 | |
| `Name` | string | — | PDG particle name | B | §3.5 | e.g. "anti_neutron", "pi+", "pi-", "proton" |
| `pdg_code` | int32 | — | PDG identifier | B | §3.5 | |
| `KineticEnergy` | float64 | MeV | primary kinetic energy at production | B | §3.5 | |
| `Px`, `Py`, `Pz` | float64 | MeV/c | primary momentum components | B | §3.5 | |
| `Vx`, `Vy`, `Vz` | float64 | mm | primary production vertex | B | §3.5 | currently equal to truth (limitation L1) |
| `Time` | float64 | ns | primary production time | B | §3.5 | |
| `Process` | string | — | creator process name | B | §3.5 | "primary" for primaries |

This table is loaded by `validation.py` and the studies; it is
**never** loaded by `reconstruction.py` (the realism audit confirms
this). Plan 47 reproduction ledger uses it only inside
`@validation_only` functions.

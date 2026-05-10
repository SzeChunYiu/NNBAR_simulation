---
id: 09_interaction
title: IO schema — Interaction_output_<run>.parquet
parent: 09_io_schema_data_dictionary
source_section: "§4"
---

## 4. Interaction table (decay/process tree)

Sparse table; populated when a primary interacts (decay, hadronic
interaction, conversion). Used by `reconstruction.py` to resolve
shower-source ancestry (plan 08 §3.5 step 1) — flagged for migration.

| Column | Dtype | Units | Semantics | Class | Rule | Notes |
|---|---|---|---|---|---|---|
| `Event_ID` | int64 | — | event index | A | §3.7 | |
| `Track_ID` | int64 | — | child track id | B | §3.4 | |
| `Parent_ID` | int64 | — | parent track id | B | §3.4 | |
| `Process` | string | — | interaction process name | B | §3.5 | e.g. "Decay", "conv", "compt" |
| `Vx`, `Vy`, `Vz` | float64 | mm | interaction vertex | B | §3.5 | |
| `Time` | float64 | ns | interaction time | B | §3.5 | |
| Optional: `secondary_pdg` | int32 | — | first secondary PDG | B | §3.5 | |
| Optional: `name` | string | — | parent particle name | B | §3.5 | |

The exact column list will be verified by codex-supervisor against
`EventAction.cc` writer; this is a v0.1 stub.

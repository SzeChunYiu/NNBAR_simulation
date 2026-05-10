---
id: 09_gpuenergy
title: IO schema — GPUEnergy_output_<run>.parquet
parent: 09_io_schema_data_dictionary
source_section: "§12"
---

## 12. GPUEnergy table

Planned output from `CeleritasCalorimeter` (plan 07 §11.4), populated
only when `WITH_CELERITAS=ON` and Celeritas is active at runtime. The
current `NNBAR_Detector-L3` source tree contains no `src/physics/`, no
`CeleritasCalorimeter`, and no `GPUEnergy_output` writer/layout; a
source scan found only reconstruction I/O accepting an optional
`GPUEnergy` kind. Therefore the active schema has zero produced columns
in the current build.

| Column | Dtype | Units | Semantics | Class | Rule | Notes |
|---|---|---|---|---|---|---|
| _none currently produced_ | — | — | No active Celeritas/GPUEnergy writer exists in this source tree | — | — | produced_by=absent; consumed_by=`io.load_run` tolerates missing `GPUEnergy_output_<run>.parquet` as an empty table |

When `CeleritasCalorimeter` is restored, this section must be replaced
with the concrete Parquet layout before any `WITH_CELERITAS=ON` sample
is registry-eligible. GPU/CPU parity remains Class C (§3.8) until plan
14 proves percent-level equivalence.

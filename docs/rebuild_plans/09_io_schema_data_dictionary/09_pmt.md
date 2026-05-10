---
id: 09_pmt
title: IO schema — PMT_output_<run>.parquet
parent: 09_io_schema_data_dictionary
source_section: "§11"
---

## 11. PMT table

Optical-photon hits at the PMT face. Populated only when
`WITH_SCINTILLATION=ON` (or Opticks active). `NNbarRun::RecordEvent`
aggregates individual optical photons into one row per `(Event_ID,
Module_ID)`, with per-photon `KE` and `t` stored as list columns.

| Column | Dtype | Units | Semantics | Class | Rule | Notes |
|---|---|---|---|---|---|---|
| `Event_ID` | int32 | dimensionless | Geant4 event id within the run | A | §3.7 | produced_by=`NNbarRun.cc:465`; consumed_by=`_pmt_photons_for_event` lines 67-83 |
| `Module_ID` | int32 | dimensionless | PMT/lead-glass module id from `replicaNumber(1)` | A | §3.7 | produced_by=`PMTSD.cc:82-84,137` → `NNbarRun.cc:427,466`; consumed_by=PMT photon grouping |
| `x`, `y`, `z` | float64 | cm | PMT face translation coordinates for the module | A | §3.1 | produced_by=`PMTSD.cc:86-89,138-140` → `NNbarRun.cc:428-469`; consumed_by=geometry diagnostics |
| `photons` | int32 | photons | count of accepted optical photons in this PMT module/event | A+C | §3.3 + §3.8 | produced_by=`PMTSD.cc:126-145` → `NNbarRun.cc:445-470`; consumed_by=`_pmt_photons_for_event` lines 74-82; QE/acceptance is Class C |
| `KE` | list<float64> | MeV | per-photon post-step kinetic-energy list for the module/event | B | §3.5 | produced_by=`PMTSD.cc:118-123,144` → `NNbarRun.cc:433,458-471`; consumed_by=diagnostics only |
| `t` | list<float64> | ns | per-photon global-time list for the module/event | A | §3.2 | produced_by=`PMTSD.cc:93-94,134` → `NNbarRun.cc:426,457-472`; consumed_by=timing diagnostics |

Consumed by: `_pmt_photons_for_event` (`reconstruction.py:67–83`)
which sums per-`Module_ID` *max* photon counts.

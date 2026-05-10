---
id: 09_scintillator
title: IO schema — Scintillator_output_<run>.parquet
parent: 09_io_schema_data_dictionary
source_section: "§9"
---

## 9. Scintillator table

Same NNbarHit-derived schema as TPC (§8) with the following
differences:

- `photons` column carries *photon-equivalent count* per
  `11136 photons/MeV` rule (per plan 07 §6.2; plan 18 audits against
  the optical-table 10000 photons/MeV value when
  `WITH_SCINTILLATION=ON`). Both factors are Class C.
- `module_ID` indexes the scintillator module per builder placement;
  the geometric mapping lives in `Scintillator_Module_Position.txt`
  (§13).

Decision-path consumers: `reconstruct_charged_objects` (matches
scintillator hits to TPC tracks); event-variable functions (per-
hemisphere energy sums).

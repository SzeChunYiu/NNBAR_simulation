---
id: 07_12_field_model
title: Simulation atomic walkthrough §12 — field model
version: 0.1
status: draft
owner: Sim Production
depends_on: [07_simulation_atomic_walkthrough]
---

## 12. Field model

The TPC drift field is provided by `util/ElectricField.cc` and
attached only to `TPC_output[0]` and `TPC_output[1]`
(`DetectorConstruction.cc:380–381`). Other TPC modules currently
inherit the world's null field. Plan 17 (field calibration) treats
this as a known incompleteness to address before any quantitative
TPC-drift study.

There is no global magnetic field. The current Geant4 simulation does
not include a B-field for charge-sign determination — this is
limitation L9 in plan 01.

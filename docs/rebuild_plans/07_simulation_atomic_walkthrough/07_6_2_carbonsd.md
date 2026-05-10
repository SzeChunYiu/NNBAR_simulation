---
id: 07_6_2_carbonsd
title: Simulation atomic walkthrough §6.2 — CarbonSD sensitive detector
version: 0.1
status: draft
owner: Sim Production
depends_on: [07_simulation_atomic_walkthrough]
---

# §6.2 `CarbonSD` sensitive detector (src/sensitive/CarbonSD.cc)

Status: pending L0 deepening.

Current summary: `CarbonSD` records hits inside the carbon foil and tags annihilation products at production. Per-step pattern follows TPCSD without the electron-counting branch.

Required coverage for this file: `Initialize`, `ProcessHits`,
`EndOfEvent` body shape, fields written to `NNbarHit`, decision
branches, and source citations in the form `(src/sensitive/CarbonSD.cc:linenumber)`.

---
id: 07_6_2_tubesd
title: Simulation atomic walkthrough §6.2 — TubeSD sensitive detector
version: 0.1
status: draft
owner: Sim Production
depends_on: [07_simulation_atomic_walkthrough]
---

# §6.2 `TubeSD` sensitive detector (src/sensitive/TubeSD.cc)

Status: pending L0 deepening.

Current summary: `TubeSD` records hits anywhere in the beampipe LVs. Used to study beampipe-origin secondaries.

Required coverage for this file: `Initialize`, `ProcessHits`,
`EndOfEvent` body shape, fields written to `NNbarHit`, decision
branches, and source citations in the form `(src/sensitive/TubeSD.cc:linenumber)`.

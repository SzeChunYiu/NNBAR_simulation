---
id: 07_6_2_leadglasssd
title: Simulation atomic walkthrough §6.2 — LeadGlassSD sensitive detector
version: 0.1
status: draft
owner: Sim Production
depends_on: [07_simulation_atomic_walkthrough]
---

# §6.2 `LeadGlassSD` sensitive detector (src/sensitive/LeadGlassSD.cc)

Status: pending L0 deepening.

Current summary: `LeadGlassSD` records hits in the active lead-glass volume.

Required coverage for this file: `Initialize`, `ProcessHits`,
`EndOfEvent` body shape, fields written to `NNbarHit`, decision
branches, and source citations in the form `(src/sensitive/LeadGlassSD.cc:linenumber)`.

---
id: 07_6_2_scintillatorsd
title: Simulation atomic walkthrough §6.2 — ScintillatorSD sensitive detector
version: 0.1
status: draft
owner: Sim Production
depends_on: [07_simulation_atomic_walkthrough]
---

# §6.2 `ScintillatorSD` sensitive detector (src/sensitive/ScintillatorSD.cc)

Status: pending L0 deepening.

Current summary: `ScintillatorSD` records hits in the plastic scintillator and computes a photon-equivalent count of `11136 photons/MeV`.

Required coverage for this file: `Initialize`, `ProcessHits`,
`EndOfEvent` body shape, fields written to `NNbarHit`, decision
branches, and source citations in the form `(src/sensitive/ScintillatorSD.cc:linenumber)`.

---
id: 07_6_2_pmtsd
title: Simulation atomic walkthrough §6.2 — PMTSD sensitive detector
version: 0.1
status: draft
owner: Sim Production
depends_on: [07_simulation_atomic_walkthrough]
---

# §6.2 `PMTSD` sensitive detector (src/sensitive/PMTSD.cc)

Status: pending L0 deepening.

Current summary: `PMTSD` records optical-photon hits in the PMT-face volume. Active only when optical photons are produced.

Required coverage for this file: `Initialize`, `ProcessHits`,
`EndOfEvent` body shape, fields written to `NNbarHit`, decision
branches, and source citations in the form `(src/sensitive/PMTSD.cc:linenumber)`.

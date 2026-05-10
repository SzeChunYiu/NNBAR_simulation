---
id: 07_6_2_unattached_sensitive_detectors
title: Simulation atomic walkthrough §6.2 — present but unattached sensitive detectors
version: 0.1
status: draft
owner: Sim Production
depends_on: [07_simulation_atomic_walkthrough]
---

# §6.2 Present but unattached sensitive detectors

`Scint_DetSD`, `ShieldSD`, and `DetArea_SD` exist in
`src/sensitive/` but are not attached in
`DetectorConstruction::ConstructSDandField`. Plan 14 flags them as
candidates for retirement or revival.

Do not deepen these files during L0 unless the attachment status changes.

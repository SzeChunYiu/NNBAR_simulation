---
id: 07_13_macros
title: Simulation atomic walkthrough §13 — macros overview
version: 0.1
status: draft
owner: Sim Production
depends_on: [07_simulation_atomic_walkthrough]
---

## 13. Macros (overview; full inventory in plan 10)

The macro tree contains:

- **Visualisation**: `gui.mac`, `init_vis.mac`, `vis.mac`,
  `opticks_test.mac`.
- **Quick smoke tests**: `quick_test.mac`, `test.mac`,
  `test_signal_quick.mac`.
- **Signal**: `macro/signal/run_signal.mac`,
  `macro/signal/run_signal_100k.mac`, with a `BeamOn.mac` driver.
- **Cosmics (current set)**: per-species (`cosmic_muon`,
  `cosmic_electron`, `cosmic_gamma`, `cosmic_neutron`, `cosmic_proton`,
  `cosmic_muon_short`), each with a per-run partition. Plan 21
  replaces these with a CRY-driven set.
- **Calibration**: lead-glass and scintillator electron/gamma/pion
  energy scans; π⁰ calibration. Plan 23 promotes these to the
  auxiliary calibration sample registry.
- **Studies (thesis-bound)**:
  `pi0_foil_mass.mac`, `pi0_foil_energy_scan.mac`,
  `charged_pion_proton_foil_stress.mac`,
  `multiprimary_pion_proton_foil_stress.mac`. These produce the
  parquet samples cited by `reconstruction.md` examples.
- **Legacy `macros/` (lower-level)**: `signal_pion_minus.mac`,
  `signal_pion_plus.mac`, `signal_proton.mac`,
  `background_compton.mac`. Plan 10 audits whether any of these are
  still consumed.

Plan 10 freezes the command-by-command inventory.

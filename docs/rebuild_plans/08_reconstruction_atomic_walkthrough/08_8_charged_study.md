---
id: 08_8
title: Reconstruction atomic walkthrough — charged study
version: 0.1
status: draft
owner: Reproducibility WG
depends_on: [08_reconstruction_atomic_walkthrough]
inputs:
  - {path: NNBAR_Detector/nnbar_reconstruction/charged_study.py, schema: source file}
outputs:
  - {path: docs/rebuild_plans/08_reconstruction_atomic_walkthrough/08_8_charged_study.md, schema: split walkthrough section}
last_updated: 2026-05-10
---

# Charged study — split from plan 08

This split file preserves and deepens plan 08 §8 so the main walkthrough
stays below the 500-line cap.

## 8. Charged study (charged_study.py, 2241 lines)

The largest module. Public surface:

- `evaluate_charged_stress(output_dir, runs)`
- `event_rows(report)`

Per `reconstruction.md` lines 270–319, the study enumerates every
`pi+`, `pi-`, and `proton` primary in `Particle`, checks whether a
same-event/same-truth-name charged object was reconstructed from TPC
hits, and reports per-species tracking efficiency, PID accuracy, and
detector hit coverage.

Plan 24 (question tree) records the per-species charged-object leaf
identity; plan 29 (charged PID) consumes the per-primary breakdown.
Like pi0_study, the structural section here is a v0.1 stub.

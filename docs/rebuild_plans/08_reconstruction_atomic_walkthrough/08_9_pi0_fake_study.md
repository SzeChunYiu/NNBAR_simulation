---
id: 08_9
title: Reconstruction atomic walkthrough — pi0 fake study
version: 0.1
status: draft
owner: Reproducibility WG
depends_on: [08_reconstruction_atomic_walkthrough]
inputs:
  - {path: NNBAR_Detector/nnbar_reconstruction/pi0_fake_study.py, schema: source file}
outputs:
  - {path: docs/rebuild_plans/08_reconstruction_atomic_walkthrough/08_9_pi0_fake_study.md, schema: split walkthrough section}
last_updated: 2026-05-10
---

# π⁰ fake study — split from plan 08

This split file preserves and deepens plan 08 §9 so the main walkthrough
stays below the 500-line cap.

## 9. π⁰ fake study (pi0_fake_study.py, 325 lines)

Public surface:

- `evaluate_pi0_fake_background(output_dir, runs, config,
  track_isolated, prompt_timing)`
- `pi0_fake_rows(report)`

Classifies π⁰-like candidates in samples that contain *no truth π⁰*
(charged stress samples, beam-neutron samples) by truth lineage.
Used to bound the fake-pi0 rate from charged backgrounds.

---
id: 08_7
title: Reconstruction atomic walkthrough — pi0 study
version: 0.1
status: draft
owner: Reproducibility WG
depends_on: [08_reconstruction_atomic_walkthrough]
inputs:
  - {path: NNBAR_Detector/nnbar_reconstruction/pi0_study.py, schema: source file}
outputs:
  - {path: docs/rebuild_plans/08_reconstruction_atomic_walkthrough/08_7_pi0_study.md, schema: split walkthrough section}
last_updated: 2026-05-10
---

# π⁰ study — split from plan 08

This split file preserves and deepens plan 08 §7 so the main walkthrough
stays below the 500-line cap.

## 7. π⁰ study (pi0_study.py, 1974 lines)

The 2 KLOC file is the most analytically dense module. It implements
the truth-vs-reco mass ladder used in the licentiate Ch 8 to motivate
the thesis π⁰ selection. Public surface:

- `evaluate_pi0_mass_ladder(output_dir, run, reconstruction)`
- `event_rows(report)`

Per-event rows are emitted at multiple ladder rungs (truth-only,
truth-direction + reco-energy, reco-direction + truth-energy, full
reco), so this is already a partial precursor to plan 38
(truth-substitution ladder). Plan 38 generalises the rung schema and
adds the canonical truth definition per leaf.

Plan 14 (validation suite) and plan 34 (fast-MC sanity) take ownership
of expanding this module's structure documentation; for v0.1, the
internal function map is recorded as a stub that codex-supervisor
deepens.

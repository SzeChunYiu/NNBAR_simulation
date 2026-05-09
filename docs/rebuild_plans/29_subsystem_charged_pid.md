---
id: 29_subsystem_charged_pid
title: Subsystem — charged PID (leaves C.1, C.5, C.6)
version: 0.1
status: draft
owner: Charged-PID POG
depends_on: [00_README, 23_sample_calibration_aux, 24_reconstruction_question_tree, 27_subsystem_dedx, 28_subsystem_range_and_stopping, 57_mva_method_protocol]
outputs:
  - {path: docs/rebuild_plans/29_subsystem_charged_pid.md, schema: this file}
acceptance:
  - {test: cut-based PID reproduces licentiate balanced-F1, method: scan-pid CLI on signal + cal samples, pass_when: ≥ baseline}
  - {test: likelihood-ratio PID benchmarked against cut-based on ladder leaf C.5, method: plan 38 matrix entry, pass_when: matrix entry recorded}
  - {test: Class B `Name` gate removed from C.1 production path, method: plan 01 audit, pass_when: zero violations}
risks:
  - {risk: removing the Name gate exposes EM and neutral tracks to PID classifier; misclassification rises, mitigation: §3 EM/neutral rejection via shower-shape and TPC topology}
estimated_effort: L
last_invented: 2026-05-09
---

# Subsystem — charged PID

*Charter.* Owns leaves C.1 (charged candidate), C.5 (π/p decision),
C.6 (rejection). Combines dE/dx (plan 27) and range (plan 28) into
a per-track classification.

## 1. Cut-based baseline (current code)

`reconstruction.py` `reconstruct_charged_objects` (plan 08 §3.4):

```
proton if  dedx >= proton_dedx_min                       # default 8.0
        OR (0 < scint_range <= short_range_cm
            AND dedx >= short_range_proton_dedx_min)     # default 4.5
charged_pion otherwise
```

Defaults are intentionally simple; `scan-pid` (plan 08 §4.2) tunes
them on labelled samples.

Class B violation: input is currently filtered to `Name ∈ {pi+, pi-,
proton, antiproton}` before the PID rule applies. Migration: drop
this filter; treat any TPC track as a candidate; the PID rule plus
EM/neutral rejection (§3) replaces the filter.

## 2. Likelihood-ratio PID (target improvement)

Per plan 57 MVA protocol:

1. Train a likelihood ratio (`L_proton / (L_proton + L_pion)`) on
   `cal_singleproton_v1` and `cal_singlepionplus/minus_v1`.
2. Features: dE/dx (truncated mean), range, scintillator energy,
   track length, n hits, lead-glass leakage.
3. Train/validation/test split with seed; check overtraining
   (plan 57 §3).
4. Score on the ladder (plan 38 leaf C.5). Improvement is reported
   as IV(C.5) reduction.

## 3. EM and neutral rejection (C.6)

When `Name` filter is removed (§1 migration), the candidate set
includes:

- Truth electrons / positrons (gamma conversions in detector
  material).
- Truth neutral-particle artefacts (rare).

Rejection rules:

- *EM rejection.* TPC track with low dE/dx + matched lead-glass
  cluster of high E and small lateral spread → tag as electron.
  See plan 32 (shower shape) for the cluster-side criterion.
- *Conversion-pair rejection.* TPC tracks coming from a vertex
  reconstructed near beampipe/silicon material with opposite-charge
  partner → tag as conversion pair (matches Ch 8.2 5 cm rule
  already implemented for electron-pair candidates).

Each rejection is implemented in Class A: lead-glass clusters and
TPC topology only.

## 4. Acceptance criteria

- §1 cut-based baseline reproduced.
- §1 Name filter removed; replaced by §3 rejections.
- §2 likelihood-ratio scored on ladder; matrix entry in plan 38.
- Plan 47 ledger row "licentiate Ch 8 charged PID accuracy"
  reproduced.

## 5. Risks

- *Risk:* likelihood-ratio overfits on calibration sample.
  *Mitigation:* plan 57 §3 overtraining check; final score on
  signal-sample-derived test set.

## 6. Dependencies

- **23, 24, 27, 28, 57** — inputs.
- *Consumed by:* plans 32 (event selection), 38 (ladder), 47.

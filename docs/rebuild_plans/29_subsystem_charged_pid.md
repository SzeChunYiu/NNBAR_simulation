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

## 1. Leaf input/output schemas

Per plan 24 C.1 / C.5 / C.6 schemas:

| Leaf | Class A inputs | Forbidden Class B | Output schema |
|---|---|---|---|
| C.1 charged candidate | V.1/V.2 track tables; TPC `Event_ID`, `x`, `y`, `z`, `t`, `eDep`, `photons`, `px`, `py`, `pz`, `xHitID`, `module_ID`, `step_info`, `vol_name` | `Name`, `Track_ID`, `Parent_ID`, `origin_vol_name`, `particle_x/y/z` | `{event_id, charged_candidate_id, candidate_id, anchor_xyz, direction_xyz, n_tpc_hits, track_quality, charged_candidate_valid}` |
| C.5 π/p decision | C.1 candidate table, C.2 dE/dx, C.3 range, C.4 scintillator association, PID thresholds | `Name`, `Track_ID`, `Parent_ID`, `origin_vol_name`, truth PID labels | `{event_id, charged_candidate_id, pid, proton_score, pion_score, thresholds, rule_version, pid_valid, decision_reason}` |
| C.6 rejection | C.1-C.5 outputs, Class A lead-glass / shower-shape observables, TPC pair topology, hit timing, geometry side-cars | `Name`, `Track_ID`, `Parent_ID`, `origin_vol_name`, `Interaction`, `particle_x/y/z`, truth PID labels | `{event_id, charged_candidate_id, rejected, rejection_flags, primary_reason, pid_before_rejection, pid_after_rejection, rule_version}` |

Current implementation citation: `reconstruct_charged_objects`
(`reconstruction.py:430-700`, plan 08 §3.4) owns the current C.1/C.5
path and emits `pid`, `dedx`, `scintillator_range`, `track_anchor`,
and `track_direction`, with `truth_name` retained for validation only
after the migration.

## 2. Cut-based baseline (current code)

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

## 3. Likelihood-ratio PID (target improvement)

Per plan 57 MVA protocol:

1. Train a likelihood ratio (`L_proton / (L_proton + L_pion)`) on
   `cal_singleproton_v1` and `cal_singlepionplus/minus_v1`.
2. Features: dE/dx (truncated mean), range, scintillator energy,
   track length, n hits, lead-glass leakage.
3. Train/validation/test split with seed; check overtraining
   (plan 57 §3).
4. Score on the ladder (plan 38 leaf C.5). Improvement is reported
   as IV(C.5) reduction.


### 3.1 Alternative comparison rows

| Alternative | Source paper / codebase | NNBAR-specific adaptation | Expected ladder leaf delta |
|---|---|---|---|
| Cut-based baseline | Existing `reconstruct_charged_objects` (`reconstruction.py:430-700`) | Keep thesis Ch 8/9 threshold form but remove the C.1 truth-name gate before production scoring. | Reproduces baseline; ladder delta comes primarily from removing truth substitution. |
| Likelihood-ratio PID | Plan 57 MVA protocol / standard likelihood-ratio classifier | Train on plan 23 charged calibration samples using C.2/C.3/C.4 features and locked train/validation/test splits. | Expected to reduce C.5 π/p confusion, especially near stopping-proton boundaries; must beat cut-based on plan 38. |

## 4. EM and neutral rejection (C.6)

When `Name` filter is removed (§2 migration), the candidate set
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

## 5. Closure-test specification

1. **Dataset ids:** `cal_singlepion_50to600MeV_v2`,
   `cal_singleproton_50to500MeV_v2`, and `sig_foil_500MeV_v3` from
   plan 03.
2. **Observable:** C.5 π/p confusion matrix, balanced F1, proton
   efficiency, charged-pion efficiency, and C.6 rejection fractions.
3. **Fitter / classifier:** run `scan-pid` for the cut-based baseline
   and the locked likelihood-ratio classifier for the improvement;
   truth labels are consumed only in the validation/labeling split.
4. **Pass criterion:** cut-based PID reproduces the licentiate
   baseline within plan 47 tolerance, the `Name` gate is absent from
   the production path, and the likelihood-ratio result has a plan 38
   C.5 ladder matrix entry before any promotion.

## 6. Acceptance criteria

- §2 cut-based baseline reproduced.
- §2 Name filter removed; replaced by §4 rejections.
- §3 likelihood-ratio scored on ladder; matrix entry in plan 38.
- Plan 47 ledger row "licentiate Ch 8 charged PID accuracy"
  reproduced.

## 7. Risks

- *Risk:* likelihood-ratio overfits on calibration sample.
  *Mitigation:* plan 57 §3 overtraining check; final score on
  signal-sample-derived test set.

## 8. Dependencies

- **23, 24, 27, 28, 57** — inputs.
- *Consumed by:* plans 32 (event selection), 38 (ladder), 47.

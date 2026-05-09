---
id: 32_subsystem_shower_shape
title: Subsystem — shower shape and charged/neutral discriminant (leaf P.2)
version: 0.1
status: draft
owner: EM-Object POG
depends_on: [00_README, 24_reconstruction_question_tree, 31_subsystem_calorimeter_clustering, 38_truth_substitution_ladder, 57_mva_method_protocol]
outputs:
  - {path: docs/rebuild_plans/32_subsystem_shower_shape.md, schema: this file}
acceptance:
  - {test: charged/neutral classifier ROC AUC ≥ 0.95 on signal + cal_singlepion samples, method: closure ROC, pass_when: pass}
  - {test: classifier benchmarked on ladder leaf P.2, method: plan 38, pass_when: matrix entry}
  - {test: classifier uses Class A inputs only, method: plan 01 audit, pass_when: zero Class B}
risks:
  - {risk: shower-shape moments depend strongly on cluster definition (plan 31), mitigation: §2 paired benchmark with each clustering option}
estimated_effort: L
last_updated: 2026-05-09
---

# Subsystem — shower shape and charged/neutral discriminant

*Charter.* Owns leaf P.2. Compute shower-shape observables for each
cluster from plan 31, then build a charged/neutral discriminant.

## 1. Shower-shape observables

For each cluster:

- **Lateral spread** — RMS of hit positions perpendicular to the
  cluster axis.
- **Depth** — mean longitudinal coordinate (energy-weighted).
- **Longitudinal moments** — first and second moments of the
  longitudinal energy profile.
- **Maximum-cell fraction** — `E_max / E_total`.
- **Cluster timing spread** — RMS of hit times.
- **Distance to nearest TPC-extrapolated track impact** — geometric
  matching to charged tracks.

All Class A.

## 2. Charged/neutral discriminant (current vs replacement)

- *Current.* Vertex-to-centroid direction inside
  `charged_cluster_match_angle_deg = 10.5°` cone of any TPC track
  direction (plan 08 §3.5 step 2). Hard cut.
- *Replacement.* Multivariate discriminant (BDT or NN) on shower
  shape + cone distance + timing match. Plan 57 protocol; trained
  on `cal_singlegamma_v1` (neutral) vs `cal_singleelectron_v1`
  (charged conversion proxy) plus signal sample for in-distribution.

## 3. Closure (plan 40)

ROC curve on:

- Truth-positive (gamma) sample: `cal_singlegamma_v1`.
- Truth-negative (charged) sample: `cal_singleelectron_v1` plus
  charged-pion-induced clusters in `sig_foil_v3` (truth-labelled
  for closure only).

Acceptance: AUC ≥ 0.95.

## 4. Acceptance criteria

- §1 observables produced for every cluster.
- §2 classifier replaces fixed-cone with paired ladder benchmark.
- §3 ROC closure passes.

## 5. Dependencies

- **24, 31, 38, 57** — inputs.
- *Consumed by:* plan 33 (photon object).

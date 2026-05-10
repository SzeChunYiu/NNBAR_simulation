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

## 1. Leaf P.2 input/output schema and observables

Leaf P.2: cluster candidates → charged/neutral discriminant inputs

- **Inputs (production, Class A only):** plan-31 cluster rows and
  hit-membership keys; underlying LeadGlass/Scintillator `eDep`,
  `x/y/z`, optional `t`; reconstructed TPC track anchors/directions
  from plans 25–30; reconstructed vertex from plan 30.
- **Current implementation evidence:** plan 08 records the hard-cone
  charged-match candidate construction in `reconstruct_photon_objects`
  (`reconstruction.py:850–889`) after truth-based TPC-track skips in
  `_tpc_tracks_to_skip_for_charged_matching`
  (`reconstruction.py:632–688`). The per-cluster charged decision is
  accepted in `build_photon_row` at `reconstruction.py:941–989`,
  with diagnostic truth/provenance classes filled at
  `reconstruction.py:990–1014`.
- **Decision rule (target):** compute shower-shape observables and a
  neutral score without using `Name`, `Parent_ID`, `Track_ID`, or
  source ancestry. The production photon-like flag is a threshold on
  the selected P.2 discriminant; truth labels enter only the training
  and closure labels governed by plan 57.
- **Outputs:** one row per cluster with `event_id`, `cluster_id`,
  `lateral_rms_cm`, `longitudinal_depth_cm`,
  `longitudinal_rms_cm`, `max_cell_fraction`,
  `cluster_time_rms_ns`, `nearest_track_distance_cm`,
  `nearest_track_angle_deg`, `neutral_score`,
  `passes_neutral_discriminant`, and model/config identifiers.

Observable definitions, all derived from Class A production inputs:

- **Lateral spread** — RMS of hit positions perpendicular to the
  cluster axis.
- **Depth** — mean longitudinal coordinate, energy-weighted.
- **Longitudinal moments** — first and second moments of the
  longitudinal energy profile.
- **Maximum-cell fraction** — `E_max / E_total`.
- **Cluster timing spread** — RMS of hit times.
- **Distance / angle to nearest TPC-extrapolated track impact** —
  geometric matching to reconstructed charged tracks.

## 2. Charged/neutral discriminant candidates

| Candidate | P.2 decision rule | Current/source citation | Class-A status | Comparison metric | Failure mode to inspect |
|---|---|---|---|---|---|
| **Hard cone (current)** | Mark charged when vertex-to-centroid direction lies within `charged_cluster_match_angle_deg = 10.5°` of a TPC-track direction. | Charged-match candidates and threshold in `reconstruct_photon_objects` (`reconstruction.py:850–889`, `941–989`, plan 08 §3.5.2). | Partly eligible: geometric cone is Class A, but current TPC-track skip logic reads truth (`reconstruction.py:632–688`). | ROC point, charged contamination, neutral efficiency. | Truth-skip path can hide conversion/electron backgrounds. |
| **Rectangular shower-shape cuts** | Apply tuned cuts on lateral RMS, depth, max-cell fraction, timing RMS, and track distance. | Replaces the single angle threshold in `build_photon_row`. | Production-eligible if thresholds are DEC-logged. | AUC/efficiency and N-1 stability for each variable. | Sharp thresholds may be unstable across clusterers. |
| **BDT discriminant** | Train a bounded tree model on the §1 observables and track-distance variables. | Plan 57-governed replacement for the current hard cone. | Production-eligible after frozen feature contract and training provenance. | ROC AUC, calibration curve, feature-ablated stability. | Overtraining to single-γ calibration topology. |
| **Neural discriminant** | Train a small NN on the same tabular features; threshold `neutral_score`. | Plan 57-governed alternative to BDT. | Production-eligible only if deterministic export and audit artifacts land. | Same as BDT plus seed/export reproducibility. | Harder to defend than BDT without clear gains. |
| **Truth-labelled diagnostic** | Use gamma/e± ancestry to label neutral or charged shower origin. | Current source labels flow through `_shower_truth_name` and `truth_charge_match_class` (`reconstruction.py:990–1014`). | Not production-eligible; validation labels only. | Upper-bound/reference ROC. | Inflates performance and fails plan 01 if used in decisions. |

Plan 38 scores all candidates on identical P.1 cluster inputs. Plan 57
requires the selected BDT/NN feature list, training split, and threshold
to be frozen before it can replace the hard-cone baseline.

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

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
- **Current implementation evidence:** the compact current source
  implements the hard-cone charged/neutral baseline inside
  `reconstruct_photon_objects` (`reconstruction.py:432-573`).
  The threshold comes from `ReconstructionConfig` as
  `charged_cluster_match_angle_deg = 8.0`. The same function also
  emits the diagnostic `truth_name` and `source_track_id` columns,
  so those fields remain validation/provenance surfaces rather than
  production discriminant inputs.
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

### 1.1 Feature formulas

Let `r_i` be the hit position relative to the cluster centroid,
`E_i` the hit energy, `t_i` the hit time, and `u` the cluster axis
from the reconstructed vertex to the centroid (or the declared
origin fallback from plan 33 when no vertex exists).

- `lateral_rms_cm = sqrt(Σ E_i |r_i - (r_i·u)u|² / Σ E_i)`.
- `longitudinal_depth_cm = Σ E_i (r_i·u) / Σ E_i`.
- `longitudinal_rms_cm = sqrt(Σ E_i ((r_i·u) - depth)² / Σ E_i)`.
- `max_cell_fraction = max(E_i) / Σ E_i`.
- `cluster_time_rms_ns = sqrt(Σ E_i (t_i - t̄)² / Σ E_i)`.
- `nearest_track_distance_cm` is the shortest distance between the
  centroid and any reconstructed TPC-track extrapolation; the angle
  column is the angle between `u` and that track direction.

If `Σ E_i = 0` or no valid axis exists, emit finite sentinel values
and `passes_neutral_discriminant = false`; never substitute truth
direction or truth charge labels.

## 2. Charged/neutral discriminant candidates

| Candidate | P.2 decision rule | Current/source citation | Class-A status | Comparison metric | Failure mode to inspect |
|---|---|---|---|---|---|
| **Hard cone (current)** | Mark charged when vertex-to-centroid direction lies within `charged_cluster_match_angle_deg = 8.0°` of a TPC-track direction. | Charged-match candidates, threshold, and output flag live in `reconstruct_photon_objects` (`reconstruction.py:432-573`) with the default in `ReconstructionConfig`. | Partly eligible: geometric cone is Class A if upstream track inputs are reconstructed objects; current row still carries provenance columns. | ROC point, charged contamination, neutral efficiency. | Track-key/provenance coupling can hide conversion/electron backgrounds. |
| **Rectangular shower-shape cuts** | Apply tuned cuts on lateral RMS, depth, max-cell fraction, timing RMS, and track distance. | Replaces the single angle threshold in `reconstruct_photon_objects` (`reconstruction.py:432-573`). | Production-eligible if thresholds are DEC-logged. | AUC/efficiency and N-1 stability for each variable. | Sharp thresholds may be unstable across clusterers. |
| **BDT discriminant** | Train a bounded tree model on the §1 observables and track-distance variables. | Plan 57-governed replacement for the current hard cone. | Production-eligible after frozen feature contract and training provenance. | ROC AUC, calibration curve, feature-ablated stability. | Overtraining to single-γ calibration topology. |
| **Neural discriminant** | Train a small NN on the same tabular features; threshold `neutral_score`. | Plan 57-governed alternative to BDT. | Production-eligible only if deterministic export and audit artifacts land. | Same as BDT plus seed/export reproducibility. | Harder to defend than BDT without clear gains. |
| **Truth-labelled diagnostic** | Join validation-only gamma/e± labels after production scoring. | Current production rows expose diagnostic `truth_name` in `reconstruct_photon_objects` (`reconstruction.py:432-573`) for validation joins only. | Not production-eligible; validation labels only. | Upper-bound/reference ROC. | Inflates performance and fails plan 01 if used in decisions. |

Plan 38 scores all candidates on identical P.1 cluster inputs. Plan 57
requires the selected BDT/NN feature list, training split, and threshold
to be frozen before it can replace the hard-cone baseline.

## 3. Closure-test specification

1. **Dataset ids:** positive labels from `cal_singlegamma_v1`;
   charged negative labels from `cal_singleelectron_v1` plus
   charged-pion-associated clusters in `sig_foil_v3`. Truth ancestry
   is used only to assign closure labels, never as a feature.
2. **Observable:** `neutral_score`, `passes_neutral_discriminant`,
   per-feature distributions from §1, neutral efficiency, charged
   fake rate, and receiver-operating-characteristic points.
3. **Fitter / estimator:** compute ROC AUC with stratified bootstrap
   confidence intervals; for fixed-threshold candidates, report the
   single ROC operating point plus Wilson intervals for efficiency and
   fake rate.
4. **Pass criterion:** selected production candidate has ROC AUC
   `≥ 0.95`, neutral efficiency `≥ 0.90` at the frozen threshold,
   and charged fake rate `≤ 0.05` on every negative sample component.
5. **Audit hook:** repeat the evaluation with all Class B columns
   removed from the reconstruction input. Features, score, and
   production pass/fail must be bitwise identical.

### 3.1 Decision-log stubs for the P.2 discriminator

Changing the charged/neutral discriminator changes photon-object
eligibility downstream. Freeze these choices through plan 05 before
they affect production photon rows:

| DEC stub | Decision to freeze | Required evidence before approval |
|---|---|---|
| `DEC-32-DISCRIMINANT-CHOICE` | Select hard cone, rectangular cuts, BDT, or NN as the production P.2 discriminator | plan-38 candidate comparison plus §3 ROC closure on every labelled component |
| `DEC-32-FEATURE-CONTRACT` | Freeze the shower-shape and nearest-track feature list, including sentinel handling | plan-57 feature contract and Class-A audit proving no truth/provenance feature enters inference |
| `DEC-32-NEUTRAL-THRESHOLD` | Freeze `neutral_score` / cut threshold and operating point | bootstrap AUC, neutral efficiency, charged fake rate, and N-1 stability evidence |

Until approval, non-current discriminants may be trained and scored
only as ladder alternatives; the current hard-cone baseline remains
the reproduction path.

## 4. Acceptance criteria

- §1 observables produced for every cluster.
- §2 classifier replaces fixed-cone with paired ladder benchmark.
- §3 ROC closure passes.

## 5. Dependencies

- **24, 31, 38, 57** — inputs.
- *Consumed by:* plan 33 (photon object).

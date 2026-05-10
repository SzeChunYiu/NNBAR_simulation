---
id: 33_subsystem_photon_object
title: Subsystem — photon object (leaves P.3, P.4)
version: 0.1
status: draft
owner: EM-Object POG
depends_on: [00_README, 18_intercalibration, 24_reconstruction_question_tree, 30_subsystem_vertex, 31_subsystem_calorimeter_clustering, 32_subsystem_shower_shape, 38_truth_substitution_ladder, 40_closure_and_pulls]
outputs:
  - {path: docs/rebuild_plans/33_subsystem_photon_object.md, schema: this file}
acceptance:
  - {test: photon direction pull width within plan 40 §2, method: closure plot on cal_singlegamma_v1, pass_when: pass}
  - {test: photon energy bias < 1% on cal_singlegamma_v1 in linear regime, method: closure plot, pass_when: pass}
  - {test: scintillator-fed photons (no LG hits) are tagged with leadglass_fraction = 0, method: §2 review, pass_when: implemented}
risks:
  - {risk: photon merging by direction proximity (current code) loses well-separated π⁰ daughters at small opening angles, mitigation: §3 angular threshold tuned and DEC-logged}
estimated_effort: M
last_updated: 2026-05-09
---

# Subsystem — photon object

*Charter.* Owns leaves P.3 (direction), P.4 (energy). Builds the
photon four-vector from clusters classified neutral by plan 32.

## 1. Leaf P.3/P.4 input/output schema

Leaf P.3/P.4: neutral clusters → photon four-vector objects

- **Inputs (production, Class A only):** plan-31 cluster row and hit
  membership, plan-32 `passes_neutral_discriminant` /
  `neutral_score`, plan-30 vertex row, calorimeter energy calibration
  constants from plan 18, and detector geometry.
- **Current implementation evidence:** plan 08 maps photon-object
  construction to `reconstruct_photon_objects`
  (`reconstruction.py:783–1101`). It caches reconstructed vertices at
  `reconstruction.py:829–849`, computes direction/path inside
  `build_photon_row` (`reconstruction.py:941–989`), emits
  lead-glass and scintillator-only source groups at
  `reconstruction.py:1046–1099`, and declares the current photon
  output schema at `reconstruction.py:793–822`. Fragment merging is
  `_merge_photon_fragments` (`reconstruction.py:502–629`).
- **Decision rule (target):** accept only clusters that passed P.2;
  compute direction from reconstructed vertex to energy-weighted
  cluster centroid; compute energy from calibrated cluster deposits;
  merge duplicate neutral fragments only by geometry/time compatibility.
- **Outputs:** `event_id`, `object_id`, `cluster_id`, `energy_mev`,
  `leadglass_edep`, `scintillator_edep`, `leadglass_fraction`,
  `cluster_x/y/z`, `cluster_time_ns`, `vertex_x/y/z`,
  `vertex_time_ns`, `photon_path_length_cm`, `ux/uy/uz`,
  `neutral_score`, `source_cluster_ids`, and diagnostic-only closure
  labels.
- **Truth-use boundary:** `truth_name`, source-track aliases, and
  truth charge classes from the current table stay diagnostic; no
  photon four-vector field may depend on them.

## 2. Direction (P.3)

Direction = `(cluster_centroid - event_vertex) / |…|`.

Vertex from plan 30 (V.4). Cluster centroid energy-weighted (per
plan 31).

When no event vertex is reconstructed (sparse-table fallback), use
origin → centroid; this is the historical fallback per
`reconstruction.md` lines 88–94.

Truth canonical (plan 38 §3.1): gamma momentum direction at
production.

## 3. Energy (P.4)

Target production energy is the calibrated P.1 cluster sum:
`energy_mev = leadglass_edep + scintillator_edep`, with both terms in
MeV and both terms derived from Class A cluster membership.

The current reproduction baseline obtains the scintillator
contribution from gamma-shower descendants via the same ancestry used
in plan 31 step 1. That value is kept only as the plan-47 baseline
and closure label; once plan 31 lands, P.4 must consume the
truth-blind P.1 cluster components instead.

Scintillator-only photons (no LG cluster) are emitted with
`leadglass_fraction = 0` so the thesis Ch 8 selection
(`leadglass_fraction ≥ 0.55`) does not accept them by construction.
Rows also carry `energy_method` (`cluster_sum`, `leadglass_only`,
`regression_calibration`, or `legacy_truth_descendant`) so plan 38 can
compare energy choices without changing the photon-object schema.

## 4. Photon merging

Truth-labelled neutral gamma fragments with nearly identical
reconstructed directions are merged before pairing
(`photon_fragment_merge_angle_deg = 2°`). Class B read; migration:
geometric direction-proximity merging, blind to truth labels.

## 5. Alternative comparison matrix

| Leaf | Candidate | Decision rule | Current/source citation | Class-A status | Comparison metric |
|---|---|---|---|---|---|
| P.3 | **Vertex → centroid (baseline target)** | Unit vector from reconstructed vertex to P.1 energy-weighted centroid. | Current row builder uses reconstructed vertex or origin fallback (`reconstruction.py:829–849`, `953–958`, `1030–1035`). | Production-eligible with plan-30 vertex. | Direction pull mean/width on `cal_singlegamma_v1`; downstream π⁰ mass. |
| P.3 | **Origin → centroid fallback** | Use detector origin when no event vertex exists. | Historical fallback documented in `reconstruction.md` lines 88–94 and plan 08 §3.5.2. | Eligible only as sparse-data fallback with explicit flag. | Pull degradation vs vertex baseline and fallback rate. |
| P.3 | **Cluster-axis fit** | Fit a shower axis from hit positions/timing and use it as direction. | Replacement for centroid-only direction inside `build_photon_row`. | Eligible if fit uses only hit geometry/timing. | Pull width and small-opening π⁰ separation. |
| P.4 | **Calibrated cluster sum (baseline target)** | Sum calibrated lead-glass plus scintillator cluster energy from P.1. | Replaces ancestry-derived scintillator descendants in current source grouping (`reconstruction.py:1046–1099`). | Production-eligible after plan-18 calibration. | Energy bias/resolution by single-γ energy bin. |
| P.4 | **Lead-glass-only energy** | Use only lead-glass cluster deposits; keep scintillator as diagnostic. | Current schema already carries `leadglass_fraction` (`reconstruction.py:793–822`). | Eligible but lower efficiency for scintillator-fed showers. | Bias for no-LG and edge showers; plan-34 selection loss. |
| P.4 | **Regression calibration** | Predict photon energy from cluster sum plus shower-shape features. | Plan 57-style replacement for raw sums. | Eligible only with frozen features and validation provenance. | Bias/resolution improvement vs calibrated sum. |
| P.3/P.4 | **Truth-labelled fragment merge (current)** | Merge fragments by neutral truth label and direction proximity. | `_merge_photon_fragments` (`reconstruction.py:502–629`). | Not production-eligible; Class B labels influence membership. | Reproduction baseline only. |
| P.3/P.4 | **Geometry/time fragment merge** | Merge nearby neutral clusters by angular, centroid, and timing compatibility. | Replaces `_merge_photon_fragments`. | Production-eligible with DEC-logged thresholds. | Duplicate rate, π⁰ daughter over-merge rate, closure pulls. |

Plan 38 records separate ladder rows for P.3 direction, P.4 energy,
and the fragment-merge policy because each can change the photon
four-vector independently.

## 6. Closure-test specification

1. **Dataset id:** `cal_singlegamma_v1` from plan 23 at 50, 100,
   200, 500, and 1000 MeV; use truth photon momentum and energy only
   in the evaluator.
2. **Observable:** P.3 angular residual and pull components, P.4
   energy response, photon reconstruction efficiency, fallback-origin
   fraction, and fragment duplicate / over-merge rates.
3. **Fitter / estimator:** fit direction pull cores with Gaussian
   means and widths; fit energy response per energy bin with Gaussian
   core plus bootstrap uncertainty; quote Wilson intervals for
   efficiency and fragment rates.
4. **Pass criterion:** direction pull width in `[0.9, 1.2]`,
   `|μ| < 0.05` for each pull component, absolute energy bias `< 1%`
   in the linear regime, photon efficiency `≥ 0.95`, and fragment
   over-merge rate `< 2%`.
5. **Audit hook:** rerun with truth/provenance columns dropped. Photon
   direction, energy, merge membership, and selected neutral status
   must be unchanged.

## 7. Acceptance criteria

- §2, §3 produce photon four-vector with stated semantics.
- §4 truth-blind merging in place.
- §6 closure passes.

## 8. Dependencies

- **18, 24, 30, 31, 32, 38, 40** — inputs.
- *Consumed by:* plan 34 (π⁰ pairing), plan 36 (event variables),
  plan 38 (ladder leaves P.3, P.4).

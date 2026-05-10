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
  - {risk: adding fragment merging can lose well-separated π⁰ daughters at small opening angles, mitigation: §3 angular threshold tuned and DEC-logged}
estimated_effort: M
last_updated: 2026-05-10
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
- **Current implementation evidence:** the compact current source
  builds photon-like objects in `reconstruct_photon_objects` (`photon.py:60-201`). That function declares the output
  columns, caches reconstructed vertices, computes the vertex-to-
  centroid direction and path length, attaches lead-glass plus
  scintillator energy for the same key, and emits diagnostic
  `truth_name` / `source_track_id` provenance fields. There is no
  separate production fragment-merge helper in the current source.
- **Decision rule (target):** accept only clusters that passed P.2;
  compute direction from reconstructed vertex to energy-weighted
  cluster centroid; compute energy from calibrated cluster deposits;
  merge duplicate neutral fragments only by geometry/time compatibility.
- **Outputs (target schema):** `event_id`, `object_id`,
  `cluster_id`, `energy_mev`, `leadglass_edep`,
  `scintillator_edep`, `leadglass_fraction`, `cluster_x/y/z`,
  `cluster_time_ns`, `vertex_x/y/z`, `vertex_time_ns`,
  `photon_path_length_cm`, `ux/uy/uz`, `neutral_score`,
  `source_cluster_ids`, and diagnostic-only closure labels. Current
  compact source emits `total_energy`, not `energy_mev`, inside
  `reconstruct_photon_objects` (`photon.py:60-201`); the rebuild
  bridge must map that field explicitly rather than implying the
  target column already exists upstream.
- **Truth-use boundary:** `truth_name`, source-track aliases, and
  truth charge classes from the current table stay diagnostic; no
  photon four-vector field may depend on them.

## 2. Direction (P.3)

Direction = `(cluster_centroid - event_vertex) / |…|`.

Vertex from plan 30 (V.4). Cluster centroid energy-weighted (per
plan 31).

When no event vertex is reconstructed (sparse-table fallback), use
origin → centroid and set the fallback flag. The current source keeps
that fallback inside `reconstruct_photon_objects` (`photon.py:60-201`).

### 2.1 Direction fallback contract

Every photon row must make the direction source auditable without
inspecting upstream tables:

| Condition | Required row values | Reporting use |
|---|---|---|
| reconstructed event vertex exists | `used_reconstructed_vertex = true`; `vertex_x/y/z` are the plan-30 vertex coordinates; `photon_path_length_cm = |cluster - vertex|` | primary P.3 direction closure |
| no reconstructed vertex exists | `used_reconstructed_vertex = false`; `vertex_x/y/z = 0`; direction is origin→centroid; row contributes to the fallback-origin fraction | sparse-data fallback audit |

The fallback flag is a production column, not a truth label. Closure
plots must report angular pulls separately for vertex-sourced and
origin-fallback rows before the fallback policy can be frozen.

### 2.2 Machine-readable P.3/P.4 photon fixture

The photon-object fixture stores one row per accepted neutral object and
makes the four-vector source auditable:

| Field | Required content | Review rule |
|---|---|---|
| `event_id`, `object_id`, `cluster_id` | stable join keys from plans 31-32 | `cluster_id` must resolve to a P.1 fixture row |
| `source_cluster_ids` | one or more P.1 clusters after merge | empty only for explicitly invalid rows |
| `energy_mev`, `energy_method` | selected P.4 energy and method tag | legacy aliases cannot masquerade as calibrated sums |
| `leadglass_edep`, `scintillator_edep`, `leadglass_fraction` | calorimeter energy components | additive with `energy_mev` for `cluster_sum` rows |
| `vertex_x`, `vertex_y`, `vertex_z`, `used_reconstructed_vertex` | P.3 direction source | fallback rows counted separately in closure |
| `ux`, `uy`, `uz`, `photon_path_length_cm` | normalized direction and path length | finite and derived from cluster/vertex geometry |
| `neutral_score`, `passes_neutral_discriminant` | consumed P.2 decision | no truth-label override is allowed |
| `merge_method_id`, `fragment_merge_flag` | duplicate-fragment policy | threshold changes require the plan-33 DEC |

Fixture review recomputes the direction unit vector and energy component
consistency from upstream P.1/P.2 rows. Dropping truth/provenance columns
may remove diagnostic labels but must not change photon four-vector
fields or merge decisions.

### 2.3 Current-to-target photon identity map

The current `object_id` from `reconstruct_photon_objects`
(`photon.py:60-201`) may be preserved only as
`legacy_photon_object_id` in reproduction rows. The target
`cluster_id` must come from the accepted plan-31 cluster fixture, and
`source_cluster_ids` records the one-or-more neutral clusters consumed
after any fragment merge. Current `source_track_id` and `truth_name`
columns remain diagnostic provenance; they cannot seed `cluster_id`,
`source_cluster_ids`, merge decisions, or the P.3/P.4 four-vector.

Truth canonical (plan 38 §3.1): gamma momentum direction at
production.

## 3. Energy (P.4)

Target production energy is the calibrated P.1 cluster sum:
`energy_mev = leadglass_edep + scintillator_edep`, with both terms in
MeV and both terms derived from Class A cluster membership.

The current reproduction baseline obtains the scintillator
contribution by matching the same `(Event_ID, Track_ID)` key inside
`reconstruct_photon_objects` (`photon.py:60-201`). That
value is kept only as the plan-47 baseline and closure label; once
plan 31 lands, P.4 must consume the truth-blind P.1 cluster
components instead.

Scintillator-only photons (no LG cluster) are emitted with
`leadglass_fraction = 0` so the thesis Ch 8 selection
(`leadglass_fraction ≥ 0.55`) does not accept them by construction.
Rows also carry `energy_method` (`cluster_sum`, `leadglass_only`,
`regression_calibration`, or `legacy_truth_descendant`) so plan 38 can
compare energy choices without changing the photon-object schema.

### 3.1 Current-to-target energy field map

Until the calibrated plan-18/31 cluster sum is implemented, the
reproduction bridge may expose current-source `total_energy` as
`energy_mev` only with `energy_method = legacy_truth_descendant` and
source provenance that points back to `reconstruct_photon_objects`
(`photon.py:60-201`). A row with `energy_method = cluster_sum` must
come from calibrated truth-blind cluster membership, not from the
current same-key scintillator lookup. This prevents plan 34/37 from
reading the target column name as evidence that production-calibrated
energy already exists.

## 4. Photon merging

The current compact source emits one photon-like row per accepted
lead-glass key and does not run a separate fragment-merge step. The
production target is an optional geometry/time merge that is blind to
truth labels, with all thresholds DEC-logged before it can affect
P.3/P.4 four-vectors.

### 4.1 A+ citation audit for current photon-object baseline

Current-source claims in §1-§5 were re-checked against the L3 worktree
before this plan was committed:

| Cited contract | Verifier evidence | Status |
|---|---|---|
| current photon-like row builder, direction fallback, energy alias, and no-fragment-merge baseline | `def reconstruct_photon_objects` resolves at `photon.py:60`, inside the cited `photon.py:60-201` range. | keep citation |

Plan 33 does not specify a runtime CLI command, and it does not cite the
removed legacy split-study files. Any future photon-object study CLI row
must pass the L3 `--help` verifier before this plan cites it.

### 4.2 Machine-readable fragment-merge fixture

If a geometry/time merge is evaluated, it writes one decision row for
each merge candidate before any photon four-vector is replaced:

| Field | Required content | Review rule |
|---|---|---|
| `merge_candidate_id` | stable key for the proposed merge | unique within event and method bundle |
| `event_id` | event containing the candidate fragments | joins to P.1/P.2 fixtures |
| `input_cluster_ids` | one or more neutral P.1 cluster ids | every id must pass the P.2 neutral gate |
| `angular_separation_deg`, `centroid_distance_cm`, `time_difference_ns` | truth-blind compatibility metrics | finite for every candidate pair/group |
| `merge_threshold_id` | threshold tuple used for the decision | changes require `DEC-33-FRAGMENT-MERGE` |
| `merge_decision` | `merge`, `keep_separate`, or `diagnostic_only` | production rows cannot be diagnostic-only |
| `output_source_cluster_ids` | clusters copied to the photon fixture | equals input ids only when `merge_decision = merge` |
| `fragment_merge_flag` | boolean copied to §2.2 photon rows | must match the merge decision |
| `truth_blind_input_hash` | hash after dropping truth/provenance fields | must preserve all merge decisions |
| `merge_status` | `pass`, `fail`, or `blocked` | blocked rows cannot feed plan-34 pairing |

The merge fixture is rejected if truth labels or generated photon ids
affect the candidate grouping, threshold comparison, or output source
cluster list.

## 5. Alternative comparison matrix

| Leaf | Candidate | Decision rule | Current/source citation | Class-A status | Comparison metric |
|---|---|---|---|---|---|
| P.3 | **Vertex → centroid (baseline target)** | Unit vector from reconstructed vertex to P.1 energy-weighted centroid. | Current row builder uses reconstructed vertex or origin fallback in `reconstruct_photon_objects` (`photon.py:60-201`). | Production-eligible with plan-30 vertex. | Direction pull mean/width on `cal_singlegamma_v1`; downstream π⁰ mass. |
| P.3 | **Origin → centroid fallback** | Use detector origin when no event vertex exists. | Current fallback is inside `reconstruct_photon_objects` (`photon.py:60-201`) and is flagged by the emitted vertex-use column. | Eligible only as sparse-data fallback with explicit flag. | Pull degradation vs vertex baseline and fallback rate. |
| P.3 | **Cluster-axis fit** | Fit a shower axis from hit positions/timing and use it as direction. | Replacement for centroid-only direction inside `reconstruct_photon_objects` (`photon.py:60-201`). | Eligible if fit uses only hit geometry/timing. | Pull width and small-opening π⁰ separation. |
| P.4 | **Calibrated cluster sum (baseline target)** | Sum calibrated lead-glass plus scintillator cluster energy from P.1. | Replaces the same-key raw energy sum inside `reconstruct_photon_objects` (`photon.py:60-201`). | Production-eligible after plan-18 calibration. | Energy bias/resolution by single-γ energy bin. |
| P.4 | **Lead-glass-only energy** | Use only lead-glass cluster deposits; keep scintillator as diagnostic. | Current photon-like schema carries `leadglass_fraction` in `reconstruct_photon_objects` (`photon.py:60-201`). | Eligible but lower efficiency for scintillator-fed showers. | Bias for no-LG and edge showers; plan-34 selection loss. |
| P.4 | **Regression calibration** | Predict photon energy from cluster sum plus shower-shape features. | Plan 57-style replacement for raw sums. | Eligible only with frozen features and validation provenance. | Bias/resolution improvement vs calibrated sum. |
| P.3/P.4 | **No fragment merge (current)** | Keep one photon-like row per accepted cluster key. | Current compact baseline is `reconstruct_photon_objects` (`photon.py:60-201`). | Production-eligible only if plan-31 cluster membership is truth-blind and duplicate rate is acceptable. | Duplicate photon rows can inflate π⁰ combinatorics. |
| P.3/P.4 | **Geometry/time fragment merge** | Merge nearby neutral clusters by angular, centroid, and timing compatibility. | New truth-blind post-processing after `reconstruct_photon_objects` (`photon.py:60-201`). | Production-eligible with DEC-logged thresholds. | Duplicate rate, π⁰ daughter over-merge rate, closure pulls. |

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

### 6.1 Machine-readable photon closure fixture

Each P.3/P.4 candidate configuration writes one closure-result row per
single-γ energy bin and direction-source category:

| Field | Required content | Review rule |
|---|---|---|
| `photon_method_id` | direction, energy, and merge method bundle | must match §5 candidate choices |
| `dataset_id`, `energy_bin_mev` | `cal_singlegamma_v1` setting | every §6 energy point gets a row |
| `direction_source` | reconstructed vertex or origin fallback | fallback rows are reported separately |
| `n_truth_photons`, `n_reco_photons` | efficiency denominator and numerator | zero denominators fail closure |
| `angular_pull_mean`, `angular_pull_width` | P.3 closure metrics | compared to §6 pass criterion |
| `energy_bias`, `energy_response_interval_68` | P.4 response and bootstrap interval | bias must stay below the §6 bound |
| `fallback_origin_fraction` | fraction using origin fallback | required before direction DEC approval |
| `fragment_duplicate_rate`, `fragment_overmerge_rate` | Wilson-interval rates | over-merge must stay within §6 budget |
| `class_b_drop_hash` | rerun artifact without truth/provenance columns | photon four-vector and merge hashes must match |
| `closure_status` | `pass`, `fail`, or `diagnostic_only` | only `pass` rows may support production choices |

Diagnostic rows may compare legacy energy aliases, but production rows
must tie their method id to plan-31/32 cluster and neutral-score inputs.

### 6.2 Decision-log stubs for photon-object choices

P.3/P.4 choices feed π⁰ mass, visible mass, and event selection, so
they need explicit methodology approval before replacing the
reproduction baseline:

| DEC stub | Decision to freeze | Required evidence before approval |
|---|---|---|
| `DEC-33-DIRECTION-METHOD` | Choose vertex→centroid, origin fallback policy, or cluster-axis fit for production photon direction | §6 angular pull closure plus fallback-rate audit by sample |
| `DEC-33-ENERGY-METHOD` | Choose calibrated cluster sum, lead-glass-only, or regression calibration for production photon energy | §6 energy-response closure and plan-18 calibration provenance |
| `DEC-33-FRAGMENT-MERGE` | Freeze truth-blind fragment-merge thresholds and duplicate policy | duplicate/over-merge rate scan and plan-01 audit proving no truth-label dependence |
| `DEC-33-SCINT-ONLY-PHOTONS` | Freeze `leadglass_fraction = 0` semantics and downstream handling for scintillator-only photon rows | plan-34/37 impact table showing they do not enter Ch 8 π⁰ selection accidentally |

Until approval, alternative direction/energy/merge outputs remain
plan-38 ladder rows; the Ch 10 reproduction keeps the current
baseline semantics.

## 7. Acceptance criteria

- §2, §3 produce photon four-vector with stated semantics.
- §4 truth-blind merging in place.
- §6 closure passes.

## 8. Dependencies

- **18, 24, 30, 31, 32, 38, 40** — inputs.
- *Consumed by:* plan 34 (π⁰ pairing), plan 36 (event variables),
  plan 38 (ladder leaves P.3, P.4).

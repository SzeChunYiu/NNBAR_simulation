---
id: 33_subsystem_photon_object
title: Subsystem — photon object (leaves P.3, P.4)
version: 0.1
status: draft
owner: EM-Object POG
depends_on: [00_README, 18_intercalibration, 24_reconstruction_question_tree, 30_subsystem_vertex, 31_subsystem_calorimeter_clustering, 32_subsystem_shower_shape, 38_truth_substitution_ladder, 40_closure_and_pulls]
outputs:
  - {path: docs/rebuild_plans/33_subsystem_photon_object.md, schema: this file}
  - {path: docs/rebuild_plans/33_subsystem_photon_object_fragment_merge_fixture.md, schema: split fragment-merge fixture}
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

Initial photon-method bundle examples:

| `photon_method_id` | Direction method | Energy method | Merge method | Required upstream ids | Method status |
|---|---|---|---|---|---|
| `legacy_current_repro` | vertex→centroid with origin fallback from current row builder | legacy `total_energy` alias | no fragment merge | `legacy_track_key_repro`, `legacy_hard_cone_v0` | diagnostic |
| `cluster_sum_vertex_v0` | plan-30 vertex→P.1 centroid, origin fallback flagged | calibrated `cluster_sum` | no fragment merge | `topological_seed_v0`, `legacy_hard_cone_v0` or approved P.2 candidate | candidate |
| `cluster_sum_vertex_merge_v0` | plan-30 vertex→merged centroid, origin fallback flagged | calibrated `cluster_sum` | geometry/time fragment merge | approved P.1/P.2 rows plus `DEC-33-FRAGMENT-MERGE` evidence | candidate |

The legacy bundle cannot be promoted because its energy and cluster
membership depend on current reproduction aliases rather than the
truth-blind P.1/P.2 contracts.

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

### 2.4 Physics derivation for P.3

#### Physics derivation

P.3 physically estimates the photon flight direction from the annihilation
vertex to the electromagnetic shower barycentre. The truth-side quantity
is the generated photon momentum unit vector at production, while the
production estimator observes only the reconstructed vertex, the P.1
cluster centroid, detector geometry, and P.2 neutral decision. For a
neutral EM shower in a calorimeter, the shower centroid is a noisy
measurement of the impact point; combining it with the best reconstructed
vertex gives the maximum-information straight-line estimator available
from Class-A inputs \cite{ParticleDataGroup:2024RPP,fabjan2020particle}.

The estimator is the normalized vector from vertex to centroid, with an
explicit origin fallback only when no reconstructed vertex exists. Its
dominant bias is vertex displacement or cluster-centroid bias inherited
from P.1 and plan 30; its variance is set by centroid resolution divided
by path length, plus vertex covariance. Robustness comes from storing the
path length, fallback flag, and source cluster ids so closure can split
the angular-pull distribution by direction source instead of hiding sparse
fallback rows.

#### Logic gaps

| Parameter | Status before production | Closure study / target date |
|---|---|---|
| origin fallback `vertex_x/y/z = 0` | `OPEN:` safe sparse-table fallback, not a physics vertex estimate | Measure fallback angular-pull tails on `cal_singlegamma_v1` and signal-like sparse rows; target 2026-06-20 |
| minimum usable `photon_path_length_cm` | `OPEN:` no lower bound preventing unstable normalization | Scan low path-length rows and require finite angular-pull RMS before accepting fallback/vertex rows; target 2026-06-20 |
| P.1 centroid weighting used by direction | tied to P.1 energy-weighted centroid, but centroid bias is `OPEN:` until P.1 closure passes | Propagate P.1 centroid residuals into P.3 angular-pull width; target 2026-06-30 |
| vertex covariance contribution | `OPEN:` plan 30 covariance not yet propagated into photon-direction uncertainty | Join plan-30 covariance rows and test pull width against plan 40; target 2026-06-30 |
| fallback-origin fraction allowed in thesis rows | `OPEN:` no signed maximum fraction | Require a reviewer-visible fallback fraction and block if angular-pull tails dominate; target 2026-07-05 |

#### Closure test for the derivation

1. Run the selected P.1/P.2 photon-candidate chain on `cal_singlegamma_v1`
   and signal-like rows with generated photon directions hidden from the
   estimator.
2. Compute the reconstructed P.3 unit vector from vertex and centroid,
   then evaluate angular residuals against the generated direction only in
   the closure artifact.
3. Split the residual distribution by `used_reconstructed_vertex`, energy
   bin, path-length bin, and P.1 cluster-quality flag.
4. Require the angular-pull width to match the propagated centroid-plus-
   vertex uncertainty and require the fallback-origin tail to be explicitly
   caveated before any thesis-facing photon direction is promoted.

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

### 3.2 Physics derivation for P.4

#### Physics derivation

P.4 physically estimates the calibrated photon energy carried by an
accepted neutral EM shower. The truth-side quantity is the generated
photon energy at production; the production estimator may use only the
calibrated P.1 lead-glass/scintillator energy components and detector
calibration constants. Calorimeter response theory predicts an energy
resolution of stochastic, noise, and constant terms, so the near-minimal
Class-A estimator is the calibrated cluster-energy sum with explicit
lead-glass fraction and method tags \cite{ParticleDataGroup:2024RPP,fabjan2020particle}.
Detector-specific scale and component response are fixed by plan 18 and
prototype calibration evidence \cite{Dunne2022CalorimeterPrototype}.

#### Logic gaps

| Parameter | Status before production | Closure study / target date |
|---|---|---|
| `energy_method = cluster_sum` calibration constants | `OPEN:` plan-18 constants not frozen in the photon fixture | Run linearity and residual scans on `cal_singlegamma_v1`; target 2026-06-30 |
| `leadglass_fraction = 0` for scintillator-only photons | Reproduction-safe convention; downstream acceptance impact is `OPEN:` | Propagate no-LG rows through plans 34/37 before DEC-33-ENERGY-METHOD; target 2026-06-20 |
| Ch 8 guard `leadglass_fraction >= 0.55` | thesis reproduction threshold, not a general P.4 calibration threshold | Run lead-glass-fraction N-1 and pi0-mass stability study; target 2026-06-25 |
| energy bias `< 1%` and efficiency `>= 0.95` | `OPEN:` acceptance-level thresholds need downstream mass/selection impact | Tie limits to plan-34 pi0 mass width and plan-37 selection stability; target 2026-07-05 |

#### Closure test for the derivation

1. Build P.4 rows from fixed P.1/P.2 fixtures using plan-18 calibration
   constants and no truth/provenance columns in the estimator table.
2. On `cal_singlegamma_v1` energy points, compare reconstructed
   `energy_mev` to hidden generated energy in the evaluator and fit bias,
   resolution, and linearity residuals.
3. Split the report by lead-glass fraction and scintillator-only rows.
4. Repeat after dropping `Track_ID`, `Parent_ID`, `Name`, process, and
   ancestry aliases; energy, method, and pass/fail hashes must match.

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

The full fragment-merge fixture is split into
`docs/rebuild_plans/33_subsystem_photon_object_fragment_merge_fixture.md`
to keep this plan below the line cap. The companion file owns the merge
candidate row schema, truth-blind hash guard, and diagnostic examples used
before any geometry/time merge can feed P.3/P.4 photon rows.


### 4.3 Physics derivation for P.3/P.4

#### Physics derivation

P.3 physically estimates the photon flight direction, defined on the
truth side as the unit vector from the annihilation vertex to the
generated photon momentum direction before detector interactions. P.4
physically estimates the photon energy deposited in the EM calorimeter
system after calibration. For an electromagnetic shower, the calorimeter
energy sum and barycentre are near-minimal sufficient observables once
the event vertex is fixed; shower containment and resolution follow the
standard radiation-length/Moliere-radius description and calorimeter
response model \cite{ParticleDataGroup:2024RPP,fabjan2020particle}.
The HIBEAM/NNBAR prototype establishes that the absolute energy scale and
lead-glass/scintillator response must be calibrated with detector data,
not inferred from truth ancestry \cite{Dunne2022CalorimeterPrototype}.

The target estimator is therefore the vertex-to-centroid unit vector for
P.3 and the calibrated P.1 cluster energy sum for P.4. The origin
fallback is a flagged sparse-data estimator, not an equivalent physics
choice. Fragment merging is allowed only when geometry and timing are
consistent with one shower, because over-merging biases the two-photon
mass spectrum in plan 34. Dominant uncertainties are vertex resolution,
cluster-centroid resolution, energy-scale calibration, calorimeter
resolution, and fragment split/merge bias.

#### Logic gaps

| Parameter | Status before production | Closure study / target date |
|---|---|---|
| origin fallback when no vertex exists | allowed only as a flagged estimator, not a primary physics choice | Measure fallback fraction and angular-pull degradation on `cal_singlegamma_v1`; target 2026-06-20 |
| photon direction normalisation and zero-path handling | `OPEN:` needs a frozen invalid-row policy for coincident vertex/centroid rows | Inject zero/near-zero path fixtures and require explicit invalid flags rather than silent unit-vector defaults; target 2026-06-15 |
| fragment-merge angular, distance, and timing thresholds | `OPEN:` diagnostic `geom_time_merge_diag_v0` thresholds are not production frozen | Scan duplicate rate versus π0 daughter over-merge rate on single-gamma and close-pi0 samples; target 2026-06-25 |
| `leadglass_fraction = 0` for scintillator-only photons and Ch 8 guard `leadglass_fraction >= 0.55` | Thesis guard is reproduced; production semantics need a signed downstream-impact DEC | Propagate scintillator-only and low-lead-glass rows through plans 34/37; target 2026-06-20 |
| closure pass limits: direction pull width `[0.9, 1.2]`, `|mu| < 0.05`, energy bias `< 1%`, photon efficiency `>= 0.95`, over-merge `< 2%` | `OPEN:` analysis-quality thresholds need downstream mass/selection impact evidence | Tie limits to pi0 mass resolution and Ch 10 cut-flow stability; target 2026-07-05 |

#### Closure test for the derivation

1. Build photon rows from fixed P.1/P.2 fixtures and the plan-30 vertex
   fixture using only Class-A cluster, neutral-score, geometry, timing,
   and calibration inputs.
2. On `cal_singlegamma_v1` energy points, compute P.3 angular residuals
   against the truth photon direction and P.4 energy response against the
   generated photon energy only inside the evaluator.
3. Split the report by reconstructed-vertex and origin-fallback rows, and
   quote the fallback fraction before any direction-method DEC can sign.
4. Run the same closure with no-merge and geometry/time merge candidates;
   require duplicate-rate improvement without exceeding the pi0
   over-merge guard.
5. Repeat after dropping `Track_ID`, `Parent_ID`, `Name`, process, and
   ancestry aliases; photon four-vector hashes and merge decisions must
   match exactly.


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

Required closure row-key inventory:

| `dataset_id` | `energy_bin_mev` | `direction_source` | Required row purpose | Acceptance guard |
|---|---:|---|---|---|
| `cal_singlegamma_v1` | 50 | reconstructed vertex | low-energy direction/energy response | §6.1 metrics present; nonzero truth denominator |
| `cal_singlegamma_v1` | 100 | reconstructed vertex | near-threshold photon response | §6.1 metrics present; nonzero truth denominator |
| `cal_singlegamma_v1` | 200 | reconstructed vertex | π⁰-relevant photon response | §6.1 metrics present; nonzero truth denominator |
| `cal_singlegamma_v1` | 500 | reconstructed vertex | mid-energy linearity check | §6.1 metrics present; nonzero truth denominator |
| `cal_singlegamma_v1` | 1000 | reconstructed vertex | high-energy linearity check | §6.1 metrics present; nonzero truth denominator |
| `cal_singlegamma_v1` | all | origin fallback | sparse-vertex fallback audit | fallback fraction and separate angular pulls present |

The inventory defines the minimum closure keys. It is not method
approval until measured metrics, fragment rates, and the Class-B drop
hash are attached for the selected photon method.

Initial photon-closure failure examples:

| `closure_case_id` | Failing pattern | Required status | Review guard |
|---|---|---|---|
| `missing_origin_fallback_rows` | reconstructed-vertex rows exist but origin-fallback category is absent | `fail` | direction DEC cannot hide sparse-vertex behaviour |
| `energy_bias_high_bin` | 1000 MeV row has `|energy_bias| >= 1%` | `fail` | linearity claim must remain per-bin, not averaged over bins |
| `fragment_overmerge_budget` | fragment duplicate rate improves but over-merge rate exceeds §6 | `fail` | merge thresholds cannot trade away π⁰ daughter separation silently |
| `legacy_energy_alias_diag` | legacy `total_energy` alias matches response but lacks calibrated P.1 membership | `diagnostic_only` | cannot support `DEC-33-ENERGY-METHOD` for production |

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

Initial scintillator-only downstream-impact examples:

| `impact_case_id` | Photon row pattern | Required downstream handling | Review guard |
|---|---|---|---|
| `scint_only_no_lg` | `leadglass_edep = 0`, `scintillator_edep > 0`, `leadglass_fraction = 0` | row may contribute to photon-efficiency diagnostics but cannot seed the Ch 8 π⁰ selection | plan-34/37 impact table shows zero accepted Ch 8 candidates from this case |
| `low_lg_fraction_edge` | both components positive but `leadglass_fraction < 0.55` | row remains a valid photon-object row while failing the Ch 8 lead-glass fraction guard | cut-flow audit separates object creation from selection rejection |
| `merged_with_lg_cluster` | scintillator-heavy fragment merges with a lead-glass fragment under an approved threshold | recompute `leadglass_fraction` from merged calibrated components rather than forcing zero | `DEC-33-FRAGMENT-MERGE` and `DEC-33-SCINT-ONLY-PHOTONS` evidence agree on the merged row |
| `legacy_truth_descendant_scint` | current reproduction alias supplies same-key scintillator energy without a target P.1 cluster sum | diagnostic only; cannot approve production P.4 energy or Ch 8 selection behavior | plan-38 ladder labels it non-production until plan-31/32 inputs exist |

Until approval, alternative direction/energy/merge outputs remain
plan-38 ladder rows; the Ch 10 reproduction keeps the current
baseline semantics.

Initial downstream-handoff examples:

| `handoff_case_id` | Photon output pattern | Consumer expectation | Review guard |
|---|---|---|---|
| `photon_fourvector_pass_to_p34` | frozen P.3/P.4 four-vector with stable `source_cluster_ids` | plan 34 may build π⁰ pairs | requires §6 closure pass and Class-B drop hash equality |
| `origin_fallback_diag_to_p36` | rows using origin fallback are explicitly flagged | plan 36 may report separate event-variable diagnostics | cannot be mixed into primary direction closure without category split |
| `fragment_merge_shadow` | merged-photon rows written beside no-merge baseline | plan 34/38 may compare pair multiplicity and over-merge rates | baseline photon ids and source clusters remain reviewable |
| `scint_only_selection_guard` | scintillator-only photons carry `leadglass_fraction = 0` | plan 34/37 must reject them from Ch 8 π⁰ selection | impact table must show zero accidental accepted candidates |

Initial production-promotion checklist:

| `promotion_check_id` | Evidence required | Blocks promotion when missing |
|---|---|---|
| `p33_fourvector_contract_present` | stable photon id, source clusters, direction method, and energy method | plan 34 cannot recompute pair kinematics reproducibly |
| `p33_all_energy_bins_pass` | closure rows for every required energy bin and direction-source category | photon response is not bounded across the calibration range |
| `p33_fragment_policy_stable` | duplicate/over-merge metrics and Class-B drop hash for fragment handling | π⁰ daughter separation can change under hidden provenance |
| `p33_scint_only_guard_audited` | impact rows for scintillator-only and low lead-glass-fraction photons | Ch 8 selection may accept unsupported photon rows |

Production P.3/P.4 promotion requires all four checks plus signed DEC
ids for direction, energy, and merge policy. Missing checks keep the
method as a plan-38 diagnostic rather than a plan-34 input.

Initial evidence-bundle examples:

| `evidence_bundle_id` | Included rows | Reviewer action |
|---|---|---|
| `p33_vertex_centroid_candidate_v0` | method bundle, all energy-bin closure rows, fallback audit, Class-B hash | candidate for plan-34 handoff if closure and DEC checks pass |
| `p33_origin_fallback_diag_v0` | origin-fallback category rows and angular-pull summary | keep separate from primary direction closure; diagnose sparse vertices |
| `p33_fragment_merge_shadow_v0` | duplicate/over-merge scans plus no-merge baseline ids | allow plan-38 comparison but block production without merge DEC |
| `p33_scint_only_blocker_v0` | scint-only impact table and Ch 8 guard audit | block plan-34 acceptance if any unsupported row seeds π⁰ selection |

Evidence bundles preserve the source-cluster, direction, and energy
method context that plan 34 needs to reproduce pair kinematics.

Initial reviewer audit cases:

| `audit_case_id` | Reviewer question | Required evidence before accept | Reject condition |
|---|---|---|---|
| `p33_fourvector_audit` | Can every photon four-vector be traced to source clusters and methods? | photon fixture row, direction method, energy method, and source-cluster ids | row has energy/direction but no stable photon id or source list |
| `p33_fallback_audit` | Are origin-fallback photons separated from vertex-based rows? | fallback flag, category closure row, and angular-pull summary | fallback rows are mixed into primary closure without a category |
| `p33_fragment_audit` | Does merging improve duplicates without hiding daughter loss? | no-merge baseline, merge scan, duplicate rate, and over-merge metric | only post-merge efficiency is shown |
| `p33_scint_guard_audit` | Are scintillator-only rows blocked from unsupported π⁰ use? | lead-glass-fraction guard and Ch 8 impact table | any unsupported row can seed a production π⁰ candidate |

## 7. Acceptance criteria

- §2, §3 produce photon four-vector with stated semantics.
- §4 truth-blind merging in place.
- §6 closure passes.
- Promotion checks prove four-vector provenance, energy-bin/category
  closure, fragment policy stability, and scintillator-only guard impact
  before plan 34 consumes photon rows.
- Evidence bundles keep fallback, fragment-merge, and scintillator-only
  diagnostics separate from the production photon-object handoff.

## 8. Dependencies

- **18, 24, 30, 31, 32, 38, 40** — inputs.
- *Consumed by:* plan 34 (π⁰ pairing), plan 36 (event variables),
  plan 38 (ladder leaves P.3, P.4).

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
last_updated: 2026-05-10
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
  `reconstruct_photon_objects` (`photon.py:60-201`).
  The threshold comes from the current `ReconstructionConfig` field
  `charged_cluster_match_angle_deg = 8.0`; the verifier transcript in
  §1.5 records the class and field grep evidence. The same function also
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

### 1.2 Sentinel and validity contract

P.2 outputs must be numerically safe for table joins and ML feature
exports while still making invalid geometry explicit:

| Condition | Required output |
|---|---|
| valid cluster axis and positive energy | compute all §1.1 features; `shape_features_valid = true` |
| zero or non-finite `Σ E_i` | set spread/depth/timing features to `0.0`; `neutral_score = 0.0`; `passes_neutral_discriminant = false`; `shape_features_valid = false`; `shape_invalid_reason = zero_energy` |
| no valid axis or centroid | same finite sentinels; `shape_invalid_reason = invalid_axis` |
| no reconstructed track candidate | `nearest_track_distance_cm = 1.0e9` finite sentinel; `nearest_track_angle_deg = 180.0`; `shape_invalid_reason` remains empty if the shower-shape features are otherwise valid |

Any row with `shape_features_valid = false` is excluded from training
labels for BDT/NN candidates but remains in efficiency denominators.

### 1.3 Machine-readable P.2 discriminant fixture

The P.2 fixture stores one row per P.1 cluster and makes the neutral
decision reproducible without looking at truth labels:

| Field | Required content | Review rule |
|---|---|---|
| `event_id`, `cluster_id`, `hit_membership_key` | join keys from plan 31 | must match the consumed P.1 fixture row |
| `shape_feature_method_id` | formula/config version for §1.1 features | frozen before model training or threshold scans |
| `lateral_rms_cm`, `longitudinal_depth_cm`, `longitudinal_rms_cm` | finite shower-shape values | sentinel values allowed only when `shape_features_valid = false` |
| `max_cell_fraction`, `cluster_time_rms_ns` | finite scalar features | ranges checked by closure histograms |
| `nearest_track_distance_cm`, `nearest_track_angle_deg` | Class-A reconstructed-track match features | no source-track or truth-charge key may enter |
| `neutral_score` | calibrated score or legacy 0/1 baseline | method-specific, never a reused uncalibrated probability |
| `passes_neutral_discriminant` | production boolean | false whenever feature validity fails |
| `shape_features_valid`, `shape_invalid_reason` | validity audit fields | required for sparse and zero-energy rows |

Fixture review recomputes the hard-cone legacy row and any selected
shower-shape features from the P.1 cluster and reconstructed-track
inputs. Dropping `Name`, `Track_ID`, `Parent_ID`, and ancestry aliases
must leave production features and pass/fail unchanged.

Initial feature-contract examples:

| `feature_contract_id` | Feature set | Allowed candidate types | Required audit | Promotion rule |
|---|---|---|---|---|
| `p2_legacy_angle_only_v0` | `nearest_track_angle_deg` plus hard-cone threshold | `legacy_rule` | Class-B drop hash for charged-match columns | reproduction baseline only |
| `p2_shape_track_features_v0` | all §1.1 shower-shape features plus nearest-track distance/angle | `rectangular`, `bdt`, `nn` | feature recomputation from P.1/P.2 inputs and provenance-drop hash | eligible after `DEC-32-FEATURE-CONTRACT` |
| `p2_shape_no_timing_ablation_v0` | same as full set but excludes `cluster_time_rms_ns` | `rectangular`, `bdt` | paired ablation row against the full feature set | diagnostic unless timing uncertainty remains unbounded |
| `p2_truth_label_oracle_blocked` | generated particle name, parent id, or source ancestry | none in production | blocked by truth-use boundary | validation labels only; never an inference contract |

Feature contracts are immutable once referenced by a candidate row. A
new contract id is required for any feature addition, removal, sentinel
change, or Class-A audit-scope change.

### 1.4 Current-to-target neutral-decision field map

The current compact source does not emit `neutral_score` or
`passes_neutral_discriminant`; it emits the charged-match diagnostic
columns `has_tpc_track`, `matched_tpc_track_id`, and
`charged_match_angle_deg` from `reconstruct_photon_objects`
(`photon.py:60-201`). The reproduction bridge may derive a hard-cone
P.2 baseline as `passes_neutral_discriminant = not has_tpc_track` and
`neutral_score = 1.0` or `0.0`, but only with
`discriminant_method = legacy_hard_cone`. Any BDT/NN or shower-shape
score must be written under a different method id and may not reuse the
legacy fields as if they were calibrated probabilities.

### 1.5 A+ citation audit for current neutral baseline

Current-source claims in §1 were re-checked against the L3 worktree
before this plan was committed:

| Cited contract | Verifier evidence | Status |
|---|---|---|
| hard-cone row builder and charged-match fields | `def reconstruct_photon_objects` resolves at `photon.py:60`, inside the cited `photon.py:60-201` range. | keep citation |
| charged-match threshold default | `grep -nE '^(def|class) ReconstructionConfig' nnbar_reconstruction/reconstruction.py` resolves the class in the current L3 source, and `grep -n 'charged_cluster_match_angle_deg'` resolves the 8.0 field in that class body. | keep verified symbol, no stale line citation |

Plan 32 does not specify a runtime CLI command, and it does not cite the
removed legacy split-study files. If the P.2 scorer later gains a CLI
entry, the command must pass the L3 `--help` verifier before it appears
in this plan.

### 1.6 Physics derivation for P.2

#### Physics derivation

P.2 physically estimates whether a P.1 cluster is compatible with a
neutral electromagnetic shower rather than a charged particle or charged
track-associated deposit. The truth-side quantity is the initiating
particle charge and electromagnetic/hadronic shower character, but the
production estimator may observe only the deposited-energy moments,
cluster timing, and reconstructed track geometry. EM shower development
has compact lateral profiles set by radiation length and Moliere radius,
and longitudinal moments plus maximum-cell fraction capture leakage and
shower-start differences \cite{ParticleDataGroup:2024RPP,fabjan2020particle}.
The nearest-track distance/angle is a Class-A proxy for charged-particle
compatibility; the HIBEAM/NNBAR calorimeter prototype motivates
calibrating those observables with detector-specific response data
\cite{Dunne2022CalorimeterPrototype}.

The selected estimator is therefore a calibrated score over energy-weighted
shape moments and reconstructed-track matching. Its dominant biases are
upstream cluster splitting/merging from P.1 and charged-track inefficiency;
its variance is driven by calorimeter energy resolution, finite cell
granularity, and limited labelled calibration samples. Robustness is
checked by feature-contract immutability, component-wise fake-rate limits,
and a Class-B drop hash proving no truth/provenance feature affects the
score.

#### Logic gaps

| Parameter | Status before production | Closure study / target date |
|---|---|---|
| `charged_cluster_match_angle_deg = 8.0` | `OPEN:` legacy hard-cone reproduction value, not derived from track/angular resolution | Scan cone angle on `cal_singlegamma_v1`, `cal_singleelectron_v1`, and charged-pion clusters; minimise fake rate at fixed neutral efficiency; target 2026-06-20 |
| finite sentinels `nearest_track_distance_cm = 1.0e9`, `nearest_track_angle_deg = 180.0`, invalid score `0.0` | `OPEN:` safe-table constants, not physics thresholds | Verify no candidate threshold treats sentinel rows as high-quality neutral clusters; target 2026-06-15 |
| rectangular shower-shape thresholds | `OPEN:` no frozen lateral/depth/max-cell/timing cuts yet | N-1 scan of each §1.1 feature; require stable ROC and feature-contract DEC; target 2026-06-30 |
| learned-score threshold `neutral_score_threshold` | `OPEN:` candidate rows leave threshold null | Bootstrap ROC scan; choose first point satisfying neutral efficiency and component fake-rate guards; target 2026-06-30 |
| pass limits AUC `>= 0.95`, neutral efficiency `>= 0.90`, fake rate `<= 0.05` | `OPEN:` analysis-quality guard needs downstream photon-yield impact study | Propagate threshold choices through plans 33/37 and require no Ch 10 reproduction regression; target 2026-07-05 |

#### Closure test for the derivation

1. Build P.2 feature rows from a fixed P.1 cluster fixture using only
   Class-A cluster, hit, timing, and reconstructed-track columns.
2. Label positives with `cal_singlegamma_v1` and negatives with
   `cal_singleelectron_v1` plus `sig_foil_v3:charged_pion_clusters`,
   keeping labels outside the inference feature table.
3. Fit or scan the candidate score, then report AUC, neutral efficiency,
   and component fake-rate intervals for every labelled component.
4. Repeat after dropping `Name`, `Track_ID`, `Parent_ID`, and ancestry
   aliases; the feature hash, score hash, and pass/fail hash must match.
5. Promote only if the chosen threshold satisfies §3 component guards and
   the downstream plan-33/37 shadow study shows no reproduction regression.

## 2. Charged/neutral discriminant candidates

| Candidate | P.2 decision rule | Current/source citation | Class-A status | Comparison metric | Failure mode to inspect |
|---|---|---|---|---|---|
| **Hard cone (current)** | Mark charged when vertex-to-centroid direction lies within `charged_cluster_match_angle_deg = 8.0°` of a TPC-track direction. | Charged-match candidates, threshold, and output flag are verified once in §1.5; implementation is `reconstruct_photon_objects` (`photon.py:60-201`). | Partly eligible: geometric cone is Class A if upstream track inputs are reconstructed objects; current row still carries provenance columns. | ROC point, charged contamination, neutral efficiency. | Track-key/provenance coupling can hide conversion/electron backgrounds. |
| **Rectangular shower-shape cuts** | Apply tuned cuts on lateral RMS, depth, max-cell fraction, timing RMS, and track distance. | Replaces the single angle threshold in `reconstruct_photon_objects` (`photon.py:60-201`). | Production-eligible if thresholds are DEC-logged. | AUC/efficiency and N-1 stability for each variable. | Sharp thresholds may be unstable across clusterers. |
| **BDT discriminant** | Train a bounded tree model on the §1 observables and track-distance variables. | Plan 57-governed replacement for the current hard cone. | Production-eligible after frozen feature contract and training provenance. | ROC AUC, calibration curve, feature-ablated stability. | Overtraining to single-γ calibration topology. |
| **Neural discriminant** | Train a small NN on the same tabular features; threshold `neutral_score`. | Plan 57-governed alternative to BDT. | Production-eligible only if deterministic export and audit artifacts land. | Same as BDT plus seed/export reproducibility. | Harder to defend than BDT without clear gains. |
| **Truth-labelled diagnostic** | Join validation-only gamma/e± labels after production scoring. | Current production rows expose diagnostic `truth_name` in `reconstruct_photon_objects` (`photon.py:60-201`) for validation joins only. | Not production-eligible; validation labels only. | Upper-bound/reference ROC. | Inflates performance and fails plan 01 if used in decisions. |

### 2.1 Machine-readable discriminator-candidate fixture

Every non-diagnostic P.2 candidate writes an inference-bundle row before
its score can enter photon-object production:

| Field | Required content | Review rule |
|---|---|---|
| `discriminant_method_id` | hard-cone, rectangular, BDT, or NN method key | matches §1.3 fixture rows |
| `candidate_type` | `legacy_rule`, `rectangular`, `bdt`, or `nn` | truth-labelled diagnostics are excluded |
| `feature_contract_id` | frozen Class-A feature list | must match §1 observables and sentinel rules |
| `training_dataset_ids` | sample ids used for labelled training, or null for rules | labels are training/evaluator only |
| `validation_split_id` | held-out split or fixed-threshold validation id | required before threshold freeze |
| `model_artifact_id` | exported model or rule artifact | null only for legacy hard-cone baseline |
| `threshold_id`, `threshold_value` | operating-point key and value | required for production `passes_neutral_discriminant` |
| `calibration_artifact_id` | score calibration row or null with reason | required for probabilistic score claims |
| `class_a_audit_hash` | feature table hash after dropping Class B columns | must match the inference input hash |
| `candidate_status` | `diagnostic`, `candidate`, `frozen`, or `blocked` | only frozen rows may replace the baseline |

The bundle is rejected if an inference feature is absent from §1, if a
truth/provenance column changes the score, or if the threshold cannot be
replayed from the saved artifact.

Initial discriminator-candidate examples:

| `discriminant_method_id` | `candidate_type` | `feature_contract_id` | `training_dataset_ids` | `validation_split_id` | `model_artifact_id` | `threshold_id`, `threshold_value` | `calibration_artifact_id` | `class_a_audit_hash` | `candidate_status` |
|---|---|---|---|---|---|---|---|---|---|
| `legacy_hard_cone_v0` | `legacy_rule` | `p2_legacy_angle_only_v0` | null | `fixed_threshold_repro` | null | `charged_cluster_match_angle_deg`, 8.0 | null | required | `diagnostic` |
| `rectangular_shape_v0` | `rectangular` | `p2_shape_track_features_v0` | [`cal_singlegamma_v1`, `cal_singleelectron_v1`, `sig_foil_v3`] | `p2_stratified_split_v0` | `rectangular_thresholds_v0` | `neutral_score_threshold`, null | null | required | `candidate` |
| `bdt_shape_v0` | `bdt` | `p2_shape_track_features_v0` | [`cal_singlegamma_v1`, `cal_singleelectron_v1`, `sig_foil_v3`] | `p2_stratified_split_v0` | `bdt_shape_v0` | `neutral_score_threshold`, null | `bdt_calibration_v0` | required | `candidate` |

The legacy hard-cone row is diagnostic until the Class-A audit proves
its charged-track inputs are truth-blind.

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

### 3.1 Machine-readable discriminator closure fixture

Each candidate discriminator writes one closure-result record before it
can be compared in plan 38 or frozen by DEC:

| Field | Required content | Review rule |
|---|---|---|
| `discriminant_method_id` | hard-cone, rectangular, BDT, NN, or diagnostic method id | must match §2 candidate row |
| `dataset_id` | `cal_singlegamma_v1`, `cal_singleelectron_v1`, or `sig_foil_v3` component | every positive and negative component gets a row |
| `feature_contract_id` | frozen §1 feature set | no unlisted feature may enter the score |
| `threshold_id` | frozen operating-point key | required for `passes_neutral_discriminant` |
| `roc_auc`, `roc_auc_interval_68` | AUC and bootstrap interval | null only for fixed-threshold legacy rows with documented reason |
| `neutral_efficiency`, `charged_fake_rate` | operating-point rates with Wilson intervals | compared to §3 pass criteria |
| `class_b_drop_hash` | rerun artifact after dropping Class B columns | must match the production-feature/pass-fail hash |
| `closure_status` | `pass`, `fail`, or `diagnostic_only` | only `pass` rows can support production selection |

Rows labelled `diagnostic_only` may inform plan 38, but they cannot
promote a discriminator or feed photon-object production rows.

Required closure row-key inventory:

| `dataset_id` | Label role | Required row purpose | Acceptance guard |
|---|---|---|---|
| `cal_singlegamma_v1` | positive neutral shower | neutral efficiency and score-shape reference | efficiency interval, AUC input, and Class-B drop hash present |
| `cal_singleelectron_v1` | charged/electron negative | electron-like charged fake-rate check | fake-rate interval present and `charged_fake_rate <= 0.05` for pass rows |
| `sig_foil_v3:charged_pion_clusters` | charged-pion-associated negative | pion/MIP fake-rate check in signal topology | fake-rate interval present and `charged_fake_rate <= 0.05` for pass rows |
| `sig_foil_v3:neutral_candidate_clusters` | in-sample neutral diagnostic | topology-matched neutral stability check | diagnostic-only unless label provenance is separated from inference |

The inventory names the minimum closure components. It does not promote
a discriminator until measured §3.1 metrics and the Class-B drop hash are
attached for every required positive and negative component.

Initial discriminator-closure failure examples:

| `closure_case_id` | Failing pattern | Required status | Review guard |
|---|---|---|---|
| `missing_negative_component` | no closure row for `cal_singleelectron_v1` or charged-pion clusters | `fail` | AUC on photons alone cannot approve a neutral discriminator |
| `fake_rate_component_fail` | aggregate fake rate passes but one negative component exceeds `0.05` | `fail` | component-wise guard is stronger than pooled ROC |
| `class_b_score_drift` | score or pass/fail hash changes after dropping provenance columns | `fail` | blocks production even when ROC metrics pass |
| `legacy_fixed_point_only` | hard-cone row has no AUC because it is a single operating point | `diagnostic_only` unless intervals and Class-B hash are present | cannot be used as a promoted learned threshold |

### 3.2 Decision-log stubs for the P.2 discriminator

Changing the charged/neutral discriminator changes photon-object
eligibility downstream. Freeze these choices through plan 05 before
they affect production photon rows:

| DEC stub | Decision to freeze | Required evidence before approval |
|---|---|---|
| `DEC-32-DISCRIMINANT-CHOICE` | Select hard cone, rectangular cuts, BDT, or NN as the production P.2 discriminator | plan-38 candidate comparison plus §3 ROC closure on every labelled component |
| `DEC-32-FEATURE-CONTRACT` | Freeze the shower-shape and nearest-track feature list, including sentinel handling | plan-57 feature contract and Class-A audit proving no truth/provenance feature enters inference |
| `DEC-32-NEUTRAL-THRESHOLD` | Freeze `neutral_score` / cut threshold and operating point | bootstrap AUC, neutral efficiency, charged fake rate, and N-1 stability evidence |

Initial neutral-threshold scan examples:

| `threshold_case_id` | Operating-point pattern | Required closure evidence | Promotion guard |
|---|---|---|---|
| `hard_cone_current_point` | reproduce the current cone decision as a fixed single ROC point | Wilson intervals for neutral efficiency and charged fake rate on every §3.1 component | diagnostic unless Class-B drop hash is stable and fake rate meets §3 |
| `rectangular_loose_neutral` | loosen shower-shape cuts to maximise neutral efficiency | charged fake-rate rise and N-1 stability rows | cannot promote if any charged component exceeds the §3 fake-rate cap |
| `rectangular_balanced_v0` | choose threshold at the first point satisfying both efficiency and fake-rate bounds | bootstrap AUC plus fixed-threshold intervals | candidate only after `DEC-32-FEATURE-CONTRACT` approval |
| `bdt_high_purity_v0` | raise score threshold for a low-fake-rate operating point | neutral-efficiency loss and downstream photon-yield impact | cannot replace Ch 10 reproduction without plan-37 cut-flow impact rows |

Until approval, non-current discriminants may be trained and scored
only as ladder alternatives; the current hard-cone baseline remains
the reproduction path.

Initial downstream-handoff examples:

| `handoff_case_id` | Discriminator output pattern | Consumer expectation | Review guard |
|---|---|---|---|
| `neutral_score_pass_to_p33` | frozen `neutral_score` and `passes_neutral_discriminant` columns | plan 33 may build photon objects from accepted neutral clusters | requires §3 closure pass and stable Class-B drop hash |
| `hard_cone_repro_diag` | current hard-cone decision emitted as reproduction baseline | plan 33 may keep it as a diagnostic ladder input | cannot be labelled as a learned or retuned discriminator |
| `feature_contract_blocked` | candidate uses unregistered or provenance-bearing features | no downstream production consumer | plan 57/DEC-32 evidence must repair the feature list first |
| `threshold_shadow_panel` | alternative thresholds written beside baseline columns | plan 37 impact studies may compare photon-yield changes | original baseline columns must remain unchanged |

Initial production-promotion checklist:

| `promotion_check_id` | Evidence required | Blocks promotion when missing |
|---|---|---|
| `p32_feature_contract_frozen` | registered feature list, sentinels, and threshold id | score cannot be reproduced by plan 33/37 reviewers |
| `p32_all_label_components_pass` | photon, electron, and charged-pion closure rows with intervals | neutral efficiency or fake rate is only partially bounded |
| `p32_truth_drop_stable` | feature, score, and pass/fail hashes match after Class-B drop | discriminator may be using provenance leakage |
| `p32_downstream_shadow_kept` | baseline and alternative threshold columns remain separate | Ch 10 reproduction could be overwritten by a retune |

A P.2 discriminator is production-eligible only when all checks point to
measured fixture rows and signed DEC ids. Otherwise the row remains a
ladder diagnostic even if one aggregate ROC number looks acceptable.

Initial evidence-bundle examples:

| `evidence_bundle_id` | Included rows | Reviewer action |
|---|---|---|
| `p32_hard_cone_repro_bundle_v0` | hard-cone fixed-point row, component fake-rate intervals, Class-B hash | keep as Ch 10 reproduction context unless promotion checks also pass |
| `p32_rectangular_candidate_bundle_v0` | feature contract, AUC rows, threshold id, and all label-component closures | candidate for plan-33 handoff review after DEC approval |
| `p32_missing_negative_bundle_v0` | photon-positive closure without electron or charged-pion rows | reject because fake-rate coverage is incomplete |
| `p32_shadow_threshold_bundle_v0` | baseline and alternative threshold result rows with separate config ids | permit plan-37 impact study but not baseline overwrite |

Evidence bundles let the reviewer separate reproduction rows, production
candidates, and blocked feature contracts before plan 33 consumes a
neutral-discriminator output.

Initial reviewer audit cases:

| `audit_case_id` | Reviewer question | Required evidence before accept | Reject condition |
|---|---|---|---|
| `p32_feature_contract_audit` | Are all scoring inputs registered, finite, and provenance-safe? | feature fixture, sentinel policy, and Class-B drop hash | any score input is unregistered or truth/provenance bearing |
| `p32_label_coverage_audit` | Do closure rows cover photon efficiency and charged fake rates? | photon, electron, and charged-pion interval rows | only positive-photon efficiency is reported |
| `p32_threshold_audit` | Is the pass/fail threshold frozen independently from shadows? | baseline threshold id, shadow ids, and DEC status | a retuned threshold overwrites the baseline column |
| `p32_handoff_audit` | Can plan 33 reproduce the neutral decision? | bundle id, score column, pass column, and feature schema version | handoff names only an aggregate ROC score |

## 4. Acceptance criteria

- §1 observables produced for every cluster.
- §2 classifier replaces fixed-cone with paired ladder benchmark.
- §3 ROC closure passes.
- Promotion checklist rows prove the feature contract, label-component
  closures, Class-B drop hash, and downstream shadow columns before plan
  33 consumes a discriminator output.
- Evidence bundles mark reproduction, candidate, shadow-threshold, and
  blocked contracts distinctly so a retune cannot overwrite the Ch 10
  baseline.

## 5. Dependencies

- **24, 31, 38, 57** — inputs.
- *Consumed by:* plan 33 (photon object).

---
id: 31_subsystem_calorimeter_clustering
title: Subsystem — calorimeter clustering (leaf P.1)
version: 0.1
status: draft
owner: EM-Object POG
depends_on: [00_README, 24_reconstruction_question_tree, 38_truth_substitution_ladder]
outputs:
  - {path: docs/rebuild_plans/31_subsystem_calorimeter_clustering.md, schema: this file}
acceptance:
  - {test: clustering uses Class A only, method: plan 01 audit, pass_when: zero Class B reads}
  - {test: clustering reproduces gamma-shower energy on cal_singlegamma_v1, method: closure plot, pass_when: ΔE/E < 5%}
  - {test: alternative clusterers benchmarked on ladder leaf P.1, method: plan 38, pass_when: matrix entry}
risks:
  - {risk: replacing the Track_ID-keyed grouping loses showers whose calorimeter deposits are sparse or disconnected, mitigation: §3 topological clustering captures contiguous deposits}
estimated_effort: L
last_updated: 2026-05-10
---

# Subsystem — calorimeter clustering

*Charter.* Owns leaf P.1. Groups lead-glass and scintillator hits
into clusters. The current code uses the simulation `Track_ID` key as
the grouping surface and emits diagnostic truth labels, so the
replacement is Class A topological / particle-flow-style clustering.

## 1. Current implementation (provisional Track_ID clustering)

The current L3 reconstruction code has no separate source-resolver
helper and no separate photon-row-builder helper. Plan 31 therefore
treats `reconstruct_photon_objects` (`photon.py:60-201`) as the current clustering surface. It
groups lead-glass rows by `(Event_ID, Track_ID)`, attaches same-key
scintillator energy, computes an energy-weighted centroid with
`_weighted_centroid` (`photon.py:28-48`), and emits one
photon-like row per surviving group.

This is still only a reproduction baseline for leaf P.1. `Track_ID`
and the diagnostic `truth_name` output can carry simulation-truth
provenance, so the production replacement must define membership from
Class-A calorimeter geometry, energy, and timing instead.

## 2. Leaf P.1 input/output schema

Leaf P.1: calorimeter hits → neutral-shower cluster candidates

- **Inputs (production, Class A only):** LeadGlass and Scintillator
  parquet rows with `Event_ID`, `eDep`, `x`, `y`, `z`, and optional
  `t` from plan 09 §§9–10. Geometry side-cars from plan 09 §13 may
  be used to define nearest-neighbour topology, cell adjacency, and
  detector-component labels.
- **Column / unit contract:** plan 09 records calorimeter `x`, `y`,
  and `z` in **cm** and `eDep` in MeV for both LeadGlass and
  Scintillator rows. P.1 outputs therefore use cm for centroids and
  MeV for energies; if legacy column names omit `_cm` / `_mev`
  suffixes, plan 09 §14 must state those units explicitly.
- **Current implementation evidence:** the compact current source
  combines clustering and photon-row emission inside
  `reconstruct_photon_objects` (`photon.py:60-201`).
  The emitted photon-like table schema in that function currently
  doubles as the cluster surface. The helper `_weighted_centroid` (`photon.py:28-48`) supplies the energy-weighted position.
- **Decision rule (target):** seed clusters from local calorimeter
  energy maxima, grow by detector adjacency / spatial proximity, and
  split or merge clusters using only hit energy, hit position, timing,
  and calibrated detector geometry. No `Track_ID`, `Parent_ID`,
  `Name`, `Proc` / process alias, or `Interaction` ancestry may
  decide cluster membership.
- **Outputs:** one row per cluster with `event_id`, `cluster_id`,
  `detectors_present`, `n_leadglass_hits`, `n_scintillator_hits`,
  `leadglass_edep`, `scintillator_edep`, `total_edep`,
  energy-weighted `cluster_x`, `cluster_y`, `cluster_z`, optional
  `cluster_time_ns`, `seed_hit_id`, topology quality flags, and a
  reproducible hit-membership key. Diagnostic truth labels may be
  joined only in validation artifacts, not in this production table.
- **Downstream consumers:** plan 32 reads the cluster row and hit
  membership for shower-shape observables; plan 33 converts accepted
  neutral clusters into photon four-vectors.
- **Truth-use boundary:** the current ancestry fields are retained
  only for closure labels and reproduction-ledger comparison; the
  production P.1 output is invalid if cluster membership changes when
  Class B columns are removed.

### 2.1 Hit-membership key contract

Every P.1 candidate must carry enough information for plan 32/33 and
plan 47 to reproduce cluster membership exactly:

| Output field | Meaning |
|---|---|
| `cluster_id` | dense per-event integer assigned after deterministic sorting by seed energy, then centroid coordinates |
| `hit_membership_key` | stable hash of the sorted member-hit keys, detector labels, and reconstruction config id |
| `member_hit_keys` | validation/debug artifact listing the sorted member-hit keys; may be stored out-of-row if the table format requires it |
| `membership_config_id` | clusterer name plus frozen threshold/version id from the relevant DEC |

A member-hit key is built from Class-A table position only: detector
kind, run id when available, event id, and input-row ordinal or a
future plan-09 hit id. It must not include `Track_ID`, `Parent_ID`,
`Name`, or process/ancestry aliases.

### 2.2 Machine-readable P.1 cluster fixture

The P.1 output fixture stores one row per cluster plus a separate
membership sidecar when member-hit lists are too large for a flat table:

| Field | Required content | Review rule |
|---|---|---|
| `event_id` | source event id | must join to plan-09 calorimeter rows |
| `cluster_id` | deterministic dense id from §2.1 | no dependence on `Track_ID` or truth ancestry |
| `clusterer_method` | selected candidate id from §3 | `legacy_track_key` only for reproduction baseline rows |
| `membership_config_id` | frozen threshold/config tag | must match the DEC that authorised the clusterer |
| `hit_membership_key` | stable hash from §2.1 | recomputed by plan-47 audit |
| `detectors_present` | lead-glass/scintillator bitset | derived from member detector labels |
| `leadglass_edep`, `scintillator_edep`, `total_edep` | MeV energy sums | non-negative and additive within rounding tolerance |
| `cluster_x`, `cluster_y`, `cluster_z` | energy-weighted centroid in cm | finite; sparse invalid cases get explicit quality flags |
| `cluster_quality_flags` | list of split/merge/sparse flags | empty list means no known caveat, not unreviewed |

Fixture review recomputes the energy sums, centroid, and membership hash
from the member-hit sidecar. A row whose fixture changes after dropping
Class B columns is rejected before plan 32 or 33 can consume it.

Initial cluster-quality flag examples:

| `cluster_quality_flag` | Trigger condition | Required review action | Downstream rule |
|---|---|---|---|
| `nominal_single_shower` | one local maximum, connected membership, finite centroid | closure row may count as nominal response | eligible for P.2/P.3 after Class-B hash passes |
| `sparse_disconnected_hits` | low-energy islands are accepted only through a documented adjacency bridge | inspect split/merge rates by energy bin | keep flag through plan 32 feature rows |
| `split_local_maxima` | one seed region is split into two candidate clusters | verify both child hit-membership keys and energy conservation | plan 33 may build separate photons only after closure |
| `merged_touching_cells` | adjacent candidates are merged by the configured merge rule | record pre/post membership hashes in closure sidecar | plan 34 over-merge guard must see the flag |
| `class_b_membership_changed` | dropping ancestry/provenance columns changes membership | fail the Class-A audit | blocked from all downstream production rows |

Quality flags are additive. An empty list is allowed only when the row
has passed the membership-hash audit and no split/merge/sparse condition
was observed.

### 2.3 Current-to-target cluster identifier map

The current compact source emits `object_id` and `source_track_id` from
`reconstruct_photon_objects` (`photon.py:60-201`), not a production
`cluster_id` or hit-membership key. A rebuild bridge may expose the
current `object_id` only as `legacy_cluster_object_id` with
`clusterer_method = legacy_track_key`; `source_track_id` remains
diagnostic provenance and must never become the P.1 `cluster_id`. The
production `cluster_id`, `hit_membership_key`, and
`membership_config_id` must be assigned after Class-A clustering so
plan 32/33 can join by truth-blind membership rather than by simulated
track ancestry.

### 2.4 A+ citation audit for current cluster baseline

Current-source claims in §1-§3 were re-checked against the L3 worktree
before this plan was committed:

| Cited contract | Verifier evidence | Status |
|---|---|---|
| compact current cluster/photon row surface | `def reconstruct_photon_objects` resolves at `photon.py:60`, inside the cited `photon.py:60-201` range. | keep citation |
| energy-weighted centroid helper | `def _weighted_centroid` resolves at `photon.py:28`, inside the cited `photon.py:28-48` range. | keep citation |

Plan 31 does not specify a runtime CLI command, and it does not cite the
removed legacy split-study files. Any future cluster-study CLI row must
pass the L3 `--help` verifier before this plan cites it.

### 2.5 Physics derivation for P.1

#### Physics derivation

P.1 physically estimates the visible neutral-shower energy deposit and
its barycentre in the lead-glass/scintillator calorimeter system. The
truth-side quantity is the set of ionisation/Cherenkov energy deposits
generated by one neutral electromagnetic shower before any reconstruction
grouping is applied. Electromagnetic shower theory predicts compact
lateral containment governed by radiation length, Moliere radius, and
sampling/readout fluctuations, so a seed-plus-neighbour clusterer is the
near-minimal Class-A estimator when the available observables are cell
position, deposited energy, detector adjacency, and optional time
\cite{ParticleDataGroup:2024RPP,fabjan2020particle}. The HIBEAM/NNBAR
prototype establishes that lead-glass calorimeter response and geometry
must be calibrated empirically rather than inferred from truth labels
\cite{Dunne2022CalorimeterPrototype}.

The estimator is therefore: find local energy maxima, grow through
geometry neighbours whose energy/time compatibility is consistent with a
single shower, and compute the energy-weighted centroid. Its dominant
statistical character is a bias from leakage/split-merge decisions plus
a variance term from calorimeter energy resolution. Robustness is driven
by deterministic membership keys and by rejecting any configuration whose
membership changes when Class-B columns are dropped.

The Wave-6 clustering derivation ledger is:

| P.1 sub-leaf | Truth-side quantity | Estimator rationale | Dominant uncertainty | Closure assertion |
|---|---|---|---|---|
| `cluster.seed` | location of a neutral-shower local energy maximum | a seed threshold suppresses noise while preserving EM shower maxima | threshold bias and low-energy fake clusters | seed scan reports response bias and fake-cluster intervals |
| `cluster.grow` | set of calorimeter cells belonging to the same shower | geometry adjacency and energy compatibility approximate lateral EM containment using Class-A inputs | neighbour radius/window choice and leakage | membership hash is invariant after Class-B columns are dropped |
| `cluster.split_merge` | separation of nearby showers versus one broad shower | local maxima and overlap rules control π⁰ over-merge and shower fragmentation | close-shower topology and shared-cell energy | single-gamma and close-π⁰ stress samples both pass split/merge limits |
| `cluster.centroid_energy` | shower energy and barycentre used by photon direction/energy | energy-weighted sums are the natural calorimeter estimator once membership is fixed | energy scale, leakage, and centroid bias | response, resolution, and centroid residuals are quoted per energy bin |

These sub-leaves keep P.1 reviewable even if several clusterer
candidates are compared: each candidate must publish the same seed,
membership, split/merge, and centroid/energy evidence before plan 33 can
consume its output.

#### Logic gaps

| Parameter | Status before production | Closure study / target date |
|---|---|---|
| `seed_threshold_mev = 5.0` in `topological_seed_v0` | `OPEN:` provisional anti-noise seed; not first-principles-derived for this geometry | Scan 1-20 MeV on `cal_singlegamma_v1`; minimise response bias plus fake-cluster rate; target 2026-06-15 |
| `time_window_ns = 10.0` | `OPEN:` placeholder until plan 61 timing resolution is frozen | Repeat P.1 closure with plan-61 nonzero timing budget and require unchanged energy response; target 2026-06-30 |
| adjacency/window ids `plan09_cell_adjacency_v0` and `plan09_fixed_window_v0` | Geometry-derived topology, but the neighbour radius/window extent is `OPEN:` | Vary adjacency radius/window size on single-gamma and close-pi0 stress samples; target 2026-06-15 |
| split/merge rules `local_maxima_split_v0`, `touching_cells_merge_v0`, and overlap fraction | `OPEN:` tuned decision boundary | Optimise split/merge Wilson intervals and pi0 over-merge guard in §4.1; target 2026-06-20 |
| closure pass limits `|DeltaE/E| < 5%`, bias `< 1%`, centroid RMS `< 1 cm`, split/merge `< 2%` | `OPEN:` analysis-quality thresholds | Tie limits to photon-object and pi0-mass resolution impact in plans 33/34; target 2026-06-30 |

#### Closure test for the derivation

1. Run each Class-A P.1 candidate on `cal_singlegamma_v1` at 50, 100,
   200, 500, and 1000 MeV with truth labels available only to the
   evaluator.
2. For each energy bin, compare measured response bias, resolution, and
   centroid RMS to the calorimeter-resolution expectation from the cited
   EM-shower references and the HIBEAM/NNBAR prototype calibration.
3. Repeat the same run after dropping `Track_ID`, `Parent_ID`, `Name`,
   process, and interaction columns; require identical membership hashes.
4. Promote only a configuration whose response, centroid, and split/merge
   metrics satisfy §4 and whose logic-gap scan row has a signed DEC.

## 3. Replacement candidates and comparison matrix

| Candidate | P.1 decision rule | Current/source citation | Class-A status | Comparison metric | Failure mode to inspect |
|---|---|---|---|---|---|
| **Topological clustering** | Seed highest-energy unassigned hit; grow through adjacent cells while neighbour significance or `eDep / Σ_cluster` exceeds threshold; split shared local maxima. | Replaces the `(Event_ID, Track_ID)` grouping inside `reconstruct_photon_objects` (`photon.py:60-201`). | Production-eligible: uses `Event_ID`, `eDep`, `x/y/z`, optional `t`, and geometry. | Energy response, centroid residual, split/merge rate on `cal_singlegamma_v1`. | Over-merges close π⁰ daughters; threshold DEC entry required. |
| **Sliding-window** | Scan fixed geometry windows around local maxima; assign each hit to the highest-window sum and merge overlapping windows. | Replaces the current photon-like row emission path in `reconstruct_photon_objects` (`photon.py:60-201`). | Production-eligible if window geometry comes only from detector layout. | Same closure metrics plus runtime and edge-cell inefficiency. | Loses irregular or grazing showers; sensitive to window size. |
| **Particle-flow-style** | Competing charged/neutral hypotheses claim hits using tracks, timing, and energy compatibility. | Interacts with charged-track matching inside `reconstruct_photon_objects` (`photon.py:60-201`). | Eligible only if truth labels are excluded and track inputs are reconstructed objects. | Closure metrics plus charged/neutral confusion against plan 32 labels. | Coupled to charged-object performance; too complex for first replacement. |
| **Track-key grouped (current)** | Group deposits by `(Event_ID, Track_ID)` and emit photon-like rows from the same function. | Current baseline is `reconstruct_photon_objects` (`photon.py:60-201`) plus `_weighted_centroid` (`photon.py:28-48`). | Not production-eligible until Track_ID provenance is either proven Class A for this decision or replaced by geometry-only membership. | Reproduction baseline only; must be beaten or matched by Class-A candidates. | Inflated closure if `Track_ID` encodes MC truth ancestry; fails plan 01 if used as production membership. |

Plan 38 ladder leaf P.1 scores each row with identical closure inputs.
Plan 47 first records the truth-labelled reproduction baseline, then
quotes the selected Class-A replacement and the residual difference.

### 3.1 Machine-readable clusterer-config fixture

Each replacement candidate has a frozen configuration row before it can
write P.1 cluster fixtures:

| Field | Required content | Review rule |
|---|---|---|
| `clusterer_config_id` | stable threshold/config key | referenced by `membership_config_id` |
| `clusterer_method` | topological, sliding-window, particle-flow-style, or legacy baseline | must match a §3 candidate |
| `seed_threshold_mev` | local-maximum or window seed threshold | null only for documented legacy baseline |
| `adjacency_rule_id` | geometry neighbour rule or window shape | resolves to a plan-09 geometry sidecar |
| `time_window_ns` | timing compatibility window or null | threshold changes require DEC approval |
| `split_rule_id`, `merge_rule_id` | split/merge policy keys | required for topological and particle-flow methods |
| `geometry_snapshot_id` | detector geometry version used to build neighbours | copied to closure artifacts |
| `class_a_input_columns` | explicit input-column allowlist | must exclude `Track_ID`, ancestry, and truth labels |
| `decision_dec_id` | `DEC-31-CLUSTERER-CHOICE` or draft replacement DEC | draft DEC keeps rows diagnostic |
| `config_status` | `diagnostic`, `candidate`, `frozen`, or `blocked` | only frozen Class-A configs may feed plans 32/33 |

The config row is rejected if a membership decision can read a column
outside the allowlist or if the geometry sidecar cannot be resolved.

Initial clusterer-config examples:

| `clusterer_config_id` | `clusterer_method` | `seed_threshold_mev` | `adjacency_rule_id` | `time_window_ns` | `split_rule_id` | `merge_rule_id` | `geometry_snapshot_id` | `class_a_input_columns` | `decision_dec_id` | `config_status` |
|---|---|---:|---|---:|---|---|---|---|---|---|
| `legacy_track_key_repro` | `legacy_track_key` | null | null | null | null | null | null | [`Event_ID`, `Track_ID`, `eDep`, `x`, `y`, `z`] | `DEC-31-TRUTH-LABEL-QUARANTINE` | `diagnostic` |
| `topological_seed_v0` | `topological` | 5.0 | `plan09_cell_adjacency_v0` | 10.0 | `local_maxima_split_v0` | `touching_cells_merge_v0` | `plan09_geometry_v0` | [`Event_ID`, `eDep`, `x`, `y`, `z`, `t`] | `DEC-31-CLUSTERER-CHOICE` | `candidate` |
| `sliding_window_v0` | `sliding-window` | 5.0 | `plan09_fixed_window_v0` | null | `window_overlap_split_v0` | `overlap_fraction_merge_v0` | `plan09_geometry_v0` | [`Event_ID`, `eDep`, `x`, `y`, `z`] | `DEC-31-CLUSTERER-CHOICE` | `candidate` |

The legacy row is diagnostic because `Track_ID` is not a production
membership input; it is retained only to reproduce current L3 behavior.

## 4. Closure-test specification

1. **Dataset id:** run `cal_singlegamma_v1` from plan 23 at 50,
   100, 200, 500, and 1000 MeV single-γ settings, with the truth
   labels used only by the evaluator.
2. **Observable:** for the selected P.1 candidate, record cluster
   reconstructed energy, energy response `(E_cluster - E_truth) /
   E_truth`, cluster centroid residual against the energy-weighted
   true deposit centroid, number of clusters per event, and the
   split/merge classification.
3. **Fitter / estimator:** fit the response distribution in each
   energy bin with a Gaussian core plus bootstrap uncertainty on the
   mean; compute centroid residual RMS and split/merge Wilson
   intervals.
4. **Pass criterion:** mean `|ΔE/E| < 5%`, absolute response bias
   `< 1%`, centroid residual RMS `< 1 cm`, and split-or-merge rate
   `< 2%` in every energy bin.
5. **Audit hook:** rerun after dropping `Track_ID`, `Parent_ID`,
   `Name`, `Process`, and `Interaction` columns. Any change in
   production cluster membership fails the Class-A gate.

### 4.1 Machine-readable cluster closure fixture

Each P.1 candidate clusterer writes one closure-result row per energy
bin so plan 38 and plan 47 can compare algorithms without parsing plots:

| Field | Required content | Review rule |
|---|---|---|
| `clusterer_method` | method id from §3 | must match the fixture's `clusterer_method` |
| `dataset_id`, `energy_bin_mev` | `cal_singlegamma_v1` setting | every required bin in §4 gets a row |
| `n_events`, `n_clusters` | denominators after quality gates | zero denominators fail closure |
| `mean_delta_e_over_e`, `response_bias_interval_68` | Gaussian-core response and bootstrap interval | compared to §4 pass criterion |
| `centroid_residual_rms_cm` | centroid closure metric | must be `< 1 cm` for a pass row |
| `split_rate`, `merge_rate` | Wilson-interval rates | each must stay within the §4 budget |
| `class_b_drop_hash` | rerun artifact with ancestry columns removed | cluster membership hash must match production run |
| `closure_status` | `pass`, `fail`, or `diagnostic_only` | only `pass` rows can support production selection |

A `diagnostic_only` row may document the Track_ID-keyed baseline, but a
production clusterer needs `closure_status = pass` in every energy bin.

Required closure row-key inventory:

| `dataset_id` | `energy_bin_mev` | Required row purpose | Acceptance guard |
|---|---:|---|---|
| `cal_singlegamma_v1` | 50 | low-energy shower response and split/merge check | all §4.1 metrics present; no zero denominator |
| `cal_singlegamma_v1` | 100 | near-threshold photon-object response | all §4.1 metrics present; no zero denominator |
| `cal_singlegamma_v1` | 200 | Ch 8 π⁰-relevant photon response | all §4.1 metrics present; no zero denominator |
| `cal_singlegamma_v1` | 500 | mid-energy linearity check | all §4.1 metrics present; no zero denominator |
| `cal_singlegamma_v1` | 1000 | high-energy linearity and over-merge stress test | all §4.1 metrics present; no zero denominator |

The inventory defines row keys only. It does not count as closure
evidence until a clusterer writes measured §4.1 metrics and the Class-B
drop hash matches.

Initial closure-failure examples:

| `closure_case_id` | Failing pattern | Required status | Review guard |
|---|---|---|---|
| `zero_denominator_bin` | required energy bin has `n_events = 0` after quality gates | `fail` | cannot average over missing bins or borrow neighbouring energy bins |
| `class_b_membership_drift` | cluster membership hash changes after dropping ancestry columns | `fail` | blocks production even if response and centroid metrics pass |
| `overmerge_high_energy` | 1000 MeV row passes response but exceeds the merge-rate budget | `fail` | threshold DEC must show a passing over-merge margin before promotion |
| `legacy_diagnostic_passlike` | Track_ID-keyed row matches closure metrics but depends on provenance grouping | `diagnostic_only` | cannot support `DEC-31-CLUSTERER-CHOICE` as production evidence |

### 4.2 Decision-log stubs for the P.1 replacement

The current Track_ID-keyed grouping is a load-bearing baseline.
Replacing it, and freezing any topological threshold, requires
plan-05 DEC entries before implementation can be signed:

| DEC stub | Decision to freeze | Required evidence before approval |
|---|---|---|
| `DEC-31-CLUSTERER-CHOICE` | Select topological, sliding-window, or particle-flow-style clustering as the production P.1 algorithm | plan-38 ladder row plus the §4 closure table on `cal_singlegamma_v1` |
| `DEC-31-ADJACENCY-THRESHOLDS` | Freeze adjacency radius / cell-neighbour rule, seed threshold, and split/merge thresholds | N-1 threshold scan showing closure pass margins and π⁰ over-merge rate |
| `DEC-31-TRUTH-LABEL-QUARANTINE` | Keep `Track_ID`-based and truth-label comparisons only in validation labels and plan-47 reproduction baselines | plan-01 audit output showing production membership unchanged after Class B columns are dropped |

Initial adjacency-threshold scan examples:

| `scan_case_id` | Varied parameter | Required diagnostic row | Promotion guard |
|---|---|---|---|
| `topo_seed_low_v0` | lower topological seed threshold below the nominal §3.1 value | closure row records extra low-energy clusters and split rate | cannot promote if `split_rate` exceeds the §4 budget in any energy bin |
| `topo_adjacency_wide_v0` | widen neighbour radius / cell adjacency | closure row records merge rate and π⁰-daughter over-merge stress | cannot promote without `DEC-31-ADJACENCY-THRESHOLDS` evidence for over-merge margin |
| `sliding_window_overlap_v0` | vary sliding-window overlap merge fraction | closure row records duplicate-cluster and edge-cell inefficiency rates | only diagnostic unless it beats topological closure without truth labels |
| `class_b_track_key_probe` | repeat the selected scan with Class-B ancestry columns dropped | `class_b_drop_hash` compared to the production scan | any membership change blocks `DEC-31-TRUTH-LABEL-QUARANTINE` approval |

These are stubs, not approved methodology. The approved decision-log
entries are created by the plan-05 governance workflow once the selected
implementation and closure evidence exist.

Initial downstream-handoff examples:

| `handoff_case_id` | Cluster output pattern | Consumer expectation | Review guard |
|---|---|---|---|
| `topological_pass_to_p2` | frozen Class-A cluster rows with stable `cluster_id` and hit membership | plan 32 may compute shower-shape features | requires matching Class-B drop hash and passing §4 closure rows |
| `diagnostic_track_key_quarantine` | Track_ID-keyed reproduction rows kept for comparison | plan 32/33 may read them only as diagnostic ladder inputs | cannot be labelled as production P.1 membership |
| `split_merge_boundary_panel` | threshold-scan rows near split/merge decision boundaries | plan 33/34 over-merge audits consume duplicate-rate evidence | threshold DEC must cite the exact scan row ids |
| `blocked_unstable_membership` | cluster membership changes under provenance drop | no downstream production consumer | plan 38 records the blocked method, but plan 32/33 do not consume it |

Initial production-promotion checklist:

| `promotion_check_id` | Evidence required | Blocks promotion when missing |
|---|---|---|
| `p31_method_row_present` | selected `clusterer_method` fixture row with stable output schema | downstream plans cannot infer hit membership semantics |
| `p31_all_energy_bins_pass` | measured §4.1 closure rows for every required energy bin | no averaging over absent or failed calibration points |
| `p31_truth_drop_stable` | Class-B drop hash matches for the selected method | production cluster membership still depends on provenance labels |
| `p31_decisions_signed` | relevant DEC ids attached for method and thresholds | threshold or algorithm changes remain diagnostic-only |

A reviewer should reject a P.1 handoff unless all four checks are
traceable to concrete fixture rows. This checklist is intentionally
stricter than the prose acceptance criteria so plan 32/33 cannot consume
a partially promoted clusterer.

Initial evidence-bundle examples:

| `evidence_bundle_id` | Included rows | Reviewer action |
|---|---|---|
| `p31_topo_prod_candidate_v0` | selected clusterer method, all energy-bin closure rows, Class-B drop hash, DEC stubs | eligible for plan-32 handoff review only if every row is measured/pass |
| `p31_trackkey_repro_only_v0` | current Track_ID-keyed baseline and closure comparison rows | keep as reproduction/diagnostic context, not production membership evidence |
| `p31_overmerge_blocked_v0` | high-energy closure row plus split/merge boundary scan | block downstream promotion and request threshold retune evidence |
| `p31_missing_bin_blocked_v0` | partial closure table missing one required energy bin | reject until the missing bin is regenerated instead of interpolated |

Evidence bundles are reviewer-facing manifests, not new algorithms. They
exist to make the promotion checklist auditable without re-reading every
scan and closure table.

Initial reviewer audit cases:

| `audit_case_id` | Reviewer question | Required evidence before accept | Reject condition |
|---|---|---|---|
| `p31_membership_semantics_audit` | Does the cluster id identify geometry-only hit membership rather than provenance grouping? | method fixture, source-field list, and Class-B drop hash | any production row still depends on provenance labels |
| `p31_closure_coverage_audit` | Are all required energy and topology bins represented? | measured closure rows for every bin named by the fixture | a missing or failed bin is averaged away |
| `p31_threshold_audit` | Is every split/merge threshold traceable to a DEC and scan row? | threshold config id, scan id, and DEC id | threshold appears only in prose or code defaults |
| `p31_handoff_audit` | Can plans 32/33 reproduce the exact cluster input? | evidence bundle id plus immutable cluster schema | handoff omits the selected method or schema version |

## 5. Acceptance criteria

- §1 violation removed.
- §4 closure passes.
- §3 ladder benchmark recorded.
- Promotion checklist and evidence-bundle rows identify the exact
  clusterer method, energy-bin closure rows, and Class-B drop hash used
  for any plan-32/33 handoff.
- Blocked or reproduction-only bundles cannot be consumed as production
  cluster membership evidence.

## 6. Dependencies

- **24** — leaf P.1.
- **38** — ladder.
- *Consumed by:* plans 32 (shower shape), 33 (photon object).

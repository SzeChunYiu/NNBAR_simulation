---
id: 33_subsystem_photon_object_fragment_merge_fixture
title: Subsystem — photon object fragment-merge fixture
version: 0.1
status: draft
owner: EM-Object POG
depends_on: [33_subsystem_photon_object, 31_subsystem_calorimeter_clustering, 32_subsystem_shower_shape]
outputs:
  - {path: docs/rebuild_plans/33_subsystem_photon_object_fragment_merge_fixture.md, schema: split fragment-merge fixture}
acceptance:
  - {test: merge rows remain truth-blind and join to P.1/P.2 fixtures, method: review, pass_when: all rows pass}
last_updated: 2026-05-10
---

# Photon-object fragment-merge fixture

This companion file keeps plan 33 below the line cap while preserving the
machine-readable fixture for optional geometry/time fragment merging.

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

Initial fragment-merge decision examples:

| `merge_candidate_id` | Input pattern | `merge_threshold_id` | Expected decision | Review guard |
|---|---|---|---|---|
| `single_cluster_passthrough` | one accepted neutral P.1 cluster | `no_merge_baseline_v0` | `keep_separate` | preserves the current one-cluster photon baseline |
| `nearby_same_shower_fragments` | two neutral clusters with small angular, centroid, and timing separation | `geom_time_merge_diag_v0` | `merge` only in diagnostic rows until DEC approval | truth-blind hash must match after provenance drop |
| `pi0_two_daughter_guard` | two energetic neutral clusters with π⁰-like opening angle | `geom_time_merge_diag_v0` | `keep_separate` | over-merge rate is counted in §6.1 before promotion |
| `truth_parent_merge_oracle` | merge proposed from generated photon ancestry | `truth_oracle_blocked` | `blocked` | validation upper bound only; never writes photon rows |

The examples define review cases for the merge fixture. They do not
create executable merge algorithms or alter the current photon baseline.

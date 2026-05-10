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

### 2.2 Current-to-target cluster identifier map

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

### 4.1 Decision-log stubs for the P.1 replacement

The current Track_ID-keyed grouping is a load-bearing baseline.
Replacing it, and freezing any topological threshold, requires
plan-05 DEC entries before implementation can be signed:

| DEC stub | Decision to freeze | Required evidence before approval |
|---|---|---|
| `DEC-31-CLUSTERER-CHOICE` | Select topological, sliding-window, or particle-flow-style clustering as the production P.1 algorithm | plan-38 ladder row plus the §4 closure table on `cal_singlegamma_v1` |
| `DEC-31-ADJACENCY-THRESHOLDS` | Freeze adjacency radius / cell-neighbour rule, seed threshold, and split/merge thresholds | N-1 threshold scan showing closure pass margins and π⁰ over-merge rate |
| `DEC-31-TRUTH-LABEL-QUARANTINE` | Keep `Track_ID`-based and truth-label comparisons only in validation labels and plan-47 reproduction baselines | plan-01 audit output showing production membership unchanged after Class B columns are dropped |

These are stubs, not approved methodology. The approved entries live in
`docs/governance/DECISION_LOG.md` once the selected implementation and
closure evidence exist.

## 5. Acceptance criteria

- §1 violation removed.
- §4 closure passes.
- §3 ladder benchmark recorded.

## 6. Dependencies

- **24** — leaf P.1.
- **38** — ladder.
- *Consumed by:* plans 32 (shower shape), 33 (photon object).

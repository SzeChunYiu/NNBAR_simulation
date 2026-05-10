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
  - {risk: removing the Parent_ID-based grouping (plan 08 §3.5) loses showers whose parent gamma has no LG hit, mitigation: §3 topological clustering captures contiguous deposits}
estimated_effort: L
last_updated: 2026-05-09
---

# Subsystem — calorimeter clustering

*Charter.* Owns leaf P.1. Groups lead-glass and scintillator hits
into clusters. The current code uses ancestry truth (`Parent_ID`,
`Interaction` table) — a Class B violation. The replacement is
Class A topological / particle-flow-style clustering.

## 1. Current implementation (Class B violation)

`reconstruction.py` (plan 08 §3.5 step 1): groups lead-glass deposits
by walking `Parent_ID` chains back to the gamma ancestor, with
`Interaction` table as ancestry map. Conversion electrons missing
their parent get reattached as gamma showers.

This is the most prominent Class B leak in the production reco path.
It was chosen for the licentiate because it gives the right answer
in MC; replacing it is the largest single migration item.

## 2. Leaf P.1 input/output schema

Leaf P.1: calorimeter hits → neutral-shower cluster candidates

- **Inputs (production, Class A only):** LeadGlass and Scintillator
  parquet rows with `Event_ID`, `eDep`, `x`, `y`, `z`, and optional
  `t` from plan 09 §§9–10. Geometry side-cars from plan 09 §13 may
  be used to define nearest-neighbour topology, cell adjacency, and
  detector-component labels.
- **Current implementation evidence:** plan 08 identifies the present
  source resolver as `_leadglass_shower_sources`
  (`reconstruction.py:407–499`) and its use inside
  `reconstruct_photon_objects` before photon-row construction
  (`reconstruction.py:890–896`). Lead-glass groups are emitted at
  `reconstruction.py:1046–1075`; scintillator-only groups at
  `reconstruction.py:1077–1099`. The emitted photon table currently
  doubles as the cluster surface (`reconstruction.py:793–822`).
- **Decision rule (target):** seed clusters from local calorimeter
  energy maxima, grow by detector adjacency / spatial proximity, and
  split or merge clusters using only hit energy, hit position, timing,
  and calibrated detector geometry. No `Track_ID`, `Parent_ID`,
  `Name`, `Process`, or `Interaction` ancestry may decide cluster
  membership.
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

## 3. Replacement candidates

| Candidate | Method | Source | Notes |
|---|---|---|---|
| **Topological clustering** | seed = highest-E hit; grow until eDep / Σ < threshold | ATLAS topo-clusters | well-studied; threshold-tunable |
| **Sliding-window** | fixed-size windows around local maxima | LHC EM calorimeters | simpler; less robust to overlap |
| **Particle-flow-style** | hypotheses compete for hits | PandoraPFA / CMS PF | most ambitious; biggest potential gain |
| **Truth-labelled (current)** | `Parent_ID` chains | legacy | Class B violation |

Plan 38 ladder leaf P.1 scores each. Plan 47 ledger reproduces
licentiate first with the truth-labelled version, then replaces.

## 4. Closure on `cal_singlegamma_v1`

For γ at fixed E:

- ΔE/E (cluster vs truth gamma KE) < 5% mean; bias < 1%.
- Cluster centroid within 1 cm of energy-weighted truth deposit.

## 5. Acceptance criteria

- §1 violation removed.
- §4 closure passes.
- §3 ladder benchmark recorded.

## 6. Dependencies

- **24** — leaf P.1.
- **38** — ladder.
- *Consumed by:* plans 32 (shower shape), 33 (photon object).

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

## 2. Replacement candidates

| Candidate | Method | Source | Notes |
|---|---|---|---|
| **Topological clustering** | seed = highest-E hit; grow until eDep / Σ < threshold | ATLAS topo-clusters | well-studied; threshold-tunable |
| **Sliding-window** | fixed-size windows around local maxima | LHC EM calorimeters | simpler; less robust to overlap |
| **Particle-flow-style** | hypotheses compete for hits | PandoraPFA / CMS PF | most ambitious; biggest potential gain |
| **Truth-labelled (current)** | `Parent_ID` chains | legacy | Class B violation |

Plan 38 ladder leaf P.1 scores each. Plan 47 ledger reproduces
licentiate first with the truth-labelled version, then replaces.

## 3. Closure on `cal_singlegamma_v1`

For γ at fixed E:

- ΔE/E (cluster vs truth gamma KE) < 5% mean; bias < 1%.
- Cluster centroid within 1 cm of energy-weighted truth deposit.

## 4. Acceptance criteria

- §1 violation removed.
- §3 closure passes.
- §2 ladder benchmark recorded.

## 5. Dependencies

- **24** — leaf P.1.
- **38** — ladder.
- *Consumed by:* plans 32 (shower shape), 33 (photon object).

---
id: 35_subsystem_kinematic_fit
title: Subsystem — kinematic fit (leaf P.7)
version: 0.1
status: draft
owner: Combined Performance
depends_on: [00_README, 24_reconstruction_question_tree, 30_subsystem_vertex, 33_subsystem_photon_object, 34_subsystem_pi0_pairing, 38_truth_substitution_ladder, 40_closure_and_pulls]
outputs:
  - {path: docs/rebuild_plans/35_subsystem_kinematic_fit.md, schema: this file}
acceptance:
  - {test: π⁰ mass-constrained fit improves σ(M_γγ) by ≥ 20%, method: paired closure pre/post fit, pass_when: improvement}
  - {test: pull mean ≈ 0, width ≈ 1 for fitted four-vectors, method: plan 40, pass_when: pass}
  - {test: χ² distribution follows expected ndf, method: closure plot, pass_when: K-S p > 0.01}
risks:
  - {risk: covariance estimation (plan 26) is approximate → fit χ² distribution is wrong, mitigation: §3 covariance audit}
estimated_effort: M
last_updated: 2026-05-09
---

# Subsystem — kinematic fit

*Charter.* Owns leaf P.7. Improves π⁰ mass resolution and event-
level four-vector consistency by mass-constrained / vertex-
constrained fits.

## 1. Mass-constrained π⁰ fit

For each pair from plan 34 satisfying basic cuts:

1. Constrain `M_γγ = m_π⁰ = 134.977 MeV`.
2. Minimise `χ² = Σ Δ_i^T Σ_i^{-1} Δ_i` over photon four-momentum
   adjustments subject to the constraint, using Lagrange
   multipliers.
3. Report fitted four-vectors, fit χ², ndf.

Belle II / GlueX style; standard kinematic-fit literature.

## 2. Vertex-constrained event fit

When the event vertex is reconstructed (plan 30):

- Constrain photon directions to point from the vertex.
- Constrain charged-track origins to the vertex.
- Joint fit returning `χ²_event`.

Used by plan 37 (event selection) as an additional cut variable.

## 3. Closure

`cal_singlegamma_v1` paired into synthetic π⁰s — verify σ(M_γγ)
improves by ≥ 20% after the constraint vs raw photon four-vectors.
On `sig_foil_v3` π⁰ candidates, the fitted-four-vector pulls follow
plan 40 §2 tolerances.

## 4. Acceptance criteria

- §1 implementation lands; §3 closure passes.
- §1 χ² distribution follows expected ndf within K-S p > 0.01.

## 5. Dependencies

- **24, 30, 33, 34, 38, 40** — inputs.
- *Consumed by:* plan 36 (event variables; uses fitted four-vectors),
  plan 37 (selection), plan 38 (ladder leaf P.7).

## 6. References

- Belle II kinematic-fit framework documentation.
- GlueX π⁰ kinematic fit notes.

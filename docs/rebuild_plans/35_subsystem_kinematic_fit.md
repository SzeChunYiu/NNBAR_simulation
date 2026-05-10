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

## 1. Leaf P.7 input/output schema

Leaf P.7: raw π⁰ candidates → fitted four-vectors and fit quality

- **Inputs (production, Class A only):** plan-34 candidate rows,
  plan-33 photon four-vectors and covariance estimates, plan-30
  vertex/covariance when available, and calibrated resolution models
  from plans 18 and 40.
- **Current implementation evidence:** plan 08 shows the current
  baseline has only raw π⁰ kinematics in `find_pi0_candidates`
  (`reconstruction.py:1316–1530`). The output schema declared at
  `reconstruction.py:1322–1365` contains mass, opening angle,
  energies, cut booleans, timing/provenance diagnostics, and failure
  reasons, but no fitted four-vector, covariance, `fit_chi2`, or
  `fit_ndf`. Raw mass is computed at `reconstruction.py:1414–1417`.
- **Decision rule (target):** for every candidate selected for fit,
  solve a constrained least-squares problem using reconstructed
  quantities and their covariance; accept or rank candidates by
  `fit_chi2/fit_ndf` only after closure validates the χ² law.
- **Outputs:** `event_id`, photon ids, raw mass, `fit_mass`,
  fitted photon four-vectors, fitted π⁰ four-vector, covariance
  summary, `fit_chi2`, `fit_ndf`, `fit_probability`,
  `fit_converged`, and `fit_failure_reason`.
- **Truth-use boundary:** truth π⁰ labels and generated four-vectors
  are closure labels only; they must not seed, constrain, or choose a
  production fit.

## 2. Mass-constrained π⁰ fit

For each pair from plan 34 satisfying basic cuts:

1. Constrain `M_γγ = m_π⁰ = 134.977 MeV`.
2. Minimise `χ² = Σ Δ_i^T Σ_i^{-1} Δ_i` over photon four-momentum
   adjustments subject to the constraint, using Lagrange
   multipliers.
3. Report fitted four-vectors, fit χ², ndf.

Belle II / GlueX style; standard kinematic-fit literature.

## 3. Vertex-constrained event fit

When the event vertex is reconstructed (plan 30):

- Constrain photon directions to point from the vertex.
- Constrain charged-track origins to the vertex.
- Joint fit returning `χ²_event`.

Used by plan 37 (event selection) as an additional cut variable.

## 4. Closure

`cal_singlegamma_v1` paired into synthetic π⁰s — verify σ(M_γγ)
improves by ≥ 20% after the constraint vs raw photon four-vectors.
On `sig_foil_v3` π⁰ candidates, the fitted-four-vector pulls follow
plan 40 §2 tolerances.

## 5. Acceptance criteria

- §2 implementation lands; §4 closure passes.
- §2 χ² distribution follows expected ndf within K-S p > 0.01.

## 6. Dependencies

- **24, 30, 33, 34, 38, 40** — inputs.
- *Consumed by:* plan 36 (event variables; uses fitted four-vectors),
  plan 37 (selection), plan 38 (ladder leaf P.7).

## 7. References

- Belle II kinematic-fit framework documentation.
- GlueX π⁰ kinematic fit notes.

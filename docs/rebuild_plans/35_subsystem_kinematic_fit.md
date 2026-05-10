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
- **Current implementation evidence:** the compact current baseline
  has only raw π⁰ kinematics in `find_pi0_candidates` (`photon.py:204-263`). It emits mass, opening angle, energy
  sums, lead-glass fraction, and the strict `passes_selection` flag,
  but no fitted four-vector, covariance, `fit_chi2`, or `fit_ndf`.
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

### 1.1 Covariance contract

The fitter may run only when each photon carries a finite energy
uncertainty and a finite angular/direction uncertainty from plans 33
and 40. The first implementation may use a diagonal covariance
(`σ_E`, `σ_θ`, `σ_φ`) per photon; off-diagonal terms are added only
after plan 40 validates them. If either photon lacks a covariance,
emit `fit_converged = false`, `fit_failure_reason =
"missing_covariance"`, and preserve the raw candidate for plan 36 /
37 consumers rather than silently substituting truth resolution.

Fit outputs record the covariance version, resolution-model tag, and
whether the vertex constraint was active so plan 38 can compare raw,
mass-only, vertex-only, and combined fits on the same candidates.

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

## 4. Alternative comparison matrix

| Candidate | P.7 decision rule | Current/source citation | Class-A status | Comparison metric | Failure mode to inspect |
|---|---|---|---|---|---|
| **No fit / raw mass (current)** | Use raw `M_γγ` from photon four-vectors and six cuts. | Current raw candidate baseline is `find_pi0_candidates` (`photon.py:204-263`), which has no fit columns. | Production-eligible baseline. | Raw mass width, pull bias, π⁰ efficiency. | Worse resolution; limited accidental rejection. |
| **Mass-constrained π⁰ fit** | Adjust photon four-vectors within covariance subject to `M_γγ = m_π⁰`. | New P.7 module after plan-34 output. | Eligible after covariance closure. | Width improvement, pull mean/width, χ² K-S p-value. | Bad covariance can fake improvement and miscalibrate χ². |
| **Vertex-constrained event fit** | Constrain photon and charged-object origins to the reconstructed vertex. | Consumes plan-30 vertex and plan-33/29 objects. | Eligible only when vertex covariance exists. | Event χ², visible-mass resolution, selection stability. | Sparse-vertex events need explicit no-fit path. |
| **Combined mass+vertex fit** | Fit π⁰ mass and common vertex constraints simultaneously. | Extends §§2–3. | Eligible after separate constraints pass. | Global χ² and downstream S.3/S.4 separation. | Harder failure diagnosis; do after simpler fits. |
| **Truth-constrained diagnostic** | Seed or constrain to generated π⁰ direction/energy. | Truth labels are evaluator-only under plan 40. | Not production-eligible. | Upper-bound resolution only. | Would violate plan 01 if used in decision path. |

Plan 38 records raw, mass-only, vertex-only, and combined-fit ladder
rows so event-variable and selection consumers can choose the simplest
validated fit.

## 5. Closure-test specification

1. **Dataset ids:** pair independent photons from `cal_singlegamma_v1`
   into synthetic π⁰ events for controlled mass closure, and run the
   selected fit on `sig_foil_v3` plan-34 candidates for in-sample
   pull and χ² validation.
2. **Observable:** raw and fitted `M_γγ`, fitted photon and π⁰
   four-vector pulls, `fit_chi2`, `fit_ndf`, `fit_probability`,
   convergence rate, and candidate ranking changes relative to raw
   mass.
3. **Fitter / estimator:** use the production constrained least-squares
   fitter; compare raw vs fitted mass widths with bootstrap paired
   uncertainty; test χ² against the expected ndf distribution with a
   K-S test.
4. **Pass criterion:** fitted mass width improves by `≥ 20%`, pull
   means are compatible with zero, pull widths are in plan-40 tolerance
   `[0.8, 1.2]`, convergence rate is `≥ 0.98`, and χ² K-S p-value
   is `> 0.01`.
5. **Audit hook:** rerun with truth labels removed from photon and π⁰
   inputs. Fitted values, convergence flags, and χ² must be unchanged.

### 5.1 Decision-log stubs for fit use

Kinematic fitting changes a downstream four-vector and may add a
selection/ranking variable, so plan-05 DEC approval is required before
any fitted value replaces the raw baseline:

| DEC stub | Decision to freeze | Required evidence before approval |
|---|---|---|
| `DEC-35-FIT-MODE` | Choose raw-only, mass-only, vertex-only, or combined mass+vertex as the production P.7 output for plan 36/37 consumers | plan-38 comparison row plus §5 width, pull, convergence, and χ² closure |
| `DEC-35-COVARIANCE-MODEL` | Freeze diagonal vs full covariance, resolution-model tag, and sparse-covariance fallback | plan-40 pull validation and explicit `missing_covariance` rate by sample |
| `DEC-35-FIT-QUALITY-USE` | Decide whether `fit_chi2`, `fit_probability`, or convergence flags may enter plan-37 selection | N-1 / ROC evidence from plan 41 and proof that the χ² K-S p-value remains `> 0.01` |

Until these entries are approved, fitted columns are diagnostic or
ladder-comparison outputs; the raw π⁰ candidate remains the
reproduction baseline.

## 6. Acceptance criteria

- §2 implementation lands; §5 closure passes.
- §2 χ² distribution follows expected ndf within K-S p > 0.01.

## 7. Dependencies

- **24, 30, 33, 34, 38, 40** — inputs.
- *Consumed by:* plan 36 (event variables; uses fitted four-vectors),
  plan 37 (selection), plan 38 (ladder leaf P.7).

## 8. References

- Belle II kinematic-fit framework documentation.
- GlueX π⁰ kinematic fit notes.

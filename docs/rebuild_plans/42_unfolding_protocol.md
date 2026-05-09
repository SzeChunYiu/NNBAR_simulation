---
id: 42_unfolding_protocol
title: Unfolding protocol — particle-level vs detector-level
version: 0.1
status: draft
owner: Analysis WG
depends_on: [00_README, 04_statistical_uncertainty, 36_subsystem_event_variables, 38_truth_substitution_ladder]
outputs:
  - {path: docs/rebuild_plans/42_unfolding_protocol.md, schema: this file}
acceptance:
  - {test: response matrix produced for at least visible invariant mass and π⁰ mass, method: §2 deliverable, pass_when: matrices saved}
  - {test: regularisation choice (IBU vs SVD) named with per-observable iteration / reg parameter, method: §3 review, pass_when: signed in DEC}
  - {test: closure on truth-MC sample passes, method: §4 closure, pass_when: pull mean ≈ 0, width ≈ 1 within tolerance}
risks:
  - {risk: model dependence — unfolded distribution depends on the prior, mitigation: §5 model-variation systematic}
estimated_effort: M
last_updated: 2026-05-09
---

# Unfolding protocol

*Charter.* When quoting a physics distribution (visible invariant
mass, π⁰ mass spectrum), the rebuild reports both detector-level
and particle-level — the latter via unfolding. This plan defines the
protocol; whether unfolded distributions are quoted in the thesis is
a separate user decision.

## 1. Why unfold

Detector-level distributions depend on the simulation; particle-level
distributions depend on physics. For thesis Ch 8/9 plots, the user
chooses which to quote based on whether the goal is to constrain
physics (particle-level) or to characterise the detector (detector-
level).

## 2. Response matrix

For every observable that the rebuild may publish at particle level:

1. Bin truth values from `Particle_output` and reco values from the
   reconstruction.
2. Compute response matrix `R_ij = P(reco bin i | truth bin j)`
   from the signal sample.
3. Save the matrix and its statistical uncertainty (per plan 04 §2
   bootstrap).

Initial coverage:

- Visible invariant mass (E.7).
- π⁰ mass (P.5 fitted).
- Sphericity (E.5).

## 3. Regularisation

Two implementations:

- **Iterative Bayesian Unfolding (IBU)** with `n_iter` to tune.
- **SVD unfolding** with regularisation parameter `k`.

Both implementations live in `pyhf` or `RooUnfold` ports;
codex-supervisor wraps the chosen library.

Per-observable choice of method + tuning parameter is signed by DEC.

## 4. Closure

- *MC closure.* Apply the response matrix to a different truth
  distribution; verify the unfolded result agrees with the alternate
  truth within statistical uncertainty.
- *Pull closure.* Per plan 40 §1 on every unfolded bin.

## 5. Model dependence

A response matrix derived from one signal model differs from one
derived from an alternative branching table (plan 13 §4). The
"signal model" systematic propagates through the response matrix
via re-derivation under each alternative, then quadrature.

## 6. Acceptance criteria

- §2 response matrices produced for ≥ 3 observables.
- §3 method choice signed.
- §4 closure passes.
- §5 systematic is propagated into plan 45.

## 7. Dependencies

- **04, 36, 38** — inputs.
- *Consumed by:* plan 47 (ledger), plan 50 (defence package), plan
  45 (systematics).

## 8. References

- D'Agostini, *NIM A* 362 (1995) 487 (IBU).
- Höcker & Kartvelishvili, *NIM A* 372 (1996) 469 (SVD).
- RooUnfold documentation.

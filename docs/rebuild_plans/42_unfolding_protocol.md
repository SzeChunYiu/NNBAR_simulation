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

For every observable that may be published at particle level, build an
explicit truth-to-reconstruction response matrix and save the exact
binning contract used by closure and unfolding. Truth inputs are Class B
and are allowed only inside this analysis/unfolding protocol, not inside
production reconstruction decisions.

### 2.1 Runnable procedure

1. Produce reconstruction tables with the plan 09 §14 schema:

   ```bash
   python -m nnbar_reconstruction.cli summarize \
       NNBAR_Detector/output/sig_foil_v3 --all-runs \
       --table output/reco/sig_foil_v3/ --json output/reco/sig_foil_v3/summary.json
   ```

2. Build response matrices from truth parquet plus reconstruction CSVs:

   ```bash
   python -m nnbar_reconstruction.cli response-matrix \
       --truth-particle NNBAR_Detector/output/sig_foil_v3/Particle_output_*.parquet \
       --truth-interaction NNBAR_Detector/output/sig_foil_v3/Interaction_output_*.parquet \
       --reco-events output/reco/sig_foil_v3/events.csv \
       --reco-pi0 output/reco/sig_foil_v3/pi0.csv \
       --observables visible_mass,pi0_mass,sphericity \
       --bootstrap 200 --out output/unfolding/response/sig_foil_v3/
   ```

3. For each observable write `response_<observable>.parquet`,
   `response_<observable>_covariance.npz`, and
   `response_<observable>_metadata.json` containing truth/reco bin
   edges, normalisation convention, bootstrap seed, source file hashes,
   and the plan 38 leaf mapping.
4. Assert every truth-bin column is normalised to
   `sum_i R_ij = 1.0 ± 1e-12` after explicit inefficiency/overflow bins
   are included. Bins with fewer than 20 truth events are merged with a
   neighbour before matrix normalisation and the merge is recorded in
   metadata.

### 2.2 Observable binning and tolerances

| Observable | Truth/reco inputs from plan 09 | Matrix binning / tolerance | Ladder leaf | Subsystem / ledger hook |
|---|---|---|---|---|
| visible invariant mass | truth four-vectors from `Particle_output`; reco `events.csv` visible mass | 25 MeV bins over 0-2500 MeV plus under/overflow; response columns normalise to `1 ± 1e-12`. | E.7 | plan 36; plan 47 §1 mass rows |
| π0 mass | truth photons/π0 ancestry from `Interaction_output`; reco `pi0.csv` mass-window candidates | 5 MeV bins over 0-300 MeV plus no-candidate bin; bins with <20 truth entries are merged. | P.5-P.7 | plans 34-35; plan 47 §1 π0 rows |
| sphericity | truth-derived event variables; reco `events.csv` sphericity | 0.02 bins on [0, 1]; bootstrap covariance must be saved for every populated bin. | E.5 | plan 36; plan 41 ROC/N-1 hooks |

Initial coverage is limited to these three observables because they are
explicit in plan 38's observable budget and have reconstruction-side
tables in plan 09 §14. New particle-level observables require a new row
here before they can be unfolded or quoted in plan 47.

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

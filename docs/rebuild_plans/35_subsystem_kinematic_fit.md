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
last_updated: 2026-05-10
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

#### 1.1.1 Machine-readable fit-input covariance fixture

Before a fit is attempted, each photon input records the covariance
surface that made the fit eligible or ineligible:

| Field | Required content | Review rule |
|---|---|---|
| `fit_input_candidate_key` | deterministic key from §1.4 | joins both photons to the candidate row |
| `photon_id` | consumed plan-33 photon id | exactly two rows per mass-constraint attempt |
| `energy_sigma_mev` | finite positive energy uncertainty | missing or non-positive blocks the fit |
| `theta_sigma_rad`, `phi_sigma_rad` | finite positive direction uncertainties | missing values produce `missing_covariance` |
| `covariance_terms` | diagonal terms initially; full matrix when approved | matrix dimension must match the chosen `fit_mode` |
| `covariance_model_id` | plan-40 covariance model tag | copied into the P.7 fit fixture |
| `resolution_model_id` | calibrated resolution source tag | required before production use |
| `covariance_status` | `valid`, `missing`, `singular`, or `diagnostic_only` | non-valid status forbids fitted outputs |
| `failure_reason_if_invalid` | status-specific reason string | must map to a §1.2 failure reason |

Initial covariance-model examples:

| `covariance_model_id` | Fit input surface | Allowed fit modes | Required closure row | Approval rule |
|---|---|---|---|---|
| `diag_energy_angle_plan40_v0` | diagonal photon energy, θ, and φ uncertainties from the plan-40 pull model | `mass_constraint` | `cal_singlegamma_v1:synthetic_pi0_pairs` | diagnostic until pull width and χ² closure pass |
| `diag_photon_plus_vertex_v0` | photon diagonal terms plus plan-30 vertex covariance | `vertex_constraint`, `combined` | `sig_foil_v3:plan34_candidates` | blocked until vertex covariance and convergence audits pass |
| `full_photon_covariance_rnd_v0` | full photon covariance matrix including off-diagonal energy-angle terms | `mass_constraint`, `combined` | dedicated plan-40 full-matrix pull row | cannot replace diagonal model without `DEC-35-COVARIANCE-MODEL` |
| `diagnostic_truth_resolution` | generated resolution labels used only as an evaluator stress test | none in production | Class-B truth-drop rerun | forbidden for fit inputs; output hashes must match after removal |

These ids are row-key examples for the fixture and closure inventory,
not runtime CLI names. The production default remains `raw_only_repro`
until a covariance-model DEC is approved.

The covariance fixture is rejected if truth resolution or generated
four-vector information appears in any fit-input field.

### 1.2 Fit-status contract

Downstream consumers must distinguish a valid raw candidate from an
attempted fit that failed. P.7 rows therefore use the following
status fields:

| Condition | `fit_converged` | `fit_failure_reason` | Downstream rule |
|---|---|---|---|
| fit succeeds | `true` | empty string | fitted four-vectors may be consumed after DEC approval |
| missing energy/direction covariance | `false` | `missing_covariance` | preserve raw candidate; do not substitute truth resolution |
| numerical minimizer fails | `false` | `minimizer_failed` | preserve raw candidate; count in convergence-rate closure |
| constraint singular or non-physical | `false` | `invalid_constraint` | preserve raw candidate; inspect covariance/model inputs |
| fit intentionally not requested | `false` | `not_run` | raw-baseline row for plan-38 comparison |

Plan 36/37 consumers must prefer fitted quantities only when
`fit_converged = true` and the relevant DEC is approved; otherwise
they consume the raw plan-34 candidate fields.

Initial fit-failure examples:

| `fit_failure_case_id` | Trigger condition | Required row values | Closure/accounting rule |
|---|---|---|---|
| `missing_one_photon_covariance` | either photon lacks finite `energy_sigma_mev`, `theta_sigma_rad`, or `phi_sigma_rad` | `fit_converged = false`, `fit_failure_reason = missing_covariance`, fitted columns null | counts in `missing_covariance_rate`; raw candidate remains available |
| `singular_covariance_matrix` | covariance matrix is non-invertible or has non-positive variance | `fit_converged = false`, `fit_failure_reason = invalid_constraint`, fitted columns null | blocks covariance-model promotion until plan-40 pull row explains it |
| `minimizer_iteration_limit` | numerical minimizer exceeds iteration or tolerance budget | `fit_converged = false`, `fit_failure_reason = minimizer_failed`, fitted columns null | counts against convergence-rate threshold in §5 |
| `combined_fit_not_authorised` | combined mode requested before mass-only and vertex-only DECs pass | `fit_converged = false`, `fit_failure_reason = not_run`, raw values preserved | diagnostic row only; cannot feed plan-36/37 fitted fields |

Failure rows are first-class denominator rows. They are not dropped from
closure tables, and no downstream plan may fill missing fitted columns
from truth or from the raw candidate under the fitted-column names.

### 1.3 Machine-readable P.7 fit fixture

The P.7 fixture stores one row per raw plan-34 candidate and preserves
raw values even when a fit fails:

| Field | Required content | Review rule |
|---|---|---|
| `event_id`, `fit_input_candidate_key` | stable join key from §1.4 | identical across raw, fitted, and failure rows |
| `photon1_id`, `photon2_id`, `pairing_method_id` | raw candidate provenance | must match the consumed plan-34 fixture |
| `fit_mode` | `raw_only`, `mass_constraint`, `vertex_constraint`, or `combined` | approved mode required before downstream use |
| `covariance_model_id`, `resolution_model_id` | fit input uncertainty tags | `missing_covariance` if absent or invalid |
| `raw_mass`, `raw_opening_angle_deg`, `raw_total_energy` | pre-fit observables | never overwritten by fitted values |
| `fit_mass`, `fit_pi0_px_py_pz_e` | fitted observables | null unless `fit_converged = true` |
| `fit_chi2`, `fit_ndf`, `fit_probability` | fit-quality outputs | consumed by plan 37 only after DEC approval |
| `fit_converged`, `fit_failure_reason` | status fields from §1.2 | failure rows remain in denominator audits |
| `fit_dec_id` | approving or draft DEC | required before fitted values replace raw variables |

Fixture review verifies that failed fits keep the raw candidate available,
that no truth four-vector or generated π⁰ id enters the fit inputs, and
that fit-quality fields are null rather than invented when the fit did
not converge.

Initial fit-mode examples:

| `fit_mode_id` | `fit_mode` | Required inputs | Expected status before DEC | Downstream rule |
|---|---|---|---|---|
| `raw_only_repro` | `raw_only` | plan-34 raw candidate fields | `not_run` fit with raw values preserved | Ch 8 reproduction baseline |
| `mass_constraint_diag_v0` | `mass_constraint` | two photons plus valid energy/direction covariance | diagnostic until §5 closure and `DEC-35-FIT-MODE` | compare mass-width improvement only |
| `vertex_constraint_diag_v0` | `vertex_constraint` | plan-30 vertex/covariance plus photon covariance | diagnostic until vertex covariance closure | compare event-level fit stability |
| `combined_fit_diag_v0` | `combined` | mass and vertex inputs both valid | blocked until simpler fits pass separately | no plan-36/37 consumption |

These ids are method examples, not executable CLI names.

### 1.4 Current-to-target fit input key

The current raw candidate table from `find_pi0_candidates`
(`photon.py:204-263`) has `event_id`, `photon1_id`, and `photon2_id`
but no explicit candidate id or fit-input key. Before P.7 runs, the
bridge must construct a deterministic `fit_input_candidate_key` from
`event_id`, the ordered photon ids, the plan-34 pairing method id, and
the cut-config id. That key is the join surface for raw, fitted, and
fit-failure rows; it must not include truth parentage, generated π⁰
ids, or row order after filtering.

### 1.5 A+ citation audit for current raw-candidate baseline

Current-source claims in §1 and §4 were re-checked against the L3
worktree before this plan was committed:

| Cited contract | Verifier evidence | Status |
|---|---|---|
| raw π⁰ candidate table and absence of fit columns | `def find_pi0_candidates` resolves at `photon.py:204`, inside the cited `photon.py:204-263` range. | keep citation |

Plan 35 does not specify a runtime CLI command, and it does not cite the
removed legacy split-study files. Any future fit-study CLI row must pass
the L3 `--help` verifier before this plan cites it.

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

### 5.1 Machine-readable fit closure fixture

Each fit mode writes one closure-result row per dataset and covariance
configuration:

| Field | Required content | Review rule |
|---|---|---|
| `fit_mode_id`, `covariance_model_id` | mass-only, vertex-only, combined, or raw baseline plus covariance tag | must match §1 fixture fields |
| `dataset_id` | synthetic π⁰ closure or `sig_foil_v3` | both controlled and in-sample rows required before DEC approval |
| `n_candidates`, `n_converged` | denominator and converged count | convergence rate must be computable |
| `raw_mass_width_mev`, `fit_mass_width_mev` | paired width comparison | verifies the §5 improvement threshold |
| `pull_mean`, `pull_width` | vector or summary pull metrics | compared to plan-40 tolerance |
| `chi2_ks_pvalue` | χ² goodness-of-fit check | must exceed the §5 threshold for production use |
| `ranking_change_rate` | fraction whose candidate ordering changes | required before plan-37 can consume fit quality |
| `missing_covariance_rate` | sparse-covariance fallback fraction | must match §1.1/§1.2 failure accounting |
| `class_b_drop_hash` | rerun artifact without truth labels | fit output and convergence hashes must match |
| `closure_status` | `pass`, `fail`, or `diagnostic_only` | only `pass` rows may support fitted production values |

Diagnostic rows may compare raw and fitted values, but raw π⁰ candidates
remain the baseline until the corresponding DEC is approved.

Required closure row-key inventory:

| `dataset_id` | Sample role | Required row purpose | Acceptance guard |
|---|---|---|---|
| `cal_singlegamma_v1:synthetic_pi0_pairs` | controlled π⁰ mass-constraint sample | raw-vs-fit width improvement and pull calibration | width, pull, convergence, and χ² metrics present |
| `sig_foil_v3:plan34_candidates` | in-sample raw π⁰ candidates | production-topology fit stability and ranking changes | convergence rate, ranking-change rate, and Class-B drop hash present |
| `sig_foil_v3:missing_covariance_sideband` | sparse covariance fallback audit | `missing_covariance` accounting and raw-candidate preservation | missing-covariance rate matches §1.2 status rows |

The inventory defines the minimum closure components. It does not approve
fitted values for plan 36/37 until measured §5.1 rows and DEC evidence
are attached.

### 5.2 Decision-log stubs for fit use

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

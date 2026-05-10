---
id: 36_subsystem_event_variables
title: Subsystem — event variables (leaves E.1–E.9)
version: 0.1
status: draft
owner: Combined Performance
depends_on: [00_README, 24_reconstruction_question_tree, 29_subsystem_charged_pid, 33_subsystem_photon_object, 34_subsystem_pi0_pairing, 35_subsystem_kinematic_fit, 38_truth_substitution_ladder, 40_closure_and_pulls]
outputs:
  - {path: docs/rebuild_plans/36_subsystem_event_variables.md, schema: this file}
acceptance:
  - {test: every variable has a name, formula, units, Class, ladder leaf, method: §2 table, pass_when: complete}
  - {test: Fox-Wolfram moments and thrust added alongside sphericity, method: §2 table, pass_when: present}
  - {test: visible invariant mass closure on signal sample within plan 40 tolerance, method: closure plot, pass_when: pass}
risks:
  - {risk: per-hemisphere split assumes detector orientation; off-axis events misclassified, mitigation: §3 hemisphere convention documented}
estimated_effort: M
last_updated: 2026-05-09
---

# Subsystem — event variables

*Charter.* Owns leaves E.1–E.9. Computes per-event observables that
feed the selection (plan 37), the truth-substitution ladder (plan
38), the analysis-level studies (plans 41–46), and the reviewer
defence package (plan 50).

## 1. Inputs

- charged-object table (plan 29)
- photon-object table (plan 33)
- π⁰ candidate table (plan 34, optionally plan-35 fitted)
- raw scintillator and lead-glass hits (plan 09)

All Class A.

## 2. Per-leaf variable schema and current evidence

Each row is Class A in production; truth labels enter only the closure
comparison in §5. Current source line references come from plan 08
§3.6.2 unless marked new.

| Leaf | Output column(s) | Formula / decision rule | Units | Current source citation | Ladder status |
|---|---|---|---|---|---|
| E.1 | `calorimeter_edep` | `Σ scintillator eDep + Σ lead-glass eDep` | MeV | `summarize_events` sums raw calorimeter hits (`reconstruction.py:906-1032`) | baseline |
| E.2 | `upper/lower_scintillator_edep`, `upper/lower_leadglass_edep` | split raw cal energy by `y > 0` / `y < 0` | MeV | hemisphere sums are emitted by `summarize_events` (`reconstruction.py:906-1032`) | baseline |
| E.3 | `*_longitudinal_energy`, `calorimeter_longitudinal_energy` | `Σ E_i z_i / r_i` | MeV | `_directional_energy` computes the ratio (`reconstruction.py:226-246`); `summarize_events` emits columns (`reconstruction.py:906-1032`) | baseline |
| E.4 | `*_transverse_energy`, `calorimeter_transverse_energy` | `Σ E_i sqrt(x_i² + y_i²) / r_i` | MeV | same as E.3 | baseline |
| E.5 | `sphericity` | `1.5 * (λ₁ + λ₂)` from normalized momentum tensor | dimensionless | `_sphericity` computes the shape (`reconstruction.py:839-850`); `summarize_events` emits it (`reconstruction.py:906-1032`) | baseline |
| E.6 | `fox_wolfram_h0`, `fox_wolfram_h2`, `thrust` | pairwise Legendre moments and thrust axis over reconstructed objects | dimensionless | new variables; no current columns in plan 08 output schema | added |
| E.7 | `visible_invariant_mass` | `√((Σ E_i)² - |Σ p_i|²)` from charged + photon four-vectors | MeV | `_visible_invariant_mass` computes mass (`reconstruction.py:853-874`); `summarize_events` emits it (`reconstruction.py:906-1032`) | baseline |
| E.8 | `calorimeter_timing_edep`, `calorimeter_out_of_time_edep` plus detector splits | sum hits inside/outside timing windows | MeV | `annotate_timing_windows` marks hit windows (`reconstruction.py:265-340`); `summarize_events` emits sums (`reconstruction.py:906-1032`) | baseline |
| E.9 | `n_charged_objects`, `n_photon_like`, `n_pi0`, `pion_multiplicity` | counts reconstructed objects and selected π⁰ rows | int | object counts are emitted by `summarize_events` (`reconstruction.py:906-1032`) | baseline |

Per-leaf **inputs** are the tables in §1; **outputs** are the listed
`events.csv` columns. E.6 is added by this plan because the licentiate
used only sphericity; plan 38 scores it as an optional discriminator.

### 2.1 Event-shape formulas for E.5/E.6

For every event-shape calculation, the object list is the
reconstructed charged/photon/π⁰ list after upstream validity gates.
Truth momenta and truth multiplicities are evaluator-only closure
labels.

- **Sphericity tensor (E.5):**
  `S_ab = Σ_i p_{i,a} p_{i,b} / Σ_i |p_i|²`. Sort eigenvalues
  `λ1 ≤ λ2 ≤ λ3`; report `sphericity = 1.5 * (λ1 + λ2)`.
- **Fox-Wolfram moments (E.6):**
  `H_l = Σ_ij |p_i||p_j| P_l(cos θ_ij) / (Σ_i |p_i|)²` for
  `l ∈ {0, 2, 4}`. `H_0` is retained as a normalization sentinel;
  `H_2` and `H_4` are the planned discriminants.
- **Thrust (E.6):**
  `T = max_n Σ_i |p_i · n| / Σ_i |p_i|`. The implementation should
  use a deterministic seed-axis scan over object directions and their
  hemispheric sums, then record the selected axis convention.
- **Sparse events:** if fewer than two valid reconstructed objects or
  zero total momentum norm is available, emit finite sentinel values
  plus `event_shape_valid = false`; do not substitute truth objects.

## 3. Hemisphere convention

The detector is symmetric about z=0 (the foil). "Upper" / "lower"
is defined by the sign of `y` (vertical) for the licentiate. Plan
36 v0.1 retains this convention; plan 47 ledger explicitly cites it
when quoting hemispheric numbers.

## 4. Alternative comparison matrix

| Leaf(s) | Candidate | Decision rule | Current/source citation | Class-A status | Comparison metric |
|---|---|---|---|---|---|
| E.1/E.2 | **Raw hit sums (current)** | Sum raw scintillator and lead-glass `eDep`, with `y` hemisphere split. | `summarize_events` energy sums (`reconstruction.py:906-1032`). | Production-eligible baseline. | Stability vs calibration changes; N-1 selection impact. |
| E.1/E.2 | **Calibrated object sums** | Sum calibrated charged/photon/π⁰ objects rather than raw hits. | Uses plan-33/35 outputs instead of raw hit sums. | Eligible after calibration closure. | Visible-mass bias and selection separation. |
| E.3/E.4 | **Hit-directional energy (current)** | Use hit position ratios `z/r` and `sqrt(x²+y²)/r`. | `_directional_energy` (`reconstruction.py:226-246`). | Production-eligible. | Agreement with object-vector projection; sensitivity to hit noise. |
| E.5/E.6 | **Sphericity-only (current thesis)** | Use normalized momentum-tensor eigenvalues. | `_sphericity` (`reconstruction.py:839-850`). | Production-eligible. | Cut-flow reproduction and ROC AUC. |
| E.5/E.6 | **Expanded event-shape set** | Add Fox-Wolfram moments and thrust to sphericity. | New plan-36 variables. | Eligible; no truth inputs. | ROC/N-1 gain over sphericity-only. |
| E.7 | **Raw visible mass (current)** | Charged fixed masses plus massless photons. | `_visible_invariant_mass` (`reconstruction.py:853-874`). | Production-eligible. | Bias/pull vs truth visible mass. |
| E.7 | **Fit-aware visible mass** | Prefer plan-35 fitted π⁰/photon four-vectors when fit converged. | Consumes plan-35 outputs. | Eligible after fit closure. | Bias/resolution improvement and selection stability. |
| E.8 | **Fixed timing windows (current)** | Use config timing resolutions and pion β bounds. | `annotate_timing_windows` (`reconstruction.py:265-340`). | Production-eligible with calibrated constants. | In/out-of-time separation and cosmic rejection. |
| E.9 | **Raw object counts (current)** | Count charged, photon-like, and selected π⁰ rows. | `summarize_events` emits object counts (`reconstruction.py:906-1032`). | Production-eligible. | Multiplicity closure and sensitivity to upstream object duplicates. |

Plan 38 should score added variables (especially E.6 and fit-aware E.7)
against the thesis baseline without deleting the reproduced Ch 10 inputs.

## 5. Closure-test specification

1. **Dataset id:** run `sig_foil_v3` for signal-visible-mass closure
   and the plan-41 signal/background samples for N-1 stability of all
   E.1–E.9 variables. Truth four-vectors are evaluator-only labels.
2. **Observable:** every §2 output column, with primary closure on
   visible invariant mass; additionally monitor hemisphere sums,
   timing in/out-of-window energy, event-shape variables, and object
   multiplicities for finite values and expected ranges.
3. **Fitter / estimator:** fit reco-minus-truth visible-mass residuals
   with a Gaussian core and bootstrap bias/width uncertainty; use
   Kolmogorov or χ² shape comparisons for added E.6 variables and
   Wilson intervals for multiplicity agreement categories.
4. **Pass criterion:** visible-mass bias `< 50 MeV`, pull width in
   `[0.8, 1.2]`, all required E.1–E.9 output columns populated, no
   non-finite values outside explicitly allowed sparse cases, and
   E.6 variables recorded in plan 38 before any selection use.
5. **Audit hook:** rerun with upstream diagnostic truth columns
   dropped. Event-variable outputs must be unchanged except for
   closure-only comparison columns.

### 5.1 Decision-log stubs for variable use

Plan 36 may add variables, change the source of an existing variable,
or make an event-shape variable eligible for plan-37 selection. Those
methodology choices need plan-05 DEC approval before they influence
quoted efficiencies:

| DEC stub | Decision to freeze | Required evidence before approval |
|---|---|---|
| `DEC-36-HEMISPHERE-CONVENTION` | Retain `y > 0` / `y < 0` as the upper/lower convention for all Ch 10 reproductions | plan-47 reproduction row showing the convention matches the licentiate cut-flow |
| `DEC-36-EVENT-SHAPE-FEATURES` | Permit Fox-Wolfram moments and thrust to enter plan-37 or plan-57 feature sets | plan-38 ladder row plus plan-41 N-1/ROC evidence against sphericity-only |
| `DEC-36-VISIBLE-MASS-SOURCE` | Choose raw visible mass vs plan-35 fit-aware visible mass as the production S.3 input | §5 closure plus plan-35 approved fit-mode DEC |
| `DEC-36-SPARSE-SENTINELS` | Freeze sentinel values and validity flags for sparse or underpopulated events | audit table proving sparse sentinels do not pass selection accidentally |

Until approval, new E.6 variables and fit-aware E.7 are recorded for
ladder studies but do not replace the Ch 10 reproduction inputs.

## 6. Acceptance criteria

- §2 table complete; every variable produced.
- E.6 Fox-Wolfram and thrust added.
- §5 closure passes.
- Plan 38 ladder rows for E.1–E.9 populated.

## 7. Dependencies

- **24, 29, 33, 34, 35, 38, 40** — inputs.
- *Consumed by:* plan 37 (selection), plan 41 (N-1 / ROC), plan 38
  (ladder).

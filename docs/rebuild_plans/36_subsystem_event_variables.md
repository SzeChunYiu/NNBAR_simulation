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
last_updated: 2026-05-10
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
| E.1 | `calorimeter_edep` | `Σ scintillator eDep + Σ lead-glass eDep` | MeV | `summarize_events` sums raw calorimeter hits (`vertex.py:322-447`) | baseline |
| E.2 | `upper/lower_scintillator_edep`, `upper/lower_leadglass_edep` | split raw cal energy by `y > 0` / `y < 0` | MeV | hemisphere sums are emitted by `summarize_events` (`vertex.py:322-447`) | baseline |
| E.3 | `*_longitudinal_energy`, `calorimeter_longitudinal_energy` | `Σ E_i z_i / r_i` | MeV | `_directional_energy` computes the ratio (`vertex.py:48-67`); event rows emit the columns | baseline |
| E.4 | `*_transverse_energy`, `calorimeter_transverse_energy` | `Σ E_i sqrt(x_i² + y_i²) / r_i` | MeV | `_directional_energy` computes the ratio (`vertex.py:48-67`); event rows emit the columns | baseline |
| E.5 | `sphericity` | `1.5 * (λ₁ + λ₂)` from normalized momentum tensor | dimensionless | `_sphericity` computes the shape (`vertex.py:255-266`); event rows emit it | baseline |
| E.6 | `fox_wolfram_h0`, `fox_wolfram_h2`, `fox_wolfram_h4`, `thrust`, `event_shape_valid` | pairwise Legendre moments and thrust axis over reconstructed objects | dimensionless / bool | new variables; no current columns in plan 08 output schema | added |
| E.7 | `visible_invariant_mass` | `√((Σ E_i)² - |Σ p_i|²)` from charged + photon four-vectors | MeV | `_visible_invariant_mass` computes mass (`vertex.py:269-290`); event rows emit it | baseline |
| E.8 | `calorimeter_timing_edep`, `calorimeter_out_of_time_edep` plus detector splits | sum hits inside/outside timing windows | MeV | `annotate_timing_windows` marks hit windows (`vertex.py:86-160`); event rows emit sums | baseline |
| E.9 | `n_charged_objects`, `n_photon_like`, `n_pi0`, `pion_multiplicity` | counts reconstructed objects and selected π⁰ rows | int | object counts are emitted by `summarize_events` (`vertex.py:322-447`) | baseline |

Per-leaf **inputs** are the tables in §1; **outputs** are the listed
`events.csv` columns. E.6 is added by this plan because the licentiate
used only sphericity; plan 38 scores it as an optional discriminator. The E.6 schema includes `fox_wolfram_h4` because §2.1 defines the retained moments as `l ∈ {0, 2, 4}`.

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

### 2.2 A+ citation audit for current event-variable baseline

Current-source claims in §2 and §4 were re-checked against the L3
worktree before this plan was committed:

| Cited contract | Verifier evidence | Status |
|---|---|---|
| event-row assembly and raw sums/counts | `def summarize_events` resolves at `vertex.py:322`, inside the cited `vertex.py:322-447` range. | keep citation |
| directional energy helper for E.3/E.4 | `def _directional_energy` resolves at `vertex.py:48`, inside the cited `vertex.py:48-67` range. | keep citation |
| sphericity helper for E.5 | `def _sphericity` resolves at `vertex.py:255`, inside the cited `vertex.py:255-266` range. | keep citation |
| visible-mass helper for E.7 | `def _visible_invariant_mass` resolves at `vertex.py:269`, inside the cited `vertex.py:269-290` range. | keep citation |
| timing-window helper for E.8 | `def annotate_timing_windows` resolves at `vertex.py:86`, inside the cited `vertex.py:86-160` range. | keep citation |

Plan 36 does not specify a runtime CLI command, and it does not cite the
removed legacy split-study files. Any future event-variable study CLI row
must pass the L3 `--help` verifier before this plan cites it.

### 2.3 Machine-readable E.1-E.9 event-variable fixture

The event-variable fixture stores one row per event after upstream object
validity gates and before plan-37 selection:

| Field | Required content | Review rule |
|---|---|---|
| `event_id` | stable event key | joins to plan-31 through plan-35 fixtures |
| `calorimeter_edep`, `upper_scintillator_edep`, `lower_scintillator_edep`, `upper_leadglass_edep`, `lower_leadglass_edep` | E.1/E.2 energy sums in MeV | non-negative and recomputable from source rows |
| `*_longitudinal_energy`, `*_transverse_energy` | E.3/E.4 directional components | finite; uses reconstructed hit positions only |
| `sphericity`, `event_shape_valid` | E.5 validity-gated shape output | sparse cases must fail explicitly |
| `fox_wolfram_h0`, `fox_wolfram_h2`, `fox_wolfram_h4`, `thrust` | E.6 optional event-shape features | disabled rows carry sentinel values plus `event_shape_valid = false` |
| `visible_invariant_mass` | E.7 visible mass in MeV | null/invalid only for explicitly sparse events |
| `calorimeter_timing_edep`, `calorimeter_out_of_time_edep` | E.8 timing-window sums | derived from timing annotations, not truth time |
| `n_charged_objects`, `n_photon_like`, `n_pi0`, `pion_multiplicity` | E.9 object counts | must match upstream fixture rows after selection gates |
| `event_variable_method_id` | source/method tag for the fixture | changes require the relevant DEC in §5.1 |

Fixture review recomputes raw sums, object counts, and validity flags from
upstream fixtures. Dropping diagnostic truth/provenance columns may remove
closure labels but must not change any production event variable.

### 2.4 Current-to-target event-variable field map

| Leaf(s) | Current emitted field(s) | Target fixture delta | Source evidence |
|---|---|---|---|
| E.1/E.2 | raw scintillator, lead-glass, calorimeter, and hemisphere energy sums | retain current names and add the shared `event_variable_method_id` | `summarize_events` (`vertex.py:322-447`) |
| E.3/E.4 | detector-level and calorimeter-level longitudinal/transverse energies | retain current names; require finite recomputation from hit positions | `_directional_energy` plus `summarize_events` (`vertex.py:48-67`, `vertex.py:322-447`) |
| E.5 | `sphericity` | add `event_shape_valid` so sparse-event sentinels are reviewable | `_sphericity` (`vertex.py:255-266`) |
| E.6 | no current production columns | add Fox-Wolfram moments and thrust as disabled-until-approved columns | new plan-36 target fields |
| E.7 | `visible_invariant_mass` | retain current name and allow null only for declared sparse cases | `_visible_invariant_mass` (`vertex.py:269-290`) |
| E.8 | timing and out-of-time energy sums for scintillator, lead-glass, and calorimeter | retain current names; require derivation from timing annotations | `annotate_timing_windows` plus `summarize_events` (`vertex.py:86-160`, `vertex.py:322-447`) |
| E.9 | charged, photon-like, π⁰, pion, proton, PMT, and electron-pair counts | fixture review checks the listed production counts against upstream rows | `summarize_events` (`vertex.py:322-447`) |

This map is the implementation checklist: a future code row may add target
columns before DEC approval, but plan-37 may not consume new E.6 or
fit-aware E.7 fields until the relevant §5.2 DEC is signed.

## 3. Hemisphere convention

The detector is symmetric about z=0 (the foil). "Upper" / "lower"
is defined by the sign of `y` (vertical) for the licentiate. Plan
36 v0.1 retains this convention; plan 47 ledger explicitly cites it
when quoting hemispheric numbers.

### 3.1 Machine-readable hemisphere convention fixture

Every event-variable method bundle records the coordinate convention used
for hemisphere-split observables:

| Field | Required content | Review rule |
|---|---|---|
| `hemisphere_convention_id` | stable key, initially `licentiate_y_sign_v1` | referenced by §2.3 event rows and plan-37 inputs |
| `vertical_axis` | `y` | changes require `DEC-36-HEMISPHERE-CONVENTION` |
| `upper_rule` | `y > 0` | must match E.2/E.8 split rows |
| `lower_rule` | `y < 0` | must match E.2/E.8 split rows |
| `boundary_rule` | hits with `y = 0` recorded in a boundary/count field or deterministic side | no silent double counting |
| `coordinate_frame_source` | detector geometry snapshot or run config id | copied to closure artifacts |
| `decision_dec_id` | `DEC-36-HEMISPHERE-CONVENTION` | draft DEC keeps convention provisional |
| `convention_status` | `draft`, `frozen`, or `blocked` | only frozen rows support final hemispheric claims |

The convention row is rejected if upper/lower energy sums cannot be
recomputed from raw hit positions using the recorded rules.

## 4. Alternative comparison matrix

| Leaf(s) | Candidate | Decision rule | Current/source citation | Class-A status | Comparison metric |
|---|---|---|---|---|---|
| E.1/E.2 | **Raw hit sums (current)** | Sum raw scintillator and lead-glass `eDep`, with `y` hemisphere split. | `summarize_events` energy sums (`vertex.py:322-447`). | Production-eligible baseline. | Stability vs calibration changes; N-1 selection impact. |
| E.1/E.2 | **Calibrated object sums** | Sum calibrated charged/photon/π⁰ objects rather than raw hits. | Uses plan-33/35 outputs instead of raw hit sums. | Eligible after calibration closure. | Visible-mass bias and selection separation. |
| E.3/E.4 | **Hit-directional energy (current)** | Use hit position ratios `z/r` and `sqrt(x²+y²)/r`. | `_directional_energy` (`vertex.py:48-67`). | Production-eligible. | Agreement with object-vector projection; sensitivity to hit noise. |
| E.5/E.6 | **Sphericity-only (current thesis)** | Use normalized momentum-tensor eigenvalues. | `_sphericity` (`vertex.py:255-266`). | Production-eligible. | Cut-flow reproduction and ROC AUC. |
| E.5/E.6 | **Expanded event-shape set** | Add Fox-Wolfram moments and thrust to sphericity. | New plan-36 variables. | Eligible; no truth inputs. | ROC/N-1 gain over sphericity-only. |
| E.7 | **Raw visible mass (current)** | Charged fixed masses plus massless photons. | `_visible_invariant_mass` (`vertex.py:269-290`). | Production-eligible. | Bias/pull vs truth visible mass. |
| E.7 | **Fit-aware visible mass** | Prefer plan-35 fitted π⁰/photon four-vectors when fit converged. | Consumes plan-35 outputs. | Eligible after fit closure. | Bias/resolution improvement and selection stability. |
| E.8 | **Fixed timing windows (current)** | Use config timing resolutions and pion β bounds. | `annotate_timing_windows` (`vertex.py:86-160`). | Production-eligible with calibrated constants. | In/out-of-time separation and cosmic rejection. |
| E.9 | **Raw object counts (current)** | Count charged, photon-like, and selected π⁰ rows. | `summarize_events` emits object counts (`vertex.py:322-447`). | Production-eligible. | Multiplicity closure and sensitivity to upstream object duplicates. |

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

### 5.1 Machine-readable event-variable closure fixture

Each event-variable method bundle writes one closure-result row per
sample and variable group:

| Field | Required content | Review rule |
|---|---|---|
| `event_variable_method_id` | source/method tag from §2.3 | must match the event fixture rows under test |
| `dataset_id` | `sig_foil_v3` or plan-41 signal/background sample | every quoted sample gets a row |
| `variable_group` | E.1/E.2, E.3/E.4, E.5/E.6, E.7, E.8, or E.9 | groups map back to §2 leaves |
| `n_events`, `n_valid_events` | denominator and finite-value count | sparse cases must be counted explicitly |
| `visible_mass_bias_mev`, `visible_mass_pull_width` | E.7 primary closure metrics | required for E.7 rows and fit-aware comparisons |
| `shape_test_statistic`, `shape_test_pvalue` | KS or χ² comparison for distributions | required for added E.6 rows |
| `multiplicity_agreement_rate` | Wilson-interval category agreement | required for E.9 rows |
| `nonfinite_outside_sparse_count` | invalid values outside declared sparse cases | must be zero for production rows |
| `class_b_drop_hash` | rerun artifact without diagnostic truth columns | production event variables must match |
| `closure_status` | `pass`, `fail`, or `diagnostic_only` | only `pass` rows may support plan-37 use |

Rows for new E.6 variables or fit-aware E.7 remain diagnostic until the
matching plan-38 ladder row and §5.2 DEC evidence are present.

### 5.2 Decision-log stubs for variable use

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

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
| E.1 | `calorimeter_edep` | `Σ scintillator eDep + Σ lead-glass eDep` | MeV | `summarize_events` sums raw cal hits (`reconstruction.py:1624–1638`, `1688–1709`) | baseline |
| E.2 | `upper/lower_scintillator_edep`, `upper/lower_leadglass_edep` | split raw cal energy by `y > 0` / `y < 0` | MeV | hemisphere sums at `reconstruction.py:1624–1638` | baseline |
| E.3 | `*_longitudinal_energy`, `calorimeter_longitudinal_energy` | `Σ E_i z_i / r_i` | MeV | `_directional_energy` and event rows (`reconstruction.py:244–264`, `1653–1654`, `1710–1715`) | baseline |
| E.4 | `*_transverse_energy`, `calorimeter_transverse_energy` | `Σ E_i sqrt(x_i² + y_i²) / r_i` | MeV | same as E.3 | baseline |
| E.5 | `sphericity` | `1.5 * (λ₁ + λ₂)` from normalized momentum tensor | dimensionless | `_sphericity` plus event row (`reconstruction.py:1533–1544`, `1728–1729`) | baseline |
| E.6 | `fox_wolfram_h0`, `fox_wolfram_h2`, `thrust` | pairwise Legendre moments and thrust axis over reconstructed objects | dimensionless | new variables; no current columns in plan 08 output schema | added |
| E.7 | `visible_invariant_mass` | `√((Σ E_i)² - |Σ p_i|²)` from charged + photon four-vectors | MeV | `_visible_invariant_mass` (`reconstruction.py:1547–1570`, `1726`) | baseline |
| E.8 | `calorimeter_timing_edep`, `calorimeter_out_of_time_edep` plus detector splits | sum hits inside/outside timing windows | MeV | `annotate_timing_windows` (`reconstruction.py:283–358`) and event sums (`1639–1652`, `1697–1709`) | baseline |
| E.9 | `n_charged_objects`, `n_photon_like`, `n_pi0`, `pion_multiplicity` | counts reconstructed objects and selected π⁰ rows | int | object filtering and row output (`reconstruction.py:1658–1677`, `1716–1724`) | baseline |

Per-leaf **inputs** are the tables in §1; **outputs** are the listed
`events.csv` columns. E.6 is added by this plan because the licentiate
used only sphericity; plan 38 scores it as an optional discriminator.

## 3. Hemisphere convention

The detector is symmetric about z=0 (the foil). "Upper" / "lower"
is defined by the sign of `y` (vertical) for the licentiate. Plan
36 v0.1 retains this convention; plan 47 ledger explicitly cites it
when quoting hemispheric numbers.

## 4. Visible invariant mass closure

On `sig_foil_v3`:

- Reco visible mass: from charged + photon + π⁰ four-vectors.
- Truth visible mass: from `Particle_output` four-vectors of all
  charged π/p and photons attributable to the primary.

Tolerance per plan 40 §2: bias < 50 MeV; pull width ∈ [0.8, 1.2].

## 5. Acceptance criteria

- §2 table complete; every variable produced.
- E.6 Fox-Wolfram and thrust added.
- §4 closure passes.
- Plan 38 ladder rows for E.1–E.9 populated.

## 6. Dependencies

- **24, 29, 33, 34, 35, 38, 40** — inputs.
- *Consumed by:* plan 37 (selection), plan 41 (N-1 / ROC), plan 38
  (ladder).

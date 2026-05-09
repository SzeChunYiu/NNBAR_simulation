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

## 2. Variable inventory

| Leaf | Variable | Formula | Units |
|---|---|---|---|
| E.1 | total calorimeter energy | `Σ scint_eDep + Σ LG_eDep` | MeV |
| E.2.1 | upper scint energy | per-hemisphere split | MeV |
| E.2.2 | lower scint energy | per-hemisphere split | MeV |
| E.2.3 | upper LG energy | per-hemisphere split | MeV |
| E.2.4 | lower LG energy | per-hemisphere split | MeV |
| E.3 | longitudinal energy `EL` | `Σ E_i cos α_i` (α from object direction vs +z) | MeV |
| E.4 | transverse energy `ET` | `Σ E_i sin α_i` | MeV |
| E.5 | sphericity | tensor eigenvalue formula (PDG) | dimensionless |
| E.6.1 | Fox-Wolfram H₀ | `Σ \|p_i\|\|p_j\| P_ℓ(cos θ_ij) / E_vis²`, ℓ=0 | dimensionless |
| E.6.2 | Fox-Wolfram H₂ | same with ℓ=2 | dimensionless |
| E.6.3 | thrust | `max_n̂ Σ \|p_i · n̂\| / Σ \|p_i\|` | dimensionless |
| E.7 | visible invariant mass | `√((Σ E_i)² - \|Σ p_i\|²)` | MeV |
| E.8.1 | in-time energy | hits within Ch 7 timing window | MeV |
| E.8.2 | out-of-time energy | hits outside window | MeV |
| E.9.1 | charged multiplicity | count of charged objects | int |
| E.9.2 | photon multiplicity | count of photon objects | int |
| E.9.3 | π⁰ multiplicity | count of selected π⁰ candidates | int |

E.6 (Fox-Wolfram + thrust) is *added* by this plan; the licentiate
used only sphericity. They are extra discriminants, scored on the
ladder.

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

---
id: 34_subsystem_pi0_pairing
title: Subsystem — π⁰ pairing (leaves P.5, P.6)
version: 0.1
status: draft
owner: EM-Object POG
depends_on: [00_README, 24_reconstruction_question_tree, 33_subsystem_photon_object, 38_truth_substitution_ladder, 40_closure_and_pulls]
outputs:
  - {path: docs/rebuild_plans/34_subsystem_pi0_pairing.md, schema: this file}
acceptance:
  - {test: π⁰ mass peak μ within 5 MeV of PDG 134.977 MeV on cal sample, method: §2 closure, pass_when: pass}
  - {test: every selection cut (mass window, total E, scint E, LG E, LG fraction, opening angle) appears as an individual passes_* column, method: schema review, pass_when: present}
  - {test: accidental rate measured on cal_singlepion_mip_v1 (no π⁰), method: §3 fake-rate, pass_when: rate documented}
risks:
  - {risk: combinatorial pairing scales O(N²) and may pick wrong partner in high-multiplicity events, mitigation: §3 best-mass-match heuristic + kinematic-fit χ² (plan 35)}
estimated_effort: M
last_updated: 2026-05-09
---

# Subsystem — π⁰ pairing

*Charter.* Owns leaves P.5 (pairing) and P.6 (accidental
rejection). Forms π⁰ candidates from photon objects.

## 1. Pairing rule

For each event:

1. List photon objects from plan 33.
2. Form all pairs `(γ_i, γ_j)` with `i < j`.
3. For each pair compute: invariant mass `M`, total energy `E`,
   opening angle `α`, scintillator energy `Σ_scint`, lead-glass
   energy `Σ_LG`, lead-glass fraction `Σ_LG / (Σ_LG + Σ_scint)`.

Each pair becomes a candidate row.

## 2. Selection per candidate (thesis Ch 8 defaults from
`reconstruction.py` `ReconstructionConfig`):

| Cut column | Default | Source |
|---|---|---|
| `passes_mass_window` | 100 ≤ M ≤ 180 MeV | thesis Ch 8 |
| `passes_total_energy` | E ≤ 720 MeV | thesis Ch 8 |
| `passes_scintillator_energy` | Σ_scint ≤ 250 MeV | thesis Ch 8 |
| `passes_leadglass_energy` | Σ_LG ≤ 980 MeV | thesis Ch 8 |
| `passes_leadglass_fraction` | LG_fraction ≥ 0.55 | thesis Ch 8 |
| `passes_opening_angle` | α ≥ 30° | thesis Ch 8 |

Strict `passes_selection` = AND of all six.

Per `reconstruction.md` §"pi0 candidates", each candidate also carries
diagnostic columns (`selection_failure_reasons`, source-track
aliases, charged-match class, prompt timing) for validation; these
are `@diagnostic_only` per plan 01.

Closure on truth π⁰s: peak μ within 5 MeV of 134.977 MeV; π⁰-mass
σ < 25 MeV after kinematic fit (plan 35).

## 3. Accidental rejection (P.6)

Accidentals are pairs where the two photons came from different
parents in truth. Two ways to bound the accidental rate:

- *Truth-side* (validation only): pairs whose truth daughters do
  not share a π⁰ parent in the `Interaction` table → `@validation_only`
  metric.
- *Reco-side* (production): kinematic-fit χ² (plan 35); high χ²
  rejects accidentals.

Plan 47 ledger quotes both.

## 4. Acceptance criteria

- §2 individual passes_* columns + `passes_selection`.
- §2 closure passes.
- §3 accidental rate produced for at least the licentiate signal
  sample.

## 5. Dependencies

- **24, 33, 38, 40** — inputs.
- *Consumed by:* plan 35 (kinematic fit), plan 36 (event variables),
  plan 37 (selection), plan 38 (ladder).

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

## 1. Leaf P.5/P.6 input/output schema and pairing rule

Leaf P.5/P.6: photon objects → π⁰ candidates and accidental tags

- **Inputs (production, Class A only):** plan-33 photon objects with
  `event_id`, `object_id`, `ux/uy/uz`, `energy_mev` (or
  `total_energy` in the current table), `leadglass_edep`,
  `scintillator_edep`, `leadglass_fraction`, and P.2 neutral-pass
  status. Plan-35 fit quantities may be joined downstream, not used
  to form raw pairs.
- **Current implementation evidence:** plan 08 maps π⁰ pairing to
  `find_pi0_candidates` (`reconstruction.py:1316–1530`). It declares
  the current output schema at `reconstruction.py:1322–1365`, forms
  unordered neutral photon pairs at `reconstruction.py:1406–1409`,
  computes opening angle, mass, energy sums, and lead-glass fraction
  at `reconstruction.py:1410–1421`, and applies the six configured
  selection booleans at `reconstruction.py:1422–1427`.
- **Decision rule:** for each event, list photon objects from plan 33,
  form all pairs `(γ_i, γ_j)` with `i < j`, compute invariant mass
  `M`, total energy `E`, opening angle `α`, `Σ_scint`, `Σ_LG`, and
  `Σ_LG / (Σ_LG + Σ_scint)`, then evaluate the cut columns in §2.
- **Outputs:** one row per pair with photon ids, `mass`,
  `opening_angle_deg`, `total_energy`, `leadglass_edep`,
  `scintillator_edep`, `leadglass_fraction`, each `passes_*` cut
  column from §2, strict `passes_selection`, and
  `selection_failure_reasons`. Diagnostic-only provenance columns
  copied from plan 33 may be written for fake/root-cause studies.
- **Truth-use boundary:** truth parentage defines validation labels
  for accidental-rate measurement only; it must not remove or accept
  a production candidate.

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

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

| Cut column | Default | Thesis source | Code citation |
|---|---|---|---|
| `passes_mass_window` | 100 ≤ M ≤ 180 MeV | thesis Ch 8 | config `pi0_mass_min/max` (`reconstruction.py:29–35`); flag block `1422–1427` |
| `passes_total_energy` | E ≤ 720 MeV | thesis Ch 8 | config `pi0_total_energy_max` (`reconstruction.py:29–35`); flag block `1422–1427` |
| `passes_scintillator_energy` | Σ_scint ≤ 250 MeV | thesis Ch 8 | config `pi0_scint_energy_max` (`reconstruction.py:29–35`); flag block `1422–1427` |
| `passes_leadglass_energy` | Σ_LG ≤ 980 MeV | thesis Ch 8 | config `pi0_leadglass_energy_max` (`reconstruction.py:29–35`); flag block `1422–1427` |
| `passes_leadglass_fraction` | LG_fraction ≥ 0.55 | thesis Ch 8 | config `pi0_leadglass_fraction_min` (`reconstruction.py:29–35`); flag block `1422–1427` |
| `passes_opening_angle` | α ≥ 30° | thesis Ch 8 | config `pi0_opening_angle_min_deg` (`reconstruction.py:29–35`); flag block `1422–1427` |

Strict `passes_selection` = AND of all six.

Per `reconstruction.md` §"pi0 candidates", each candidate also carries
diagnostic columns (`selection_failure_reasons`, source-track
aliases, charged-match class, prompt timing) for validation; these
are `@diagnostic_only` per plan 01.

Closure on truth π⁰s is specified in §5; plan 35 separately
measures the post-fit mass resolution.

## 3. Accidental rejection (P.6)

Accidentals are pairs where the two photons came from different
parents in truth. Two ways to bound the accidental rate:

- *Truth-side* (validation only): pairs whose truth daughters do
  not share a π⁰ parent in the `Interaction` table → `@validation_only`
  metric.
- *Reco-side* (production): kinematic-fit χ² (plan 35); high χ²
  rejects accidentals.

Plan 47 ledger quotes both.

## 4. Alternative comparison matrix

| Leaf | Candidate | Decision rule | Current/source citation | Class-A status | Comparison metric |
|---|---|---|---|---|---|
| P.5 | **All unordered pairs (current)** | Pair every neutral photon pair once by object-id ordering. | Current implementation at `reconstruction.py:1406–1409` (plan 08 §3.5.3). | Production-eligible; O(N²). | π⁰ efficiency, candidate multiplicity, runtime. |
| P.5 | **Best mass match per photon** | Build all pairs, then greedily keep pairs closest to `m_π⁰` without reusing photons. | Replacement after raw pair enumeration. | Eligible; mass threshold DEC required. | Correct-pair efficiency and high-multiplicity fake rate. |
| P.5 | **Kinematic-fit ranked pairing** | Rank raw pairs by plan-35 χ² and mass pull. | Consumes plan-35 fit outputs after raw pair construction. | Eligible once fit covariance is validated. | Mass resolution and accidental rejection at fixed efficiency. |
| P.6 | **Six-cut selection (current)** | Apply mass, total-energy, scintillator-energy, lead-glass-energy, LG-fraction, and opening-angle cuts. | Config defaults at `reconstruction.py:29–35`; booleans at `1422–1427`; failure reasons at `1428–1437`, `1519–1526`. | Production-eligible; thresholds must be thesis-cited or DEC-logged. | Signal efficiency, fake rate, N-1 sensitivity. |
| P.6 | **Prompt-timing veto** | Require photon time residuals near zero before accepting prompt π⁰s. | Current diagnostic prompt timing at `reconstruction.py:1390–1402`, `1451–1469`, `1508–1512`. | Eligible after timing calibration and DEC. | Accidental-rate reduction vs efficiency loss. |
| P.6 | **Truth-parent label** | Reject pairs whose photons do not share a truth π⁰ parent. | Validation-only diagnostic inherited from source aliases. | Not production-eligible. | Upper-bound accidental rejection only. |

Plan 38 records P.5 pairing and P.6 accidental-rejection choices
separately so a better ranking can be adopted without changing the
thesis six-cut baseline.

## 5. Closure-test specification

1. **Dataset ids:** use `sig_foil_v3` truth π⁰ decays for signal
   closure and `cal_singlepion_mip_v1` as the no-π⁰ accidental
   sample; truth parentage labels are evaluator-only.
2. **Observable:** raw and selected `M_γγ`, opening angle, selected
   candidate multiplicity, per-cut pass fractions, correct-pair
   efficiency, and accidental-pair rate.
3. **Fitter / estimator:** fit the selected `M_γγ` peak with a
   Gaussian core plus sideband background; quote bootstrap uncertainty
   on the peak mean and width, and Wilson intervals for accidental
   rates.
4. **Pass criterion:** selected mass peak `|μ - 134.977 MeV| < 5 MeV`,
   raw selected width `< 35 MeV`, post-plan-35 width `< 25 MeV`, and
   no-π⁰ accidental selected-candidate rate documented with a finite
   confidence interval.
5. **Audit hook:** rerun after dropping photon truth/provenance
   columns. The raw pair list, kinematic quantities, cut booleans, and
   `passes_selection` must be unchanged.

### 5.1 Decision-log stubs for π⁰ pairing and cuts

P.5/P.6 choices change candidate multiplicity and the Ch 8 π⁰
baseline, so threshold or ranking changes require plan-05 approval:

| DEC stub | Decision to freeze | Required evidence before approval |
|---|---|---|
| `DEC-34-PAIRING-RULE` | Retain all unordered pairs or select a best-pair / fit-ranked pairing policy | §5 correct-pair efficiency, candidate multiplicity, and runtime comparison |
| `DEC-34-PI0-CUT-BASELINE` | Freeze the six thesis Ch 8 cuts and their default thresholds as reproduction columns | plan-47 reproduction row plus per-cut pass fractions from §5 |
| `DEC-34-RETUNED-PI0-CUTS` | Approve any mass, energy, fraction, opening-angle, or prompt-timing retune | N-1/ROC evidence and explicit preservation of the Ch 8 baseline columns |
| `DEC-34-ACCIDENTAL-LABELING` | Restrict truth-parent labels to validation-only accidental-rate estimates | plan-01 audit and rerun showing pair/cut outputs unchanged without truth columns |

Until approval, alternative pair rankings and retuned cuts are plan-38
ladder rows only; `passes_selection` remains the Ch 8 reproduction
baseline.

## 6. Acceptance criteria

- §2 individual passes_* columns + `passes_selection`.
- §5 closure passes.
- §3 accidental rate produced for at least the licentiate signal
  sample.

## 7. Dependencies

- **24, 33, 38, 40** — inputs.
- *Consumed by:* plan 35 (kinematic fit), plan 36 (event variables),
  plan 37 (selection), plan 38 (ladder).

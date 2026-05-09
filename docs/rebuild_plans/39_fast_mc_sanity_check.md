---
id: 39_fast_mc_sanity_check
title: Fast-MC inverse closure check
version: 0.1
status: draft
owner: Combined Performance
depends_on: [00_README, 04_statistical_uncertainty, 24_reconstruction_question_tree, 38_truth_substitution_ladder]
inputs: []
outputs:
  - {path: docs/rebuild_plans/39_fast_mc_sanity_check.md, schema: this file}
  - {path: nnbar_reconstruction/fast_mc/, schema: smearing/closure code}
acceptance:
  - {test: smear-truth distributions match reco-only distributions within stated tolerance, method: per-observable closure plot, pass_when: tolerance met for at least visible_invariant_mass and π⁰-mass peak}
risks:
  - {risk: closure passes but reco code has a bias the smearing model also has, mitigation: §3 independent smearing parameters from external references}
estimated_effort: M
last_updated: 2026-05-09
---

# Fast-MC inverse closure check

*Charter.* Independent of the truth-substitution ladder. The ladder
runs reco-only and truth-at-L through the *same reco code*, so a bias
in that code is invisible to the ladder. Fast-MC takes the truth and
*smears* it with parameterised resolutions (independent of reco code),
then asks whether the smeared distribution matches reco-only's
distribution. Disagreement reveals reco-code biases the ladder
cannot.

## 1. Method

For each observable in plan 38 §2:

1. Take truth values from `Particle_output` and `Interaction` tables.
2. Apply parameterised smearing per leaf (Gaussian / non-Gaussian as
   appropriate). Parameters drawn from external references — *not*
   fitted to the reco distribution.
3. Compare smeared distribution to reco-only distribution via:
   - mean offset (bias)
   - RMS ratio (resolution)
   - K–S statistic (shape)

Tolerance: per-observable, recorded in §4. Bias < 5% of nominal
resolution; RMS ratio in [0.8, 1.2]; K–S p > 0.01.

## 2. Smearing parameters

Independent reference sources (not fitted):

| Leaf | Resolution | Source |
|---|---|---|
| V.4 vertex z | σ_z ≈ 5 mm | TPC drift resolution from MIP closure (plan 18) |
| V.4 vertex r | σ_r ≈ 5 mm | TPC pad pitch + MS estimate (plan 15) |
| P.3 photon direction | σ_θ ≈ 30 mrad | shower transverse spread / depth (plan 32) |
| P.4 photon energy | σ_E / E ≈ 5%/√E | lead-glass calibration (plan 18) |
| C.2 dE/dx | σ_dE/dx ≈ 10% | Bethe-Bloch + saturation (plan 27) |
| C.3 range | σ_range ≈ 1 cm | scintillator pitch (plan 28) |

These parameters become Class C constants registered in plan 09.

## 3. Independence guarantee

The smearing parameters are *not* fitted to reco-only distributions.
They are external references. If reco-only is biased, the smeared
distribution differs from it; the closure flags the discrepancy.

If reco-only and smeared agree but disagree with truth (the impossible
case in this design), it would mean both the reco code and the
smearing share the same bias source — flagged as L-class limitation
in plan 01 §6.

## 4. Acceptance criteria per observable

| Observable | Bias tolerance | RMS-ratio range | K–S p |
|---|---|---|---|
| visible invariant mass | ≤ 50 MeV | [0.7, 1.3] | > 0.01 |
| π⁰-mass peak | ≤ 5 MeV | [0.7, 1.3] | > 0.01 |
| sphericity | ≤ 0.05 | [0.7, 1.3] | > 0.01 |
| total calorimeter energy | ≤ 50 MeV | [0.7, 1.3] | > 0.01 |

Tighter tolerances applied as the rebuild matures.

## 5. Risks

- *Risk:* shared bias (see §3) silently passes both reco and smear.
  *Mitigation:* third independent path — analytical truth Monte
  Carlo (plan 13's signal model) computes truth distribution
  directly from the branching table; comparing reco / smear / truth-MC
  catches shared biases.

## 6. Dependencies

- **04, 24, 38** — same as plan 38.
- *Consumed by:* plans 25–37 (each consults the closure for its
  leaf), plan 47, plan 50.

## 7. References

- Standard fast-MC literature (e.g. ATLAS Atlfast II, Delphes).

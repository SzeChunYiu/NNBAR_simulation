---
id: 13_signal_model
title: Signal model — n̄-A annihilation final-state branching
version: 0.1
status: draft
owner: Physics Modeling
depends_on: [00_README, 04_statistical_uncertainty, 12_physics_list_audit]
inputs:
  - {path: NNBAR_Detector/src/core/PrimaryGeneratorAction.cc, schema: primary generator}
  - {path: data/registry/physics_list/, schema: physics list configurations}
outputs:
  - {path: docs/rebuild_plans/13_signal_model.md, schema: this file}
  - {path: data/registry/signal_models/<tag>.yml, schema: per-model branching tables}
acceptance:
  - {test: branching-ratio table is sourced from a cited measurement or theory paper, method: §3 citation review, pass_when: every channel has a citation}
  - {test: at least two alternative branching tables are registered as systematic variations, method: §4 review, pass_when: ≥ 2}
  - {test: simulator output multiplicity distribution closes against the §3 reference within statistical uncertainty, method: per-multiplicity histogram, pass_when: chi-square/dof < 2}
risks:
  - {risk: n̄-A branching is theory-extrapolated from n̄p; uncertainty is irreducible without a measurement, mitigation: §4 alternative models bracket the range; plan 45 propagates}
  - {risk: foil composition (carbon-12) interaction differs from Geant4 default antineutron physics, mitigation: §5 carbon-specific closure test}
estimated_effort: M
last_updated: 2026-05-09
---

# Signal model — n̄-A annihilation final-state branching

*Charter.* The signal is antineutron annihilation on the foil and
beampipe materials. The detector observes the multi-pion final state.
This plan records how the simulation generates that final state, with
what branching ratios, with what citation chain, and which
alternatives bracket the modelling uncertainty.

The licentiate Chapters 5–6 establish the simulation; this plan
makes the source physics machine-checkable and defensible.

## 1. Final-state topology

Antineutron annihilation on a nucleon (n̄N) at rest produces:

- π⁺ π⁻ π⁰
- π⁺ π⁻ 2π⁰
- π⁺ π⁻ 3π⁰
- 2π⁺ 2π⁻
- 2π⁺ 2π⁻ π⁰
- 3π⁺ 3π⁻ (rare)
- η + nπ, ω + nπ, ρ + nπ (resonant subdominant channels)
- K K̄ + nπ (small)

Average pion multiplicity ⟨n_π⟩ ≈ 4.5 for n̄p annihilation at rest;
total energy ≈ 2 m_n ≈ 1879 MeV; transverse momentum scales with
phase space.

## 2. How Geant4 generates this

The signal generator path:

1. `PrimaryGeneratorAction` emits an antineutron at the foil (mode-
   dependent kinematics; plan 07 §10.1).
2. Geant4 transports the antineutron until it stops or interacts.
3. `G4HadronPhysicsFTFP_BERT` plus `G4StoppingPhysics` produces the
   annihilation final state on the foil nucleus (carbon-12 in the
   default foil; silicon in beampipe regions).
4. Final-state pions, kaons, etas, etc. propagate through detector
   geometry per the rest of the physics list.

The branching ratio table is *implicit* in Geant4's hadronic models;
the rebuild does not override it for the nominal sample. The
alternatives in §4 either replace the table or reweight events.

## 3. Citation chain

The branching-ratio reference set used by the audit is explicit and
ordered by evidential role:

| Role | Full reference | Local bibliography status | Use in the audit |
|---|---|---|---|
| Low-energy n̄p / p̄p annihilation review | Claude Amsler and F. Myhrer, "Low Energy Antiproton Physics," *Annual Review of Nuclear and Particle Science* **41**, 219--267 (1991), doi:10.1146/annurev.ns.41.120191.001251. | **Missing from `overleaf-hibeam-thesis/ref.bib` in the current scan; add key `AmslerMyhrer1991LowEnergyAntiproton` before thesis freeze.** | Primary source for at-rest annihilation branching and resonance content used by `branching_amsler1991`. |
| Nuclear-medium extrapolation | E. Friedman and A. Gal, "In-medium nuclear interactions of low-energy hadrons," *Physics Reports* **452**(4--5), 89--153 (2007), doi:10.1016/j.physrep.2007.08.002. | **Missing from `ref.bib` in the current scan; add key `FriedmanGal2007InMedium`.** The current file instead has `Friedman:2008es` (Phys. Rev. D **78**, 016002, 2008). | Physics basis for the nuclear-medium alternative and the carbon/silicon target systematic. |
| Antineutron-specific review | T. Bressani and A. Filippi, "Antineutron physics," *Physics Reports* **383**, 213--297 (2003), doi:10.1016/S0370-1573(03)00233-3. | Present as `Bressani:2003pv`. | Cross-check that the n̄p-derived branching model is not relying solely on antiproton data. |
| Low-energy n̄-nucleus model | E. S. Golubeva and L. A. Kondratyuk, "Annihilation of low energy antineutrons on nuclei," *Nucl. Phys. B Proc. Suppl.* **56**, 103--107 (1997), doi:10.1016/S0920-5632(97)00260-0. | Present as `Golubeva:1997`. | Nuclear-target correction and multiplicity-shape comparison. |
| NNBAR intranuclear model | E. S. Golubeva, J. L. Barrow, and C. G. Ladd, "Model of n̄ annihilation in experimental searches for n̄ transformations," *Phys. Rev. D* **99**, 035002 (2019), doi:10.1103/PhysRevD.99.035002. | Present as `Golubeva:2018mrz`. | Modern event-generator alternative for `branching_intranuclear2019`. |
| NNBAR detector tradition | S.-C. Yiu *et al.*, "Status of the Design of an Annihilation Detector to Observe Neutron-Antineutron Conversions at the European Spallation Source," *Symmetry* **14**, 76 (2022), doi:10.3390/sym14010076; F. Backman *et al.*, "The development of the NNBAR experiment," *JINST* **17**, P10046 (2022), doi:10.1088/1748-0221/17/10/P10046. | Present as `sym14010076` and `Backman_2022`. | Binds this rebuild's signal observables to prior NNBAR simulation figures and selections. |

Plan 47 ledger records which reference each thesis number cites; plan
50 defence package binds them to the result. Bibliography gaps in the
table above are not methodology blockers for Wave 2 planning, but they
are thesis-freeze blockers because plan 13 acceptance requires every
reference to resolve to `ref.bib`.

## 4. Alternative models (systematic variations)

| Tag | Variation | Source |
|---|---|---|
| `nominal_geant4` | Geant4's built-in FTFP hadronic | §2 default |
| `branching_amsler1991` | Reweight events to match Amsler & Myhrer table | hand-tuned weights |
| `branching_friedman2007` | Reweight to Friedman & Gal nuclear-modified branching | theory-driven |
| `eta_omega_enhanced` | +1σ on η/ω fractions | sensitivity bracket |
| `eta_omega_suppressed` | −1σ on η/ω fractions | sensitivity bracket |

Per plan 04 §6, alternative-model deltas combine in quadrature into
the signal-model systematic for any quoted observable.

## 5. Foil-specific closure

The licentiate's foil is carbon-12 (plan 07 §5.3). The reconstructed
multi-pion multiplicity, total visible energy, and pion-charge ratio
on signal samples must close against the reference distributions in
§3 within statistical uncertainty.

Closure metric: per-multiplicity histogram of the *truth* final-state
pions in `Particle_output_*.parquet` for the signal sample. χ²/dof
< 2 against the Amsler 1991 table is the pass.

When the foil is replaced by silicon (TARGET_BUILD=0 plus beampipe
silicon as target), the reference set shifts to n̄-Si data — sparse;
plan 13 records "limited reference" and bumps the systematic.

## 6. Acceptance criteria

- §3 citation chain is complete; every reference resolves to a paper
  in `bibliography/` or `ref.bib`.
- §4 alternative-model registry has ≥ 2 entries.
- §5 closure plot has been produced for the current `nominal_geant4`
  configuration and lives in plan 47 ledger.
- Plan 45 systematics taxonomy includes a "signal model" nuisance
  parameter populated from §4.

## 7. Risks and mitigations

- *Risk:* n̄-A branching extrapolation has poorly known systematic.
  *Mitigation:* §4 alternatives bracket the known range; we report
  the larger of the alternatives' deltas as the signal-model
  systematic.
- *Risk:* foil-vs-beampipe target mixing — events from the silicon
  beampipe may pollute the foil-origin sample.
  *Mitigation:* plan 20 sample-regen explicitly tags origin volume;
  plan 47 quotes foil-origin numbers separately.

## 8. Dependencies

- **04** — uncertainty propagation.
- **12** — physics list provides the underlying hadronic generator.
- *Consumed by:* plan 20 (signal sample), plan 21 (cosmic-neutron
  uses related physics for closure), plan 47 (ledger), plan 45
  (systematics).

## 9. References

- Amsler & Myhrer, *Annu. Rev. Nucl. Part. Sci.* 41 (1991) 219.
- Friedman & Gal, *Phys. Rep.* 452 (2007) 89.
- HIBEAM/NNBAR TDR (cited by overleaf-hibeam-thesis ref.bib).
- Geant4 Physics Reference Manual, hadronic models chapter.

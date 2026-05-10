---
id: 13_signal_model
title: Signal model — n̄-A annihilation final-state branching
version: 0.1
status: draft
owner: Physics Modeling
depends_on: [00_README, 04_statistical_uncertainty, 12_physics_list_audit]
inputs:
  - {path: NNBAR_Detector/src/PrimaryGeneratorAction.cc, schema: primary generator}
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
last_updated: 2026-05-10
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
| Low-energy n̄p / p̄p annihilation review | C. Amsler and F. Myhrer, "Low-energy antiproton physics," *Ann. Rev. Nucl. Part. Sci.* **41**, 219--267 (1991), doi:10.1146/annurev.ns.41.120191.001251. | Verified in `ref.bib` as `\cite{amsler:1991}` on 2026-05-10. | Source for the at-rest p̄p/n̄p branching reference and resonance-enriched grouped-channel checks. |
| Nuclear-medium extrapolation | E. Friedman and A. Gal, "In-medium nuclear interactions of low-energy hadrons," *Physics Reports* **452**, 89--153 (2007), doi:10.1016/j.physrep.2007.08.002. | Verified in `ref.bib` as `\cite{friedman:2007}` on 2026-05-10; the related n-nbar lifetime calculation remains `\cite{Friedman:2008es}`. | Source for carbon/silicon medium-modification brackets in `branching_friedman2007`. |
| Antineutron-specific review | T. Bressani and A. Filippi, "Antineutron physics," *Physics Reports* **383**, 213--297 (2003), doi:10.1016/S0370-1573(03)00233-3. | Present as `\cite{Bressani:2003pv}`. | Cross-check that the n̄p-derived branching model is not relying solely on antiproton data. |
| Low-energy n̄-nucleus model | E. S. Golubeva and L. A. Kondratyuk, "Annihilation of low energy antineutrons on nuclei," *Nucl. Phys. B Proc. Suppl.* **56**, 103--107 (1997), doi:10.1016/S0920-5632(97)00260-0. | Present as `\cite{Golubeva:1997}`. | Nuclear-target correction and multiplicity-shape comparison. |
| NNBAR intranuclear model | E. S. Golubeva, J. L. Barrow, and C. G. Ladd, "Model of n̄ annihilation in experimental searches for n̄ transformations," *Phys. Rev. D* **99**, 035002 (2019), doi:10.1103/PhysRevD.99.035002. | Present as `\cite{Golubeva:2018mrz}`. | Modern event-generator alternative for `branching_intranuclear2019`. |
| NNBAR detector tradition | S.-C. Yiu *et al.*, "Status of the Design of an Annihilation Detector to Observe Neutron-Antineutron Conversions at the European Spallation Source," *Symmetry* **14**, 76 (2022), doi:10.3390/sym14010076; F. Backman *et al.*, "The development of the NNBAR experiment," *JINST* **17**, P10046 (2022), doi:10.1088/1748-0221/17/10/P10046. | Present as `\cite{sym14010076}` and `\cite{Backman_2022}`. | Binds this rebuild's signal observables to prior NNBAR simulation figures and selections. |

Plan 47 ledger records which reference each thesis number cites; plan
50 defence package binds them to the result. The Stage D.3 bibliography repair added the two previously missing
source keys, so the Amsler/Myhrer and Friedman/Gal rows are now usable
as bibliography-backed alternatives. Rows still need explicit registry
payloads before weights are applied to a thesis number.

## 4. Alternative models (systematic variations)

The nominal sample keeps Geant4's FTFP/BERT annihilation model intact.
Alternative models are applied as *analysis weights* unless the row
explicitly requests regeneration. The common recipe is:

1. Classify each signal event by truth final-state signature from
   `Particle_output_*.parquet`: charged pion count, neutral pion/
   photon count, eta/omega/rho tags where present, kaon count, and
   target volume (foil carbon vs beampipe silicon).
2. Build a nominal branching table from `nominal_geant4` truth counts
   after the same event-quality preselection used by the ledger row.
3. For alternative table `A`, assign
   `w_event = BR_A(channel) / BR_nominal(channel)`; if only a grouped
   channel is available, use the grouped multiplicity bin and record
   the grouping in the row notes.
4. Renormalise weights so `sum(w_event)` equals the unweighted event
   count before computing the observable. The systematic shift is the
   weighted-vs-nominal delta propagated per plan 04 §6.

| Tag | Variation | Source/input | Reweighting recipe | Registry payload |
|---|---|---|---|---|
| `nominal_geant4` | Geant4's built-in FTFP/BERT + stopping model | §2 default, physics tag `nominal` from plan 12 | Unit weights; records the truth-channel table used as the denominator for alternatives. | `data/registry/signal_models/nominal_geant4.yml`: Geant4 version, physics tag, channel counts, preselection hash. |
| `branching_amsler1991` | Enabled low-energy p̄p/n̄p at-rest branching reference. | `\cite{amsler:1991}` (§3) | Map Geant4 truth channels to grouped final states (`π+π-π0`, `π+π-2π0`, `2π+2π-`, resonance-enriched bins); apply grouped-channel weights after the registry records the extracted branching table. | `branching_table`, `channel_map`, `unmapped_fraction`, max event weight, and cite key `amsler:1991`. |
| `branching_friedman2007` | Enabled nuclear-medium modification for carbon/silicon targets. | `\cite{friedman:2007}` (§3) plus `\cite{Friedman:2008es}` as the related n-nbar lifetime calculation. | Start from the enabled at-rest branching table, then apply target-dependent multiplicity migration for carbon and silicon categories. | `target_tables`, `target_volume_rule`, per-target normalisation factors, and cite key `friedman:2007`. |
| `branching_intranuclear2019` | Modern intranuclear n̄ transformation generator alternative | `\cite{Golubeva:2018mrz}` and `\cite{Barrow:2021svu}` (§3) | Reweight by charged/neutral pion multiplicity and nuclear-remnant category; if a generated comparison sample exists, prefer direct sample ratio over analytic weights. | Generator tag, multiplicity table, remnant categories, comparison-sample id if available. |
| `eta_omega_enhanced` / `eta_omega_suppressed` | Enabled resonance-fraction sensitivity bracket. | `\cite{amsler:1991}` for resonance-enriched low-energy annihilation channels and `\cite{Bressani:2003pv}` for antineutron-specific context. | Multiply events containing η or ω truth particles by `(1 ± σ_res)` and renormalise; the registry must state `σ_res` before a ledger row uses the bracket. | `sigma_res`, affected PDG ids, renormalisation factor, and cite keys `amsler:1991`, `Bressani:2003pv`. |

At least two enabled alternatives are required before the signal-model
nuisance can be marked complete. After the 2026-05-10 Stage D.3 bib
repair, the bibliography-backed enabled candidates are
`branching_amsler1991`, `branching_friedman2007`,
`branching_intranuclear2019`, and the η/ω resonance-fraction bracket.
Per plan 04 §6, alternative-model deltas combine in quadrature into the
signal-model systematic for any quoted observable unless plan 45 later
records correlations between the alternatives.

## 5. Foil-specific closure

The licentiate's foil is carbon-12 (plan 07 §5.3). The reconstructed
multi-pion multiplicity, total visible energy, and pion-charge ratio
on signal samples must close against the reference distributions in
§3 within statistical uncertainty.

Closure metric: per-multiplicity histogram of the *truth* final-state
pions in `Particle_output_*.parquet` for the signal sample. Once the
`branching_amsler1991` registry table is extracted from the cited
review, closure may be labelled against the Amsler/Myhrer at-rest
reference; until the table payload exists, it remains a bibliography-
backed but not yet numerically weighted comparison.

When the foil is replaced by silicon (TARGET_BUILD=0 plus beampipe
silicon as target), the reference set shifts to n̄-Si data — sparse;
plan 13 records "limited reference" and bumps the systematic.

## 6. Acceptance criteria

- §3 citation chain is complete: every non-TODO reference resolves to a
  paper in `bibliography/` or `ref.bib`, and TODO rows are not used as
  factual sources.
- §4 alternative-model registry has ≥ 2 enabled entries with resolving
  bibliography keys.
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

- `\cite{amsler:1991}` for low-energy antiproton / antineutron at-rest
  branching and resonance context.
- `\cite{friedman:2007}` for in-medium low-energy hadron interactions.
- `\cite{Friedman:2008es}` for the related n-nbar nuclear-disappearance
  lifetime calculation.
- HIBEAM/NNBAR TDR (cited by overleaf-hibeam-thesis ref.bib).
- Geant4 Physics Reference Manual, hadronic models chapter.

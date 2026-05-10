---
id: 45_systematics_taxonomy
title: Systematics taxonomy — named uncertainties + correlation tree
version: 0.1
status: draft
owner: Analysis WG
depends_on: [00_README, 04_statistical_uncertainty, 12_physics_list_audit, 13_signal_model, 14_background_models, 17_field_calibration, 18_intercalibration, 38_truth_substitution_ladder]
outputs:
  - {path: docs/rebuild_plans/45_systematics_taxonomy.md, schema: this file}
  - {path: data/systematics/registry.yml, schema: machine-readable nuisance list}
acceptance:
  - {test: every nuisance parameter has name, source, ±1σ definition, affected observables, method: registry review, pass_when: full coverage}
  - {test: correlation matrix between nuisances declared, method: §2 review, pass_when: matrix populated}
  - {test: every quoted result cites the nuisances applied, method: ledger cross-reference, pass_when: zero unflagged numbers}
risks:
  - {risk: double-counting if a calibration uncertainty enters both as a Class C constant and a nuisance parameter, mitigation: §3 single-source rule}
estimated_effort: M
last_updated: 2026-05-09
---

# Systematics taxonomy

*Charter.* The single registry of every systematic uncertainty. Each
nuisance is named, defined, sourced, scoped, and assigned a
correlation with every other nuisance. Plan 47 ledger and plan 50
defence package refer to nuisance names verbatim.

## 1. Nuisance registry (initial set)

Correlation flags are group labels consumed by §2: nuisances sharing a
flag are tested for non-zero correlation before the final covariance is
frozen; otherwise they default to independent.

| ID | Name | Source | ±1σ definition | Affected observables | Correlation flags |
|---|---|---|---|---|---|
| N1 | TPC W-value | plan 17 §3 | nominal 23.6 eV varied by the reference spread 26.0–27.4 eV; implement as ±15% gain on TPC ionisation charge | dE/dx, charged PID, foil-track acceptance | `detector_calibration`, `charged_pid` |
| N2 | Scintillator yield | plan 18 §3 | nominal 11136 photons/MeV; ±1136 photons/MeV spans the optical-table value 10000 photons/MeV | scintillator energy, E.1/E.2, E.3/E.4, S.1, S.5 | `detector_calibration`, `calorimeter_energy` |
| N3 | Lead-glass calibration | plan 18 §4 | per-energy linear-fit slope/intercept varied by the fitted 1σ covariance; pre-fit envelope capped by the 5% closure criterion | lead-glass energy, photon energy, π⁰ mass, visible mass | `detector_calibration`, `calorimeter_energy` |
| N4 | Physics list | plan 12 §3 | discrete model envelope over `nominal_hp`, `qgsp_bert`, `qgsp_bic`, and `em_opt0`; quote half-spread as ±1σ-equivalent | hadronic multiplicity, secondary interactions, neutron transport | `hadronic_model`, `background_shape` |
| N5 | Signal branching | plan 13 §4 | discrete model envelope over `nominal_geant4`, `branching_amsler1991`, `branching_friedman2007`, and η/ω ±1σ brackets | per-channel signal efficiency, π⁰/photon multiplicity, event shapes | `signal_model` |
| N6 | Cosmic flux | plan 14 §1.4 | ±15% on CRY normalisation, covering solar-cycle/date/location uncertainty | cosmic background normalisation, cosmic cut-flow rates | `background_normalization`, `cosmic` |
| N7 | Beam-neutron flux | plan 22 §§1,4 | ±10% on beam-neutron per-pulse yield until the ESS MCPL/parameterised source is frozen; preserve the plan-22 14 Hz conversion separately | beam-neutron normalisation, capture-γ and secondary rates | `background_normalization`, `beam_neutron` |
| N8 | Geometry alignment | plan 16 §3 | scenario envelope over `perfect`, `nominal_survey`, and `worst_case_construction`; quote half-spread of affected observable | vertex resolution, track-cluster matching, π⁰ mass | `geometry`, `tracking`, `calorimeter_energy` |
| N9 | Optical-photon yield | plan 18 §4 | optical-on/off paired residual after Cerenkov/eDep conversion; absolute residual is the ±1σ range | lead-glass response in optical builds, photon energy | `detector_calibration`, `optical`, `calorimeter_energy` |
| N10 | Material budget | plan 15 §§2,6 | ±5% per-region radiation-length envelope until measured composition is cited; recompute conversion and scattering observables | photon conversion rate, multiple scattering, vertex and π⁰ resolutions | `geometry`, `material_budget`, `background_shape` |

## 2. Correlation matrix

A nuisance is fully correlated with itself, fully anti-correlated
with its inverse, and otherwise nominally uncorrelated. Special
cases are seeded from the §1 flags:

| Pair / group | Initial correlation | How it is frozen |
|---|---:|---|
| same nuisance varied up/down | -1.0 | analytic by construction |
| same correlation flag, e.g. N2/N3/N9 `calorimeter_energy` | `rho_measured` | paired toy/reconstruction runs; default 0 until measured |
| N1/N4 ionisation-model overlap | `rho_measured` | paired W-value and physics-list variation |
| N5 signal branching vs N6/N7 background fluxes | 0.0 | independent source models |
| N8 geometry vs N10 material budget | `rho_measured` | geometry/material paired scenario envelope |
| no shared flag and no listed exception | 0.0 | default independence |

DEC stubs:

| DEC id | Convention to sign | Default |
|---|---|---|
| `DEC-45-CORRELATION-SEED` | initial correlation policy before paired runs exist | self = +1, up/down = -1, unshared pairs = 0 |
| `DEC-45-CALIBRATION-GROUPING` | whether N2/N3/N9 share the `calorimeter_energy` group | group them and require paired runs before final covariance |
| `DEC-45-GEOMETRY-MATERIAL-GROUPING` | whether N8/N10 are correlated | treat as measured-only correlation, default 0 |

## 3. Single-source rule

A calibration uncertainty enters the analysis exactly once. If it
appears as a Class C constant uncertainty (plan 04 §6) it does not
also appear as a nuisance parameter; if it appears as a nuisance, the
Class C value is the nominal.

## 4. Acceptance criteria

- §1 registry complete; ≥ 10 nuisances.
- §2 correlation matrix populated.
- §3 single-source rule audited (no double-counting).
- Plan 47 ledger and plan 50 defence package cite nuisance IDs by
  name.

## 5. Risks

- *Risk:* nuisances missing for unmodelled effects (plan 01 §6
  limitations).
  *Mitigation:* §1 N* assignments include "limitation" rows for L1,
  L2, L3, L4 explicitly; plan 50 surfaces them as "unbounded by
  current rebuild".

## 6. Dependencies

- **04, 12, 13, 14, 17, 18, 38** — inputs.
- *Consumed by:* plan 46 (significance), plan 47, plan 50.

## 7. References

- ATLAS / CMS standard nuisance-parameter conventions.

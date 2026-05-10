---
id: 15_material_budget
title: Material budget — radiation lengths, interaction lengths, tracking-material map
version: 0.1
status: draft
owner: Physics Modeling
depends_on: [00_README, 07_simulation_atomic_walkthrough]
inputs:
  - {path: NNBAR_Detector/src/Detector_Module/*.cc, schema: geometry source}
  - {path: NNBAR_Detector/src/DetectorConstruction.cc, schema: top-level geometry source}
outputs:
  - {path: docs/rebuild_plans/15_material_budget.md, schema: this file}
  - {path: output/studies/material_budget/, schema: traversal scans}
acceptance:
  - {test: every active geometry volume has X0 and λI documented, method: §3 table coverage, pass_when: zero gaps}
  - {test: material map produced for nominal pion at nominal angle, method: §4 plot, pass_when: plot exists in plan 47}
  - {test: gamma-conversion fraction is computed for typical photon energies, method: §5 number, pass_when: number agrees with Geant4 within 5%}
risks:
  - {risk: material additions in geometry refactors silently change X0, mitigation: plan 53 CI tracks total per-region X0 against a baseline}
  - {risk: scintillator-plastic composition discrepancy vs. real plastic, mitigation: §6 cited composition}
estimated_effort: M
last_updated: 2026-05-10
---

# Material budget

*Charter.* For every detector volume, record the material, density,
radiation length X₀, nuclear interaction length λ_I, and the resulting
total material a typical particle traverses on its way through the
detector. The material map drives multiple-scattering, photon
conversion, and track-resolution estimates; without it those numbers
are unsupported.

## 0.1 Wave 6 derivation — material interaction budget

### Physics derivation

**What is physically measured.** The material budget measures the
truth-side amount of matter a particle traverses between the foil and
each detector subsystem. The load-bearing quantities are integrated
`X/X₀` for electromagnetic showering, photon conversion, and multiple
scattering; integrated `X/λ_I` for hadronic reinteractions; and the
per-region material identity/density that converts path length into
mass thickness.

**Estimator rationale.** Radiation length is the natural material
coordinate for electron bremsstrahlung, photon pair production, and
EM shower development; nuclear interaction length is the natural
coordinate for pion/proton/neutron reinteractions. PDG material and
passage-of-particles formulae therefore define the estimator basis
`\cite{ParticleDataGroup:2024RPP}`, while NIST tables and the Geant4
material table provide the source values used by the simulation
`\cite{NISTSTAR,Agostinelli2003,Allison2016}`. The Highland multiple-
scattering approximation converts `X/X₀` into an angular-resolution
floor, and the pair-production attenuation approximation converts
`X/X₀` into a photon-conversion prior.

**Statistical character.** A material map is deterministic for a fixed
geometry and material table; the uncertainty is dominated by systematic
composition, density, and geometry-survey errors rather than counting
statistics. Ray-trace sampling error only enters when the map is
approximated on a finite `(θ, φ)` grid. The closure target is therefore
not a fitted central value but agreement between analytic material
formulae, the Geant4 runtime material table, and particle-gun response.

### Logic gaps

- **Material constants `X₀` and `λ_I`.** Grounding: §1 uses PDG/NIST
  element values and mass-weighted mixtures, but the sign-off source is
  Geant4's runtime `G4MaterialTable`. `OPEN:` dump
  `GetRadlen()` and `GetNuclearInterLength()` for every active material
  and replace provisional mixture values; target resolution date
  2026-06-15.
- **Geometry path lengths (100 µm foil, ∼20 mm beampipe/walls, 25 cm
  gas, ∼5 cm scintillator, ∼30 cm lead glass).** Grounding: plan 07 and
  source geometry define the dimensions; this plan's current list is a
  planning summary. `OPEN:` replace with ray-traced nominal paths from
  the constructed geometry for the acceptance directions; target
  resolution date 2026-06-15.
- **Multiple-scattering constants (13.6 MeV and 0.038 log term).**
  Grounding: PDG passage-of-particles Highland approximation
  `\cite{ParticleDataGroup:2024RPP}`; no analysis tuning is allowed
  unless plan 26 records a closure-motivated correction.
- **Photon-conversion factor `7/9`.** Grounding: high-energy pair-
  production attenuation in radiation-length units
  `\cite{ParticleDataGroup:2024RPP}`. `OPEN:` verify the approximation
  against Geant4 photon-gun conversion fractions in the relevant energy
  range and material stack; target resolution date 2026-06-22.
- **Acceptance anchor particles (π⁺ at 500 MeV and γ at 200 MeV,
  θ=90°, φ=0°).** Grounding: current §5 review anchors. `OPEN:`
  confirm these anchors cover the thesis ledger rows, or add a small
  grid in momentum and angle before using the map as a universal
  correction; target resolution date 2026-06-22.
- **Composition vendor gaps.** Grounding: §1 marks scintillator,
  lead-glass, coatings, and shielding concrete as source-defined but
  vendor-uncited. `OPEN:` attach vendor datasheets or mark the affected
  material constants as plan-45 composition nuisances; target
  resolution date 2026-06-22.

### Closure test for the derivation

1. Dump the Geant4 material table for the nominal geometry and compare
   every material's density, `X₀`, and `λ_I` to the §1 inventory.
2. Ray-trace charged and neutral test particles from the foil over the
   acceptance grid and integrate `X/X₀` and `X/λ_I` per subsystem.
3. Run pion and photon guns at the §5 anchor points. Compare measured
   scattering widths and conversion fractions to the Highland and
   `1 - exp(-(7/9) X/X₀)` predictions with plan-04 uncertainty
   propagation.
4. Store the material-map tables and closure deltas in plan 47. If the
   analytic-vs-Geant4 conversion fraction differs by more than the
   existing 5% acceptance threshold, keep material-budget rows
   `mismatch` or `blocked` until the source composition and geometry
   are reconciled.

## 1. Material inventory

For every `G4Material` instantiated in the active geometry, the
inventory records: name, composition, density, radiation length X₀,
nuclear interaction length λ_I, and citation/status. Values below are
Wave-2 planning values: elemental X₀ values are from NIST PML / PDG
material tables, λ_I values are PDG nuclear-interaction lengths, and
mixture values are mass-weighted from the `src/Detector_Module/*.cc`
and `src/DetectorConstruction.cc` source composition until a runtime
`G4MaterialTable` dump supersedes them.
Centimetre values are computed with the density used in source.

| Material | Active volume(s) / source | Composition and density | X₀ (g/cm²; cm) | λ_I (g/cm²; cm) | Citation / status |
|---|---|---|---|---|---|
| `Galactic` | World/default filler; `src/DetectorConstruction.cc` material block | H-like vacuum, `universe_mean_density` | effectively ∞ | effectively ∞ | Geant4 vacuum convention; no material budget contribution. |
| `Carbon_target` | Foil; `src/DetectorConstruction.cc` volume block | C, 3.52 g/cm³ | 42.70; 12.1 | 86.8; 24.7 | NIST/PDG carbon values recast to code density. Prior 18.8 cm graphite value used lower density; code density must win. |
| `Aluminum` | Beampipe and TPC walls; `src/Detector_Module/beampipe_geometry.cc`, `src/Detector_Module/TPC_geometry.cc` | Al, 2.70 g/cm³ | 24.01; 8.89 | 106.4; 39.4 | NIST/PDG Al. |
| `Copper` | Beam stop/conductors; `src/Detector_Module/beampipe_geometry.cc` | Cu, 8.90 g/cm³ | 12.86; 1.45 | 137.3; 15.4 | NIST/PDG Cu. |
| `StainlessSteel` | Beampipe/cosmic shielding steel; `src/Detector_Module/beampipe_geometry.cc`, `src/Detector_Module/Cosmic_Shielding_geometry.cc` | Fe 0.68, Cr 0.19, Ni 0.10, Mn 0.02, Si 0.01; 8.02 g/cm³ | ≈13.9; 1.73 | ≈132; 16.5 | Mass-weighted PDG element table; alloy grade needs engineering citation. |
| `Silicon` | Silicon detectors; `src/Detector_Module/Silicon_geometry.cc` | Si, 2.33 g/cm³ | 21.82; 9.36 | 106.0; 45.5 | NIST/PDG Si. |
| `B4C` | Beam coating/shield component; `src/Detector_Module/beampipe_geometry.cc`, `src/Detector_Module/Silicon_geometry.cc` | B 0.80, C 0.20; 2.52 g/cm³ | ≈50.1; 19.9 | ≈86; 34.1 | Mass-weighted B/C; verify against vendor B4C grade. |
| `el_Li6` | Beam coating isotope; `src/Detector_Module/beampipe_geometry.cc`, `src/Detector_Module/Silicon_geometry.cc` | ⁶Li, 0.460 g/cm³ | ≈82.8; 180 | ≈82; 178 | Isotopic Li approximation; confirm via Geant4 isotope material dump. |
| `Li6F` | Silicon/beampipe coating; `src/Detector_Module/beampipe_geometry.cc`, `src/Detector_Module/Silicon_geometry.cc` | ⁶Li 0.475, F 0.500, natural Li 0.025; 2.635 g/cm³ | ≈39.5; 15.0 | ≈86; 32.6 | Mass-weighted Li/F; isotope treatment needs MaterialTable dump. |
| `LiF` | Beampipe coating; `src/Detector_Module/beampipe_geometry.cc` | Li 0.50, F 0.50; 2.635 g/cm³ | ≈39.5; 15.0 | ≈86; 32.6 | Mass-weighted Li/F. |
| `el_Cd` | Beam coating/absorber; `src/Detector_Module/beampipe_geometry.cc` | Cd, 8.65 g/cm³ | 8.91; 1.03 | ≈158; 18.3 | NIST/PDG Cd. |
| `Lead` / `Lead_shield` | Cosmic and beampipe shielding; `src/Detector_Module/Cosmic_Shielding_geometry.cc`, `src/Detector_Module/beampipe_shielding_geometry.cc` | Pb, 11.29 g/cm³ | 6.37; 0.564 | 199.6; 17.7 | NIST/PDG Pb. |
| `CO2` | TPC gas component; `src/Detector_Module/TPC_geometry.cc` | CO₂, 1.84 mg/cm³ | ≈36.2; 1.97×10⁴ | ≈90; 4.9×10⁴ | NIST/PDG compound estimate; active only as `Gas` component. |
| `Gas` | TPC drift gas; `src/Detector_Module/TPC_geometry.cc` | Ar/CO₂ 80/20 by volume (≈0.78/0.22 by mass), 1.70 mg/cm³ | ≈22.3; 1.31×10⁴ | ≈113; 6.65×10⁴ | Source comments define mixture; confirm with runtime MaterialTable. |
| `Scint` | Scintillator modules; `src/Detector_Module/Scintillator_geometry.cc` | H 0.524573, C 0.475427; 1.023 g/cm³ | ≈45; ≈44 | ≈79; ≈77 | **Needs vendor citation.** Source comment says BC-408 datasheet, but no datasheet/key is present; H/C mass fractions also need audit. |
| `LeadGlass` | Lead-glass calorimeter; `src/Detector_Module/LeadGlass_geometry.cc` | O 0.156453, Si 0.080866, Ti 0.008092, As 0.002651, Pb 0.751938; 6.22 g/cm³ | ≈7.87; 1.27 | ≈158; 25.4 | **Needs vendor citation.** Source says PDG, but glass type/vendor and composition provenance are not cited. |
| `AlMgF2` | Lead-glass coating; `src/Detector_Module/LeadGlass_geometry.cc` | Al 0.331, F 0.408, Mg 0.261; 2.9007 g/cm³ | ≈27.5; 9.48 | ≈94.6; 32.6 | Mass-weighted PDG element values; coating stack needs vendor citation. |
| `PMT_window_mat` | PMT/quartz window; `src/Detector_Module/LeadGlass_geometry.cc` | SiO₂, 2.200 g/cm³ | ≈27.1; 12.3 | ≈97.5; 44.3 | NIST/PDG fused-silica/quartz proxy. |
| `PE_B4C_concrete` | Cosmic shielding alternative; `src/Detector_Module/Cosmic_Shielding_geometry.cc` | 15-element concrete/B4C/PE mix, 1.97 g/cm³ | ≈32.6; 16.5 | ≈86; 43.7 | Source mass fractions; needs shielding vendor/engineering citation. |
| `MagnadenseHC` | Cosmic shielding baseline; `src/Detector_Module/Cosmic_Shielding_geometry.cc` | Fe-heavy concrete (Fe 0.579, O 0.332, plus minor elements), 3.8 g/cm³ | ≈18.3; 4.82 | ≈114; 30.0 | Source mass fractions; needs Magnadense HC product citation. |

**Inventory gaps to close before plan-15 sign-off:** dump
`G4Material::GetRadlen()` and `GetNuclearInterLength()` for every row,
attach vendor citations for `Scint`, `LeadGlass`, shielding concrete,
and coatings, and decide whether component-only materials (`CO2`) are
kept in the sign-off table or moved to an appendix.

## 2. Material map per region

The material map records per-region totals that a particle of given
type/angle/energy crosses on its way out of the foil:

```
foil         → 100 µm carbon (≈ 5×10⁻⁴ X₀)
beampipe     → ~ 20 mm Al/steel + Si layers (≈ few % X₀)
TPC gas      → 25 cm gas (negligible X₀)
TPC walls    → some plastic / Al
scintillator → ~ 5 cm plastic
lead glass   → ~ 30 cm SF-6 (≈ many X₀)
```

Codex-supervisor produces a 2-D material map (X₀ vs (η, φ) or (θ, φ))
by ray-tracing test particles at construction time.

## 3. Multiple-scattering estimate

For a charged pion of momentum p crossing material of X/X₀:

```
θ_MS ≈ 13.6 MeV / (β c p) · √(X/X₀) · (1 + 0.038 ln(X/X₀))
```

Plan 26 (track-fit pulls) consumes this to set the floor on track
direction resolution. The current `_track_anchor_and_direction`
algorithm (plan 08 §3.2) does not include scattering; the future
Kalman fit (plan 25) does.

## 4. Photon conversion estimate

For a γ traversing material of X/X₀:

```
P(conversion) = 1 - exp(-(7/9) · X/X₀)
```

Plan 28 (photon objects) uses this to estimate the rate at which
photons convert before reaching the lead glass. Conversion electrons
produce TPC tracks that the charged-cluster veto must distinguish
from primary charged tracks.

## 5. Acceptance criteria

- §1 inventory is complete (codex-supervisor enumerates against
  `G4MaterialTable` at build time).
- §2 material map is produced as a plot for at least: π⁺ at 500 MeV
  through (θ=90°, φ=0°), and γ at 200 MeV at the same angle.
- §3 multiple-scattering estimates feed plan 26 acceptance.
- §4 conversion rate at lead-glass front face is computed and
  recorded.

## 6. Risks and mitigations

- *Risk:* scintillator and lead-glass composition assumed, not
  cited.
  *Mitigation:* §1 citation field is mandatory; codex-supervisor
  flags missing citations in v0.2 review.
- *Risk:* material additions in geometry refactors silently change
  the budget.
  *Mitigation:* plan 53 CI computes total X₀ on a fixed ray and
  compares against the recorded baseline; large deltas block the
  PR.

## 7. Dependencies

- **07_simulation_atomic_walkthrough** — geometry source.
- *Consumed by:* plan 16 (geometry), plan 25 (vertex / track fit),
  plan 26 (track fit pulls), plan 28 (photon objects), plan 33
  (truth-substitution ladder uses scattering-floor).

## 8. References

- PDG review of particle physics, "Passage of Particles Through
  Matter" chapter.
- NIST PML radiation-length tables.
- Geant4 `G4MaterialTable` runtime API.

2026-05-10 bib audit: the Wave 6 citation keys used above resolve in
`/Users/billy/Desktop/projects/overleaf-hibeam-thesis/ref.bib`:
`ParticleDataGroup:2024RPP`, `NISTSTAR`, `Agostinelli2003`, and
`Allison2016`. Source-file references in §1 intentionally name verified
files without line numbers; runtime `G4MaterialTable` dumps remain the
sign-off source for exact material constants.

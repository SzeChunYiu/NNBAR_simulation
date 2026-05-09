---
id: 15_material_budget
title: Material budget — radiation lengths, interaction lengths, tracking-material map
version: 0.1
status: draft
owner: Physics Modeling
depends_on: [00_README, 07_simulation_atomic_walkthrough]
inputs:
  - {path: NNBAR_Detector/src/detector/*.cc, schema: geometry source}
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
last_updated: 2026-05-09
---

# Material budget

*Charter.* For every detector volume, record the material, density,
radiation length X₀, nuclear interaction length λ_I, and the resulting
total material a typical particle traverses on its way through the
detector. The material map drives multiple-scattering, photon
conversion, and track-resolution estimates; without it those numbers
are unsupported.

## 1. Material inventory

For every G4Material instantiated in the active geometry, the
inventory records:

| Field | Source |
|---|---|
| Name | `G4Material::GetName()` |
| Composition | element fractions |
| Density | g/cm³ |
| X₀ | g/cm² and cm |
| λ_I | g/cm² and cm |
| Citation | NIST PML or vendor data sheet |

Materials documented in `DetectorConstruction.cc` (plan 07 §5.1):

- *Galactic vacuum.* World filler. Negligible material.
- *Carbon target.* density 3.52 g/cm³ (graphite-like). X₀ = 18.8 cm
  (NIST). λ_I = 38.1 cm. Plan 16 confirms the foil thickness
  (100 µm). Per-traversal X₀ fraction ≈ 5 × 10⁻⁴.

The remaining materials are defined inside the per-subsystem geometry
builders. Codex-supervisor enumerates them in v0.2:

- TPC fill gas (Ar/CO₂ mixture; nominal 90/10 — confirm).
- Scintillator plastic (likely BC-408 or EJ-200 equivalent).
- Lead glass (typically SF-6 or similar; high-Z).
- Beampipe steel.
- Beampipe silicon vertex layers.
- Cosmic shielding (likely concrete or iron).
- Beampipe shielding.

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

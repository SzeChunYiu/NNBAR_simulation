---
id: 07_5_6_sd_and_field_assignment
title: Simulation atomic walkthrough §5.6 — sensitive detector and field assignment
version: 0.1
status: draft
owner: Sim Production
depends_on: [07_simulation_atomic_walkthrough]
---

### 5.6 Sensitive detector and field assignment (`ConstructSDandField`)

`DetectorConstruction.cc:305–384`:

| Volume | Sensitive detector | Class |
|---|---|---|
| `CarbonLV` | `Carbon_Detector` (CarbonSD) | `CarbonSD` |
| `SiliconLV` (×n) | `siliconDetector` (SiliconSD) | `SiliconSD` |
| `BeampipeLV` (×n) | `tubeDetector` (TubeSD) | `TubeSD` |
| `TPCLV` (×12) | `TPCDetector` | `TPCSD` |
| `ScintLV` (×n) | `scintDetector` | `ScintillatorSD` |
| `LeadGlass_output[0]` | `LeadGlassDetector` | `LeadGlassSD` |
| `LeadGlass_output[1]` (PMT face) | `PMTDetector` | `PMTSD` |

Note: `ScintillatorSD` and `Scint_DetSD` both exist in the source
tree; the SD attached to the scintillator volumes is `ScintillatorSD`.
`Scint_DetSD` is reserved or unused — plan 14 (validation suite) flags
this for review. Similarly `ShieldSD` and `DetArea_SD` exist as files
but the active SD attachments here cover only Carbon, Silicon, Tube
(beampipe), TPC, Scintillator, LeadGlass, and PMT.

The TPC field manager (`DetectorConstruction.cc:354–382`) attaches a
`G4UniformElectricField`-like object via `util/ElectricField.cc` to
`TPC_output[0]` and `TPC_output[1]` (the first front-back pair of
front/back TPC mother volumes). Stepper:
`G4DormandPrince745` with 8 variables (E-field). `MinStep = 1 mm`,
`DeltaOneStep = 1 mm`, `LargestAcceptableStep = 1 cm`. Plan 17
audits whether this assignment covers all 12 modules
(it does not — only the first two LVs are field-managed; this is
a known limitation flagged in plan 17).

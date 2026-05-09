---
id: 17_field_calibration
title: TPC field calibration — drift field, drift velocity, gain
version: 0.1
status: draft
owner: Sim Production
depends_on: [00_README, 01_realism_contract, 07_simulation_atomic_walkthrough]
inputs:
  - {path: NNBAR_Detector/src/util/ElectricField.cc, schema: field source}
  - {path: NNBAR_Detector/src/sensitive/TPCSD.cc, schema: TPC SD}
  - {path: NNBAR_Detector/src/physics/TPCDriftManager.cc, schema: drift simulation}
outputs:
  - {path: docs/rebuild_plans/17_field_calibration.md, schema: this file}
  - {path: data/registry/calibration/tpc_field_<tag>.yml, schema: per-config field record}
acceptance:
  - {test: drift field is uniform within stated tolerance over the active TPC volume, method: field-map scan, pass_when: < 1% deviation}
  - {test: W-value cross-check between TPCSD (23.6 eV) and reference (26-27.4 eV) is reconciled, method: closure plot, pass_when: chosen value defended in DEC entry}
  - {test: only TPC modules 0 and 1 are field-managed today (limitation), method: source review, pass_when: limitation L9-equiv documented}
risks:
  - {risk: only first two TPC LVs get the field; the other 10 modules drift in null field, mitigation: §2 records as known incompleteness, plan 25 vertex study quantifies}
  - {risk: TPC W-value mismatch between sensitive detector and reference data, mitigation: §3 audit + DEC}
estimated_effort: M
last_updated: 2026-05-09
---

# TPC field calibration

*Charter.* Audit the TPC drift field configuration, the W-value used
to convert energy deposit to ionisation, and the gain-saturation
behaviour. These constants are Class C (plan 01 §2.3) and propagate
into every dE/dx-derived observable.

## 1. Field source

`NNBAR_Detector/src/util/ElectricField.cc` provides the TPC drift
field (a `G4UniformElectricField`-equivalent). Attached at
`DetectorConstruction.cc:380–381` to **only `TPC_output[0]` and
`TPC_output[1]`** — the first two LVs of the 12 TPC modules.

This is a known incompleteness. The remaining 10 modules drift in
the world's null field. Plan 25 (vertex) quantifies the consequence
on TPC tracking.

Stepper: `G4DormandPrince745` with 8 variables (E-field). MinStep
= 1 mm; DeltaOneStep = 1 mm; LargestAcceptableStep = 1 cm.

## 2. Field uniformity

Codex-supervisor produces a field-map scan across the TPC volume by
calling `ElectricField::GetFieldValue` on a 3-D grid. The map records
the magnitude and direction at each point and reports the maximum
deviation from the nominal.

Acceptance: < 1% deviation over the active volume (the grid excludes
edges within 5 mm of the field cage).

## 3. Drift velocity and W-value

The TPC SD (`TPCSD.cc:102`) uses **W-value = 23.6 eV** to convert
step `eDep` to electron count via Poisson sampling. The reference
W-value for the Ar/CO₂ mixture (90/10) is 26–27.4 eV depending on
the source (PDG; Sauli, *Principles of operation of multiwire
proportional and drift chambers*, CERN 77–09).

This is a documented discrepancy
(`docs/detector_fundamental_question_tree.md` §3). Plan 17 must:

1. Decide the production value (with a DEC entry in plan 05).
2. Record the chosen value as a Class C constant in plan 09.
3. Propagate the difference between 23.6 eV and the reference into
   plan 45 systematics as a "TPC W-value" nuisance with ±15% range.

Drift velocity is set indirectly through Geant4's stepper handling;
the rebuild does not currently override it. If GarfieldGPU is enabled
(plan 07 §11.1, `WITH_GARFIELD_GPU=ON`), the drift velocity is
controlled by `TPCDriftManager` parameters which codex-supervisor
enumerates in v0.2.

## 4. Gain and saturation

Geant4 does not natively model gas-gain saturation. The current
simulation stores the bare ionisation electron count
(`TPCSD.cc:104`); the reconstruction's `dedx` is computed from this
count and the step length.

Real-detector gain saturation matters for high-dE/dx tracks
(stopping protons, low-energy pions). The seam in plan 02
`energy_nonlinearity` slot can install a saturation curve when
real-data calibration is available. Until then, gain saturation is
limitation L3 (plan 01 §6).

## 5. Acceptance criteria

- §2 field map produced; uniformity within 1%.
- §3 W-value DEC entry approved; reference chosen and recorded.
- §3 systematic propagation lands in plan 45.
- §1 limitation (only first 2 TPC LVs get the field) is documented
  here and feeds plan 25 with a "field coverage" caveat.

## 6. Risks and mitigations

- *Risk:* the limited field assignment is fundamental — extending
  to all 12 modules requires touching the geometry builders.
  *Mitigation:* plan 25 vertex study quantifies the bias from
  unfielded modules; if it dominates resolution the seam in §1 gets
  patched.
- *Risk:* W-value choice locks downstream PID thresholds.
  *Mitigation:* plan 04 §6 propagation; the threshold scan
  (plan 24 calibration.py) is re-run after any change.

## 7. Dependencies

- **07** — field source identification.
- *Consumed by:* plan 09 (Class C entry), plan 25 (vertex), plan 27
  (dE/dx), plan 45 (systematics).

## 8. References

- Sauli, *Principles of operation of multiwire proportional and
  drift chambers*, CERN 77–09.
- PDG "Passage of Particles Through Matter".

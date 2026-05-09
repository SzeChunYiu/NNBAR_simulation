---
id: 18_intercalibration
title: TPC ↔ Scintillator ↔ LeadGlass intercalibration
version: 0.1
status: draft
owner: Reproducibility WG
depends_on: [00_README, 04_statistical_uncertainty, 07_simulation_atomic_walkthrough, 17_field_calibration, 23_sample_calibration_aux]
inputs:
  - {path: data/registry/cal_*, schema: calibration sample IDs}
outputs:
  - {path: docs/rebuild_plans/18_intercalibration.md, schema: this file}
  - {path: data/calibration/intercalibration_<tag>.yml, schema: per-pass calibration constants}
acceptance:
  - {test: TPC dE/dx anchored to MIP pion in scintillator overlap, method: §2 closure, pass_when: relative residual < 5%}
  - {test: scintillator photon yield (10000 vs 11136 photons/MeV) reconciled, method: §3 cross-check, pass_when: chosen value defended in DEC}
  - {test: lead-glass linearity vs electron beam reference in {50, 100, 200, 500, 1000} MeV, method: §4 closure, pass_when: residual < 5%}
risks:
  - {risk: optical-on / optical-off inconsistency in lead-glass response, mitigation: §4 paired sample with WITH_SCINTILLATION on / off}
  - {risk: scintillator yield drift between SD constant (11136) and optical table (10000), mitigation: §3 explicit reconciliation}
estimated_effort: M
last_updated: 2026-05-09
---

# TPC ↔ Scintillator ↔ LeadGlass intercalibration

*Charter.* Anchor every sub-detector's energy/charge calibration to a
shared reference. The single reference here is *Geant4 truth* (deposited
energy at hit time); the audit ensures that derived quantities (electron
count, scintillator photon-equivalent, lead-glass calorimetric energy)
agree across overlap regions and between optical-on/off configurations.

The intercalibration is *not* a real-detector calibration; it is a
self-consistency audit of the simulation pipeline. Any discrepancy
exposed here propagates into a systematic via plan 45.

## 1. Reference quantity

For every hit in every SD, Geant4 records `eDep` (MeV).
Intercalibration verifies that downstream derived quantities are
consistent with `eDep`:

- TPC: electrons = `eDep / W_value` (W = 23.6 eV per plan 17 §3).
- Scintillator: photons = `eDep × yield` (yield = 11136 photons/MeV
  per plan 07 §6.2).
- Lead glass: calorimetric energy = `eDep × calibration_factor`
  (currently 1.0; plan 18 audits whether saturation/linearity
  corrections are needed).
- PMT: photons recorded directly via optical-photon tracking when
  `WITH_SCINTILLATION=ON`; per-PMT efficiency Class C.

## 2. TPC ↔ Scintillator MIP closure

Cross-calibration via minimum-ionising pions:

1. Run `cal_singlepion_mip_v1` (plan 23) — π+ at fixed momentum,
   crossing TPC and scintillator.
2. Compute mean dE/dx in the TPC.
3. Compute mean scintillator response per cm of plastic.
4. Verify both agree with the Bethe–Bloch prediction within 5%.

Closure metric: relative residual of (measured / Bethe–Bloch). > 5%
escalates to plan 27 (dE/dx).

## 3. Scintillator yield reconciliation

The scintillator photon-equivalent count uses **11136 photons/MeV**
in the SD per `reconstruction.md` line 105, but the material optical
properties table uses **10000 photons/MeV** when
`WITH_SCINTILLATION=ON`.

Plan 18 must:

1. Identify the source of each value (BC-408 spec sheet vs. legacy
   constant).
2. Pick one as the production value with a DEC entry.
3. Document which value is consumed in fast-mode (no optical) and
   optical-mode runs.
4. Propagate the difference into plan 45 as a "scintillator yield"
   systematic with the absolute delta as the range.

## 4. Lead-glass calibration vs electron beam

Run `cal_singleelectron_v1` (plan 23) at {50, 100, 200, 500, 1000}
MeV.

Closure: per-energy mean lead-glass response should follow a linear
calibration up to ~1 GeV with a saturation onset at higher energy.
Residual to a linear fit < 5% is the pass.

Optical-on / optical-off paired closure: the same sample run with
`WITH_SCINTILLATION=ON` and `OFF` should yield the same calorimetric
energy after applying the appropriate Cerenkov / eDep conversion.
Disagreement quantifies the optical-photon-tracking systematic.

## 5. Acceptance criteria

- §2 MIP closure passes.
- §3 yield reconciliation has a DEC entry and a propagated systematic.
- §4 linearity closure passes for each energy point.
- §4 optical on/off closure passes within stated tolerance.

## 6. Risks and mitigations

- *Risk:* the calibration samples in plan 23 are not yet registered.
  *Mitigation:* plan 18 v0.1 stays in `draft` until plan 23 v0.2
  registers them.
- *Risk:* lead-glass non-linearity at high E breaks the linear fit.
  *Mitigation:* §4 acceptance is per-energy-bin residual, not a
  single linear fit; non-linear regime is documented.

## 7. Dependencies

- **04** — uncertainty propagation.
- **07** — SD source for the constants being audited.
- **17** — TPC W-value.
- **23** — calibration samples.
- *Consumed by:* plan 27 (dE/dx), plan 31 (event variables use
  intercalibrated energies), plan 45 (systematics), plan 47 (ledger).

## 8. References

- Birks, *Theory and Practice of Scintillation Counting* (1964).
- BC-408 / EJ-200 plastic scintillator data sheets.
- SF-6 / SF-2 lead-glass calibration references (vendor data).

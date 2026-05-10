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
last_updated: 2026-05-10
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

Numbered closure procedure:

1. Run `cal_singlepion_mip_v1` (plan 23) using
   `macro/calibration/scintillator/calib_pion_mip.mac`, with the pion
   momentum fixed in the MIP region and the origin at the foil center.
2. Build a per-track table with TPC path length, TPC `eDep`, TPC
   electron count recomputed with the plan 17 production W-value
   (23.6 eV), scintillator path length, and scintillator `eDep`.
3. Compute two observables for each track: `tpc_dedx_mev_per_cm` and
   `scint_dedx_mev_per_cm`. Store means, bootstrap errors, and pulls
   using plan 04 §2.
4. Compare both detector estimates against the same Bethe–Bloch MIP
   reference for the configured pion momentum. The reference value and
   material density used in the calculation are written to the output
   provenance block.
5. Produce `output/calibration/mip_closure/summary.json`,
   `output/calibration/mip_closure/rows.csv`, and a pull plot with TPC
   and scintillator points on the same axis.
6. Pass if both detector residuals are < 5% and their difference is
   consistent within the bootstrap uncertainty. A residual > 5%
   escalates to plan 27 (dE/dx) or plan 28 (range/stopping), depending
   on which side fails.

## 3. Scintillator yield reconciliation

The scintillator photon-equivalent count uses **11136 photons/MeV**
in the SD per `reconstruction.md` line 105, but the material optical
properties table uses **10000 photons/MeV** when
`WITH_SCINTILLATION=ON`.

**DEC-2026-05-10-6 stub — scintillator yield mode policy.**
Context: fast-mode `ScintillatorSD` stores a photon-equivalent count
using 11136 photons/MeV, while optical-mode material properties use
10000 photons/MeV. Decision: keep **11136 photons/MeV** as the
production value for fast-mode photon-equivalent rows because existing
reconstruction code consumes that column. Keep **10000 photons/MeV** as
the optical material-table value in optical-on samples, but mode-tag
those samples and apply a `11136/10000 = 1.1136` comparison scale when
checking against fast-mode photon-equivalent quantities. Follow-up:
promote this stub to the decision log after the first paired optical
on/off closure run.

Numbered closure procedure:

1. Source inventory: cite `ScintillatorSD` for 11136 photons/MeV and
   `Scintillator_geometry.cc` optical properties for 10000 photons/MeV.
2. Run the same scintillator calibration macro twice:
   `WITH_SCINTILLATION=OFF` for fast-mode photon-equivalent output and
   `WITH_SCINTILLATION=ON` for optical-photon transport.
3. For each run, compute `scint_yield_observed = photons / eDep_MeV`
   per hit and aggregate by scintillator layer and stave.
4. Convert optical-mode photon counts onto the fast-mode convention via
   the scale factor 1.1136 before comparing yields.
5. Record `yield_fast = 11136`, `yield_optical_table = 10000`, the
   scale factor, and the observed residuals in
   `output/calibration/scint_yield_reconciliation/summary.json`.
6. Pass if the scaled optical-mode yield and fast-mode yield agree
   within 5% after bootstrap uncertainty. Otherwise, plan 45 receives a
   scintillator-yield nuisance with a ±11.4% prior until a vendor/spec
   citation or data calibration narrows it.

## 4. Lead-glass calibration vs electron beam

Numbered closure procedure:

1. Run `cal_singleelectron_v1` (plan 23) with
   `macro/calibration/leadglass/calib_electron_validation.mac` at
   {50, 100, 200, 500, 1000} MeV.
2. For each energy point, aggregate lead-glass `eDep`, PMT photon
   count when optical photons are enabled, leakage energy, and event
   containment flags.
3. Fit `E_reco = a + b E_true` over the five points using bootstrap
   uncertainties from plan 04 §2. Store the fit covariance and
   per-point residuals.
4. Pass the fast-mode linearity check if every point has
   `abs(E_reco - E_fit) / E_true < 5%`.
5. Repeat the run with `WITH_SCINTILLATION=ON` and `OFF`. Apply the
   appropriate Cerenkov / eDep conversion before comparing the two
   modes.
6. Pass the optical on/off closure if the mode-pair residual at each
   energy point is < 5%. Otherwise, record the maximum residual as the
   lead-glass optical-tracking systematic in plan 45.
7. Produce `output/calibration/leadglass_linearity/summary.json`,
   `output/calibration/leadglass_linearity/rows.csv`, and a residual
   plot used by plan 47 rows that quote lead-glass calibration numbers.

## 5. Acceptance criteria

- §2 MIP closure passes.
- §3 yield reconciliation has DEC-2026-05-10-6 promoted or explicitly
  kept as a stub, and a propagated systematic.
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

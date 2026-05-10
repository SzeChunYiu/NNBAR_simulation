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
  - {test: scintillator photon yield (fast-mode 11136 vs optical table 0) reconciled, method: §3 cross-check, pass_when: chosen value defended in DEC}
  - {test: lead-glass linearity vs electron beam reference in {50, 100, 200, 500, 1000} MeV, method: §4 closure, pass_when: residual < 5%}
risks:
  - {risk: optical-enabled / fast-mode inconsistency in lead-glass response, mitigation: §4 paired sample after an optical mode is source-backed}
  - {risk: scintillator yield drift between SD constant (11136) and disabled optical table (0), mitigation: §3 explicit reconciliation}
estimated_effort: M
last_updated: 2026-05-10
---

# TPC ↔ Scintillator ↔ LeadGlass intercalibration

*Charter.* Anchor every sub-detector's energy/charge calibration to a
shared reference. The single reference here is *Geant4 truth* (deposited
energy at hit time); the audit ensures that derived quantities (electron
count, scintillator photon-equivalent, lead-glass calorimetric energy)
agree across overlap regions and between fast and future optical-enabled configurations.

The intercalibration is *not* a real-detector calibration; it is a
self-consistency audit of the simulation pipeline. Any discrepancy
exposed here propagates into a systematic via plan 45.

## 0.1 Wave 6 derivation — cross-subsystem energy anchor

### Physics derivation

**What is physically measured.** Intercalibration measures whether the
same Geant4 truth energy deposit maps consistently into TPC electron
count, scintillator photon-equivalent count, and lead-glass
calorimetric energy. The ground-truth quantity is `eDep` at hit time;
the derived quantities are calibration transforms with subsystem-
specific constants and possible non-linearities.

**Estimator rationale.** A minimum-ionising charged pion crossing both
TPC gas and scintillator gives a common dE/dx anchor because the same
Bethe--Bloch energy-loss physics underlies both detectors
`\cite{ParticleDataGroup:2024RPP,NISTSTAR}`. Plastic-scintillator
light yield and lead-glass calorimetric response then connect the
common energy-deposit scale to the detector-specific observables, with
BC-408 and lead-glass data sheets supplying the material-response
priors where source constants are insufficient
`\cite{SaintGobainBC408DataSheet,SchottSF5DataSheet}`. The correct
intercalibration estimator is therefore a set of closure residuals
against the same `eDep`, not a tuned rescaling chosen after looking at
the final event selection.

**Statistical character.** The per-hit truth `eDep` is deterministic
for a fixed Geant4 trajectory, while TPC electron counts are Poisson-
sampled and optical photons would add transport/detection variance
when enabled. The dominant current uncertainty is systematic:
scintillator fast-mode yield is source-backed but optical yield is
disabled, calibration macros are absent, and lead-glass optical-mode
linearity is not yet source-backed. These gaps become plan-45
intercalibration nuisances or blocked ledger rows.

### Logic gaps

- **MIP residual threshold <5%.** Grounding: §2 uses a practical
  closure threshold for TPC/scintillator agreement. `OPEN:` derive the
  allowed residual from downstream dE/dx/PID sensitivity in plans 27
  and 29, or replace with a detector-calibration requirement; target
  resolution date 2026-06-22.
- **Fast scintillator yield 11136 photons/MeV and optical yield 0.**
  Grounding: DEC-2026-05-10-6 and source line evidence in §3.
  `OPEN:` restore a nonzero optical yield with provenance or keep
  optical-mode rows blocked; target resolution date 2026-06-15.
- **Lead-glass scan energies {50, 100, 200, 500, 1000} MeV and <5%
  residual.** Grounding: §4 electron-beam closure design. `OPEN:`
  confirm these points bracket the photon/electron energies in thesis
  ledger rows and derive the 5% residual from mass/energy-resolution
  budgets; target resolution date 2026-06-22.
- **Calibration sample macros.** Grounding: §2 and §4 explicitly mark
  historical macro paths as absent rather than source facts. `OPEN:`
  implement or replace `cal_singlepion_mip_v1` and
  `cal_singleelectron_v1` before promoting this plan out of draft;
  target resolution date 2026-06-15.
- **Gain/light non-linearities.** Grounding: plan 02 has a seam but no
  calibrated curve. `OPEN:` decide whether non-linearity is negligible
  in the thesis energy range or register a plan-45 nuisance; target
  resolution date 2026-06-29.

### Closure test for the derivation

1. Build per-hit truth tables with `eDep`, path length, subsystem id,
   and all derived observables for the MIP pion and electron
   calibration samples.
2. For TPC/scintillator MIP tracks, compare dE/dx residuals against a
   common Bethe--Bloch/NIST reference and bootstrap the detector
   difference.
3. For scintillator fast/optical modes, compute photons per MeV by
   layer and stop with `blocked-disabled-optics` if the source optical
   yield remains zero.
4. For lead glass, fit the electron-scan response and record residuals
   per energy point. Store all constants, covariance matrices, and
   failure modes in plan 47; do not tune downstream cuts until the
   intercalibration residual is either closed or propagated as a
   systematic.

## 1. Reference quantity

For every hit in every SD, Geant4 records `eDep` (MeV).
Intercalibration verifies that downstream derived quantities are
consistent with `eDep`:

- TPC: electrons = `eDep / W_value` (W = 23.6 eV per plan 17 §3).
- Scintillator: fast-mode photon-equivalent count = `eDep × 11136`
  in `src/Sensitive_Detector/ScintillatorSD.cc`; optical-mode material
  yield is currently disabled in `src/Detector_Module/Scintillator_geometry.cc`.
- Lead glass: calorimetric energy = `eDep × calibration_factor`
  (currently 1.0; plan 18 audits whether saturation/linearity
  corrections are needed).
- PMT: photons recorded directly via optical-photon tracking only after
  an optical-enabled mode is source-backed; per-PMT efficiency Class C.

## 2. TPC ↔ Scintillator MIP closure

Numbered closure procedure:

1. Run `cal_singlepion_mip_v1` (plan 23) with the pion momentum fixed
   in the MIP region and the origin at the foil center, after L2/L3
   restores or writes the missing MIP macro. The historical target
   path `macro/calibration/scintillator/calib_pion_mip.mac` is
   classified as `blocked-absent` in plan 23 §3, so it is not cited as
   a currently existing input file.
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

A+ verifier status on 2026-05-10: the fast-mode scintillator SD
stores a photon-equivalent count as `energyDeposit*11136.` at current
L3 line 142 of `src/Sensitive_Detector/ScintillatorSD.cc`. The material
optical-properties table does **not** contain a 10000 photons/MeV
source value; current L3 line 82 of
`src/Detector_Module/Scintillator_geometry.cc` sets
`SCINTILLATIONYIELD` to `0./MeV` and only leaves a comment with older
candidate values. The previous 10000-vs-11136 comparison was therefore
not source-observed and is replaced by the disabled-optical-yield gap
below.

**DEC-2026-05-10-6 stub — scintillator yield mode policy.**
Context: fast-mode `ScintillatorSD` stores a photon-equivalent count
using 11136 photons/MeV, while the current optical material table has
`SCINTILLATIONYIELD = 0./MeV`. Decision: keep **11136 photons/MeV** as
the production value for fast-mode photon-equivalent rows because
existing reconstruction code consumes that column. Treat optical-mode
scintillation yield as **blocked-disabled** until a nonzero material
property is restored with provenance. Follow-up: promote this stub to
the decision log after the first paired fast/optical closure run or
a source-backed optical yield is committed.

Numbered closure procedure:

1. Source inventory: cite `src/Sensitive_Detector/ScintillatorSD.cc`
   for 11136 photons/MeV and
   `src/Detector_Module/Scintillator_geometry.cc` for the current
   disabled optical `SCINTILLATIONYIELD = 0./MeV`.
2. Run the same scintillator calibration macro twice only after the
   optical table has a nonzero, provenance-backed scintillation yield:
   the fast-mode photon-equivalent output and the future optical-photon
   transport output. The current L3 worktree has no source-observed
   `WITH_SCINTILLATION` switch, so the optical leg is blocked until that
   mode is restored or replaced.
3. For each run, compute `scint_yield_observed = photons / eDep_MeV`
   per hit and aggregate by scintillator layer and stave.
4. If optical yield remains zero, stop with `blocked-disabled-optics`
   rather than scaling zero-yield output into agreement. If a nonzero
   yield is restored, convert optical-mode photon counts onto the
   fast-mode convention using `yield_fast / yield_optical_table`.
5. Record `yield_fast = 11136`, the source-backed
   `yield_optical_table`, the scale factor, and the observed residuals
   in `output/calibration/scint_yield_reconciliation/summary.json`.
6. Pass if the scaled optical-mode yield and fast-mode yield agree
   within 5% after bootstrap uncertainty. Otherwise, plan 45 receives a
   scintillator-yield nuisance equal to the measured residual until a
   vendor/spec citation or data calibration narrows it.

## 4. Lead-glass calibration vs electron beam

Numbered closure procedure:

1. Run `cal_singleelectron_v1` (plan 23) at
   {50, 100, 200, 500, 1000} MeV after L2/L3 restores or writes a
   source-backed macro for that scan. The historical target path
   `macro/calibration/leadglass/calib_electron_validation.mac` is
   verified absent in the L3 worktree on 2026-05-10 (plan 23 §5), so
   this plan treats it as `OPEN(L2/L3, target 2026-06-15)` rather than
   an existing input file.
2. For each energy point, aggregate lead-glass `eDep`, PMT photon
   count when optical photons are enabled, leakage energy, and event
   containment flags.
3. Fit `E_reco = a + b E_true` over the five points using bootstrap
   uncertainties from plan 04 §2. Store the fit covariance and
   per-point residuals.
4. Pass the fast-mode linearity check if every point has
   `abs(E_reco - E_fit) / E_true < 5%`.
5. Repeat the run in fast and optical-enabled modes once the optical
   mode is source-backed. Apply the appropriate Cerenkov / eDep
   conversion before comparing the two modes.
6. Pass the fast/optical closure if the mode-pair residual at each
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
- §4 fast/optical closure passes within stated tolerance once optical mode is source-backed.

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

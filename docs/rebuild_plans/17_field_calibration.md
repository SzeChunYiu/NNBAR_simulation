---
id: 17_field_calibration
title: TPC field calibration — drift field, drift velocity, gain
version: 0.1
status: draft
owner: Sim Production
depends_on: [00_README, 01_realism_contract, 07_simulation_atomic_walkthrough]
inputs:
  - {path: NNBAR_Detector/src/ElectricField.cc, schema: field source}
  - {path: NNBAR_Detector/src/Sensitive_Detector/TPCSD.cc, schema: TPC SD}
  - {path: NNBAR_Detector/src/DetectorConstruction.cc, schema: field-manager attachment}
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
last_updated: 2026-05-10
---

# TPC field calibration

*Charter.* Audit the TPC drift field configuration, the W-value used
to convert energy deposit to ionisation, and the gain-saturation
behaviour. These constants are Class C (plan 01 §2.3) and propagate
into every dE/dx-derived observable.

## 1. Field source

`NNBAR_Detector/src/ElectricField.cc` provides the TPC drift
field through `ElectricField::GetFieldValue`. `DetectorConstruction.cc`
attaches the field manager to **only `TPC_output[0]` and
`TPC_output[1]`** at the current L3 lines 259--260 — the first two LVs
of the 12 TPC modules.

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

The TPC SD (`src/Sensitive_Detector/TPCSD.cc`) uses **W-value = 23.6 eV** at the current L3 line 99 to convert
step `eDep` to electron count via Poisson sampling. The reference
W-value for the Ar/CO₂ mixture (90/10) is 26–27.4 eV depending on
the source (PDG; Sauli, *Principles of operation of multiwire
proportional and drift chambers*, CERN 77–09).

This is a documented discrepancy
(`docs/detector_fundamental_question_tree.md` §3). Plan 17 locks the
production-vs-reference policy as follows:

**DEC-2026-05-10-5 stub — TPC W-value production constant.**
Context: the as-built `TPCSD` output already used 23.6 eV, while the
gas-reference range for Ar/CO₂ (90/10) is approximately 26.0–27.4 eV.
Decision: keep **23.6 eV** as the production constant for all current
rebuild reproduction rows and frozen `sig_foil_v3`-style samples,
because changing it would silently rewrite existing electron-count and
dE/dx observables. Treat **26.0 eV** as the reference alternative for
closure plots and systematic reweighting, not as the default until a
new dataset version is regenerated. Follow-up: promote this stub to the
decision log and update the plan 09 Class C row when the TPC calibration
registry exists.

Production-vs-reference handling:

| Quantity | Value | Role | Rationale |
|---|---:|---|---|
| `tpc_w_value_ev.production` | 23.6 eV | default conversion in current samples | identity-default; matches `src/Sensitive_Detector/TPCSD.cc` and existing ledger rows |
| `tpc_w_value_ev.reference` | 26.0 eV | closure/reweighting target | rounded Ar/CO₂ literature value, avoids over-precision before gas-mixture validation |
| `tpc_w_value_ev.upper_reference` | 27.4 eV | systematic envelope endpoint | preserves the high end of the cited reference range |

The propagation rule is deterministic: for a step with fixed energy
deposit, the expected electron count scales as
`N_e(reference) = N_e(production) * 23.6 / W_reference`. Thus the 26.0
eV closure point is a −9.2% electron-count shift relative to the
current production output; the 27.4 eV endpoint is a −13.9% shift. Plan
45 should round this to a symmetric ±15% "TPC W-value" nuisance until a
dedicated gas-gain calibration narrows the range.

Drift velocity is set indirectly through Geant4's stepper handling;
the rebuild does not currently override it. A+ verifier status on
2026-05-10: no `TPCDriftManager` source file and no `WITH_GARFIELD_GPU`
code path are present in the L3 worktree, so Garfield/TPC drift-manager
claims are future TODOs rather than current source facts.

## 4. Gain and saturation

Geant4 does not natively model gas-gain saturation. The current
simulation stores the bare ionisation electron count
(`src/Sensitive_Detector/TPCSD.cc`, current L3 line 142 stores the
count through `SetPhotons`); the reconstruction's `dedx` is computed
from this count and the step length.

Real-detector gain saturation matters for high-dE/dx tracks
(stopping protons, low-energy pions). The seam in plan 02
`energy_nonlinearity` slot can install a saturation curve when
real-data calibration is available. Until then, gain saturation is
limitation L3 (plan 01 §6).

## 5. Acceptance criteria

- §2 field map produced; uniformity within 1%.
- §3 W-value DEC stub recorded; production/reference values chosen and
  promoted to the decision log before any regenerated TPC sample is
  frozen.
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

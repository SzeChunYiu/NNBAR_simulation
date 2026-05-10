---
id: 27_subsystem_dedx
title: Subsystem — dE/dx (leaf C.2)
version: 0.1
status: draft
owner: Charged-PID POG
depends_on: [00_README, 17_field_calibration, 23_sample_calibration_aux, 24_reconstruction_question_tree, 25_subsystem_tpc_hits_to_tracks, 26_subsystem_track_fit_and_pulls]
outputs:
  - {path: docs/rebuild_plans/27_subsystem_dedx.md, schema: this file}
acceptance:
  - {test: dE/dx vs βγ matches Bethe-Bloch on cal_singlepion / cal_singleproton, method: closure plot, pass_when: residual < 5%}
  - {test: truncated-mean estimator chosen with cut fraction recorded, method: §2 review, pass_when: signed in DEC}
risks:
  - {risk: TPC W-value mismatch (plan 17) shifts dE/dx scale, mitigation: §3 paired audit with W=23.6 vs reference}
estimated_effort: M
last_updated: 2026-05-09
---

# Subsystem — dE/dx

*Charter.* Owns leaf C.2 (plan 24 §3). dE/dx is the headline TPC
PID variable. Estimator choice and calibration determine π/p
separation.

## 1. Estimator

Per-track dE/dx is the energy deposit per unit length, with a
truncated-mean estimator to suppress Landau-tail outliers:

```
dE/dx = mean( sorted(eDep / step_length)[k_low : k_high] )
```

Cut fractions: drop top 30%, bottom 10% (literature default; revisit
on calibration sample). Recorded as DEC entry.

Per plan 24 C.2 schema:

| Class A inputs | Forbidden Class B |
|---|---|
| C.1 charged-candidate table; TPC step columns `Event_ID`, `eDep`, `TrackLength`, `x`, `y`, `z`, `t`, `photons`, `step_info` | `Name`, `Track_ID`, `Parent_ID`, `origin_vol_name`, `particle_x`, `particle_y`, `particle_z` |

Current implementation citation: `reconstruct_charged_objects`
(`reconstruction.py:430-700`, plan 08 §3.4) already emits `dedx`,
but the value is downstream of the current truth-name candidate gate.

Output schema: `{event_id, charged_candidate_id, dedx_mev_per_cm,
estimator, n_steps_used, path_length_cm, low_truncation_fraction,
high_truncation_fraction, calibration_source}`.

## 2. Calibration anchor

Plan 17 W-value (23.6 eV in TPCSD; reference 26-27.4 eV). dE/dx
output is `(eDep / step_length)`; the W-value enters via the
electron count downstream.

Calibration anchor: MIP π+ from `cal_singlepion_mip_v1` (plan 23).
Mean dE/dx at MIP = ~1.6 keV/cm in Ar/CO₂ 90/10 (literature).
Closure: simulator output should match within 5%.

## 3. Bethe-Bloch closure

For each sample in plan 23 charged set, compute mean dE/dx vs βγ.
Fit to Bethe-Bloch:

```
-<dE/dx> = K (z²/β²) [½ ln(2 m_e c² β² γ² T_max / I²) - β² - δ/2]
```

Residuals < 5% across [0.5, 5] in βγ is the pass.

## 4. Saturation

Real TPC gas gain saturates at high dE/dx (stopping protons). Geant4
does not model gain saturation; the rebuild applies it via the
digitisation seam (plan 02 `energy_nonlinearity`) when real-data
calibration becomes available.

For now, the simulation produces *unsaturated* dE/dx; this is
limitation L3 (plan 01 §6) and propagates to plan 45 systematics.

## 5. Acceptance criteria

- §3 closure within 5% across the charged calibration set.
- §1 truncated-mean cut fractions documented in DEC.
- §4 saturation limitation noted in plan 47 ledger for any
  high-dE/dx-quoted result.

## 6. Dependencies

- **17, 23, 25, 26** — inputs.
- *Consumed by:* plan 29 (charged PID), plan 38 (ladder leaf C.2).

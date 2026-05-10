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
  - {test: dE/dx vs βγ matches Bethe-Bloch on cal_singlepion_50to600MeV_v2 / cal_singleproton_50to500MeV_v2, method: closure plot, pass_when: residual < 5%}
  - {test: truncated-mean estimator chosen with cut fraction recorded, method: §2 review, pass_when: signed in DEC}
risks:
  - {risk: TPC W-value mismatch (plan 17) shifts dE/dx scale, mitigation: §3 paired audit with W=23.6 vs reference}
estimated_effort: M
last_updated: 2026-05-10
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
(`reconstruction.py:352-431`, plan 08 §3.4) already emits `dedx`,
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

### 2.1 Alternative comparison rows

| Alternative | Source paper / codebase | NNBAR-specific adaptation | Expected ladder leaf delta |
|---|---|---|---|
| Arithmetic mean baseline | Existing `reconstruct_charged_objects` (`reconstruction.py:352-431`) | Preserve current `dedx` computation as a reproducibility reference after removing any C.1 truth-name candidate gate. | No intended C.2 gain; establishes the current tail-sensitive baseline for plan 38. |
| Truncated mean | Standard TPC PID / ALICE-style charged-particle dE/dx | Sort per-step `eDep / step_length`, drop bottom 10% and top 30%, and record the chosen cut fractions in the C.2 schema. | Expected to improve C.2 stability against Landau tails and reduce C.5 PID confusion. |
| Landau/MPV fit | TPC cluster-charge Landau-Gaussian fit literature | Use only when a track has enough Class A TPC samples; report fit status and fall back to truncated mean for sparse tracks. | Better high-tail control for long tracks, but limited gain for short NNBAR TPC segments. |
| Bethe-Bloch residual template | Plan 23 calibration samples plus Bethe-Bloch closure in §3 | Convert dE/dx to species-agnostic residuals versus βγ bins only in calibration/validation; production C.2 remains truth-free. | Improves calibration diagnostics for C.2 but does not by itself replace plan 29 PID scoring. |

## 3. Closure-test specification

1. **Dataset ids:** `cal_singlepion_50to600MeV_v2` and
   `cal_singleproton_50to500MeV_v2` from plan 03.
2. **Observable:** mean reconstructed `dedx_mev_per_cm` versus
   validation-only βγ bins, with pion and proton curves reported
   separately.
3. **Fitter / model:** fit the Bethe-Bloch form
   `-<dE/dx> = K (z^2/beta^2) [0.5 ln(2 m_e c^2 beta^2 gamma^2 T_max / I^2) - beta^2 - delta/2]`
   after the C.2 estimator has produced Class A dE/dx values; truth
   momentum enters only in the closure fitter.
4. **Pass criterion:** residual < 5% across βγ in `[0.5, 5]`; if the
   TPC W-value discrepancy dominates, record the paired plan 17
   calibration limitation and do not tune PID thresholds silently.

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

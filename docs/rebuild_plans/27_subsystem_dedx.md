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

### 1.1 Leaf schema block

Leaf C.2 — dE/dx estimator

- **inputs (Class A):** C.1 charged-candidate rows plus TPC step
  `Event_ID`, `eDep`, `TrackLength`, `x`, `y`, `z`, `t`,
  `photons`, `step_info`, and any V.2 path-length/covariance fields
  used to normalise the step length.
- **forbidden (Class B):** `Name`, `Track_ID`, `Parent_ID`,
  `origin_vol_name`, `particle_x`, `particle_y`, `particle_z`.
- **decision rule:** compute dE/dx from Class A energy deposits and
  path length only, using the signed estimator and truncation
  fractions; truth species and truth momentum are excluded until the
  validation fitter consumes frozen output.
- **output schema:** `event_id: int`, `charged_candidate_id: int`,
  `dedx_mev_per_cm: float`, `estimator: str`,
  `n_steps_used: int`, `path_length_cm: float`,
  `low_truncation_fraction: float`,
  `high_truncation_fraction: float`, `calibration_source: str`.
- **allowed truth use:** `validation_only` for Bethe-Bloch closure,
  ladder scoring, and calibration residual plots.
- **downstream consumers:** plans 29, 38, 40, and charged-PID
  systematics in plan 45.

### 1.2 Column contract

| Class A inputs | Forbidden Class B |
|---|---|
| C.1 charged-candidate table; TPC step columns `Event_ID`, `eDep`, `TrackLength`, `x`, `y`, `z`, `t`, `photons`, `step_info` | `Name`, `Track_ID`, `Parent_ID`, `origin_vol_name`, `particle_x`, `particle_y`, `particle_z` |

Current implementation citation: `reconstruct_charged_objects`
(`charged.py:149-228`, plan 08 §3.4) already emits `dedx`,
but the value is downstream of the current truth-name candidate gate.

Output schema: `{event_id, charged_candidate_id, dedx_mev_per_cm,
estimator, n_steps_used, path_length_cm, low_truncation_fraction,
high_truncation_fraction, calibration_source}`.

### 1.3 Machine-readable C.2 dE/dx fixture

The C.2 fixture freezes the per-candidate ionisation estimator before
PID scoring or Bethe-Bloch closure consumes truth labels. It stores one
row per charged candidate plus a contribution sidecar for the TPC
samples used by the estimator:

| Fixture field | Meaning / invariant |
|---|---|
| `event_id`, `charged_candidate_id` | join key inherited from C.1/V.1 |
| `estimator_id` | stable method/version label, such as `truncated_mean_v1` |
| `dedx_mev_per_cm` | finite estimator value, or null with a failure reason |
| `path_length_cm`, `path_length_source` | positive normalisation length and its source label |
| `n_steps_used` | number of Class A TPC samples after quality cuts |
| `low_truncation_fraction`, `high_truncation_fraction` | signed fractions used by the estimator |
| `truncation_applied` | whether the configured estimator actually removed samples |
| `dedx_quality_state`, `dedx_failure_reason` | §5 quality contract in machine-readable form |
| `calibration_source` | provenance label for the calibration constants used |

The contribution sidecar is keyed by `(event_id, charged_candidate_id,
estimator_id)` and records the ordered TPC sample ids, raw `eDep`, path
increment, and whether each sample survived truncation. Dropping
`Name`, `Track_ID`, `Parent_ID`, and validation-only momentum/species
fields from production input must not change the C.2 fixture; only
closure residual artifacts may read those validation labels.

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
| Arithmetic mean baseline | Existing `reconstruct_charged_objects` (`charged.py:149-228`) | Preserve current `dedx` computation as a reproducibility reference after removing any C.1 truth-name candidate gate. | No intended C.2 gain; establishes the current tail-sensitive baseline for plan 38. |
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

## 5. Calibration-quality and DQM handoff

C.2 must expose estimator health separately from the PID decision. The
quality fields below are written with the dE/dx row and aggregated by
plan 66 per run:

| Field | Meaning | Consumer |
|---|---|---|
| `dedx_quality_state` | `pass`, `warn`, `fail`, or `not_applicable` for the estimator | plans 29, 66 |
| `dedx_failure_reason` | first blocking reason, if any | plan 47 caveats |
| `path_length_source` | `v2_covariance`, `class_a_track_length`, or `legacy_span` | plans 26, 38 |
| `truncation_applied` | whether the signed low/high fractions were used | plan 05 DEC audit |
| `calibration_residual_fraction` | validation-only Bethe-Bloch residual once closure runs | plan 45 systematics |

Quality semantics:

- `pass` means the dE/dx value is finite, uses a finite positive path
  length, and records the estimator and truncation fractions.
- `warn` means the value is finite but uses a degraded path-length source,
  too few samples for the preferred truncation, or a calibration residual
  outside the advisory band.
- `fail` means the estimator is non-finite, has non-positive path length,
  or depends on a production-forbidden truth species/name gate.
- `not_applicable` is reserved for candidates rejected before C.2 is
  attempted.

Plan 29 may consume `dedx_mev_per_cm` only when `dedx_quality_state` is
`pass` or an explicitly accepted `warn`. A hard PID veto based on these
quality fields requires a plan 05 decision and a plan 38 C.2/C.5 ladder
comparison.

## 6. Stage E.1 implementation handoff

For L3's charged-side redesign, C.2 should be a typed estimator module:

1. Input rows come from C.1 candidates, V.2 path-length/covariance
   outputs, and Class A TPC energy-deposit samples.
2. The arithmetic-mean baseline is preserved as a named reproduction
   mode; the default production mode is the signed truncated mean once
   the DEC records its low/high fractions.
3. The module writes §1 physics fields and §5 quality fields in one row
   per charged candidate, with nulls plus reasons when C.2 is not
   applicable.
4. Bethe-Bloch residuals and truth momentum live only in the closure
   artifact namespace after the production C.2 table is frozen.
5. Plan 45 receives a calibration nuisance input from the closure
   residual, not from hand-edited PID thresholds.

## 7. Acceptance criteria

- §3 closure within 5% across the charged calibration set.
- §1 truncated-mean cut fractions documented in DEC.
- §4 saturation limitation noted in plan 47 ledger for any
  high-dE/dx-quoted result.

## 8. Dependencies

- **17, 23, 25, 26** — inputs.
- *Consumed by:* plan 29 (charged PID), plan 38 (ladder leaf C.2).

---
id: 28_subsystem_range_and_stopping
title: Subsystem — range and stopping (leaf C.3)
version: 0.1
status: draft
owner: Charged-PID POG
depends_on: [00_README, 18_intercalibration, 23_sample_calibration_aux, 24_reconstruction_question_tree, 25_subsystem_tpc_hits_to_tracks]
outputs:
  - {path: docs/rebuild_plans/28_subsystem_range_and_stopping.md, schema: this file}
acceptance:
  - {test: scintillator range estimate on cal_singleproton_50to500MeV_v2 vs validation path-length residual < 1 cm, method: per-sample closure, pass_when: pass}
  - {test: Bragg-peak position resolved within scintillator bar pitch on stopping protons, method: §3 closure, pass_when: pass}
risks:
  - {risk: scintillator hit pitch limits range resolution, mitigation: §3 documented hardware floor}
estimated_effort: S
last_updated: 2026-05-10
---

# Subsystem — range and stopping

*Charter.* Owns leaf C.3 (plan 24 §3). The scintillator stopping
range distinguishes short-range protons from long-range pions.

## 1. Range estimator

Match scintillator hits to TPC track via configurable angle and
distance (plan 08 §3.4: `charged_scintillator_match_angle_deg = 10°`,
`charged_scintillator_match_distance_cm = 15 cm`).

Range = max distance from track entry to last associated scintillator
hit, projected along the track direction.

Outputs: `range_cm`, `range_eDep` (energy in matched hits).

Per plan 24 C.3 schema:

| Class A inputs | Forbidden Class B |
|---|---|
| C.1 charged-candidate table; V.2 direction table; C.4 matched scintillator hit columns `Event_ID`, `x`, `y`, `z`, `t`, `eDep`, `photons`, `module_ID`, `vol_name`, `step_info`; scintillator geometry side-car | `Name`, `Track_ID`, `Parent_ID`, `origin_vol_name`, `particle_x`, `particle_y`, `particle_z` |

Current implementation citation: `reconstruct_charged_objects`
(`reconstruction.py:352-431`, plan 08 §3.4) reports
`scintillator_range` after matching hits by angular/distance cuts or,
for sparse legacy tables, exact `Track_ID` fallback. The fallback is
not a production C.3 rule.

Output schema: `{event_id, charged_candidate_id, range_cm,
range_edep_mev, n_scintillator_hits, last_hit_module_id,
bragg_peak_position_cm, range_valid}`.

## 2. Bragg-peak

For stopping protons, the energy-vs-position profile peaks near the
end of the range. The Bragg-peak position is the inflection in
cumulative eDep as a function of distance along the track.

The Wave 2 baseline keeps Bragg information as a diagnostic feature:
`bragg_peak_position_cm` is written when at least three matched
scintillator hits define an ordered profile, and is null otherwise.
Promotion into PID requires a plan 29 / plan 57 comparison showing
incremental C.5 discrimination beyond `{range_cm, dedx_mev_per_cm}`
without consuming truth labels in the production decision path.

### 2.1 Alternative comparison rows

| Alternative | Source paper / codebase | NNBAR-specific adaptation | Expected ladder leaf delta |
|---|---|---|---|
| Farthest matched scintillator hit | Existing `reconstruct_charged_objects` (`reconstruction.py:352-431`) | Preserve the angular/distance match as the reproduction baseline; disable the exact `Track_ID` fallback for production C.3. | Baseline C.3 range with known granularity floor from scintillator pitch. |
| Projected path-length integration | Range-stack / sampling-calorimeter reconstruction practice | Project V.2 track direction through ordered scintillator modules and accumulate Class A hit distances until the last in-time module. | Expected to reduce range bias when hits skip modules or the farthest-hit point is noisy. |
| Bragg-profile endpoint fit | Stopping-proton Bragg-curve reconstruction | Fit cumulative eDep versus projected distance and report `bragg_peak_position_cm` plus fit quality. | Improves stopping-proton discrimination for C.5 when enough scintillator hits exist. |
| PSTAR-constrained range check | NIST PSTAR proton ranges used only in validation | Compare reconstructed range to kinetic-energy bins inside closure; do not use truth KE or species in production. | Adds calibration/systematics leverage for C.3 without loosening Class A production rules. |

## 3. Closure-test specification

1. **Dataset id:** `cal_singleproton_50to500MeV_v2` from plan 03,
   with stopping-proton slices identified only inside validation.
2. **Observable:** reconstructed `range_cm`, `range_edep_mev`, and
   `bragg_peak_position_cm` versus validation path length and initial
   kinetic-energy bins.
3. **Fitter / model:** compare mean range to PSTAR proton ranges and
   fit the cumulative eDep profile to locate the Bragg inflection;
   truth path length is a validation target, not an estimator input.
4. **Pass criterion:** mean range agrees within 1 cm or one
   scintillator bar pitch, whichever is larger; Bragg peak is resolved
   within one bar pitch for stopping protons.

## 4. Acceptance criteria

- §3 closure passes.
- §2 Bragg-peak diagnostic is either written with a valid fit-status
  flag or explicitly null with a reason; any PID promotion cites a
  plan 38 C.3/C.5 ladder delta.

## 5. Dependencies

- **18, 23, 24, 25** — inputs.
- *Consumed by:* plan 29 (PID).

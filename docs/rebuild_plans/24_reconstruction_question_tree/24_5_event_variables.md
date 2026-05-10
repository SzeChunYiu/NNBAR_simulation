---
id: 24_5_event_variables_branch
title: Reconstruction question tree - event-variable branch
version: 0.1
status: draft
owner: Methodology Council
parent: 24_reconstruction_question_tree
last_updated: 2026-05-09
---

# Reconstruction question tree - event-variable branch

This file is a split-out branch of `docs/rebuild_plans/24_reconstruction_question_tree.md`
created to keep each plan file under the 500-line cap. It inherits the
truth-leakage gate, acceptance criteria, dependencies, and references from
plan 24.

## 5. Event-variable branch

**What is the irreducible event-shape evidence that distinguishes a
multi-pion annihilation from cosmic / beam backgrounds?**

Answer now: combinations of calorimeter total energy, sphericity (or
Fox-Wolfram moments), longitudinal/transverse split, visible
invariant mass, and timing-window sums distinguish the multi-pion
final state from single-track cosmics or thermal beam-induced
events.

### 5.1 Leaves under event variables

| Leaf ID | Decision |
|---|---|
| `E.1` | Total calorimeter energy (Σ scint + lead-glass eDep) |
| `E.2` | Per-hemisphere split (upper/lower scint, upper/lower LG) |
| `E.3` | Longitudinal energy `E_L = Σ E_i cos α_i` |
| `E.4` | Transverse energy `E_T = Σ E_i sin α_i` |
| `E.5` | Sphericity (eigenvalue decomposition of momentum tensor) |
| `E.6` | Fox-Wolfram moments (alternative event-shape) |
| `E.7` | Visible invariant mass from object 4-vectors |
| `E.8` | In-time / out-of-time energy split (Ch 7 timing window) |
| `E.9` | Object multiplicities (charged / photon / π⁰) |

**Owning subsystem plan:** plan 36 (event variables).

Leaf E.1: calorimeter hits → total visible calorimeter energy
  inputs (Class A): Scintillator and LeadGlass hit columns
                    (Event_ID, eDep, t, x, y, z, module_ID,
                    vol_name, step_info) plus optional calibrated
                    photon-count columns from plan 18
  forbidden (Class B): Track_ID, Parent_ID, Name, origin_vol_name,
                       Interaction ancestry, truth primary energy
  decision rule: sum calibrated deposited energy over scintillator
                 and lead-glass hits per event, preserving detector
                 sub-sums; plan 08 §3.6 names this surface
                 `calorimeter_edep`.
  output schema: {event_id: int64, total_calorimeter_energy_mev:
                  float64, scintillator_energy_mev: float64,
                  leadglass_energy_mev: float64,
                  n_calorimeter_hits: int32,
                  calibration_version: string}
  allowed truth use: validation_only
  downstream consumers: S.1, S.5, S.6; plans 36, 37, 41

Leaf E.2: calorimeter hits + geometry → hemisphere energy split
  inputs (Class A): Scintillator and LeadGlass hit columns
                    (Event_ID, eDep, x, y, z, module_ID, vol_name),
                    geometry side-cars, and the plan 36 hemisphere
                    convention
  forbidden (Class B): Track_ID, Parent_ID, Name, origin_vol_name,
                       truth event topology labels
  decision rule: partition deposited energy by the documented upper /
                 lower detector convention (plan 36 §3, sign of y in
                 the baseline) and report scintillator and lead-glass
                 sub-sums separately.
  output schema: {event_id: int64, upper_scintillator_mev: float64,
                  lower_scintillator_mev: float64,
                  upper_leadglass_mev: float64,
                  lower_leadglass_mev: float64,
                  hemisphere_convention: string}
  allowed truth use: validation_only
  downstream consumers: S.5, S.6; plans 36, 37, 41

Leaf E.3: reconstructed objects → longitudinal energy EL
  inputs (Class A): selected charged, photon, and π0 object energies
                    and directions; V.4 event vertex; beam-axis
                    convention from geometry
  forbidden (Class B): truth particle momenta, truth event axis,
                       Track_ID, Parent_ID, Name
  decision rule: compute `EL = Σ E_i cos(alpha_i)` with alpha measured
                 between each reconstructed object direction and the
                 declared longitudinal axis, matching the Ch 9
                 definition quoted in plan 08 §3.6.
  output schema: {event_id: int64, longitudinal_energy_mev: float64,
                  n_objects_used: int32, axis_definition: string,
                  signed_longitudinal_energy_mev: float64}
  allowed truth use: validation_only
  downstream consumers: S.6; plans 36, 37, 41

Leaf E.4: reconstructed objects → transverse energy ET
  inputs (Class A): selected charged, photon, and π0 object energies
                    and directions; V.4 event vertex; beam-axis
                    convention from geometry
  forbidden (Class B): truth particle momenta, truth event axis,
                       Track_ID, Parent_ID, Name
  decision rule: compute `ET = Σ E_i sin(alpha_i)` using the same
                 object list and longitudinal-axis convention as E.3;
                 invalid objects contribute neither energy nor truth
                 substitutions.
  output schema: {event_id: int64, transverse_energy_mev: float64,
                  n_objects_used: int32, axis_definition: string,
                  object_selection_version: string}
  allowed truth use: validation_only
  downstream consumers: S.6; plans 36, 37, 41

Leaf E.5: reconstructed object momenta → sphericity
  inputs (Class A): charged, photon, and π0 reconstructed momenta or
                    energy-direction four-vectors after C/P selection
  forbidden (Class B): truth particle momenta, truth multiplicities,
                       Track_ID, Parent_ID, Name
  decision rule: build the standard sphericity tensor from
                 reconstructed three-momenta and use its eigenvalues
                 to compute the scalar sphericity; plan 08 §3.6 records
                 this as the current event-shape baseline.
  output schema: {event_id: int64, sphericity: float64,
                  eigenvalues: float64[3], n_objects_used: int32,
                  tensor_normalization: string}
  allowed truth use: validation_only
  downstream consumers: S.4, S.6; plans 36, 37, 41

Leaf E.6: reconstructed object momenta → Fox-Wolfram moments
  inputs (Class A): charged, photon, and π0 reconstructed momenta or
                    energy-direction four-vectors after C/P selection
  forbidden (Class B): truth particle momenta, truth decay topology,
                       Track_ID, Parent_ID, Name
  decision rule: compute normalized Fox-Wolfram moments from all
                 reconstructed object pairs and record thrust as the
                 plan 36 companion shape variable; these are alternate
                 event-shape discriminants and do not replace E.5
                 until ladder-scored.
  output schema: {event_id: int64, fox_wolfram_h0: float64,
                  fox_wolfram_h2: float64, fox_wolfram_h4: float64,
                  thrust: float64, n_objects_used: int32,
                  moment_order_max: int32}
  allowed truth use: validation_only
  downstream consumers: S.6; plans 36, 37, 41

Leaf E.7: reconstructed object four-vectors → visible invariant mass
  inputs (Class A): accepted charged-object four-vectors, photon
                    four-vectors, π0 fitted candidates, and their
                    covariance summaries
  forbidden (Class B): truth visible mass, truth particle four-vectors,
                       truth decay ancestry, Track_ID, Parent_ID, Name
  decision rule: sum reconstructed visible four-vectors and compute
                 `sqrt(E^2 - |p|^2)`, recording failures when the
                 object covariance or energy is invalid; plan 08 §3.6
                 treats the result as an analysis surface.
  output schema: {event_id: int64, visible_invariant_mass_mev:
                  float64, visible_energy_mev: float64,
                  visible_momentum_mev: float64[3], n_objects_used:
                  int32, mass_valid: bool}
  allowed truth use: validation_only
  downstream consumers: S.3, S.6; plans 36, 37, 41

Leaf E.8: calorimeter hit timing → in-time / out-of-time energy split
  inputs (Class A): Scintillator and LeadGlass hit columns
                    (Event_ID, eDep, t, x, y, z, module_ID), V.4
                    vertex time/position when available, and Ch 7
                    timing-window constants
  forbidden (Class B): truth particle time of flight, Track_ID,
                       Parent_ID, Name, Interaction ancestry
  decision rule: classify hit energy as in-time or out-of-time using
                 reconstructed timing residuals and the configured Ch 7
                 window; truth flight time can only be used in closure
                 plots.
  output schema: {event_id: int64, in_time_energy_mev: float64,
                  out_of_time_energy_mev: float64,
                  timing_window_ns: float64,
                  n_in_time_hits: int32, n_out_of_time_hits: int32,
                  timing_reference: string}
  allowed truth use: validation_only
  downstream consumers: S.1, S.6; plans 36, 37, 41

Leaf E.9: selected reconstructed objects → object multiplicities
  inputs (Class A): post-rejection charged-object table (C.6),
                    photon-like object table (P.2-P.4), selected π0
                    table (P.5-P.7), and validity flags
  forbidden (Class B): truth multiplicities, truth particle names,
                       Track_ID, Parent_ID, Interaction ancestry
  decision rule: count only reconstruction objects that pass their
                 observable validity and rejection gates, preserving
                 separate charged, photon, and π0 multiplicities for
                 selection and cut-flow accounting.
  output schema: {event_id: int64, n_charged: int32,
                  n_photons: int32, n_pi0: int32,
                  n_rejected_charged: int32,
                  multiplicity_rule_version: string}
  allowed truth use: validation_only
  downstream consumers: S.2, S.6; plans 36, 37, 41

### Next measurement (event-variable branch)

Per-variable distribution comparison: signal sample (plan 20) vs
cosmic sample (plan 21) vs beam-neutron sample (plan 22). N-1 plots
in plan 41.

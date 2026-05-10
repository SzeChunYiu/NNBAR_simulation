---
id: 58_pileup_at_ess_intensity
title: Pile-up at ESS beam intensity
version: 0.1
status: draft
owner: Analysis WG
depends_on: [00_README, 01_realism_contract, 14_background_models, 22_sample_neutron_beam, 36_subsystem_event_variables, 37_subsystem_event_selection, 44_background_taxonomy, 45_systematics_taxonomy, 47_reproduction_ledger]
outputs:
  - {path: docs/rebuild_plans/58_pileup_at_ess_intensity.md, schema: this file}
  - {path: output/pileup/<study_id>/overlay_events.parquet, schema: §4 event overlay table}
  - {path: output/pileup/<study_id>/occupancy_by_subsystem.parquet, schema: §5 occupancy table}
acceptance:
  - {test: ESS time structure is explicit, method: §2 review, pass_when: 14 Hz and 2.86 ms pulse width are named with source cross-references}
  - {test: per-event and per-second conventions are separated, method: §3 review, pass_when: no rate row mixes the two units}
  - {test: overlay closure uses paired cosmic_cry_essLund samples, method: §7 closure, pass_when: signal acceptance and background occupancy intervals are saved}
  - {test: limitation L11 is either carried or closed, method: §8 ledger handoff, pass_when: plan 01 limitation status is explicit}
risks:
  - {risk: pile-up overlay can accidentally use truth time ordering as a reconstruction input, mitigation: §4 restricts production inputs to hit times and reconstructed tables}
  - {risk: per-event probabilities are mistaken for per-second rates, mitigation: §3 rate-unit fixture requires explicit conversion factors}
  - {risk: sparse paired-run coverage hides high-occupancy tails, mitigation: §7 demands tail quantiles and zero-survivor intervals}
estimated_effort: M
last_updated: 2026-05-10
---

# Pile-up at ESS beam intensity

*Charter.* Close or quantify plan-01 limitation L11 for analyses that
quote NNBAR signal acceptance or background rejection at ESS intensity.
The current rebuild treats simulated events independently. This plan
specifies the first overlay study that folds signal, cosmic, and
beam-induced backgrounds into the ESS pulse structure without confusing
per-event Monte Carlo probabilities with per-second experimental rates.

## 1. Scope and source crosswalk

This plan owns the analysis protocol for pile-up. It does not change the
primary Geant4 event generator, detector geometry, or event-selection
thresholds. It defines the tables, unit conventions, closure checks, and
decision stubs that L3 code must implement before any thesis-facing
statement says that pile-up is negligible.

Required source cross-references:

| Source | Relevant statement | How plan 58 consumes it |
|---|---|---|
| plan 01 §6 | limitation L11 says there is no pile-up between cosmic and signal events | every result carries `L11_open` until §7 closure is measured |
| plan 14 §1.4 | cosmic limitations include no beam time-structure / cosmic-signal pile-up | cosmic overlay rows must include CRY rate convention and limitation flags |
| plan 14 §2.3 | ESS beam is pulsed at about 14 Hz with about 2.86 ms long pulses | §2 freezes the v0.1 beam-time constants used by the overlay |
| plan 22 §4 | beam-neutron outputs are per-event rates and must be folded with pulse rate and yield | §3 separates per-event, per-pulse, and per-second rate rows |
| plan 44 §1 | background nodes name cosmic and beam-neutron sample ids and expected-rate conventions | §6 imports node ids rather than inventing new background categories |

The plan is intentionally conservative. If a required input is missing,
the study writes a blocked row with a reason; it does not backfill a
rate from prose or from an unrelated sample.

### 1.1 Non-goals

- No event-selection retuning. Any threshold change belongs to plan 37
  or plan 41 and needs a plan-05 decision.
- No detector response upgrade. Energy noise, timing jitter, trigger,
  and readout dead-time remain plan-01 limitations unless a dedicated
  digitisation/DAQ plan closes them.
- No truth-driven overlay matching. Generated particle labels may tag
  validation rows, but production pile-up decisions consume only times,
  energies, positions, and reconstructed objects.
- No single-number background quote. Pile-up produces occupancy and
  survival distributions that plan 44/46/47 consume with intervals.

## 2. Beam-time model

The v0.1 model uses a minimal ESS pulse clock:

| Parameter | v0.1 value | Meaning | Status |
|---|---:|---|---|
| `ess_pulse_rate_hz` | 14.0 | pulses per second | copied from plans 14 and 22 |
| `ess_pulse_width_ms` | 2.86 | long-pulse window used for in-pulse overlays | copied from plan 14 §2.3 |
| `pulse_period_ms` | 71.4286 | `1000 / ess_pulse_rate_hz` | derived |
| `in_pulse_fraction` | 0.0400 | `ess_pulse_width_ms / pulse_period_ms` | derived |
| `out_of_pulse_window_ms` | 68.5686 | complement of the long pulse in one period | derived |

The overlay engine samples a pulse id, then samples hit times relative
to that pulse. Signal candidates are assigned to the nominal pulse. Beam
neutron overlays are sampled inside the pulse unless a source manifest
explicitly models a delayed component. Cosmic overlays are sampled over
the full pulse period because cosmic arrivals are not locked to the ESS
beam structure.

### 2.1 Time-window definitions

| Window id | Definition | Used by |
|---|---|---|
| `signal_nominal_pulse` | event time in `[0, ess_pulse_width_ms]` | signal + prompt beam neutron overlay |
| `cosmic_period_window` | event time in `[0, pulse_period_ms]` | cosmic accidental overlay |
| `late_capture_window` | delayed component declared by a beam-neutron source manifest | capture-gamma diagnostics |
| `analysis_timing_window` | reconstructed in-time window from plan 36 variables | event-variable occupancy and S.1/S.5 stress tests |

The first implementation may use a rectangular pulse model. A realistic
proton-current profile is a later method choice and must create a new
`beam_time_model_id` plus a DEC row.

## 3. Rate-unit contract

Plan 58 uses three distinct units. Reviewers must be able to audit which
unit appears in every table cell.

| Unit | Symbol | Example field | Allowed conversion |
|---|---|---|---|
| per generated event | `P_event` | selected beam-neutron survival in a Monte Carlo sample | multiply by source normalisation to get per pulse |
| per pulse | `N_pulse` | expected overlays in one ESS pulse | multiply by 14 Hz to get per second |
| per second | `R_second` | expected overlay or survivor rate at ESS intensity | divide by live-time model for exposure periods |

Machine-readable rate rows carry:

| Field | Required content | Review rule |
|---|---|---|
| `rate_row_id` | stable key | unique within study |
| `source_node_id` | plan-44 background node or `signal` | no unregistered source id |
| `base_unit` | `per_event`, `per_pulse`, or `per_second` | mandatory |
| `base_value` | central value in base unit | null if blocked |
| `conversion_factor` | pulse yield, 14 Hz, or live-time factor | null only when no conversion is applied |
| `converted_unit` | target unit or null | must differ from `base_unit` when populated |
| `limitation_flags` | includes `L11` until overlay closure passes | non-empty for blocked rows |
| `normalisation_dec_id` | DEC that approved the source normalisation | draft or null rows stay provisional |

A plan-47 ledger row fails review if it quotes a per-second result from
an event probability without a populated conversion factor and source DEC.

## 4. Overlay protocol

The overlay is a table transformation after raw simulation and before
reconstruction summaries. It can be implemented either by merging hit
tables and rerunning reconstruction, or by joining already reconstructed
objects for a diagnostic stress test. Only the hit-level path can close
L11 for thesis numbers.

### 4.1 Event overlay table

| Column | Meaning |
|---|---|
| `overlay_event_id` | synthetic event id for the combined event |
| `signal_event_id` | source signal event id or null for background-only closure |
| `cosmic_event_ids` | list of overlaid cosmic event ids |
| `beam_event_ids` | list of overlaid beam-neutron event ids |
| `pulse_id` | sampled ESS pulse index |
| `time_model_id` | e.g. `ess_rectangular_14hz_2p86ms_v0` |
| `overlay_mode` | `hit_level`, `reco_object_level`, or `diagnostic_only` |
| `source_rate_row_ids` | rate rows used to sample multiplicities |
| `random_seed` | deterministic seed for replay |
| `limitation_flags` | open limitations after overlay construction |

The overlay table is append-only. Regenerating with a new rate or time
model creates a new `study_id` rather than replacing prior rows.

### 4.2 Production-input boundary

Allowed production inputs are hit tables, reconstructed object tables,
run manifests, event times, positions, deposited energies, and sample ids.
Truth labels, generated parentage, and source-track ancestry may be
written only to validation sidecars. If dropping validation sidecars
changes an overlay decision, the row is blocked.

## 5. Occupancy by subsystem

The occupancy study reports detector stress before and after the plan-37
selection. It must include TPC, scintillator, and lead-glass because the
Wave 4 charge explicitly asks for those subsystems.

| Subsystem | Occupancy metric | Event-variable hook | Failure mode |
|---|---|---|---|
| TPC | hit count, track-candidate count, projected-vertex multiplicity | `n_charged_objects`, `has_foil_tpc_track`, vertex rows | fake foil track or split vertex |
| Scintillator | total, upper, lower, in-time, and out-of-time eDep | `scintillator_edep`, upper/lower and timing fields | S.1/S.5 false veto or accidental pass |
| Lead glass | total, timing, upper/lower eDep and photon-object count | `leadglass_edep`, `n_photon_like`, pi0 rows | fake photon or pi0 candidate |
| Event selection | cumulative cut-flow differences | plan-37 `pass_*` columns | acceptance loss or background leakage |

### 5.1 Occupancy table

| Column | Meaning |
|---|---|
| `study_id`, `overlay_event_id`, `dataset_role` | study and row identity |
| `subsystem` | `tpc`, `scintillator`, `leadglass`, or `selection` |
| `metric_name` | metric from §5 |
| `baseline_value` | value before overlay |
| `overlay_value` | value after overlay |
| `delta_value` | overlay minus baseline |
| `tail_quantile` | p95/p99 marker for aggregate rows |
| `interval_method` | Wilson, bootstrap, or Feldman-Cousins as appropriate |
| `status` | `pass`, `warn`, `fail`, or `blocked` |

The table must preserve zero-count rows. A zero observed pile-up survivor
is a limit row, not evidence that the effect is exactly zero.

## 6. Study matrix

| Study id | Base sample | Overlay sample | Mode | Purpose | Promotion rule |
|---|---|---|---|---|---|
| `pileup_sig_plus_cosmic_A_v0` | `sig_foil_v3` | `cosmic_cry_essLund_overburdenA_v1` | hit-level | nominal cosmic+signal occupancy | eligible after paired-run closure |
| `pileup_sig_plus_cosmic_B_v0` | `sig_foil_v3` | `cosmic_cry_essLund_overburdenB_v1` | hit-level | overburden systematic | plan-45 cosmic-flux nuisance input |
| `pileup_sig_plus_beam_direct_v0` | `sig_foil_v3` | `beam_neutron_hibeam_direct_v1` | hit-level | prompt beam-neutron occupancy | blocked until source DEC and rates exist |
| `pileup_cosmic_only_diag_v0` | null | `cosmic_cry_essLund_overburdenA_v1` | reco-object diagnostic | fast cut-flow stress check | diagnostic only |
| `pileup_capture_gamma_diag_v0` | `sig_foil_v3` | `beam_neutron_hibeam_captgamma_v1` | hit-level | EM pile-up in lead glass | blocked until capture-gamma sample is frozen |

## 7. Closure procedure

1. Freeze a `time_model_id` with the §2 constants and record the source
   crosswalk from plans 14 and 22.
2. Build baseline reconstruction tables for `sig_foil_v3` and both
   `cosmic_cry_essLund_*` samples.
3. Generate paired overlays for at least the nominal and systematic
   cosmic samples using deterministic seeds.
4. Rerun reconstruction on hit-level overlays and write event, object,
   and cut-flow tables.
5. Compare signal S.6 acceptance with and without overlay using Wilson
   intervals; report the acceptance difference and its interval.
6. Compare background survivor counts with Feldman-Cousins intervals
   when survivor counts are zero or sparse.
7. Save TPC/scintillator/lead-glass occupancy distributions with p95
   and p99 tails.
8. Assert that validation sidecars can be dropped without changing any
   production overlay assignment or selection result.
9. Emit a closure row for each study id with `closure_status` equal to
   `pass`, `warn`, `fail`, or `blocked`.

### 7.1 Pass criteria

| Criterion | Pass rule |
|---|---|
| signal acceptance shift | absolute S.6 acceptance shift is smaller than the plan-45 assigned pile-up nuisance or explicitly carried as a larger nuisance |
| cosmic overlay tail | p99 scintillator and lead-glass occupancy tails have intervals and named caveats |
| zero survivor handling | zero survivors are reported as F-C upper limits, never as exact zero |
| source independence | dropping truth/provenance sidecars leaves overlay multiplicities and production decisions unchanged |
| paired-run coverage | both `cosmic_cry_essLund_overburdenA_v1` and `cosmic_cry_essLund_overburdenB_v1` have rows or the missing row is blocked |

## 8. Systematics, limitations, and ledger handoff

Plan 58 produces a pile-up nuisance input for plan 45 and a limitation
status for plan 47/50.

| Handoff | Content |
|---|---|
| plan 45 | pile-up acceptance shift, occupancy-tail uncertainty, cosmic-rate and beam-rate covariance flags |
| plan 44 | source-node survivor and occupancy rows keyed by background node |
| plan 46 | sparse-count interval choice for overlay survivors |
| plan 47 | thesis reproduction row caveat: `L11_open`, `L11_partially_closed`, or `L11_closed_for_study_id` |
| plan 50 | reviewer caveat text for any unclosed pile-up source |

Decision-log stubs:

| DEC id | Decision to freeze | Required evidence |
|---|---|---|
| `DEC-58-TIME-MODEL` | rectangular ESS pulse model or richer current profile | source crosswalk, constants, and replay seed convention |
| `DEC-58-OVERLAY-MODE` | hit-level overlay as thesis-facing closure path | sidecar-drop audit and reconstruction rerun manifest |
| `DEC-58-RATE-CONVERSION` | per-event to per-pulse/per-second conversion | plan-22 source normalisation and plan-44 node mapping |
| `DEC-58-PILEUP-NUISANCE` | pile-up nuisance value passed to plan 45 | paired-run closure intervals and occupancy tails |

## 9. Acceptance checklist

A plan-58 result is reviewable only if all checklist rows are populated:

| Check | Evidence artifact | Failure state |
|---|---|---|
| time constants frozen | `time_model_id` row with 14 Hz and 2.86 ms | blocked without constants |
| rate units separated | §3 rate fixture | blocked if unit conversion is implicit |
| hit-level overlay available | overlay manifest and reconstructed tables | diagnostic-only otherwise |
| paired cosmic closure complete | A and B overburden rows | nuisance cannot be bounded |
| subsystem occupancy saved | §5 occupancy table | cannot close L11 |
| zero counts intervalised | plan-46/F-C interval row | exact-zero claim rejected |
| truth sidecars droppable | sidecar-drop hash equality | production path blocked |
| DEC stubs named | §8 table | no thesis-facing promotion |

## 10. A+ verifier transcript

Before this plan was committed, the supporting plan files were checked
for existence and the cited section anchors were searched by heading or
keyword. No runtime CLI command is specified by this plan; the overlay
producer remains a blocked L3 implementation gate until its help output
exists.

| Claim | Verifier |
|---|---|
| plan 01 limitation L11 exists | `grep -n "L11" docs/rebuild_plans/01_realism_contract.md` |
| plan 14 §1.4 and §2.3 exist | `grep -n "^### 1.4\|^### 2.3" docs/rebuild_plans/14_background_models.md` |
| plan 22 time-correlation section exists | `grep -n "^## 4. Time correlation limitation" docs/rebuild_plans/22_sample_neutron_beam.md` |
| plan 44 background nodes exist | `grep -n "cosmic_cry_essLund\|beam_neutron_hibeam" docs/rebuild_plans/44_background_taxonomy.md` |
| no invented Python CLI surface | this plan names no runnable nnbar reconstruction module command; overlay remains an L3 implementation gate |

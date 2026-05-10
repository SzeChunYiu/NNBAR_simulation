---
id: 61_time_of_flight_discrimination
title: Time-of-flight discrimination for cosmic and signal separation
version: 0.1
status: draft
owner: Timing POG
depends_on: [00_README, 01_realism_contract, 17_field_calibration, 18_intercalibration, 25_subsystem_tpc_hits_to_tracks, 27_subsystem_dedx, 30_subsystem_vertex, 36_subsystem_event_variables, 37_subsystem_event_selection, 41_n_minus_1_and_roc_studies, 44_background_taxonomy, 45_systematics_taxonomy]
outputs:
  - {path: docs/rebuild_plans/61_time_of_flight_discrimination.md, schema: this file}
  - {path: output/tof/<study_id>/tof_candidates.parquet, schema: §4 candidate table}
  - {path: output/tof/<study_id>/tof_closure.parquet, schema: §7 closure table}
acceptance:
  - {test: TPC drift-time plus scintillator hit-time estimator is defined, method: §§2-4 review, pass_when: formula and input boundary are explicit}
  - {test: cosmic-vs-signal separation is measured, method: §7 closure, pass_when: cal_* and cosmic_* slices have ROC and interval rows}
  - {test: timing-resolution budget names each subsystem contribution, method: §5 review, pass_when: TPC/scintillator/vertex/clock terms are listed}
  - {test: plan 36 timing variables remain the event-level handoff, method: §8 review, pass_when: no hidden replacement of E.8 columns}
risks:
  - {risk: current simulation hit times have no jitter, mitigation: §5 carries plan-01 L2 and requires smeared-resolution stress tests}
  - {risk: TOF discriminator becomes a hidden selection cut, mitigation: §6 keeps it as a candidate sidecar until DEC-61-TOF-SELECTION is signed}
  - {risk: cosmic timing closure is biased by generation window choices, mitigation: §7 requires both cal_* prompt slices and cosmic_* out-of-time slices}
estimated_effort: M
last_updated: 2026-05-10
---

# Time-of-flight discrimination

*Charter.* Define a timing discriminator that combines TPC drift-time
information with scintillator hit times to separate prompt signal-like
activity from cosmic or beam-related out-of-time activity. The output is
a candidate sidecar and closure package; it does not retune plan-37
selection until its resolution budget and ROC evidence are reviewed.

## 1. Scope and cross-references

Plan 61 is the Wave-4 timing study for L1. It reads the reconstruction
and event-variable plans without changing their ownership:

| Source plan | Consumed concept | Plan-61 use |
|---|---|---|
| plan 25 | TPC hit-to-track inputs and timing/order assumptions | TPC-side time anchor and track path estimate |
| plan 27 | dE/dx and charged-particle beta/gamma closure | beta-hypothesis and PID-aware TOF expectation |
| plan 30 | reconstructed vertex position/time handoff | path-length origin and prompt-time reference |
| plan 36 | E.8 timing-window energy variables | event-level timing handoff and out-of-time energy comparison |
| plan 37 | S.1-S.6 cut-flow | measure whether TOF improves or biases selection |
| plan 44 | cosmic and beam-neutron background nodes | cosmic-vs-signal closure categories |
| plan 45 | timing, calibration, and cosmic-flux nuisances | resolution and residual-systematic handoff |

Non-goals:

- No detector digitisation. Plan 01 limitation L2 remains open until a
  timing-jitter model lands.
- No replacement of plan-36 E.8 columns. Plan 61 may add a TOF sidecar;
  plan 36 keeps the canonical event-level timing sums.
- No truth time in production. Truth time can label closure slices but
  cannot enter the TOF score.

## 2. Inputs and estimator definition

The estimator uses reconstructed-only quantities:

| Input | Source | Production status |
|---|---|---|
| TPC hit times for a charged track | plan-25 track hit membership | Class A with plan-01 L2 caveat |
| scintillator hit time and position | plan-09 raw scintillator hits / plan-36 E.8 inputs | Class A with timing-resolution caveat |
| reconstructed vertex position/time | plan 30 event vertex | Class A, invalid if vertex fit fails |
| charged PID hypothesis and beta estimate | plan 27 / plan 29 candidate sidecar | candidate; can be disabled |
| speed-of-light constant and particle masses | reconstruction config / PDG constants | calibration constants, not truth labels |

For a charged candidate matched to a scintillator hit, define:

`tof_observed_ns = scintillator_time_ns - tpc_track_time_anchor_ns`.

The path length is the reconstructed distance from the vertex to the
scintillator impact point, including a track-path correction if plan 25
supplies a fitted direction. The beta estimate is:

`beta_tof = path_length_cm / (c_cm_per_ns * tof_observed_ns)`.

The prompt-signal residual for a mass/PID hypothesis is:

`tof_residual_ns = tof_observed_ns - path_length_cm / (beta_hypothesis * c_cm_per_ns)`.

A cosmic-like candidate is expected to show one or more of: wrong sign
or unphysical beta, large absolute residual, inconsistent top/bottom
scintillator timing, or timing that is out of the plan-36 prompt window.

### 2.1 Sparse and invalid cases

| Condition | Required output |
|---|---|
| no matched scintillator hit | `tof_valid = false`, reason `missing_scintillator_match` |
| no valid TPC time anchor | `tof_valid = false`, reason `missing_tpc_anchor` |
| no valid reconstructed vertex/path | `tof_valid = false`, reason `missing_path_length` |
| nonpositive observed TOF for outgoing hypothesis | `tof_valid = false`, reason `nonpositive_tof` |
| beta outside `(0, 1.2]` after resolution allowance | `tof_valid = false`, reason `unphysical_beta` |

Invalid TOF rows are carried into denominators. They cannot be silently
removed from signal-efficiency or background-rejection closure.

### 2.2 Physics derivation for TOF discrimination

#### Physics derivation

Plan 61 physically estimates particle time of flight and promptness from
reconstructed timing and path length. The truth-side quantity is the
particle velocity and production time; the production estimator observes
TPC time anchors, scintillator hit times, reconstructed vertex/path
geometry, and optional PID beta hypotheses. Relativistic kinematics gives
`TOF = path / (beta c)`, so prompt signal-like candidates should have
residuals compatible with the calibrated timing-resolution budget, while
cosmics and delayed beam backgrounds can produce unphysical beta,
top/bottom asymmetry, or out-of-window residuals
\cite{ParticleDataGroup:2024RPP}.

The estimator is therefore a validity-gated residual and score sidecar:
compute observed TOF, derive beta, compare to a hypothesis residual, and
propagate every invalid case into denominators. Dominant uncertainty is
timing resolution (TPC anchor, scintillator hit, clock, vertex time),
followed by path-length uncertainty, PID beta uncertainty, generation
window assumptions for cosmics, and ideal-timing bias from current
simulation. A zero-resolution TOF score is invalid because it would treat
perfect simulation timestamps as detector performance.

The Wave-6 resolution-term derivation ledger is:

| Term leaf | Truth-side quantity | Estimator rationale | Dominant uncertainty | Closure assertion |
|---|---|---|---|---|
| `tof.tpc_anchor` | charged-track time at the TPC reference surface | TPC hit-time aggregation supplies the start anchor for reconstructed charged paths | drift calibration, hit-time jitter, and field-map dependence | cal_* prompt tracks must yield a nonzero `sigma_tpc_anchor_ns` nuisance row |
| `tof.scint_hit` | scintillator interaction time for the matched outgoing particle | scintillator timestamp supplies the stop time and carries the dominant prompt-timing measurement | light transport, electronics response, and ideal-timing caveat L2 | scintillator residual width must remain nonzero after smearing/model import |
| `tof.vertex_time_path` | production time and path from reconstructed vertex to scintillator | vertex/path covariance converts spatial uncertainty into timing residual variance | vertex time fit failures and path-length covariance | invalid vertex/path rows stay in denominators with explicit reasons |
| `tof.clock_sync` | common time-base alignment between TPC and scintillator systems | a clock-offset nuisance is required before combining two timing subsystems | external synchronisation and run-dependent offsets | every approved score names a clock nuisance or blocks promotion |
| `tof.pid_beta` | expected beta for the charged PID hypothesis | relativistic `path/(beta c)` expectation turns PID/range information into a timing residual prediction | PID misassignment and mass-hypothesis ambiguity | PID-disabled and PID-enabled score modes are both included in ROC/N-1 closure |

These term leaves make TOF a resolution-budget calculation rather than a
hidden cut on ideal timestamps. The TOF sidecar can be promoted only
when every nonzero residual term is traceable to a calibration or
smearing artifact and every missing term is represented as a blocker.

#### Logic gaps

| Parameter | Status before production | Closure study / target date |
|---|---|---|
| `c_cm_per_ns` and beta hypothesis masses | physics constants; exact config source still needs DEC trace | Verify constants and units in `DEC-61-TOF-ESTIMATOR`; target 2026-06-20 |
| beta validity allowance `(0, 1.2]` | `OPEN:` resolution allowance, not a physical beta limit | Scan allowance under timing smearing and require stable invalid-rate accounting; target 2026-06-30 |
| timing-resolution terms in §5 | `OPEN:` every term starts unmeasured and L2 remains open | Measure cal_* residual widths and assign nonzero nuisance terms; target 2026-07-05 |
| residual-cut multiplier `k` and score threshold | `OPEN:` no production operating point frozen | ROC scan on cal_* and cosmic_* slices with plan-37 signal-loss intervals; target 2026-07-05 |
| TOF selection use | sidecar-only until `DEC-61-TOF-SELECTION` | Compare E.8-only versus TOF sidecar rejection and prevent baseline overwrite; target 2026-07-10 |

#### Closure test for the derivation

1. Build TOF candidate rows from reconstructed TPC, scintillator, vertex,
   and PID sidecars with every invalid reason preserved.
2. Measure prompt residual distributions on cal_* slices and cosmic
   rejection on CRY overburden A/B slices with intervals.
3. Decompose the residual width into the §5 resolution terms and reject
   any configuration with zero total timing variance.
4. Run ROC/N-1 comparisons between E.8 timing variables and TOF scores,
   keeping TOF as a shadow selection unless the DEC is signed.
5. Drop truth labels and generated times; TOF scores, validity reasons,
   and candidate pass/fail decisions must remain unchanged.

## 3. Candidate score and discrimination modes

The v0.1 score is a sidecar with three modes:

| Mode | Score definition | Use |
|---|---|---|
| `residual_cut_v0` | threshold on `abs(tof_residual_ns)` and beta validity | transparent baseline |
| `hemisphere_delta_v0` | top/bottom scintillator timing asymmetry plus residual | cosmic rejection diagnostic |
| `tabular_tof_bdt_v0` | small model using TOF, residual, path, dE/dx, and plan-36 timing sums | candidate only under plan 57 |

The score output is `tof_signal_score` in `[0,1]` and a boolean
`passes_tof_candidate`. The boolean is not part of plan-37 S.1-S.6 until
`DEC-61-TOF-SELECTION` is approved.

## 4. TOF candidate table

| Column | Meaning |
|---|---|
| `event_id`, `candidate_id` | stable event and charged-object keys |
| `track_id_reco` | reconstructed charged object id, not truth Track_ID |
| `scintillator_hit_id` | matched scintillator object/hit key |
| `path_length_cm` | reconstructed path from vertex to scintillator hit |
| `tpc_track_time_anchor_ns` | TPC-side time anchor |
| `scintillator_time_ns` | matched scintillator hit time |
| `tof_observed_ns` | observed scintillator minus TPC time |
| `beta_tof` | reconstructed beta from TOF |
| `beta_hypothesis` | optional PID-aware beta hypothesis |
| `tof_residual_ns` | residual against the hypothesis |
| `tof_signal_score` | calibrated or rule-based prompt score |
| `passes_tof_candidate` | sidecar boolean candidate |
| `tof_valid`, `tof_invalid_reason` | validity contract |
| `tof_method_id` | score and resolution model key |
| `diagnostic_truth_label` | validation sidecar only |

Dropping `diagnostic_truth_label` must not change score, pass/fail, or
invalid-reason fields.

## 5. Resolution budget

The timing closure report decomposes the width of `tof_residual_ns` into
terms. v0.1 deliberately carries no production numeric resolution. Each
term starts as an owned open slot and becomes usable only after a measured
calibration row, a documented smearing model, or a signed external
calibration import fills the required artifact fields.

| Term | Symbol | Owner | Initial status |
|---|---|---|---|
| TPC drift-time anchor | `sigma_tpc_anchor_ns` | plan 25 / field calibration | open, exact-hit-time caveat L2 |
| scintillator hit time | `sigma_scint_hit_ns` | plan 18 / plan 36 | open, current config uses ideal timing inputs |
| vertex time | `sigma_vertex_time_ns` | plan 30 | open, null if no vertex time fit |
| path-length uncertainty | `sigma_path_cm` | plan 25 / plan 30 | derived from track and vertex covariance |
| clock synchronisation | `sigma_clock_ns` | calibration POG | open, external calibration |
| PID beta hypothesis | `sigma_beta_hypothesis` | plan 27 / plan 29 | measured on calibration slices |

The total nominal variance is stored as:

`sigma_tof_total_ns2 = sigma_tpc_anchor_ns^2 + sigma_scint_hit_ns^2 + sigma_vertex_time_ns^2 + (sigma_path_cm / (beta*c))^2 + sigma_clock_ns^2 + sigma_beta_term_ns^2`.

A result with `sigma_tof_total_ns2 = 0` is blocked because it indicates
that ideal simulation timing has been mistaken for detector resolution.

| Resolution-field key | Required content before use |
|---|---|
| `term_id` | one of the §5 stable symbols |
| `central_value` / `unit` | measured or imported resolution value with units |
| `source_artifact_id` | calibration slice, smearing study, or external calibration import |
| `limitation_ids` | includes `L2` until detector timing jitter is closed |
| `nuisance_id` | plan-45 timing/calibration nuisance row or null with reason |
| `decision_dec_id` | signed `DEC-61-RESOLUTION-BUDGET` or successor |
| `resolution_status` | `open`, `diagnostic`, `candidate`, or `approved` |

## 6. Rejection and promotion rules

| Rule id | Candidate decision | Promotion guard |
|---|---|---|
| `tof_prompt_baseline` | require valid TOF and `abs(tof_residual_ns) < k * sigma_tof_total` | can be compared to S.1-S.6 but not inserted without DEC |
| `tof_cosmic_veto` | veto candidates with large top/bottom timing asymmetry or late residual | needs cosmic closure and signal-loss interval |
| `tof_beam_late_veto` | veto late neutral/charged timing clusters in beam-neutron windows | needs plan-58/59 compatibility review |
| `tof_score_shadow` | save BDT/NN score without selection effect | plan 57 export and calibration artifacts required |

If TOF becomes production-facing, plan 37 receives a new sidecar column
or a Wave-5 selection extension. Existing Ch 10 reproduction columns are
not overwritten.

## 7. Closure procedure

The required closure suite has calibration and background slices:

| Slice | Dataset pattern | Purpose |
|---|---|---|
| `cal_singlepion_tof_v0` | `cal_singlepion_*` | prompt charged-pion timing response |
| `cal_singleproton_tof_v0` | `cal_singleproton_*` | slower beta hypothesis and dE/dx coupling |
| `cal_singlegamma_timing_v0` | `cal_singlegamma_*` | neutral EM timing control through plan 36 |
| `cosmic_overburdenA_tof_v0` | `cosmic_cry_essLund_overburdenA_v1` | nominal cosmic rejection |
| `cosmic_overburdenB_tof_v0` | `cosmic_cry_essLund_overburdenB_v1` | cosmic-rate/systematic cross-check |
| `beam_neutron_late_tof_diag_v0` | `beam_neutron_hibeam_*` | late beam-related diagnostic |

Procedure:

1. Build the TOF candidate table for each slice after standard
   reconstruction tables exist.
2. Compute prompt-efficiency, cosmic-rejection, and invalid-row rates
   with Wilson intervals.
3. Build ROC curves for `tof_signal_score` and compare to plan-36 E.8
   timing-energy variables alone.
4. Report signal efficiency loss after plan-37 S.6 if the TOF boolean is
   applied as a shadow veto.
5. Save residual distributions split by PID hypothesis, path-length bin,
   detector hemisphere, and validity reason.
6. Stress the score by smearing timing terms according to §5 and record
   the resulting nuisance shift.
7. Verify that truth labels can be dropped without changing any score or
   candidate decision.

### 7.1 Closure pass criteria

| Metric | Pass rule |
|---|---|
| prompt calibration efficiency | meets the chosen operating point with an interval on each cal_* slice |
| cosmic rejection | improves rejection or provides a measured null result with interval |
| invalid-rate accounting | invalid rows are reported by reason and dataset |
| resolution budget | nonzero total resolution and every open term has an owner |
| sidecar-drop audit | production score unchanged after validation labels are removed |

## 8. Handoff to event variables and systematics

Plan 61 writes a TOF sidecar and aggregate closure rows. Plan 36 remains
the event-level owner of in-time/out-of-time energy sums.

| Consumer | Handoff |
|---|---|
| plan 36 | optional `tof_summary_id` and aggregate timing-quality diagnostics |
| plan 37 | shadow comparison against S.1-S.6; no default threshold change |
| plan 41 | N-1 / ROC rows for TOF score and E.8 timing variables |
| plan 44 | cosmic and beam-neutron timing rejection rows |
| plan 45 | timing-resolution and residual-background nuisance inputs |
| plan 50 | reviewer caveat if L2 timing jitter remains unclosed |

Decision-log stubs:

| DEC id | Decision to freeze | Required evidence |
|---|---|---|
| `DEC-61-TOF-ESTIMATOR` | formula, path convention, and time-anchor convention | candidate table replay and source crosswalk |
| `DEC-61-RESOLUTION-BUDGET` | timing-resolution terms and smearing profile | cal_* residual widths and nonzero uncertainty terms |
| `DEC-61-TOF-SELECTION` | whether TOF enters production selection | ROC, signal-loss interval, and background-rejection evidence |
| `DEC-61-TOF-NUISANCE` | timing nuisance passed to plan 45 | smeared-closure shifts and covariance flags |

## 9. Acceptance checklist

| Check | Evidence artifact | Failure state |
|---|---|---|
| estimator defined | §2 formula and §4 schema | cannot implement sidecar |
| invalid rows retained | invalid-rate table | biased efficiency denominator |
| resolution nonzero | §5 budget row | ideal timing mistaken for detector timing |
| cal_* closure complete | prompt-efficiency rows | no signal timing calibration |
| cosmic_* closure complete | rejection rows | no cosmic-separation claim |
| E.8 comparison saved | ROC against plan-36 timing sums | no incremental-value evidence |
| truth labels droppable | sidecar-drop hash | production path blocked |
| DEC stubs named | §8 table | no selection promotion |

## 10. A+ verifier transcript

Before this plan was committed, the local plan dependencies were checked
for existence and timing-related section content. This plan contains no
runtime nnbar module command and no source-code line citation.

| Claim | Verifier |
|---|---|
| plan 25 track/timing source exists | `grep -nE "time|track" docs/rebuild_plans/25_subsystem_tpc_hits_to_tracks.md` |
| plan 27 dE/dx / beta closure exists | `grep -nE "dE/dx|beta" docs/rebuild_plans/27_subsystem_dedx.md` |
| plan 36 E.8 timing variables exist | `grep -nE "E.8|timing" docs/rebuild_plans/36_subsystem_event_variables.md` |
| plan 44 cosmic nodes exist | `grep -n "cosmic_cry_essLund" docs/rebuild_plans/44_background_taxonomy.md` |
| no stale code citation | no `*.py:<line>` citation appears in this plan |

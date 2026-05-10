---
id: 08_6_validation
title: Reconstruction atomic walkthrough — validation public surface
version: 0.1
status: draft
owner: Reproducibility WG
depends_on: [08_reconstruction_atomic_walkthrough, 01_realism_contract, 09_io_schema_data_dictionary]
inputs:
  - {path: NNBAR_Detector/nnbar_reconstruction/validation.py, schema: source file}
outputs:
  - {path: docs/rebuild_plans/08_reconstruction_atomic_walkthrough/08_6_validation.md, schema: split walkthrough section}
last_updated: 2026-05-10
---

# Validation public surface — split from plan 08

This split file preserves and deepens plan 08 §6 so the main walkthrough
stays below the 500-line cap while validation receives function-level detail.

## 6. Validation (validation.py, 509 lines)

`validation.py` is a truth-aware reporting module, not a reconstruction
decision module. The CLI injects truth tables before validation
(`cli.py:239–248`), and `reconstruction.md:212–256` describes the
reported readiness payload. Class B reads here are validation-only and
must not be interpreted as permission for reconstruction decision paths
to read truth columns.

### 6.1 Metric helpers used by the public surface

- `_charged_pid_truth(name)` (`validation.py:35–41`) maps Class B
  charged `truth_name` diagnostics from `charged.csv` (plan 09 §14.2,
  lines 274–280): exact `"proton"` ⇒ `proton`; `"pi+"`, `"pi-"`, or
  `"charged_pion"` ⇒ `charged_pion`; anything else is ignored.
- `_photon_charge_truth(name)` and `_photon_charge_match_truth(row)`
  (`validation.py:44–72`) map photon truth diagnostics. The hardcoded
  charged set is `{e+, e-, mu+, mu-, pi+, pi-, proton, antiproton,
  deuteron, alpha}`; neutral is `{gamma, neutron, pi0, opticalphoton}`.
  If `truth_charge_match_class` exists, only `charged` and `neutral`
  are labelable; `unmatchable_charged` and `unknown` are counted as
  exclusions (`validation.py:66–72`, `345–369`; reconstruction.md
  lines 114–118).
- `_electron_pair_truth(name1, name2)` (`validation.py:84–90`) treats a
  truth-labelled e+/e- pair as true only when the carried Class B labels
  multiply to opposite signs. Labels missing or outside `{e-, e+}` are
  unlabeled.
- `_binary_report(...)` (`validation.py:93–131`) computes TP/FP/TN/FN,
  class counts, accuracy, precision/recall, negative recall, and
  balanced F1. `usable` is hardcoded to require at least one truth
  positive and one truth negative (`validation.py:117–131`).
- `_pi0_selection_report(...)` (`validation.py:185–316`) is shared by
  all π⁰ selector summaries. It derives truth π⁰ event ids from
  `Particle.Name == "pi0"`, then counts selected truth/non-truth events,
  selected candidates, candidate lineage/near-track counts, feature
  summaries, efficiency, false-positive event rate, and usability.

### 6.2 `evaluate_reconstruction_truth(result)`

**Source:** `NNBAR_Detector/nnbar_reconstruction/validation.py:319–428`.

**Inputs:** a reconstruction result dictionary. It reads `charged`,
`photons`, `electron_pairs`, `events`, `Particle`, and `pi0` tables
(`validation.py:322–327`). Required and optional columns:

- `charged.truth_name` (Class B diagnostic; plan 09 §14.2, lines
  274–280) and `charged.pid_guess` (reconstructed PID from plan 08
  §3.4) drive charged PID validation (`validation.py:329–343`).
- `photons.truth_name`, optional `photons.truth_charge_match_class`
  (Class B/provenance diagnostics), and `photons.has_tpc_track`
  (reconstructed charged/neutral match; plan 09 §14.4, lines 288–293)
  drive photon charged-match validation (`validation.py:345–369`).
- `electron_pairs.track1_truth_name` and `track2_truth_name` are Class B
  validation labels carried by the e+/e- pair table (plan 09 §14.3,
  lines 283–287; `validation.py:152–181`).
- `events.event_id` and `events.n_charged_objects` define neutral-event
  ids for the π⁰-only neutral-event diagnostic (`validation.py:371–375`;
  plan 09 §14.6, lines 305–312).
- `Particle.Event_ID` (Class A id) and `Particle.Name` (Class B truth;
  plan 09 §3, lines 85–89) define truth/non-truth π⁰ events inside
  `_pi0_selection_report` (`validation.py:216–224`).
- `pi0.event_id`, `passes_selection`, `passes_mass_window`,
  `near_charged_track_photons`, `total_energy`,
  `max_abs_vertex_time_residual_ns`, lineage/pair-label diagnostics,
  and feature columns are read when present (plan 09 §14.5, lines
  295–303; `validation.py:225–287`).

**Decision rule:** missing/empty charged or photon required columns yield
empty binary reports (`validation.py:329–360`). Otherwise charged truth
labels are reduced to proton-vs-charged-pion and predictions are
`pid_guess == "proton"` (`validation.py:332–343`). Photon labels prefer
`truth_charge_match_class`; excluded counts are recorded for
`unmatchable_charged` and `unknown`; predictions are
`has_tpc_track.astype(bool)` (`validation.py:350–369`). Neutral-event ids
are events where `n_charged_objects == 0` (`validation.py:371–375`). The
π⁰ summaries are produced with hardcoded selector variants: strict
`passes_selection`; mass-window; mass-window plus
`near_charged_track_photons == 0`; mass-window plus neutral event;
combined isolated-neutral; mass-window plus `total_energy >= 400 MeV`;
and mass-window plus prompt timing where
`max_abs_vertex_time_residual_ns <= DEFAULT_CONFIG.pi0_prompt_time_max_abs_residual_ns`
(`validation.py:376–426`). The default prompt timing threshold is 2 ns
per `reconstruction.md:238–241`.

**Outputs:** a dict containing `charged_pid`, `photon_charged_match`,
`electron_pairs`, `pi0_selection`, `pi0_mass_window_selection`,
`pi0_mass_window_track_isolated_selection`,
`pi0_mass_window_neutral_event_selection`,
`pi0_mass_window_isolated_neutral_event_selection`,
`pi0_mass_window_high_energy_selection`,
`pi0_mass_window_prompt_timing_selection`, and `overall_usable`
(`validation.py:376–428`). `overall_usable` is true only when charged PID
and photon charged-match are both usable (`validation.py:427`).

**Truth reads:** Class B truth/provenance columns `truth_name`,
`truth_charge_match_class`, electron-pair truth names, `Particle.Name`,
and π⁰ pair/lineage diagnostics. This is expected validation-only truth
use, not reconstruction decision-path use under plan 08 §3.7.

### 6.3 `aggregate_reconstruction_truth(results)`

**Source:** `NNBAR_Detector/nnbar_reconstruction/validation.py:431–446`.

**Inputs:** a list of reconstruction result dictionaries. Inputs are the
same tables required by `evaluate_reconstruction_truth` after aggregation;
no parquet columns are read directly here.

**Decision rule:** collect the union of table keys across all result
dicts, concatenate present non-empty DataFrames for each key with
`ignore_index=True`, and substitute an empty DataFrame when none exist
(`validation.py:434–445`). The combined dict is delegated to
`evaluate_reconstruction_truth` (`validation.py:446`).

**Outputs:** the same validation report schema as
`evaluate_reconstruction_truth`.

**Truth reads:** none directly; Class B diagnostics are consumed only by
the delegated `evaluate_reconstruction_truth` call.

### 6.4 `assess_validation_readiness(report, *, min_class_count=1, min_accuracy=0.0, min_balanced_f1=0.0, min_electron_pair_purity=1.0, min_pi0_efficiency=0.0)`

**Source:** `NNBAR_Detector/nnbar_reconstruction/validation.py:449–509`.
The CLI exposes the same readiness floors as command-line arguments
(`cli.py:402–421`) and can turn failed readiness into exit code 1 with
`--fail-on-not-ready` (`cli.py:287–294`).

**Inputs:** a validation report dict, not raw parquet tables. Required
metric sections are `charged_pid` with `true_proton`/`true_pion`, and
`photon_charged_match` with `true_charged`/`true_neutral`
(`validation.py:460–463`). Optional readiness checks inspect
`electron_pairs.n_labeled`/`purity` and `pi0_selection.usable`/`efficiency`
(`validation.py:480–497`).

**Decision rule:** for charged PID and photon charged-match, fail if
`usable` is false, any required class count is below `min_class_count`,
`accuracy` is below `min_accuracy`, or `balanced_f1` is below
`min_balanced_f1` (`validation.py:464–478`). If any electron pairs are
truth-labelled, fail when purity is below `min_electron_pair_purity`
(`validation.py:480–487`). Only when `min_pi0_efficiency > 0` does the
π⁰ gate require usable strict π⁰ selection and efficiency above that
floor (`validation.py:489–497`).

**Outputs:** a dict with `passed`, `failed_requirements`, and a
`requirements` echo of all five threshold values (`validation.py:499–509`).

**Truth reads:** none. Truth dependence is already summarized into the
input validation report.

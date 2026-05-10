---
id: 08_9
title: Reconstruction atomic walkthrough — pi0 fake study
version: 0.1
status: draft
owner: Reproducibility WG
depends_on: [08_reconstruction_atomic_walkthrough]
inputs:
  - {path: NNBAR_Detector/nnbar_reconstruction/pi0_fake_study.py, schema: source file}
outputs:
  - {path: docs/rebuild_plans/08_reconstruction_atomic_walkthrough/08_9_pi0_fake_study.md, schema: split walkthrough section}
last_updated: 2026-05-10
---

# π⁰ fake study — split from plan 08

This split file preserves and deepens plan 08 §9 so the main walkthrough
stays below the 500-line cap.

## 9. π⁰ fake study (pi0_fake_study.py, 325 lines)

The module classifies π⁰-like reconstructed candidates in samples that
are intended to contain no primary truth π⁰. It is explicitly
truth-backed: lineage tracing is a diagnostic to explain residual fakes,
not a reconstruction decision path.

### 9.1 Helper map

- `_source_aliases(value)` (`pi0_fake_study.py:29–37`) parses the
  comma-separated `photon1_source_track_ids` / `photon2_source_track_ids`
  π⁰ provenance columns into integer source-track aliases.
- `_lineage_index(raw_tables)` (`pi0_fake_study.py:40–67`) builds a
  Class B ancestry index keyed by `(Event_ID, Track_ID)` from
  `Interaction`, `LeadGlass`, `Scintillator`, `TPC`, and `Silicon` raw
  tables. Required columns are `Event_ID`, `Track_ID`, `Parent_ID`, and
  `Name`; optional diagnostic fields are `Proc`, `Origin`,
  `Current_Vol`, and `Volume`. Plan 09 classifies `Event_ID` as Class A
  and `Track_ID`/`Parent_ID`/`Name` as Class B in the Particle and hit
  schemas (plan 09 §3 lines 85–89, §4 lines 109–116, §8 lines 151–169).
- `_trace_lineage(...)` (`pi0_fake_study.py:70–88`) walks parent links
  until a missing node, self-cycle, or repeated track id terminates the
  chain.
- `_truth_pi0_events(raw_tables)` (`pi0_fake_study.py:91–96`) finds
  primary truth-π⁰ events from `Particle.Event_ID` (Class A event id) and
  `Particle.Name` (Class B truth label; plan 09 §3 lines 85–89).
- `_selector_label(...)` (`pi0_fake_study.py:109–122`) records the active
  reco-only selector: always `passes_mass_window`, optionally
  `near_charged_track_photons == 0`, and optionally
  `max_abs_vertex_time_residual_ns <= <config threshold> ns`.

### 9.2 `evaluate_pi0_fake_candidates(result, raw_tables, *, run=None, config=DEFAULT_CONFIG, track_isolated=True, prompt_timing=False)`

**Source:** `NNBAR_Detector/nnbar_reconstruction/pi0_fake_study.py:125–257`.

**Inputs:** reconstructed `result["pi0"]` plus raw truth/provenance tables.
The π⁰ table must contain `event_id` and `passes_mass_window`; otherwise
it returns an empty report (`pi0_fake_study.py:136–156`). Optional π⁰
columns read when present are `near_charged_track_photons`,
`max_abs_vertex_time_residual_ns`, `photon1_source_track_ids`,
`photon2_source_track_ids`, `mass`, `total_energy`, `opening_angle_deg`,
`photon_truth_name_pair`, `photon_truth_charge_match_class_pair`, and
`charged_lineage_photons` (`pi0_fake_study.py:158–226`; plan 09 §14.5,
lines 295–303). Raw tables supply the Class B lineage fields listed in
§9.1.

**Decision rule:** start with mass-window candidates
(`passes_mass_window == true`; `pi0_fake_study.py:158`). If
`track_isolated` is true, require `near_charged_track_photons == 0`, and
if the column is absent select nothing (`pi0_fake_study.py:159–164`). If
`prompt_timing` is true, require
`max_abs_vertex_time_residual_ns <= config.pi0_prompt_time_max_abs_residual_ns`,
again selecting nothing if the column is absent (`pi0_fake_study.py:165–175`).
Events with primary truth π⁰ are excluded before fake classification
(`pi0_fake_study.py:177–180`). For each remaining selected candidate,
photon source aliases are traced through the lineage index; a secondary
π⁰ ancestor is counted only when a lineage node has `name == "pi0"` and a
non-primary, non-self parent id (`pi0_fake_study.py:183–205`).

**Outputs:** a dict with `run`, `selector`, `summary`, and `rows`
(`pi0_fake_study.py:252–257`). Each row records selected-candidate
kinematics, truth/provenance pairs, charged-lineage and near-track
counts, prompt-time residual, and secondary-π⁰ ancestor ids/origins/
volumes (`pi0_fake_study.py:207–227`). The summary counts selected
candidates/events, secondary-π⁰-lineage candidates/events, secondary
origin/volume counts, charge-class pair counts, and truth-name pair
counts (`pi0_fake_study.py:229–251`).

**Truth reads:** Class B raw ancestry (`Track_ID`, `Parent_ID`, `Name`,
origin/process/volume provenance) and Class B diagnostic pair labels from
`pi0.csv`. This is diagnostic fake-root-cause analysis and is not a
reconstruction decision path under plan 08 §3.7.

### 9.3 `pi0_fake_rows(report)`

**Source:** `NNBAR_Detector/nnbar_reconstruction/pi0_fake_study.py:260–261`.

**Inputs:** the report dict emitted by `evaluate_pi0_fake_candidates` or
`evaluate_pi0_fake_background`.

**Decision rule:** no filtering or transformation beyond
`pd.DataFrame(report.get("rows", []))`.

**Outputs:** a tabular DataFrame with the per-candidate row schema listed
in §9.2, used by the CLI `--table` path (`cli.py:331–350`, `460–495`).

**Truth reads:** none directly.

### 9.4 `evaluate_pi0_fake_background(output_dir, *, runs, config=DEFAULT_CONFIG, track_isolated=True, prompt_timing=False)`

**Source:** `NNBAR_Detector/nnbar_reconstruction/pi0_fake_study.py:264–325`.

**Inputs:** an output directory and explicit run list. For each run it
reconstructs tables with `reconstruct_run(output_dir, run, config)` and
loads raw parquet tables with `load_run(output_dir, run)`
(`pi0_fake_study.py:272–285`). CLI flags map `--include-near-charged` to
`track_isolated=False`, `--prompt-timing` to `prompt_timing=True`, and
PID candidate thresholds to the reconstruction config (`cli.py:331–350`,
`460–495`).

**Decision rule:** evaluate each run independently with
`evaluate_pi0_fake_candidates`, concatenate all candidate rows, and count
aggregate selected events by `(run, event_id)` so run-local event ids do
not collide (`pi0_fake_study.py:273–313`).

**Outputs:** a dict with scalar `run` when exactly one run is requested,
`runs`, `selector`, aggregate `summary`, `run_reports`, and all `rows`
(`pi0_fake_study.py:314–325`). `reconstruction.md:770–790` describes how
the saved fake-study reports are interpreted: residual charged-background
candidates often trace to real secondary π⁰ activity, and prompt timing
removes most residuals without truth labels.

**Truth reads:** delegated to `evaluate_pi0_fake_candidates`.

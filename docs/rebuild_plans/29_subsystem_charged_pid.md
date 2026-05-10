---
id: 29_subsystem_charged_pid
title: Subsystem — charged PID (leaves C.1, C.5, C.6)
version: 0.1
status: draft
owner: Charged-PID POG
depends_on: [00_README, 23_sample_calibration_aux, 24_reconstruction_question_tree, 27_subsystem_dedx, 28_subsystem_range_and_stopping, 57_mva_method_protocol]
outputs:
  - {path: docs/rebuild_plans/29_subsystem_charged_pid.md, schema: this file}
acceptance:
  - {test: cut-based PID reproduces licentiate balanced-F1, method: scan-pid CLI on signal + cal samples, pass_when: ≥ baseline}
  - {test: likelihood-ratio PID benchmarked against cut-based on ladder leaf C.5, method: plan 38 matrix entry, pass_when: matrix entry recorded}
  - {test: Class B `Name` gate removed from C.1 production path, method: plan 01 audit, pass_when: zero violations}
risks:
  - {risk: removing the Name gate exposes EM and neutral tracks to PID classifier; misclassification rises, mitigation: §3 EM/neutral rejection via shower-shape and TPC topology}
estimated_effort: L
last_updated: 2026-05-10
---

# Subsystem — charged PID

*Charter.* Owns leaves C.1 (charged candidate), C.5 (π/p decision),
C.6 (rejection). Combines dE/dx (plan 27) and range (plan 28) into
a per-track classification.

## 1. Leaf input/output schemas

Per plan 24 C.1 / C.5 / C.6 schemas:

| Leaf | Class A inputs | Forbidden Class B | Output schema |
|---|---|---|---|
| C.1 charged candidate | V.1/V.2 track tables; TPC `Event_ID`, `x`, `y`, `z`, `t`, `eDep`, `photons`, `px`, `py`, `pz`, `xHitID`, `module_ID`, `step_info`, `vol_name` | `Name`, `Track_ID`, `Parent_ID`, `origin_vol_name`, `particle_x/y/z` | `{event_id, charged_candidate_id, candidate_id, anchor_xyz, direction_xyz, n_tpc_hits, track_quality, charged_candidate_valid}` |
| C.5 π/p decision | C.1 candidate table, C.2 dE/dx, C.3 range, C.4 scintillator association, PID thresholds | `Name`, `Track_ID`, `Parent_ID`, `origin_vol_name`, truth PID labels | `{event_id, charged_candidate_id, pid, proton_score, pion_score, thresholds, rule_version, pid_valid, decision_reason}` |
| C.6 rejection | C.1-C.5 outputs, Class A lead-glass / shower-shape observables, TPC pair topology, hit timing, geometry side-cars | `Name`, `Track_ID`, `Parent_ID`, `origin_vol_name`, `Interaction`, `particle_x/y/z`, truth PID labels | `{event_id, charged_candidate_id, rejected, rejection_flags, primary_reason, pid_before_rejection, pid_after_rejection, rule_version}` |

### 1.1 Leaf schema block — C.1 charged candidate

- **inputs (Class A):** V.1/V.2 track rows plus TPC `Event_ID`,
  `x`, `y`, `z`, `t`, `eDep`, `photons`, `px`, `py`, `pz`,
  `xHitID`, `module_ID`, `step_info`, `vol_name`.
- **forbidden (Class B):** `Name`, `Track_ID`, `Parent_ID`,
  `origin_vol_name`, `particle_x`, `particle_y`, `particle_z`.
- **decision rule:** promote any Class A TPC track passing quality and
  containment cuts into a charged candidate; species names and truth
  track IDs may not filter the production candidate set.
- **output schema:** `event_id: int`, `charged_candidate_id: int`,
  `candidate_id: int`, `anchor_xyz: float[3]`,
  `direction_xyz: float[3]`, `n_tpc_hits: int`,
  `track_quality: float`, `charged_candidate_valid: bool`.
- **allowed truth use:** `validation_only` for candidate efficiency
  and truth-substitution ladder rows.
- **downstream consumers:** C.2, C.3, C.5, C.6, plans 32, 38, and 47.

### 1.2 Leaf schema block — C.5 π/p decision

- **inputs (Class A):** C.1 charged candidates, C.2 dE/dx, C.3
  range/stopping fields, C.4 scintillator association, and signed PID
  thresholds or likelihood-ratio calibration artifacts.
- **forbidden (Class B):** `Name`, `Track_ID`, `Parent_ID`,
  `origin_vol_name`, truth PID labels, and truth kinetic energy.
- **decision rule:** assign π/p labels from Class A PID observables
  using the signed threshold or likelihood-ratio rule version; truth
  labels are allowed only in training/validation splits.
- **output schema:** `event_id: int`, `charged_candidate_id: int`,
  `pid: str`, `proton_score: float`, `pion_score: float`,
  `thresholds: dict`, `rule_version: str`, `pid_valid: bool`,
  `decision_reason: str`.
- **allowed truth use:** `labeling` for locked calibration-sample
  training and `validation_only` for score reporting; never during
  production scoring.
- **downstream consumers:** C.6, plans 32, 38, 45, 47, and 57.

### 1.3 Leaf schema block — C.6 rejection

- **inputs (Class A):** C.1-C.5 outputs, lead-glass/shower-shape
  observables, TPC pair topology, hit timing, geometry side-cars, and
  conversion-veto state derived from reconstructed vertices.
- **forbidden (Class B):** `Name`, `Track_ID`, `Parent_ID`,
  `origin_vol_name`, `Interaction`, `particle_x`, `particle_y`,
  `particle_z`, and truth PID labels.
- **decision rule:** apply EM, neutral, and conversion rejection using
  reconstructed topology and calorimeter observables only; rejected
  candidates retain the pre-rejection PID for auditability.
- **output schema:** `event_id: int`, `charged_candidate_id: int`,
  `rejected: bool`, `rejection_flags: list[str]`,
  `primary_reason: str | null`, `pid_before_rejection: str`,
  `pid_after_rejection: str | null`, `rule_version: str`.
- **allowed truth use:** `validation_only` for rejection efficiency,
  fake-rate, and ladder scoring after C.6 output is frozen.
- **downstream consumers:** plans 32, 38, 43, 45, and 47.

Current implementation citation: `reconstruct_charged_objects`
(`charged.py:151-228`, plan 08 §3.4) owns the current C.1/C.5
path and emits `pid`, `dedx`, `scintillator_range`, `track_anchor`,
and `track_direction`, with `truth_name` retained for validation only
after the migration.

### 1.4 Machine-readable charged-PID fixtures

The charged-PID seam is split into three target fixtures so C.1
candidate formation, C.5 species scoring, and C.6 rejection can be
tested independently by the ladder:

| Fixture | Required fields | Production invariant |
|---|---|---|
| C.1 charged candidate | `event_id`, `charged_candidate_id`, `candidate_id`, `track_quality`, `charged_candidate_valid`, `candidate_failure_reason` | dropping `Name` and `Track_ID` cannot remove a production candidate |
| C.5 PID score | `event_id`, `charged_candidate_id`, `pid`, `proton_score`, `pion_score`, `thresholds`, `rule_version`, `pid_valid`, `decision_reason` | truth species and truth kinetic energy are absent from scoring input |
| C.6 rejection | `event_id`, `charged_candidate_id`, `rejected`, `rejection_flags`, `primary_reason`, `pid_before_rejection`, `pid_after_rejection`, `rule_version` | rejection reasons are reconstructed topology or calorimeter states, never truth labels |

Training/validation labels for likelihood-ratio or threshold scans live
in separate closure artifacts keyed by `(event_id,
charged_candidate_id, rule_version)`. A production PID fixture is valid
only if C.2 and C.3 fixture hashes match the dE/dx and range inputs
used to compute the C.5 row.

## 2. Cut-based baseline (current code)

`/Volumes/MyDrive/nnbar/nnbar/NNBAR_Detector-L3/nnbar_reconstruction/charged.py`
`reconstruct_charged_objects` (plan 08 §3.4):

```
proton if  dedx >= proton_dedx_min                       # default 8.0
        OR (0 < scint_range <= short_range_cm
            AND dedx >= short_range_proton_dedx_min)     # default 4.5
charged_pion otherwise
```

Defaults are intentionally simple; `scan-pid` (plan 08 §4.2) tunes
them on labelled samples.

Class B violation: input is currently filtered to `Name ∈ {pi+, pi-,
proton, antiproton}` before the PID rule applies. Migration: drop
this filter; treat any TPC track as a candidate; the PID rule plus
EM/neutral rejection (§3) replaces the filter.

## 3. Likelihood-ratio PID (target improvement)

Per plan 57 MVA protocol:

1. Train a likelihood ratio (`L_proton / (L_proton + L_pion)`) on
   `cal_singleproton_v1` and `cal_singlepionplus/minus_v1`.
2. Features: dE/dx (truncated mean), range, scintillator energy,
   track length, n hits, lead-glass leakage.
3. Train/validation/test split with seed; check overtraining
   (plan 57 §3).
4. Score on the ladder (plan 38 leaf C.5). Improvement is reported
   as IV(C.5) reduction.


### 3.1 Alternative comparison rows

| Alternative | Source paper / codebase | NNBAR-specific adaptation | Expected ladder leaf delta |
|---|---|---|---|
| Cut-based baseline | Existing `reconstruct_charged_objects` (`charged.py:151-228`) | Keep thesis Ch 8/9 threshold form but remove the C.1 truth-name gate before production scoring. | Reproduces baseline; ladder delta comes primarily from removing truth substitution. |
| Likelihood-ratio PID | Plan 57 MVA protocol / standard likelihood-ratio classifier | Train on plan 23 charged calibration samples using C.2/C.3/C.4 features and locked train/validation/test splits. | Expected to reduce C.5 π/p confusion, especially near stopping-proton boundaries; must beat cut-based on plan 38. |

## 4. EM and neutral rejection (C.6)

When `Name` filter is removed (§2 migration), the candidate set
includes:

- Truth electrons / positrons (gamma conversions in detector
  material).
- Truth neutral-particle artefacts (rare).

Rejection rules:

- *EM rejection.* TPC track with low dE/dx + matched lead-glass
  cluster of high E and small lateral spread → tag as electron.
  See plan 32 (shower shape) for the cluster-side criterion.
- *Conversion-pair rejection.* TPC tracks coming from a vertex
  reconstructed near beampipe/silicon material with opposite-charge
  partner → tag as conversion pair (matches Ch 8.2 5 cm rule
  already implemented for electron-pair candidates).

Each rejection is implemented in Class A: lead-glass clusters and
TPC topology only.

## 5. Closure-test specification

1. **Dataset ids:** `cal_singlepion_50to600MeV_v2`,
   `cal_singleproton_50to500MeV_v2`, and `sig_foil_500MeV_v3` from
   plan 03.
2. **Observable:** C.5 π/p confusion matrix, balanced F1, proton
   efficiency, charged-pion efficiency, and C.6 rejection fractions.
3. **Fitter / classifier:** run `scan-pid` for the cut-based baseline
   and the locked likelihood-ratio classifier for the improvement;
   truth labels are consumed only in the validation/labeling split.
4. **Pass criterion:** cut-based PID reproduces the licentiate
   baseline within plan 47 tolerance, the `Name` gate is absent from
   the production path, and the likelihood-ratio result has a plan 38
   C.5 ladder matrix entry before any promotion.

## 6. Stage E.1 implementation handoff

For L3's charged-side redesign, the C.5 production fixture is now split
from the legacy charged-object row. The production-like hook is
`classify_charged_candidates` (`charged_pid.py:60-118`), which consumes
plan-25 C.1 candidates plus plan-27 C.2 and plan-28 C.3 rows. The
current help-verified calibration scan surface is still `scan-pid`; it
calls `scan_charged_pid_thresholds` (`calibration.py:27-134`), which
scores labels from `truth_name` after `reconstruct_charged_objects`
has emitted the legacy rows. That scan is valid for calibration only,
not for production charged-PID fixture decisions.

Plan-side gates for the L3 implementation:

1. Consume the plan-25 C.1 candidate rows, plan-27 C.2 dE/dx rows,
   plan-28 C.3 range rows, and C.4 scintillator-association sidecar;
   do not re-open raw TPC truth columns in the C.5 scorer.
2. Emit separate C.1, C.5, and C.6 fixture rows with the fields in
   §1.4 and hashes of the consumed C.2/C.3 inputs.
3. Preserve the cut-based threshold rule as a named reproduction mode,
   then add likelihood-ratio scoring only behind a plan 57
   train/validation/test artifact and a plan 05 decision entry.
4. Keep EM/neutral rejection reasons observable-only: lead-glass
   shower-shape, conversion-pair topology, hit timing, and geometry
   side-cars. Truth `Name` and `Interaction` can appear only in
   validation or labeling artifacts.
5. Keep the current charged-PID tests in `tests/test_charged_reco.py`:
   `test_classify_charged_candidates_uses_dedx_and_range_thresholds`
   (`tests/test_charged_reco.py:282-329`) covers the cut rule and output
   schema, and
   `test_classify_charged_candidates_real_sample_has_plan_29_schema`
   (`tests/test_charged_reco.py:331-350`) covers the real-output chain
   from C.1/C.2/C.3 into C.5. Extend them so dropping `Name`,
   `Track_ID`, and truth kinetic energy cannot change production
   candidate creation or production scoring.
6. Plan 66 consumes charged-PID validity, rejection-reason fractions,
   and rule-version drift once the C.5/C.6 fixtures are present.

### 6.1 Stage E.1 code-gap checklist

The live L3 hook already produces truth-free cut-based PID rows, but
the promoted C.1/C.5/C.6 fixture set still needs explicit provenance
and rejection coverage. L3 can promote charged PID only after these
gaps close in `classify_charged_candidates` (`charged_pid.py:60-118`):

| Gap | Current live behavior | Required promotion behavior |
|---|---|---|
| C.2/C.3 provenance | the scorer reads dE/dx and range rows but does not store consumed input hashes | add fixture hashes for the exact C.2 and C.3 rows used by each C.5 decision |
| threshold identity | `rule_version=plan29_cut_pid_v0` and threshold values are emitted | keep the rule version stable, and require a plan 05 decision before any threshold or likelihood-ratio promotion changes it |
| C.4 association | the cut rule uses dE/dx and range only | add the C.4 scintillator-association sidecar when plan 28 exposes associated-hit provenance |
| rejection coverage | invalid candidates/dE/dx rows are rejected with `invalid_candidate_or_dedx` | add explicit EM/neutral/conversion rejection reasons from observable-only lead-glass, timing, and topology inputs before C.6 is complete |
| truth-invariance test | current tests assert schema and thresholds, but not Class B-drop invariance | extend tests so dropping `Name`, `Track_ID`, and truth kinetic energy cannot change production C.5/C.6 rows |

Acceptance of this checklist is a plan-side gate, not a request for L0
to edit L3 code. The matching L3 patch must update
`test_classify_charged_candidates_uses_dedx_and_range_thresholds`
(`tests/test_charged_reco.py:282-329`) and
`test_classify_charged_candidates_real_sample_has_plan_29_schema`
(`tests/test_charged_reco.py:331-350`) so the synthetic and real-output
chains assert the provenance, rejection, and truth-invariance fields.

### 6.2 Stage E.1 promotion invariants

C.5 is the first charged-side decision that can directly alter the
analysis category, so promotion requires more than a schema match. L3
may replace or extend the cut rule only if these invariants stay true:

| Invariant | Current live behavior | Replacement requirement |
|---|---|---|
| truth blindness | `classify_charged_candidates` (`charged_pid.py:60-118`) consumes C.1 candidates plus C.2 dE/dx and C.3 range rows | production C.5/C.6 rows must be unchanged when `Name`, `Track_ID`, truth kinetic energy, and interaction labels are removed |
| calibration separation | `scan-pid` and `scan_charged_pid_thresholds` (`calibration.py:27-134`) may score truth labels for calibration | the calibrated threshold or likelihood artifact must be frozen before production scoring and cited through plan 57/plan 05 |
| rule identity | current rows emit `rule_version=plan29_cut_pid_v0` and threshold values | any threshold, likelihood-ratio, or rejection-taxonomy change must version the rule and keep old rows reproducible |
| input provenance | current C.5 rows read dE/dx and range values but do not persist consumed-row hashes | promoted rows must hash the exact C.2, C.3, and later C.4 sidecar rows used for each PID decision |
| observable-only rejection | current invalid rows use `invalid_candidate_or_dedx` | EM, neutral, conversion, and geometry rejections must come from observable lead-glass/timing/topology fields, never truth `Name` or `Interaction` |
| test invariance | current tests cover thresholds and real-output schema | tests must explicitly drop Class B columns and assert identical C.1/C.5/C.6 production rows before plan 38 ladder scoring |

These invariants keep C.5 as a reproducible analysis rule rather than a
hidden truth filter. They also define what the future likelihood-ratio
replacement must prove before it can supersede the cut-based baseline.

## 7. Acceptance criteria

- §2 cut-based baseline reproduced.
- §2 Name filter removed; replaced by §4 rejections.
- §3 likelihood-ratio scored on ladder; matrix entry in plan 38.
- Plan 47 ledger row "licentiate Ch 8 charged PID accuracy"
  reproduced.
- §6 Stage E.1 handoff is actionable for L3: current production and
  calibration hooks are cited, production C.1/C.5/C.6 inputs and
  outputs are named, promotion invariants are explicit, current
  charged-reco tests are cited, and the remaining tests must prove the
  production scorer is invariant to dropping Class B truth columns.

## 8. Risks

- *Risk:* likelihood-ratio overfits on calibration sample.
  *Mitigation:* plan 57 §3 overtraining check; final score on
  signal-sample-derived test set.

## 9. Dependencies

- **23, 24, 27, 28, 57** — inputs.
- *Consumed by:* plans 32 (event selection), 38 (ladder), 47.

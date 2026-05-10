---
id: 29_stage_e1_handoff
title: Charged PID Stage E.1 implementation handoff
version: 0.1
status: draft
owner: Charged-PID POG
parent: 29_subsystem_charged_pid
last_updated: 2026-05-10
---

# Charged PID Stage E.1 implementation handoff

This annex is split from `docs/rebuild_plans/29_subsystem_charged_pid.md`
to keep both files under the 500-line cap. It is normative for plan 29
Stage E.1 implementation and inherits plan 29's acceptance, risks, and
dependencies.

## 6. Stage E.1 implementation handoff

For L3's charged-side redesign, the C.5 production fixture is now split
from the legacy charged-object row. The production-like hook is
`classify_charged_candidates` (`nnbar_reconstruction/charged_pid.py:60-118`), which consumes
plan-25 C.1 candidates plus plan-27 C.2 and plan-28 C.3 rows. The
current help-verified calibration scan surface is still `scan-pid`; it
calls `scan_charged_pid_thresholds` (`nnbar_reconstruction/calibration.py:27-134`), which
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
gaps close in `classify_charged_candidates` (`nnbar_reconstruction/charged_pid.py:60-118`):

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
| truth blindness | `classify_charged_candidates` (`nnbar_reconstruction/charged_pid.py:60-118`) consumes C.1 candidates plus C.2 dE/dx and C.3 range rows | production C.5/C.6 rows must be unchanged when `Name`, `Track_ID`, truth kinetic energy, and interaction labels are removed |
| calibration separation | `scan-pid` and `scan_charged_pid_thresholds` (`nnbar_reconstruction/calibration.py:27-134`) may score truth labels for calibration | the calibrated threshold or likelihood artifact must be frozen before production scoring and cited through plan 57/plan 05 |
| rule identity | current rows emit `rule_version=plan29_cut_pid_v0` and threshold values | any threshold, likelihood-ratio, or rejection-taxonomy change must version the rule and keep old rows reproducible |
| input provenance | current C.5 rows read dE/dx and range values but do not persist consumed-row hashes | promoted rows must hash the exact C.2, C.3, and later C.4 sidecar rows used for each PID decision |
| observable-only rejection | current invalid rows use `invalid_candidate_or_dedx` | EM, neutral, conversion, and geometry rejections must come from observable lead-glass/timing/topology fields, never truth `Name` or `Interaction` |
| test invariance | current tests cover thresholds and real-output schema | tests must explicitly drop Class B columns and assert identical C.1/C.5/C.6 production rows before plan 38 ladder scoring |

These invariants keep C.5 as a reproducible analysis rule rather than a
hidden truth filter. They also define what the future likelihood-ratio
replacement must prove before it can supersede the cut-based baseline.

### 6.3 Stage E.1 producer/consumer contract

The L3 C.5/C.6 patch must expose a stable table boundary so plan 38
ladder rows, plan 47 ledgers, and plan 66 DQM can consume charged-PID
decisions without re-running calibration scans or reopening truth labels:

| Contract item | Required behavior | Downstream check |
|---|---|---|
| input key | consume one C.1 candidate keyed by `(event_id, charged_candidate_id)` plus the selected C.2 `estimator_id` and C.3 `range_id` rows | C.5 rows can be joined to the exact dE/dx and range facts used for scoring |
| output key | emit one C.5 row keyed by `(event_id, charged_candidate_id, pid_decision_id)` and optional C.6 rejection rows keyed by `(event_id, charged_candidate_id, rejection_id)` | plan 38 and plan 47 count attempted candidates without inferring missing rows as accepted or rejected physics |
| rule provenance | record `rule_version`, `classifier_family`, and threshold or likelihood-artifact hashes in every manifest | plan 05 can audit any threshold or classifier change before promotion |
| source hashes | record C.1, C.2, C.3, and optional C.4 sidecar hashes before writing C.5/C.6 outputs | plan 47 can prove the same upstream tables fed PID, signal-efficiency, and DQM artifacts |
| rejection taxonomy | restrict production reasons to observable invalid-state, EM-like, neutral-like, conversion-like, and geometry-loss categories | plan 66 aggregates rejection fractions without reading `Name`, `Interaction`, or truth energy |
| calibration boundary | consume frozen calibration artifacts only; do not call `scan-pid` from the production scorer | closure studies can score labels after the C.5/C.6 table is frozen, but cannot alter production rows |

This contract keeps `classify_charged_candidates`
(`nnbar_reconstruction/charged_pid.py:60-118`) as the Stage E.1 C.5/C.6
producer until L3 replaces the classifier behind the same keys.

### 6.4 Stage E.1 verification command

L3's C.5/C.6 patch is promotable only when the charged-PID slice
exercises both the synthetic threshold/rejection path and the real-output
C.1/C.2/C.3→C.5 chain:

```bash
pytest tests/test_charged_reco.py::test_classify_charged_candidates_uses_dedx_and_range_thresholds \
       tests/test_charged_reco.py::test_classify_charged_candidates_real_sample_has_plan_29_schema
```

The review note for that patch must quote the command output and the
C.5/C.6 artifact manifest fields `rule_version`, `thresholds`,
`pid_valid`, `decision_reason`, `rejection_flags`, and the consumed
C.2/C.3 row hashes. A likelihood-ratio replacement also needs the plan
57 train/validation/test artifact and a plan 05 decision before it can
replace the cut-based baseline.

### 6.5 Stage E.1 artifact manifest schema

The C.5/C.6 producer must write a manifest that freezes rule identity,
thresholds, consumed C.2/C.3 rows, and rejection taxonomy before plan 38
or plan 47 consumes charged-PID decisions:

```yaml
schema_version: plan29_c5_c6_pid@stage-e1
dataset_id: <plan-03 dataset id>
producer: classify_charged_candidates
rule_version: plan29_cut_pid_v0 | <plan-05-approved successor>
classifier_family: cut_based | likelihood_ratio
thresholds_hash: <sha256 of threshold payload>
input_c1_hash: <sha256 of C.1/V.1 candidate table>
input_c2_hash: <sha256 of C.2 dE/dx table>
input_c3_hash: <sha256 of C.3 range table>
input_c4_hash: <sha256 of scintillator-association sidecar or null>
output_pid_hash: <sha256 of C.5 PID table>
output_rejection_hash: <sha256 of C.6 rejection table>
rejection_reasons_allowed: [none, invalid_candidate_or_dedx, em_like_observable, neutral_like_observable, conversion_like_observable, geometry_outside_acceptance]
truth_columns_absent: [Name, Track_ID, truth_kinetic_energy, Interaction]
calibration_artifact: scan-pid | plan57_locked_split | null
```

The manifest is invalid if `classifier_family=likelihood_ratio` lacks a
plan 57 split artifact and a plan 05 decision, or if any truth column is
listed as a production input. Plans 38 and 47 consume this manifest
before accepting C.5/C.6 ladder or ledger rows.

### 6.6 Stage E.1 fixture matrix

The C.5/C.6 replacement patch must prove that charged-PID decisions are
rule-versioned, source-hashed, and truth-blind before plan 38 or plan 47
consumes the PID manifest:

| Fixture case | Required input condition | Required assertion |
|---|---|---|
| truth-column drop | C.1/C.2/C.3 rows are run with and without `Name`, `Track_ID`, truth kinetic energy, and interaction labels | C.5/C.6 rows, `rule_version`, `pid_valid`, and rejection reasons are unchanged |
| invalid C.2 input | a candidate has a failed or non-applicable dE/dx estimator row | PID emits a rejected row with `decision_reason=invalid_candidate_or_dedx` rather than silently dropping the candidate |
| invalid C.3 input | range row is failed, edge-gated, or unavailable | PID records the configured range-handling reason and does not infer proton/pion class from null `range_cm` |
| threshold boundary | dE/dx and range values straddle the cut-based threshold values | `classifier_family=cut_based`, threshold hashes, and pass/fail decisions reproduce the frozen `rule_version` |
| likelihood candidate | a likelihood-ratio artifact is supplied during review | promotion remains blocked unless plan 57 split hashes and a plan 05 decision are present in the manifest |
| real C.1/C.2/C.3 chain | real paired output flows through plans 25, 27, and 28 before PID production | C.5 consumes frozen upstream hashes and never calls `scan-pid` or reads calibration labels during production scoring |

The review artifact for any PID replacement must map each fixture row to
the synthetic or real-output selector in §6.4. Rows that depend on plan
57 likelihood artifacts remain calibration-only until their manifest
contains both the split hash and the plan 05 decision id.

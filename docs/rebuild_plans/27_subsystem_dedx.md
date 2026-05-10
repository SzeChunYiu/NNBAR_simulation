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

Legacy implementation citation: `reconstruct_charged_objects`
(`nnbar_reconstruction/charged.py:151-228`, plan 08 §3.4) already emits `dedx`,
but the value is downstream of the current truth-name candidate gate.
The live Stage E.1 hook is `reconstruct_dedx_table`
(`nnbar_reconstruction/dedx.py:91-119`), which consumes V.1 candidate `hit_indices`, calls
`truncated_mean_dedx` (`nnbar_reconstruction/dedx.py:41-70`), and obtains path increments
from `_step_lengths` (`nnbar_reconstruction/dedx.py:28-38`) without reading truth labels.

Output schema: `{event_id, charged_candidate_id, dedx_mev_per_cm,
estimator, n_steps_used, path_length_cm, low_truncation_fraction,
high_truncation_fraction, calibration_source}`. The current live hook
emits this physics schema; §5 quality columns remain an explicit L3
follow-up before closure sign-off.

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

### 1.4 Physics derivation

- **What is physically measured:** C.2 measures the TPC specific ionisation
  estimator, `dE/dx`, for each charged candidate. The truth-side reference is
  the Bethe-Bloch expectation as a function of βγ and species, used only for
  validation after production rows are frozen.
- **Estimator rationale:** per-step ionisation samples have a long high tail,
  so the arithmetic mean is inefficient for PID. A truncated mean removes the
  largest Landau-tail deposits while retaining enough central samples to follow
  the Bethe-Bloch curve; PDG passage-of-particles material and ALICE TPC PID
  practice justify this estimator family
  \cite{ParticleDataGroup:2024RPP,alice2014performance}.
- **Statistical character:** the estimator variance is dominated by straggling
  and short track length. Bias enters through truncation fractions,
  path-length normalisation, threshold losses, and gas/W-value calibration.
  Robustness requires persisting the selected/rejected sample sidecar and the
  calibration source instead of changing PID thresholds in response to closure
  residuals.
- **Citation:** the cited keys above were checked against
  `/Users/billy/Desktop/projects/overleaf-hibeam-thesis/ref.bib` on
  2026-05-10.

### 1.5 Logic gaps

1. **Low truncation fraction = 0.10 and high fraction = 0.30:** OPEN: scan low
   fractions 0-20% and high fractions 10-50% on pion/proton calibration
   samples; optimise Bethe-Bloch residual and downstream C.5 separation;
   target resolution date 2026-05-17.
2. **Minimum sample count after truncation:** OPEN: determine the smallest
   `n_steps_used` whose residual bias remains within 5%; target resolution date
   2026-05-17.
3. **Path-length estimator:** OPEN: compare `TrackLength`, per-hit coordinate
   differences, and V.2 geometry-derived path length; figure of merit is dE/dx
   residual by angle and candidate length; target resolution date 2026-05-24.
4. **Calibration scale / W-value:** OPEN: propagate plan-17 gas W-value and
   electron-yield calibration into a versioned `calibration_source`; target
   resolution date 2026-05-24.
5. **Closure βγ window `[0.5, 5]` and residual band 5%:** keep as the current
   plan-27 validation gate until the calibration scan records a plan-05
   decision to tighten or widen it.

### 1.6 Closure test for the derivation

1. Run `reconstruct_dedx_table` on frozen C.1/V.1 candidates for
   `cal_singlepion_50to600MeV_v2` and `cal_singleproton_50to500MeV_v2` using
   only Class-A TPC energy deposits and path-length fields.
2. Persist the C.2 row plus contribution sidecar before joining truth species
   or momentum.
3. In a `validation_only` closure fitter, compute Bethe-Bloch residuals versus
   βγ for pions and protons, binned by `n_steps_used`, path-length source, and
   truncation fractions.
4. The derivation passes when residuals stay within the 5% band or the
   calibration limitation is signed in plan 17/45 without silently changing the
   C.5 production PID threshold.

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
| Arithmetic mean baseline | Existing `reconstruct_charged_objects` (`nnbar_reconstruction/charged.py:151-228`) | Preserve current `dedx` computation as a reproducibility reference after removing any C.1 truth-name candidate gate. | No intended C.2 gain; establishes the current tail-sensitive baseline for plan 38. |
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

For L3's charged-side redesign, C.2 is now a typed estimator seam with
explicit remaining gates:

1. Input rows come from C.1 candidates, V.2 path-length/covariance
   outputs when available, and Class A TPC energy-deposit samples. The
   live hook currently uses V.1 hit indices and Class A step lengths; it
   must prefer V.2 path-length/covariance once plan 26 exposes the full
   table.
2. The arithmetic-mean baseline is preserved as a named reproduction
   mode; the default production mode is the signed truncated mean once
   the DEC records its low/high fractions.
3. The module writes §1 physics fields in one row per charged candidate;
   L3 still must add `dedx_quality_state`, `dedx_failure_reason`,
   `path_length_source`, `truncation_applied`, and contribution-sidecar
   rows before plan 40/45 closure can treat C.2 as complete.
4. Bethe-Bloch residuals and truth momentum live only in the closure
   artifact namespace after the production C.2 table is frozen.
5. Plan 45 receives a calibration nuisance input from the closure
   residual, not from hand-edited PID thresholds.
6. Plan 66 consumes dE/dx quality and path-length-source fractions once
   the §5 fields are present.

### 6.1 L3 target module, functions, and tests

- **Target module:** extend `nnbar_reconstruction/dedx.py`.
- **Public functions:** `truncated_mean_dedx(steps)` (`nnbar_reconstruction/dedx.py:41-70`)
  and `reconstruct_dedx_table(candidates, tpc)` (`nnbar_reconstruction/dedx.py:91-119`).
- **Current unit coverage:** `tests/test_charged_reco.py` already
  checks the signed truncation behavior in
  `test_truncated_mean_dedx_drops_plan_27_tails`
  (`tests/test_charged_reco.py:168-181`) and candidate-hit membership in
  `test_reconstruct_dedx_table_uses_candidate_hit_membership`
  (`tests/test_charged_reco.py:184-207`).
- **Current integration coverage:** the real-output schema path is
  `test_reconstruct_dedx_table_real_sample_has_plan_27_schema`
  (`tests/test_charged_reco.py:209-221`), which chains plan-25
  candidates into `reconstruct_dedx_table`.
- **Remaining test obligation:** extend those tests for missing or
  non-positive step lengths, explicit `path_length_source`, and the
  future `dedx_quality_state` / `dedx_failure_reason` fields once L3
  exposes them.

### 6.2 Stage E.1 code-gap checklist

The live L3 hook already proves that C.2 can be reconstructed without
truth labels, but the promoted fixture still needs the explicit quality
and provenance fields from §1.3/§5. L3 can promote C.2 only after these
gaps close in `reconstruct_dedx_table` (`nnbar_reconstruction/dedx.py:91-119`) and
`truncated_mean_dedx` (`nnbar_reconstruction/dedx.py:41-70`):

| Gap | Current live behavior | Required promotion behavior |
|---|---|---|
| estimator identity | `estimator=truncated_mean` and `calibration_source=plan27_truncated_mean_v0` are emitted | add a stable `estimator_id` that keys the DEC-approved low/high fractions and calibration source |
| path provenance | `path_length_cm` is emitted from `TrackLength`, `trackl`, `step_length`, or coordinate deltas | add `path_length_source` so plan 26 and plan 38 can separate covariance-derived, Class-A track-length, and degraded span normalisations |
| truncation provenance | low/high fractions are emitted, but selected/removed samples are not persisted | add `truncation_applied` plus the contribution sidecar keyed by `(event_id, charged_candidate_id, estimator_id)` |
| quality state | missing/empty/non-positive paths produce NaN physics values without a machine-readable C.2 state | add `dedx_quality_state` and `dedx_failure_reason` with `pass`, `warn`, `fail`, or `not_applicable` semantics from §5 |
| validation separation | Bethe-Bloch closure is specified but not linked to the production row id | write closure residuals only after the production row is frozen and key them to `estimator_id` |

Acceptance of this checklist is a plan-side gate, not a request for L0
to edit L3 code. The matching L3 patch must update
`test_truncated_mean_dedx_drops_plan_27_tails`
(`tests/test_charged_reco.py:168-181`),
`test_reconstruct_dedx_table_uses_candidate_hit_membership`
(`tests/test_charged_reco.py:184-207`), and
`test_reconstruct_dedx_table_real_sample_has_plan_27_schema`
(`tests/test_charged_reco.py:209-221`) so the synthetic and real-output
chains assert every required C.2 promotion column.

### 6.3 Stage E.1 promotion invariants

The current live hook is a truth-blind C.2 bridge. L3 may replace the
estimator or path-length source only if these invariants remain explicit
in the production table and in the plan-27 tests:

| Invariant | Current live behavior | Replacement requirement |
|---|---|---|
| truth blindness | `reconstruct_dedx_table` (`nnbar_reconstruction/dedx.py:91-119`) joins V.1 hit membership to Class A TPC energy-deposit rows | output must be unchanged when particle species, truth momentum, parentage, and legacy track ids are absent |
| estimator identity | `truncated_mean_dedx` (`nnbar_reconstruction/dedx.py:41-70`) emits `estimator=truncated_mean` and `calibration_source=plan27_truncated_mean_v0` | promoted rows must add a stable `estimator_id` that keys truncation fractions, calibration constants, and DEC history |
| path provenance | `path_length_cm` is derived from Class A length-like fields or coordinate deltas | promoted rows must add `path_length_source` and must not substitute validation-only truth path length into production C.2 |
| truncation audit | current rows preserve low/high fractions but not selected sample ids | replacement must emit `truncation_applied` and a contribution sidecar keyed by `(event_id, charged_candidate_id, estimator_id)` |
| quality-state semantics | missing or non-positive path support currently yields null physics values without a machine-readable reason | promoted rows must set `dedx_quality_state` and `dedx_failure_reason` with the §5 `pass`/`warn`/`fail`/`not_applicable` meanings |
| validation separation | Bethe-Bloch residuals are a closure artifact, not a production input | closure residual rows must join to frozen `estimator_id` rows and never change `dedx_mev_per_cm` after the production table is written |

These invariants are the C.2 promotion gate for L3's implementation
patch. They keep plan 29 PID and plan 45 calibration nuisances from
learning hidden truth labels or silently changing the dE/dx estimator
between calibration and signal samples.

### 6.4 Stage E.1 producer/consumer contract

The L3 C.2 patch must expose enough provenance for PID, closure, and
calibration-nuisance consumers to reproduce the exact estimator inputs:

| Contract item | Required behavior | Downstream check |
|---|---|---|
| input key | consume C.1/V.1 candidates by `(event_id, charged_candidate_id)` plus the V.1 `hit_membership_key` when available | dE/dx rows can be joined back to the frozen candidate and hit sidecar without using truth labels |
| output key | emit one C.2 row keyed by `(event_id, charged_candidate_id, estimator_id)` | plan 29 can join PID features without guessing which estimator was active |
| contribution sidecar | write one contribution row per selected or rejected TPC step with truncation state | plan 40/45 closure can audit selected samples without re-running truncation |
| source hashes | record V.1 candidate hash, TPC input hash, truncation fractions, and calibration source in the manifest | plan 47 can prove the same C.2 inputs fed PID and systematics artifacts |
| path handoff | set `path_length_source` to distinguish Class-A step length, coordinate span, or future V.2 covariance path length | plan 38 separates estimator skill from degraded path-length availability |
| failure taxonomy | emit `dedx_quality_state` and `dedx_failure_reason` for empty, non-positive, or non-finite rows | plan 66 DQM and plan 29 PID do not infer failures from NaN `dedx_mev_per_cm` |

This contract keeps `reconstruct_dedx_table`
(`nnbar_reconstruction/dedx.py:91-119`) as the Stage E.1 C.2 producer
until L3 swaps in an implementation that preserves the same keys.

### 6.5 Stage E.1 verification command

L3's C.2 patch is promotable only when the dE/dx slice exercises the
truncation unit, synthetic candidate membership, and real-output chain:

```bash
pytest tests/test_charged_reco.py::test_truncated_mean_dedx_drops_plan_27_tails \
       tests/test_charged_reco.py::test_reconstruct_dedx_table_uses_candidate_hit_membership \
       tests/test_charged_reco.py::test_reconstruct_dedx_table_real_sample_has_plan_27_schema
```

The review note for that patch must quote the command output and the
C.2 artifact manifest fields `estimator_id`, `path_length_source`,
`truncation_applied`, `dedx_quality_state`, `dedx_failure_reason`, and
`calibration_source`. If the real-output selector skips, C.2 remains a
unit-test-only bridge and cannot feed plan 29 PID promotion or plan 45
calibration nuisances.

### 6.6 Stage E.1 artifact manifest schema

The C.2 producer must write a manifest that freezes estimator identity,
path-length provenance, and truncation settings before PID or nuisance
artifacts consume the dE/dx rows:

```yaml
schema_version: plan27_c2_dedx@stage-e1
dataset_id: <plan-03 dataset id>
producer: reconstruct_dedx_table
estimator_id: <stable estimator version>
estimator: truncated_mean | arithmetic_mean_reproduction | landau_mpv
input_v1_hash: <sha256 of V.1 candidate table>
input_tpc_hash: <sha256 of TPC input table>
output_dedx_hash: <sha256 of C.2 dE/dx table>
contribution_sidecar_hash: <sha256 of selected/rejected step sidecar>
low_truncation_fraction: <float>
high_truncation_fraction: <float>
path_length_source_values: [class_a_track_length, coordinate_span, v2_covariance_path, degraded_missing]
quality_states_allowed: [pass, warn, fail, not_applicable]
failure_reasons_allowed: [none, empty_candidate, missing_step_length, nonpositive_step_length, nonfinite_energy_deposit]
calibration_source: <plan-17-or-plan-23 calibration id>
```

The manifest is invalid if the truncation fractions differ from the DEC
entry named by `estimator_id` or if contribution-sidecar rows cannot be
joined back to `(event_id, charged_candidate_id, estimator_id)`. Plans
29, 40, 45, and 66 consume this manifest before trusting dE/dx values
or calibration residuals.

### 6.7 Stage E.1 fixture matrix

The C.2 replacement patch must prove the estimator is keyed, calibrated,
and truth-blind before plan 29 PID or plan 45 nuisance artifacts consume
the dE/dx table:

| Fixture case | Required input condition | Required assertion |
|---|---|---|
| truth-column drop | candidate membership and TPC steps are run with and without species, parentage, and legacy track labels | `dedx_mev_per_cm`, `estimator_id`, quality state, and contribution sidecar keys are unchanged |
| truncation tails | one candidate has low and high ionization outliers around a stable core | selected/rejected contribution rows reproduce the signed low/high fractions and set `truncation_applied=true` |
| missing path length | candidate steps have finite energy but no positive Class A path-length support | a C.2 row is emitted with a documented failure reason and no downstream PID feature is inferred from NaN |
| nonfinite energy deposit | one or more selected steps have nonfinite `eDep` or equivalent energy-deposit value | nonfinite samples are excluded or the row fails with `dedx_failure_reason=nonfinite_energy_deposit` |
| V.2 path handoff | the same candidate has both Class A coordinate span and a future V.2 path/covariance payload | `path_length_source` records which source was used and the manifest hash identifies the upstream V.2 table |
| real candidate chain | real paired output is reconstructed through plan 25 candidates before dE/dx production | C.2 consumes frozen candidate keys and does not read validation labels to repair estimator inputs |

The review artifact for the L3 patch must map each fixture row to a
test selector or to an explicit not-promoted quality state in the C.2
manifest. Rows that need plan 26 covariance support may remain gated
until the V.2 manifest is present, but they must still define the
expected `path_length_source` value.

## 7. Acceptance criteria

- §3 closure within 5% across the charged calibration set.
- §1 truncated-mean cut fractions documented in DEC.
- §4 saturation limitation noted in plan 47 ledger for any
  high-dE/dx-quoted result.
- §6 Stage E.1 handoff is actionable for L3: the target public
  functions, current unit/integration tests, remaining test obligation,
  promotion invariants, producer/consumer contract, verification
  command, artifact manifest schema, fixture matrix, and required C.2 fields (`estimator_id`, `dedx_mev_per_cm`,
  `path_length_cm`, `path_length_source`, `n_steps_used`, truncation
  fractions, `truncation_applied`, `dedx_quality_state`,
  `dedx_failure_reason`, `calibration_source`, and contribution sidecar
  rows) are all named before replacement promotion.

## 8. Dependencies

- **17, 23, 25, 26** — inputs.
- *Consumed by:* plan 29 (charged PID), plan 38 (ladder leaf C.2).

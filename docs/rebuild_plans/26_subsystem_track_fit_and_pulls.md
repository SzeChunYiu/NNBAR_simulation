---
id: 26_subsystem_track_fit_and_pulls
title: Subsystem — track fit, residuals, pulls (leaf V.2)
version: 0.1
status: draft
owner: Tracking POG
depends_on: [00_README, 04_statistical_uncertainty, 24_reconstruction_question_tree, 25_subsystem_tpc_hits_to_tracks, 38_truth_substitution_ladder, 40_closure_and_pulls]
outputs:
  - {path: docs/rebuild_plans/26_subsystem_track_fit_and_pulls.md, schema: this file}
acceptance:
  - {test: pull distribution mean / width within plan 40 §2 tolerance for V.2, method: closure plot, pass_when: pass}
  - {test: per-coordinate covariance reported by every fitter, method: code review, pass_when: covariance present}
  - {test: V.2 alternatives scored in the plan 38 ladder matrix, method: ladder IV(V.2) row, pass_when: visible-mass and vertex-residual deltas recorded}
risks:
  - {risk: current direction estimator has no covariance → vertex aggregation in V.4 cannot weight tracks, mitigation: §2 Kalman path provides Σ}
estimated_effort: M
last_updated: 2026-05-10
---

# Subsystem — track fit and pull distributions

*Charter.* Owns leaf V.2 (track direction estimation) plus its
covariance. The covariance feeds vertex aggregation (V.4) and
charged-PID dE/dx normalisation (C.2).

## 1. Inputs and outputs

Inputs: track-candidate hit list from V.1.
Outputs: `(direction, Σ_direction)` per candidate, plus `χ²/ndf` and
per-hit residuals for closure.

Per plan 24 V.2 schema:

### 1.1 Leaf schema block

Leaf V.2 — track fit, residuals, and pulls

- **inputs (Class A):** V.1 candidate hit indices plus TPC
  `Event_ID`, `x`, `y`, `z`, `t`, `eDep`, `photons`, `px`, `py`,
  `pz`, `xHitID`, `module_ID`, `step_info`, `vol_name`.
- **forbidden (Class B):** `Track_ID`, `Parent_ID`, `Name`,
  `origin_vol_name`, `particle_x`, `particle_y`, `particle_z`.
- **decision rule:** estimate the track direction and covariance from
  Class A hit coordinates only; truth direction may be used only after
  reconstruction output is frozen for pull scoring.
- **output schema:** `event_id: int`, `candidate_id: int`,
  `anchor_xyz: float[3]`, `direction_xyz: float[3]`,
  `direction_covariance: float[3,3]`, `chi2_ndf: float`,
  `n_direction_hits: int`, `direction_method: str`,
  `residuals_xyz: list[float[3]]`, `pulls_theta_phi: float[2]`.
- **allowed truth use:** `validation_only` for closure pulls and plan
  38 ladder rows; forbidden in the V.2 production fitter.
- **downstream consumers:** plans 27, 30, 38, 40, and any V.4 vertex
  aggregation that weights tracks by direction covariance.

### 1.2 Column contract

| Class A inputs | Forbidden Class B |
|---|---|
| V.1 candidate table; referenced TPC columns `Event_ID`, `x`, `y`, `z`, `t`, `eDep`, `photons`, `px`, `py`, `pz`, `xHitID`, `module_ID`, `step_info`, `vol_name` | `Track_ID`, `Parent_ID`, `Name`, `origin_vol_name`, `particle_x`, `particle_y`, `particle_z` |

Output schema:

```
event_id
candidate_id
anchor_xyz
direction_xyz
direction_covariance
chi2_ndf
n_direction_hits
direction_method
residuals_xyz
pulls_theta_phi
```

### 1.3 Machine-readable V.2 fit fixture

The V.2 fixture freezes the fitted direction before vertexing, dE/dx,
or truth-pull code can inspect validation labels. It stores one row per
V.1 candidate and keeps variable-length residuals in a sidecar:

| Fixture field | Meaning / invariant |
|---|---|
| `event_id`, `candidate_id` | join key inherited from the V.1 fixture |
| `fit_id` | stable identifier for the configured V.2 fitter and version |
| `direction_x`, `direction_y`, `direction_z` | finite unit vector, or null with a failure reason |
| `cov_xx`, `cov_xy`, `cov_xz`, `cov_yy`, `cov_yz`, `cov_zz` | symmetric direction-covariance components in a fixed order |
| `chi2_ndf`, `n_residual_degrees_of_freedom` | goodness-of-fit scalars used by plan 40 closure |
| `n_direction_hits`, `direction_method` | hit count and method label consumed by ladder rows |
| `fit_quality_state`, `fit_failure_reason` | §4 quality contract in machine-readable form |
| `covariance_valid`, `fit_degraded` | explicit downstream guardrails for weighted vertexing |

The residual sidecar is keyed by `(event_id, candidate_id, fit_id)` and
stores one residual row per contributing hit. Production rows must be
bitwise unchanged when validation-only truth direction fields are
removed from the evaluator input; only `pulls_theta_phi` and closure
artifact rows may change.

### 1.4 Physics derivation

- **What is physically measured:** V.2 measures the reconstructed unit
  direction and covariance of a charged-particle track segment. The truth-side
  quantity is the generated momentum direction, used only after the production
  fit row is frozen.
- **Estimator rationale:** in the no-curvature baseline, the straight-line
  total-least-squares/PCA axis is the near-optimal estimator for independent
  coordinate errors; a Kalman filter becomes the natural extension when
  process noise, material scattering, or magnetic curvature is introduced.
  PDG passage-of-particles material establishes multiple-scattering and
  tracking-error terms, ALICE documents TPC track-fitting practice, and Kalman
  gives the covariance-recursive formulation
  \cite{ParticleDataGroup:2024RPP,alice2014performance,Kalman:1960new}.
- **Statistical character:** the central-value bias comes from sparse
  first/last-hit fallbacks, unmodelled multiple scattering, and V.1 merge/split
  errors. The variance budget is hit-count and lever-arm dominated until plan
  17 supplies per-hit drift uncertainties. Robustness requires explicit
  `fit_degraded` and `covariance_valid` fields so V.4 can down-weight rather
  than silently trust under-constrained fits.
- **Citation:** the three keys above were checked against
  `/Users/billy/Desktop/projects/overleaf-hibeam-thesis/ref.bib` on
  2026-05-10.

### 1.5 Logic gaps

1. **Minimum finite coordinates = 2:** two points define a direction but leave
   zero residual degrees of freedom; production rows with exactly two hits are
   allowed only as `fit_degraded=true`.
2. **Covariance minimum hit count = 3:** `_covariance` currently returns zeros
   below three hits. OPEN: replace zero-vector covariance with
   `covariance_valid=false` plus a failure reason; target resolution date
   2026-05-24.
3. **Per-hit coordinate uncertainty:** OPEN: derive σx, σy, σz from plan-17
   drift/gain calibration and `cal_singlepion_50to600MeV_v2` residuals; figure
   of merit is pull width closure by hit-count bin; target resolution date
   2026-05-24.
4. **Multiple-scattering/process-noise term:** OPEN: use plan-16 material maps
   and PDG scattering formulae to set the Kalman process covariance before any
   Kalman replacement is promoted; target resolution date 2026-05-31.
5. **Pull tolerance `|mu| < 0.05`, width `[0.9, 1.1]`:** keep the current plan
   40 gate until a signed plan-05 decision changes the closure tolerance.

### 1.6 Closure test for the derivation

1. Run `fit_track_candidates` on V.1 candidates from
   `cal_singlepion_50to600MeV_v2`, using only Class-A TPC hit coordinates.
2. Persist the fit row and residual sidecar, then drop all Class-B truth
   direction/species columns and assert the production fit row is unchanged.
3. Join truth momentum only inside a `validation_only` pull scorer; compute
   `pull_theta` and `pull_phi` in bins of `n_direction_hits`, lever arm, and
   `fit_degraded` state.
4. The derivation passes when non-degraded rows close to mean zero and width
   one under the plan-40 tolerance, while two-hit/degraded rows are excluded or
   down-weighted explicitly rather than contaminating the nominal pull width.

## 2. Current implementation and alternatives

- *Legacy current.* `_track_anchor_and_direction` (plan 08 §3.2;
  `nnbar_reconstruction/charged.py:62-81`): direction is `(last_hit - first_hit) / |…|`;
  no covariance.
- *Live Stage E.1 hook.* `fit_track_candidates` (`nnbar_reconstruction/track_fit.py:55-117`)
  consumes plan-25 V.1 `hit_indices`, fetches Class A TPC coordinates,
  runs `_fit_line` (`nnbar_reconstruction/track_fit.py:32-43`), writes
  `direction_method=linear_pca`, residual vectors, χ²/ndf, and a
  covariance vector from `_covariance` (`nnbar_reconstruction/track_fit.py:46-52`). This
  unblocks V.3/V.4 and C.2 consumers, but it still needs the full §1.3
  quality fields (`fit_id`, failure reason, covariance validity,
  degraded flag) before final closure sign-off.
- *Kalman fit.* Seeded by V.1; produces direction + covariance +
  residuals. Standard ACTS implementation. Provides χ²/ndf.
- *Linear least-squares (PCA).* Cheaper than Kalman; gives
  covariance from the eigen-decomposition. Acceptable for straight
  tracks.

### 2.1 Alternative comparison rows

| Alternative | Source paper / codebase | NNBAR-specific adaptation | Expected ladder leaf delta |
|---|---|---|---|
| Current first-last direction | Existing `_track_anchor_and_direction` (`nnbar_reconstruction/charged.py:62-81`) | Preserve as reproducibility baseline and degraded fallback when too few hits exist for a covariance fit. | No V.2 improvement; documents current truth-free but covariance-free baseline. |
| Linear least-squares / PCA | Standard straight-line total least squares | Fit straight tracks in `(x, y, z)` because plan 17 has no B-field curvature; derive covariance from residuals. | Expected to improve plan 38 IV(V.2) pull width and enable V.4 weighted vertexing with low implementation cost. |
| Kalman fit | ACTS Kalman track-fitting codebase | Seed from V.1/PCA state and run straight-track process model until magnetic-field scenarios exist. | Best covariance model for plan 38 IV(V.2); likely similar central value to PCA in no-B-field data, but cleaner covariance propagation to V.4. |

The rebuild's recommended path: Linear LS → Kalman when momentum
measurement (curvature in B-field) becomes relevant. Currently no
B-field, so Linear LS suffices.

## 3. Closure-test specification (per plan 40 §2)

1. **Dataset id:** `cal_singlepion_50to600MeV_v2` from plan 03,
   using fiducial tracks with a V.1 candidate and validation truth
   direction available.
2. **Observable:** per-coordinate pull distributions,
   `pull_theta = (theta_fit - theta_true) / sigma_theta_fit` and
   `pull_phi = (phi_fit - phi_true) / sigma_phi_fit`.
3. **Fitter / matcher:** run the V.2 fitter under test (current,
   PCA, or Kalman); match to truth only inside a `@validation_only`
   closure function after the reconstruction output is frozen.
4. **Pass criterion:** `|mu| < 0.05` and width in `[0.9, 1.1]` for
   both pull coordinates, with covariance fields present for every
   non-degraded fitted candidate and a plan 38 IV(V.2) row recorded
   for the fitted direction choice.

## 4. Covariance and quality handoff

The V.2 output must make degraded fits explicit so downstream plans can
choose whether to consume a direction. The production table adds these
quality fields beside the physics fields in §1:

| Field | Meaning | Consumer |
|---|---|---|
| `fit_quality_state` | `pass`, `warn`, `fail`, or `not_applicable` for the candidate | plans 30, 66 |
| `fit_failure_reason` | first blocking reason, if any | plan 47 caveats |
| `covariance_valid` | covariance matrix finite, symmetric, and positive semidefinite | plans 30, 40 |
| `fit_degraded` | true when first-last direction is used because the fitter lacks enough hits | plan 38 ladder rows |
| `n_residual_degrees_of_freedom` | residual degrees of freedom used for χ²/ndf | plan 40 pulls |

Quality semantics:

- `pass` means the direction is finite, covariance is valid, and the
  residual degrees of freedom are sufficient for the configured fitter.
- `warn` means the direction is finite but covariance is missing,
  degraded, or close to singular; plan 30 may consume it with reduced
  weight.
- `fail` means the direction is non-finite or based on fewer than two
  usable Class A coordinates.
- `not_applicable` is reserved for candidates rejected by V.1 before a
  V.2 fit is attempted.

The DQM hook in plan 66 aggregates the fraction of `warn` and `fail`
rows per run. A sudden increase is a run-quality problem, not a reason
to silently retune vertex or PID thresholds.

## 5. Stage E.1 implementation handoff

For L3's reconstruction redesign, V.2 is now a standalone module seam
with explicit remaining gates:

1. Accept V.1 candidate hit indices and fetch only Class A TPC columns.
2. The live baseline runs PCA/linear LS and labels rows with
   `direction_method=linear_pca`; Kalman remains a later replacement once
   its covariance model is source-backed.
3. Emit the §1 direction and covariance schema plus the §4 quality
   fields in one row per V.1 candidate. The current hook partially
   satisfies this; L3 still must add `fit_id`, `fit_failure_reason`,
   `covariance_valid`, `fit_degraded`, and
   `n_residual_degrees_of_freedom` before plan 40 closure can treat the
   table as complete.
4. Retain `_track_anchor_and_direction` only as a named degraded
   baseline, never as an unlabeled production-equivalent result.
5. Freeze the V.2 table before any truth direction, pull, or ladder
   scorer reads it.
6. Plan 66 consumes `fit_quality_state`, covariance validity, degraded
   fraction, and hit count as run-quality fields once those columns are
   present.

### 5.1 L3 target module, functions, and tests

- **Target module:** extend `nnbar_reconstruction/track_fit.py`.
- **Public function:** `fit_track_candidates(candidates, tpc)`
  (`nnbar_reconstruction/track_fit.py:55-117`).
- **Current unit coverage:** `tests/test_charged_reco.py` already
  asserts the V.2 direction schema, finite PCA direction, covariance
  vector, residual rows, and `direction_method=linear_pca` in
  `test_fit_track_candidates_emits_plan_26_direction_schema`
  (`tests/test_charged_reco.py:120-151`).
- **Current integration coverage:** the real-output chain from plan-25
  candidates into the V.2 fitter is
  `test_fit_track_candidates_real_sample_consumes_candidate_rows`
  (`tests/test_charged_reco.py:153-165`).
- **Remaining test obligation:** extend the same test file with an
  explicit one-hit / missing-coordinate failure-state case once L3 adds
  `fit_id`, `fit_failure_reason`, `covariance_valid`, `fit_degraded`,
  and `n_residual_degrees_of_freedom`.

### 5.2 Stage E.1 code-gap checklist

The live L3 hook is intentionally close to, but not yet identical to,
the §1.3 fixture. L3 can promote V.2 only after the following concrete
gaps close in `fit_track_candidates` (`nnbar_reconstruction/track_fit.py:55-117`):

| Gap | Current live behavior | Required promotion behavior |
|---|---|---|
| fitter identity | `direction_method=linear_pca` is emitted, but no stable `fit_id` column is present | add a versioned `fit_id` (for example `linear_pca_v1`) so plan 38 and plan 40 can key rows across reruns |
| covariance shape | `_covariance` (`nnbar_reconstruction/track_fit.py:46-52`) is stored as `direction_covariance` vector | either expand to the six `cov_*` fields in §1.3 or document a deterministic vector order consumed by plans 30 and 40 |
| failure reason | `fit_quality_state` is present, but one-hit / bad-coordinate rows do not carry a machine-readable reason | add `fit_failure_reason` with values such as `insufficient_class_a_hits` or `nonfinite_class_a_coordinates` |
| covariance gate | covariance validity is implicit in downstream interpretation | add `covariance_valid` so plan 30 can down-weight or reject singular fits without re-deriving the check |
| degraded baseline | first-last direction remains available as `_track_anchor_and_direction` (`nnbar_reconstruction/charged.py:62-81`) | expose degraded use as `fit_degraded=true` rather than silently mixing it with PCA rows |
| residual degrees of freedom | `chi2_ndf` and `residuals_xyz` are emitted | add `n_residual_degrees_of_freedom` so plan 40 pull-width tests can reject under-constrained fits |

Acceptance of this checklist is a plan-side gate, not a request for L0
to edit L3 code. The matching L3 patch must update
`test_fit_track_candidates_emits_plan_26_direction_schema`
(`tests/test_charged_reco.py:120-151`) and
`test_fit_track_candidates_real_sample_consumes_candidate_rows`
(`tests/test_charged_reco.py:153-165`) so every required column is
asserted in both synthetic and real-output chains.

### 5.3 Stage E.1 promotion invariants

The current live hook is good enough as a degraded linear-PCA bridge,
but L3 may not promote a replacement fitter unless these invariants
stay true across synthetic and real-output tests:

| Invariant | Current live behavior | Replacement requirement |
|---|---|---|
| truth blindness | `fit_track_candidates` (`nnbar_reconstruction/track_fit.py:55-117`) consumes V.1 hit indices and Class A `x/y/z` coordinates; it does not need truth momentum or `Track_ID` | replacement output must be unchanged when Class B direction, species, parentage, and legacy track-id columns are dropped |
| stable fitter identity | `direction_method=linear_pca` is the only current method label | promoted rows must add a versioned `fit_id` while keeping `direction_method` as the human-readable algorithm family |
| covariance semantics | `_covariance` (`nnbar_reconstruction/track_fit.py:46-52`) currently writes a flattened coordinate covariance vector | replacement must either emit the six §1.3 covariance components or publish a deterministic vector order plus `covariance_valid` |
| degraded-row visibility | `_track_anchor_and_direction` (`nnbar_reconstruction/charged.py:62-81`) remains only a legacy first-last fallback | any fallback use must set `fit_degraded=true` and cannot be mixed silently with PCA or Kalman rows |
| residual accounting | current rows include `residuals_xyz`, `chi2_ndf`, and `n_direction_hits` | promoted rows must carry a residual sidecar and `n_residual_degrees_of_freedom` so plan 40 can reject under-constrained fits |
| failure-state stability | the live hook only exposes `fit_quality_state=pass/fail` | replacements must add `fit_failure_reason` and keep `pass`/`warn`/`fail`/`not_applicable` meanings consistent with §4 and plan 66 |

These invariants are the promotion gate for V.2, not a request for L0
to edit L3 code. Any Kalman or ACTS-backed replacement must extend the
plan-26 tests named in §5.1/§5.2 so the same assertions run before plan
38 ladder scoring or plan 40 pull closure consumes the table.

### 5.4 Stage E.1 producer/consumer contract

The L3 V.2 patch must make the table boundary explicit enough that C.2,
C.3, V.4, and plan 40 can consume it without re-opening TPC rows:

| Contract item | Required behavior | Downstream check |
|---|---|---|
| input key | consume exactly one V.1 row keyed by `(event_id, candidate_id, hit_membership_key)` | plan 25 hit sidecar and V.2 rows have matching event/candidate multiplicity |
| output key | emit one V.2 row keyed by `(event_id, candidate_id, fit_id)` for every attempted V.1 row | missing or failed fits are represented as rows with `fit_quality_state=fail`, not silent row drops |
| residual sidecar | write residual rows keyed by `(event_id, candidate_id, fit_id, hit_index)` | plan 40 pull closure can count residual degrees of freedom without parsing `residuals_xyz` blobs |
| source hashes | record V.1 table hash and TPC input hash in the V.2 manifest | plan 47 can prove the same V.1 candidate set fed C.2/C.3/V.4 artifacts |
| covariance handoff | publish either six covariance components or a documented vector order plus `covariance_valid` | plan 30 vertex weighting and plan 40 pull tests reject singular covariance deterministically |
| failure taxonomy | use `fit_failure_reason` values from §4 for non-finite, under-constrained, or degraded rows | plan 66 DQM aggregates failure fractions without inferring causes from null coordinates |

This contract keeps `fit_track_candidates`
(`nnbar_reconstruction/track_fit.py:55-117`) as the only Stage E.1 V.2
producer until L3 replaces the implementation behind the same keys.

### 5.5 Stage E.1 verification command

L3's V.2 patch is promotable only when the fitter slice exercises both
the synthetic schema path and the real-output C.1→V.2 chain:

```bash
pytest tests/test_charged_reco.py::test_fit_track_candidates_emits_plan_26_direction_schema \
       tests/test_charged_reco.py::test_fit_track_candidates_real_sample_consumes_candidate_rows
```

The review note for that patch must quote the command output and the
V.2 artifact manifest fields `fit_id`, `direction_method`,
`covariance_valid`, `fit_degraded`, `fit_quality_state`, and
`fit_failure_reason`. A replacement fitter that passes only synthetic
rows cannot feed plan 30 or plan 40; the real-output selector must run
against the paired V.1 candidate fixture before promotion.

### 5.6 Stage E.1 artifact manifest schema

The V.2 producer must write a manifest that freezes fitter identity,
source hashes, and covariance conventions before any downstream vertex,
range, dE/dx, or pull artifact consumes the fit rows:

```yaml
schema_version: plan26_v2_fits@stage-e1
dataset_id: <plan-03 dataset id>
producer: fit_track_candidates
fit_id: <stable fitter version>
direction_method: linear_pca | kalman | degraded_first_last
input_v1_hash: <sha256 of V.1 candidate table>
input_tpc_hash: <sha256 of TPC input table>
output_fit_hash: <sha256 of V.2 fit table>
residual_sidecar_hash: <sha256 of residual sidecar>
covariance_representation: six_components | row_major_3x3_vector
covariance_valid_values: [true, false]
fit_degraded_values: [true, false]
quality_states_allowed: [pass, warn, fail, not_applicable]
failure_reasons_allowed: [none, insufficient_class_a_hits, nonfinite_class_a_coordinates, singular_covariance, degraded_fallback]
```

The manifest is invalid if V.2 rows are silently dropped relative to the
V.1 input key set or if covariance order is omitted. Plans 27, 28, 30,
40, and 66 consume this manifest before trusting direction covariance or
fit-quality fractions.

### 5.7 Stage E.1 fixture matrix

The V.2 replacement patch must prove that the fitter boundary is stable
before dE/dx, range, vertex, or pull studies consume the fit manifest:

| Fixture case | Required input condition | Required assertion |
|---|---|---|
| truth-column drop | V.1 candidate rows and TPC hits are run with and without Class B labels or truth momentum columns | `direction_method`, direction vector, covariance payload, and quality state are unchanged |
| one-hit candidate | a V.1 row references only one finite TPC hit | a V.2 row is still emitted with `fit_quality_state=fail`, `fit_failure_reason=insufficient_class_a_hits`, and no silent key drop |
| nonfinite coordinate | one candidate references a hit with nonfinite `x`, `y`, or `z` | the row is rejected or degraded with a machine-readable failure reason and the residual sidecar excludes invalid hits |
| V.1 multiplicity | two candidates in the same event share no hit indices | V.2 output preserves `(event_id, candidate_id, hit_membership_key)` multiplicity and emits a unique `fit_id` per candidate |
| covariance convention | the same candidate is written through six-component and vector covariance representations during migration review | manifest records the chosen order, `covariance_valid`, and downstream consumers do not infer order from column names alone |
| real C.1 to V.2 chain | real paired output fixture is reconstructed through plan 25 candidate rows first | V.2 consumes the frozen V.1 keys and does not re-cluster or reopen raw TPC rows to repair fit inputs |

The review artifact for any fitter replacement must quote which rows in
this matrix are covered by synthetic tests and which are covered by the
real-output selector from §5.5. A matrix row may remain unpromoted only
if the manifest marks the corresponding quality state as unavailable to
plans 27, 28, 30, 40, and 66.

## 6. Acceptance criteria

- §3 closure passes on calibration sample.
- Direction covariance is reported into output schema.
- §5 Stage E.1 handoff is actionable for L3: the target public
  function, current unit/integration tests, remaining failure-state test
  obligation, promotion invariants, producer/consumer contract,
  verification command, artifact manifest schema, fixture matrix, and required V.2
  fields (`fit_id`, direction components,
  covariance components, `chi2_ndf`, `n_residual_degrees_of_freedom`,
  `direction_method`, residual sidecar rows, `fit_quality_state`,
  `fit_failure_reason`, `covariance_valid`, and `fit_degraded`) are all
  named before replacement promotion.

## 7. Dependencies

- **04, 25, 38, 40** — closure machinery, ladder scoring, and inputs.
- *Consumed by:* plans 27 (dE/dx normalised by track length), 30
  (vertex aggregation weighted by Σ), 38 (ladder).

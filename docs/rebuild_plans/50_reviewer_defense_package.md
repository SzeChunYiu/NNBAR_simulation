---
id: 50_reviewer_defense_package
title: Reviewer defence package — canonical answer set per result
version: 0.1
status: draft
owner: Reproducibility WG
depends_on: [00_README, 01_realism_contract, 03_dataset_registry, 38_truth_substitution_ladder, 45_systematics_taxonomy, 46_significance_protocol, 47_reproduction_ledger, 51_reviewer_question_registry, 52_run_orchestration, 53_ci_regression_suite, 54_open_data_archival, 55_internal_note_template, 56_glossary]
outputs:
  - {path: docs/rebuild_plans/50_reviewer_defense_package.md, schema: this file}
  - {path: output/defense/<row_id>.yml, schema: per-result defence package}
acceptance:
  - {test: every thesis-quoted result has a defence package, method: ledger row cross-reference, pass_when: full coverage}
  - {test: every package has the seven blocks in §1, method: per-package review, pass_when: complete}
risks:
  - {risk: package becomes a checkbox exercise, mitigation: §3 reviewer-question registry feeds back into §1 block list}
estimated_effort: M
last_updated: 2026-05-09
---

# Reviewer defence package

*Charter.* For every quoted result, a self-contained answer set that
addresses the foreseeable reviewer questions. The package is generated
automatically from the ledger row and the registries; reviewer
discovery of a new question (plan 51) loops back into expanding §1.

## 1. Package blocks

```yaml
result_id: LIC-CH10-NUM-1
quoted_value: 0.70 ± stat ± sys
defence:
  sample:
    id: sig_foil_v3
    hash: <sha>
    geant4_version: <ver>
    physics_list: nominal (FTFP_BERT, no _HP)
    digitiser: default_identity_v1
    build_id: build-prod-<rev>
  reproducing_command: |
    python -m nnbar_reconstruction.cli validate-reco \
        NNBAR_Detector/output/sig_foil_v3 --runs 0,1,... \
        --json output/defense/LIC-CH10-NUM-1/validate_reco.json
  reproducing_command_template_id: validate_reco_cutflow_v1
  ladder_sensitivity:
    primary_observable: visible_invariant_mass
    dominant_leaves: [P.4, V.4, P.3]   # IV(L) sorted
    matrix_path: output/ladder/sig_foil_v3/visible_invariant_mass.yml
  calibration_sensitivity:
    nuisances: [N1 (TPC W-value), N2 (Scint yield), N3 (LG calibration)]
    bracket: ± 0.04 (sum-in-quadrature)
  background_sensitivity:
    surviving_channels: []
    upper_limits:
      - sub_channel: cosmic_muon
        FC_90CL: < X.X × 10⁻⁵
  acceptance_footprint:
    fiducial_volume_definition: <reference plan 43>
    blind_spots: <enumerate from acceptance map>
  limitations_flags:
    - L1 (no position smearing)
    - L2 (no timing jitter)
    - L3 (no electronic noise)
    - L11 (no pile-up)
    # ... select from plan 01 §6 those that bear on this result
  decision_log_entries: [DEC-YYYY-MM-DD-N, ...]
  validation_metrics:
    pull_mean: 0.02
    pull_width: 1.05
    closure_chi2_dof: 1.1
  l1_review_evidence:
    overlay_rollup: <path or package key>
    defence_routing_crosswalk: <artifact-key-or-null>
    owner_signoff_refs: [RQ-L1-SELECTION-CUTFLOW:<owner-hash>]
    rerun_manifest: <path-or-null>
    rerun_transcript: <path-or-null>
    command_template_ids: [validate_reco_cutflow_v1]
    command_template_verifier_hashes:
      - sha256:b3cee4613afed558d4704df3dc5b281271aed768965d79a09603f812496806f0
    command_template_verifier_sources:
      - plan52:validate_reco_cutflow_v1
    ci_report: <path-or-null>
    archive_inventory: <path-or-null>
    archive_drill: <path-or-null>
    note_annex: <path-or-null>
    glossary_audit: <path-or-null>
    staleness_summary: <plan50-staleness-id-or-path>
    review_artifact_hashes:
      package: sha256:<hash-or-null>
      rerun_manifest: sha256:<hash-or-null>
      rerun_transcript: sha256:<hash-or-null>
      command_template_verifier: sha256:<hash-or-null>
      defence_routing_crosswalk: sha256:<hash-or-null>
      ci_report: sha256:<hash-or-null>
      note_annex: sha256:<hash-or-null>
      glossary_audit: sha256:<hash-or-null>
      staleness_summary: sha256:<hash-or-null>
      archive_inventory: sha256:<hash-or-null>
      archive_drill: sha256:<hash-or-null>
    staleness_status: current | stale | blocked
```

## 2. Mapping reviewer questions to blocks

Plan 51's reviewer-question registry feeds back into §1. Common
questions map:

- *"Did you use truth?"* → realism audit log; check `sample.digitiser`
  and the leaf-by-leaf `Class B` flag in the ladder matrix.
- *"Reproduce your old result"* → ledger row + `reproducing_command`.
- *"Where is your error budget?"* → `ladder_sensitivity` block.
- *"What if W-value is wrong?"* → `calibration_sensitivity` block.
- *"Is your π⁰ peak fit-bias-free?"* → `validation_metrics` block.
- *"Are your event-shape variables standard?"* → cite plan 48
  (Fox-Wolfram, Bjorken-Brodsky).
- *"What if the sample is unphysical?"* → `acceptance_footprint`
  + `limitations_flags`.


### 2.1 L1 EM/selection defence overlays

The L1 slice adds result-specific overlays for EM-object and selection
questions seeded in plan 51 §2.1. A package for any result that depends
on plans 31-37, 45, 58, 59, 61, or 64 must include the matching overlay
rows below in addition to the generic §1 blocks.

| Overlay id | Applies when result uses | Required package fields | Reviewer question answered |
|---|---|---|---|
| `em_cluster_truth_blindness` | P.1/P.2/P.3 photon or cluster rows | clusterer method id, Class-B drop hash, closure row ids, selected DEC ids | whether EM reconstruction used truth grouping |
| `pi0_cut_decomposition` | pi0 or Ch 8/Ch 10 selection rows | six pi0 cut booleans, final AND column, cut-config id, failure-reason schema | whether the pi0 acceptance can be audited cut-by-cut |
| `selection_cutflow_identity` | plan-37 S.1-S.6 rows | canonical `pass_*` column names, cumulative order, independent and cumulative counts | whether the cut-flow is reproducible from current tables |
| `pileup_l11_status` | any acceptance or background row with L11 open | plan-58 study id, overlay mode, paired cosmic rows, occupancy tails, limitation status | whether pile-up changes the quoted result |
| `strange_v0_contamination` | beam-neutron or EM fake background rows | plan-59 source node, PDG branching snapshot, V0 rejection closure, residual interval | whether K_S/Lambda/Sigma leakage is bounded |
| `tof_timing_resolution` | timing or cosmic-rejection rows | TOF method id, nonzero resolution budget, cal/cosmic closure rows, E.8 comparison | whether timing rejection survives detector resolution |
| `bayesian_prior_sensitivity` | low-count limit rows | Jeffreys and flat prior upper limits, ratios to plan-46 primary limit, sensitivity status | whether the limit is prior-sensitive |
| `unbounded_caveat_status` | any EM/selection claim affected by limitations that lack numeric nuisance bounds | limitation id, affected result ids, caveat text, owner, and condition for reopening | whether unbounded assumptions are visible rather than hidden as zero-width systematics |

The generator must fail closed if an overlay applies but the required
fields are absent. A package may mark an overlay `not_applicable` only
with a reason that references the result's plan-24 leaves or plan-44
background node.


### 2.2 Machine-readable L1 overlay fixture

Each L1 overlay in §2.1 is stored as a list entry under the defence
package key `l1_overlays`. The generator writes one entry per overlay
that applies to the result and one explicit `not_applicable` entry for
every overlay that does not apply. This keeps reviewer routing stable
when a result changes from an EM-object claim to a pure statistics claim
or vice versa.

```yaml
required_l1_overlay_ids: [em_cluster_truth_blindness, pi0_cut_decomposition,
  selection_cutflow_identity, pileup_l11_status, strange_v0_contamination,
  tof_timing_resolution, bayesian_prior_sensitivity, unbounded_caveat_status]
l1_overlays:
  - overlay_id: selection_cutflow_identity
    applicability: applies | not_applicable | blocked
    reason: <why this overlay applies or does not apply>
    source_plans: [37, 47]
    required_artifacts:
      - <path or ledger key>
    artifact_status: present | blocked | missing
    reviewer_question_ids: [RQ-L1-SELECTION-CUTFLOW]
    caveat_text: <one-sentence reviewer-facing caveat, or null>
    last_verified: YYYY-MM-DD
  - overlay_id: unbounded_caveat_status
    applicability: applies | not_applicable | blocked
    reason: <limitation id and affected EM/selection result>
    source_plans: [1, 45, 50, 55]
    required_artifacts:
      - plan45_caveat_or_numeric_bound_row
      - plan55_unbounded_caveat_note_row
    artifact_status: present | blocked | missing
    reviewer_question_ids: [RQ-L1-UNBOUNDED-CAVEATS]
    caveat_text: <reviewer-facing caveat required when artifact_status is blocked>
    last_verified: YYYY-MM-DD
```

Review rules:

| Rule | Failure caught |
|---|---|
| every package has exactly the `required_l1_overlay_ids` set | reviewer asks an L1 question with no routing row |
| `applicability = applies` requires at least one artifact key | prose claims that cannot be replayed |
| `artifact_status = blocked` requires `caveat_text` | hidden missing evidence |
| `not_applicable` requires a result-specific reason | blanket suppression of difficult checks |
| reviewer-question ids must exist in plan 51 | stale overlay/question mapping |

The fixture is intentionally independent of the eventual output format
(YAML, JSON, or parquet). Plan 53 audits the keys and required status
fields before any thesis-freeze package is accepted.


### 2.3 L1 overlay promotion status

A package exposes a compact L1 roll-up so a reviewer can see whether an
EM/selection result is ready for thesis quotation before reading every
artifact. The roll-up is derived from the §2.2 overlay entries and from
plans 51-56; it is not hand-edited prose.

```yaml
l1_overlay_rollup:
  result_id: LIC-CH10-NUM-1
  package_revision: <rev>
  overall_status: ready | blocked | caveated
  required_links:
    reviewer_questions: present | missing
    owner_signoff: present | missing
    rerun_manifest: present | blocked | missing
    rerun_transcript: present | blocked | missing
    command_template_registry: present | missing
    command_template_verifiers: present | missing
    defence_routing_crosswalk: present | missing
    ci_report: present | missing
    archive_inventory: present | missing
    archive_drill: present | missing
    note_annex: present | missing
    glossary_audit: present | missing
    staleness_summary: present | missing
    review_artifact_hashes: present | missing
  blocking_overlays:
    - overlay_id: pileup_l11_status
      blocker: no paired overlay closure yet
    - overlay_id: strange_v0_contamination
      blocker: no Lambda-enriched V0 closure yet
    - overlay_id: tof_timing_resolution
      blocker: no nonzero-resolution TOF closure yet
    - overlay_id: bayesian_prior_sensitivity
      blocker: no Bayesian prior-sensitivity table yet
    - overlay_id: unbounded_caveat_status
      blocker: no unbounded-limitation caveat closure yet
```

Promotion rules:

| Rule | Failure caught |
|---|---|
| `overall_status: ready` requires no blocked overlays | thesis quote proceeds despite missing L1 evidence |
| every blocking overlay appears in plan 51 | package blocker has no reviewer-question owner |
| owner sign-off agrees with plan 51 answered rows | defence package closes a reviewer question without accountable approval |
| rerun manifest status agrees with plan 52 | package says reproducible when the rerun bundle is blocked |
| rerun transcript status agrees with plan 52 | package says refreshed artifacts exist without execution evidence |
| command template registry agrees with plan 52 | package transcript uses unsupported or mutable command semantics |
| command template verifier hashes and sources agree with plan 52 | package trusts refreshed artifacts without A+ command-surface proof |
| defence routing crosswalk covers every required overlay | package has an overlay with no rerun, archive, or note route |
| CI report status agrees with plan 53 | stale package skips the A+ citation gate |
| note annex and glossary audit links are present for quoted notes | thesis prose diverges from package evidence |
| review-artifact hashes agree with the plan-54 inventory | package links cannot be proven to match archived review artifacts |

The roll-up lets the package stay fail-closed: a missing artifact becomes
`blocked` or `missing`, never an omitted row. The rerun manifest records
what should be refreshed; the rerun transcript records what actually ran,
and both must agree before `overall_status: ready` is allowed.


### 2.4 L1 package staleness invalidation

A defence package can become stale even when all required links still
exist. L1 packages therefore carry an invalidation summary generated from
hashes and plan revisions before any `ready` roll-up is accepted.

```yaml
l1_staleness:
  package_revision: <rev>
  checked_against:
    plan50_overlay_schema: <hash>
    plan51_question_registry: <hash>
    plan52_rerun_manifest: <hash>
    plan52_rerun_transcript: <hash>
    plan52_command_templates: <hash>
    plan52_command_template_verifiers:
      - sha256:b3cee4613afed558d4704df3dc5b281271aed768965d79a09603f812496806f0
    defence_routing_crosswalk: <hash>
    plan53_ci_report: <hash>
    plan54_archive_inventory: <hash>
    plan54_archive_drill: <hash-or-null>
    review_artifact_hashes: <hash>
    plan55_note_annex: <hash>
    plan56_glossary_audit: <hash>
  status: current | stale | blocked
  stale_reasons: []
```

Invalidation rules:

| Changed input | Required package action |
|---|---|
| plan-51 question text, route, or status | regenerate affected overlay roll-up and reopen answered rows if artifact hashes changed |
| plan-52 manifest, transcript, command-template, or verifier hash | mark refreshed-artifact overlays stale until output hashes and command semantics are rechecked |
| defence-routing crosswalk hash | rerun overlay-to-rerun/archive/note parity before package promotion |
| plan-53 L1 CI report hash | rerun package audit before thesis-freeze promotion |
| plan-54 inventory or drill hash | mark archive-facing package status stale until DOI evidence is reconciled |
| review-artifact hash bundle | mark package stale until package, CI, note, and glossary hashes are reconciled |
| plan-55 annex row | compare note-facing caveat text with package caveat text |
| plan-56 term sign-off | recheck every overlay that uses the changed term |

`overall_status: ready` is allowed only when `l1_staleness.status` is
`current`. A stale package is still archived for provenance, but it cannot
be used as thesis evidence until regenerated.

### 2.5 L1 defence-routing crosswalk

The defence-routing crosswalk is the package-local copy of the route that
plan 53 audits across plans 50, 52, 54, 55, and 56. It is regenerated with
the package so an examiner can start from one overlay id and find the
question owner, rerun bundle, archive member, note annex, and glossary term
without searching every plan by hand.

```yaml
l1_defence_routing_crosswalk:
  crosswalk_id: l1_defence_routing_crosswalk
  source_hashes:
    plan50_overlay_schema: <hash>
    plan51_question_registry: <hash>
    plan52_rerun_manifest: <hash>
    plan53_ci_rule: <hash>
    plan54_archive_inventory: <hash>
    plan55_note_annex: <hash>
    plan56_glossary_audit: <hash>
  routes:
    em_cluster_truth_blindness: {question_ids: [RQ-L1-EM-P1-CLUSTERING, RQ-L1-EM-P2-DISCRIMINANT], rerun_bundle_member_id: em_object_chain, archive_pack_member_id: em_object_chain, note_annex_block: em_object_chain, glossary_terms: [defence overlay, rerun transcript, L1 archive pack member, defence routing]}
    pi0_cut_decomposition: {question_ids: [RQ-L1-PI0-CUTS], rerun_bundle_member_id: em_object_chain, archive_pack_member_id: em_object_chain, note_annex_block: em_object_chain, glossary_terms: [defence overlay, rerun transcript, L1 archive pack member, defence routing]}
    selection_cutflow_identity: {question_ids: [RQ-L1-SELECTION-CUTFLOW], rerun_bundle_member_id: ch10_cutflow, archive_pack_member_id: ch10_cutflow, note_annex_block: event_variable_and_cutflow_identity, glossary_terms: [pass_* columns, L1 archive pack member, defence routing]}
    pileup_l11_status: {question_ids: [RQ-L1-PILEUP-L11], rerun_bundle_member_id: pileup_l11, archive_pack_member_id: pileup_l11, note_annex_block: pile_up_caveat, glossary_terms: [blocked template, defence routing]}
    strange_v0_contamination: {question_ids: [RQ-L1-STRANGE-BARYON], rerun_bundle_member_id: strange_v0, archive_pack_member_id: strange_v0, note_annex_block: strange_background_caveat, glossary_terms: [blocked template, defence routing]}
    tof_timing_resolution: {question_ids: [RQ-L1-TOF], rerun_bundle_member_id: tof_timing, archive_pack_member_id: tof_timing, note_annex_block: timing_tof_cross_check, glossary_terms: [blocked template, defence routing]}
    bayesian_prior_sensitivity: {question_ids: [RQ-L1-BAYES-LIMIT], rerun_bundle_member_id: bayesian_limits, archive_pack_member_id: bayesian_limits, note_annex_block: limit_convention_cross_check, glossary_terms: [blocked template, defence routing]}
    unbounded_caveat_status: {question_ids: [RQ-L1-UNBOUNDED-CAVEATS], rerun_bundle_member_id: unbounded_caveats, archive_pack_member_id: unbounded_caveats, note_annex_block: unbounded_caveat_status, glossary_terms: [unbounded caveat status, defence routing]}
  status: current | stale | blocked
```

Crosswalk review rules:

| Rule | Failure caught |
|---|---|
| every `required_l1_overlay_ids` entry appears exactly once in `routes` | overlay added to package but not to rerun/archive/note surfaces |
| every `question_ids` entry exists in plan 51 and maps back to the same overlay | reviewer owner points at the wrong defence row |
| bundle, archive, and note ids match plans 52, 54, and 55 | package route cannot be reproduced or archived |
| every route names at least one plan-56 glossary term | thesis prose can introduce an unsigned synonym |
| `status: current` requires the source hashes to match §2.4 staleness input | examiner receives a stale crosswalk as promotion evidence |

## 3. Generation

A defence package is generated automatically by codex-supervisor
when:

1. A ledger row reaches green status in plan 47.
2. A new reviewer question is added to plan 51 that affects an
   existing row.

The generator joins ledger rows × dataset manifests × ladder matrices
× nuisance registry × decision log to produce the YAML.

## 4. Acceptance criteria

- §1 schema instantiated; first three defence packages produced
  for the licentiate Ch 10 cuts.
- §2 mapping covered for every entry in plan 51 v0.1.
- L1 packages include the §2.3 overlay roll-up before any affected
  result is promoted to thesis-quote status.
- Ready L1 packages include plan-52 rerun manifest, transcript,
  command-template registry, and verifier links when refreshed artifacts
  are claimed.
- Ready L1 packages carry a current §2.4 staleness summary.
- Ready L1 packages expose the defence-routing crosswalk used by plan 53
  to prove overlay, rerun, archive, and note parity.
- The package schema exposes `l1_review_evidence` links for overlays, owner
  sign-off, rerun artifacts, command templates, verifier hashes/sources, CI reports,
  note annexes, glossary audits, staleness summaries, review-artifact hashes,
  and staleness status.
- §3 generation automated.

## 5. Dependencies

- **01, 03, 38, 45, 46, 47, 51** — inputs.
- *Consumed by:* plan 51 (loop back), thesis chapter writing.

## 6. References

- HIBEAM PhD reproducibility appendix — defence-package precedent.

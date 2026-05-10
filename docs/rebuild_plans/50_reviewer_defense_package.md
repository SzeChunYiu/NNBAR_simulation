---
id: 50_reviewer_defense_package
title: Reviewer defence package — canonical answer set per result
version: 0.1
status: draft
owner: Reproducibility WG
depends_on: [00_README, 01_realism_contract, 03_dataset_registry, 38_truth_substitution_ladder, 45_systematics_taxonomy, 46_significance_protocol, 47_reproduction_ledger]
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
        NNBAR_Detector/output/sig_foil_v3 --runs 0,1,...
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
    owner_signoff_refs: [RQ-L1-SELECTION-CUTFLOW:<owner-hash>]
    rerun_manifest: <path-or-null>
    rerun_transcript: <path-or-null>
    command_template_ids: [validate_reco_cutflow_v1]
    command_template_verifier_hashes: [sha256:<hash>]
    ci_report: <path-or-null>
    note_annex: <path-or-null>
    glossary_audit: <path-or-null>
    staleness_summary: <plan50-staleness-id-or-path>
    review_artifact_hashes:
      ci_report: sha256:<hash-or-null>
      note_annex: sha256:<hash-or-null>
      glossary_audit: sha256:<hash-or-null>
      staleness_summary: sha256:<hash-or-null>
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
on plans 31-37, 58, 59, 61, or 64 must include the matching overlay
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
```

Review rules:

| Rule | Failure caught |
|---|---|
| every package has all seven §2.1 overlay ids | reviewer asks an L1 question with no routing row |
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
    ci_report: present | missing
    note_annex: present | missing
    glossary_audit: present | missing
    staleness_summary: present | missing
    review_artifact_hashes: present | missing
  blocking_overlays:
    - overlay_id: pileup_l11_status
      blocker: no paired overlay closure yet
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
| command template verifier hashes agree with plan 52 | package trusts refreshed artifacts without A+ command-surface proof |
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
    plan52_command_template_verifiers: <hash>
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
| plan-53 L1 CI report hash | rerun package audit before thesis-freeze promotion |
| plan-54 inventory or drill hash | mark archive-facing package status stale until DOI evidence is reconciled |
| review-artifact hash bundle | mark package stale until package, CI, note, and glossary hashes are reconciled |
| plan-55 annex row | compare note-facing caveat text with package caveat text |
| plan-56 term sign-off | recheck every overlay that uses the changed term |

`overall_status: ready` is allowed only when `l1_staleness.status` is
`current`. A stale package is still archived for provenance, but it cannot
be used as thesis evidence until regenerated.

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
- The package schema exposes `l1_review_evidence` links for overlays, owner
  sign-off, rerun artifacts, command templates, verifier hashes, CI reports,
  note annexes, glossary audits, staleness summaries, review-artifact hashes,
  and staleness status.
- §3 generation automated.

## 5. Dependencies

- **01, 03, 38, 45, 46, 47, 51** — inputs.
- *Consumed by:* plan 51 (loop back), thesis chapter writing.

## 6. References

- HIBEAM PhD reproducibility appendix — defence-package precedent.

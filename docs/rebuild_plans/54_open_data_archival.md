---
id: 54_open_data_archival
title: Open-data archival — Zenodo, DOI, RECAST-style preservation
version: 0.1
status: draft
owner: Reproducibility WG
depends_on: [00_README, 03_dataset_registry, 11_build_and_runtime_environment, 47_reproduction_ledger, 50_reviewer_defense_package, 51_reviewer_question_registry, 52_run_orchestration, 53_ci_regression_suite, 55_internal_note_template, 55_internal_note_template_l1_annex_fixture, 56_glossary]
outputs:
  - {path: docs/rebuild_plans/54_open_data_archival.md, schema: this file}
acceptance:
  - {test: thesis-freeze package contains samples + plots + ledger + code at a Zenodo DOI, method: DOI registration, pass_when: DOI minted}
  - {test: Docker / Singularity image reproduces a smoke run from scratch, method: container build, pass_when: smoke reproduces}
  - {test: per-sample retention policy (plan 03 §11) enforced, method: registry audit, pass_when: zero retain-violations}
risks:
  - {risk: Zenodo size cap (50 GB / record) exceeded by full samples, mitigation: §3 split by sample tier}
estimated_effort: M
last_updated: 2026-05-09
---

# Open-data archival

*Charter.* At thesis-freeze, the rebuild publishes a self-contained
artifact set under a Zenodo DOI and a reproducible container. The
purpose is not "code release"; it is "the thesis is reproducible by
a stranger in five years."

## 1. Archival package contents

For each thesis-freeze:

- *Code.* Snapshot of `NNBAR_Detector/` and `nnbar_reconstruction/`
  at the freeze rev.
- *Plans.* Snapshot of `docs/rebuild_plans/` (this directory).
- *Decision log.* Snapshot of `docs/governance/DECISION_LOG.md`.
- *Ledger.* Snapshot of `docs/thesis_reproduction_ledger.md`.
- *Defence packages.* `output/defense/*.yml`.
- *Samples.* Selected (not all — see §3 retention) frozen samples.
- *Container.* Docker / Singularity image with pinned Geant4,
  Python, Arrow, etc.
- *README.* Top-level "how to reproduce" pointing at the container
  and the ledger.

### 1.1 L1 EM/selection defence artifact pack

The thesis-freeze archive must preserve the L1 defence overlays as a
coherent artifact pack so a reviewer can rerun or inspect the EM and
selection claims without reconstructing the whole plan tree by hand.

| Pack member | Minimum archived artifact | Why it is retained |
|---|---|---|
| EM-object chain | plan-31 through plan-35 closure rows, method ids, and Class-B drop-hash summaries | proves photon/pi0 evidence is truth-blind and replayable |
| Ch 10 cut-flow | plan-37 independent `pass_*` counts and cumulative cut-flow rows | preserves the exact selection identity used by ledger rows |
| pile-up L11 | plan-58 overlay manifests, occupancy tables, and L11 status rows | shows whether independent-event assumptions are still caveated |
| strange V0 | plan-59 branching snapshot, V0 candidate summary, and residual intervals | preserves K_S/Lambda/Sigma contamination evidence |
| TOF timing | plan-61 TOF candidate summaries, resolution budgets, and ROC rows | preserves timing-separation evidence and caveats |
| Bayesian limits | plan-64 prior-sensitivity table and plan-46 comparison ratios | preserves low-count prior-sensitivity evidence |
| unbounded caveats | plan-45 caveat-only limitations, plan-50 `unbounded_caveat_status` overlays, and plan-55 note rows | prevents caveat-only assumptions from disappearing from the freeze record |
| defence routing | plan-50 overlays, plan-51 question seeds, plan-52 rerun manifests, transcripts, and command-template registry, plan-55 annex, plan-56 glossary terms | lets a future reader map artifacts to reviewer questions |

If a pack member is blocked at freeze, archive the blocked manifest row,
the missing input name, and the owning plan instead of dropping the row.
That rule keeps open caveats visible in the DOI record.

### 1.2 Machine-readable L1 archive inventory

The archival package includes an `l1_defence_inventory` manifest so the
Zenodo record can be audited without opening every defence package. The
manifest is generated at thesis-freeze from plan 50 packages, plan 52
rerun manifests, execution transcripts, command-template registry rows,
plan 53 L1 CI reports, plan 55 notes, and plan 56 glossary audits.

```yaml
l1_defence_inventory:
  freeze_id: thesis-freeze-<date>
  members:
    - pack_member: em_object_chain
      source_plans: [31, 32, 33, 34, 35, 50, 51, 52, 55]
      artifact_paths:
        - output/defense/<row_id>.yml
        - output/reconstruction/em_chain_closure/<bundle_id>.yml
      artifact_hashes:
        - sha256:<hash-or-null>
      status: present | blocked | stale
      caveat: <required until P.1-P.7 closure rows are present>
      staleness_summary_hash: sha256:<hash-or-null>
      defence_routing_crosswalk_hash: sha256:<hash-or-null>
      owner_signoff_refs: [RQ-L1-EM-P1-CLUSTERING:<owner-hash-or-null>]
      rerun_manifest_hash: sha256:<hash-or-null>
      rerun_transcript_hash: sha256:<hash-or-null>
      command_template_ids: [validate_reco_allruns_v1]
      command_template_verifier_hashes:
        - sha256:b3cee4613afed558d4704df3dc5b281271aed768965d79a09603f812496806f0
      command_template_verifier_sources:
        - plan52:validate_reco_allruns_v1
      ci_report_hash: sha256:<hash-or-null>
      note_annex_hash: sha256:<hash-or-null>
      glossary_audit_hash: sha256:<hash-or-null>
      archive_drill_hash: sha256:<hash-or-null>
    - pack_member: ch10_cutflow
      source_plans: [37, 47, 50, 51, 52, 55]
      artifact_paths:
        - output/defense/<row_id>.yml
      artifact_hashes:
        - sha256:<hash>
      status: present | blocked | retired | stale
      caveat: null
      staleness_summary_hash: sha256:<hash-or-null>
      defence_routing_crosswalk_hash: sha256:<hash-or-null>
      owner_signoff_refs: [RQ-L1-SELECTION-CUTFLOW:<owner-hash>]
      rerun_manifest_hash: sha256:<hash-or-null>
      rerun_transcript_hash: sha256:<hash-or-null>
      command_template_ids: [validate_reco_cutflow_v1]
      command_template_verifier_hashes:
        - sha256:b3cee4613afed558d4704df3dc5b281271aed768965d79a09603f812496806f0
      command_template_verifier_sources:
        - plan52:validate_reco_cutflow_v1
      ci_report_hash: sha256:<hash-or-null>
      note_annex_hash: sha256:<hash-or-null>
      glossary_audit_hash: sha256:<hash-or-null>
      archive_drill_hash: sha256:<hash-or-null>
    - pack_member: pileup_l11
      source_plans: [1, 44, 50, 51, 52, 55, 58]
      artifact_paths:
        - output/defense/<row_id>.yml
        - output/pileup/<study_id>/overlay_manifest.yml
      artifact_hashes:
        - sha256:<hash-or-null>
      status: present | blocked | stale
      caveat: <required until paired pile-up closure is present>
      staleness_summary_hash: sha256:<hash-or-null>
      defence_routing_crosswalk_hash: sha256:<hash-or-null>
      owner_signoff_refs: [RQ-L1-PILEUP-L11:<owner-hash-or-null>]
      rerun_manifest_hash: sha256:<hash-or-null>
      rerun_transcript_hash: sha256:<hash-or-null>
      command_template_ids: [blocked_missing_input_v1]
      command_template_verifier_hashes: []
      command_template_verifier_sources: []
      ci_report_hash: sha256:<hash-or-null>
      note_annex_hash: sha256:<hash-or-null>
      glossary_audit_hash: sha256:<hash-or-null>
      archive_drill_hash: sha256:<hash-or-null>
    - pack_member: strange_v0
      source_plans: [14, 22, 44, 50, 51, 52, 55, 59]
      artifact_paths:
        - output/defense/<row_id>.yml
        - output/strange_baryon/<study_id>/v0_candidates.parquet
      artifact_hashes:
        - sha256:<hash-or-null>
      status: present | blocked | stale
      caveat: <required until Lambda-enriched closure is present>
      staleness_summary_hash: sha256:<hash-or-null>
      defence_routing_crosswalk_hash: sha256:<hash-or-null>
      owner_signoff_refs: [RQ-L1-STRANGE-BARYON:<owner-hash-or-null>]
      rerun_manifest_hash: sha256:<hash-or-null>
      rerun_transcript_hash: sha256:<hash-or-null>
      command_template_ids: [blocked_missing_input_v1]
      command_template_verifier_hashes: []
      command_template_verifier_sources: []
      ci_report_hash: sha256:<hash-or-null>
      note_annex_hash: sha256:<hash-or-null>
      glossary_audit_hash: sha256:<hash-or-null>
      archive_drill_hash: sha256:<hash-or-null>
    - pack_member: tof_timing
      source_plans: [36, 41, 45, 50, 51, 52, 55, 61]
      artifact_paths:
        - output/defense/<row_id>.yml
        - output/tof/<study_id>/tof_closure.parquet
      artifact_hashes:
        - sha256:<hash-or-null>
      status: present | blocked | stale
      caveat: <required until cal and cosmic TOF closure rows are present>
      staleness_summary_hash: sha256:<hash-or-null>
      defence_routing_crosswalk_hash: sha256:<hash-or-null>
      owner_signoff_refs: [RQ-L1-TOF:<owner-hash-or-null>]
      rerun_manifest_hash: sha256:<hash-or-null>
      rerun_transcript_hash: sha256:<hash-or-null>
      command_template_ids: [blocked_missing_input_v1]
      command_template_verifier_hashes: []
      command_template_verifier_sources: []
      ci_report_hash: sha256:<hash-or-null>
      note_annex_hash: sha256:<hash-or-null>
      glossary_audit_hash: sha256:<hash-or-null>
      archive_drill_hash: sha256:<hash-or-null>
    - pack_member: bayesian_limits
      source_plans: [4, 46, 50, 51, 52, 55, 64]
      artifact_paths:
        - output/defense/<row_id>.yml
        - output/bayesian_limits/<result_id>/prior_sensitivity.yml
      artifact_hashes:
        - sha256:<hash-or-null>
      status: present | blocked | stale
      caveat: <required until Jeffreys and flat-prior comparison rows exist>
      staleness_summary_hash: sha256:<hash-or-null>
      defence_routing_crosswalk_hash: sha256:<hash-or-null>
      owner_signoff_refs: [RQ-L1-BAYES-LIMIT:<owner-hash-or-null>]
      rerun_manifest_hash: sha256:<hash-or-null>
      rerun_transcript_hash: sha256:<hash-or-null>
      command_template_ids: [blocked_missing_input_v1]
      command_template_verifier_hashes: []
      command_template_verifier_sources: []
      ci_report_hash: sha256:<hash-or-null>
      note_annex_hash: sha256:<hash-or-null>
      glossary_audit_hash: sha256:<hash-or-null>
      archive_drill_hash: sha256:<hash-or-null>
    - pack_member: unbounded_caveats
      source_plans: [1, 45, 50, 51, 52, 55, 56]
      artifact_paths:
        - output/defense/<row_id>.yml
        - docs/rebuild_plans/45_systematics_taxonomy.md
      artifact_hashes:
        - sha256:<hash-or-null>
      status: present | blocked | stale
      caveat: <required unless status is present>
      staleness_summary_hash: sha256:<hash-or-null>
      defence_routing_crosswalk_hash: sha256:<hash-or-null>
      owner_signoff_refs: [RQ-L1-UNBOUNDED-CAVEATS:<owner-hash-or-null>]
      rerun_manifest_hash: sha256:<hash-or-null>
      rerun_transcript_hash: sha256:<hash-or-null>
      command_template_ids: [blocked_missing_input_v1]
      command_template_verifier_hashes: []
      command_template_verifier_sources: []
      ci_report_hash: sha256:<hash-or-null>
      note_annex_hash: sha256:<hash-or-null>
      glossary_audit_hash: sha256:<hash-or-null>
      archive_drill_hash: sha256:<hash-or-null>
    - pack_member: defence_routing
      source_plans: [50, 51, 52, 53, 54, 55, 56]
      artifact_paths:
        - output/defense/<row_id>.yml
        - docs/rebuild_plans/50_reviewer_defense_package.md
        - docs/rebuild_plans/51_reviewer_question_registry.md
        - docs/rebuild_plans/52_run_orchestration.md
        - docs/rebuild_plans/53_ci_regression_suite.md
        - docs/rebuild_plans/55_internal_note_template.md
        - docs/rebuild_plans/55_internal_note_template_l1_annex_fixture.md
        - docs/rebuild_plans/56_glossary.md
      artifact_hashes:
        - sha256:<hash-or-null>
      status: present | blocked | stale
      caveat: <required if any linked routing artifact is stale or blocked>
      staleness_summary_hash: sha256:<hash-or-null>
      defence_routing_crosswalk_hash: sha256:<hash-or-null>
      owner_signoff_refs: [L1-routing-owner:<owner-hash-or-null>]
      rerun_manifest_hash: sha256:<hash-or-null>
      rerun_transcript_hash: sha256:<hash-or-null>
      command_template_ids: [validate_reco_cutflow_v1, validate_reco_allruns_v1, blocked_missing_input_v1]
      command_template_verifier_hashes:
        - sha256:b3cee4613afed558d4704df3dc5b281271aed768965d79a09603f812496806f0
      command_template_verifier_sources:
        - plan52:validate_reco_cutflow_v1
        - plan52:validate_reco_allruns_v1
      ci_report_hash: sha256:<hash-or-null>
      note_annex_hash: sha256:<hash-or-null>
      glossary_audit_hash: sha256:<hash-or-null>
      archive_drill_hash: sha256:<hash-or-null>
```

Inventory review rules:

| Rule | Failure caught |
|---|---|
| every §1.1 pack member appears exactly once | DOI omits a reviewer-critical evidence class |
| `present` rows have at least one hash | archived artifact cannot be integrity-checked |
| owner sign-off refs are archived for answered rows | future reader cannot identify who approved question closure |
| rerun manifest hashes are archived for every pack member | archived evidence cannot be tied to the plan-52 request bundle |
| rerun transcript hashes are archived or explicitly null for blocked rows | archived rerun evidence cannot distinguish planned from executed work |
| command-template ids are archived with rerun rows | future rerun cannot know which verified command contract applied |
| command-template verifier hashes are archived | future rerun cannot prove the command surface was verified |
| CI, note-annex, and glossary hashes are archived | package evidence cannot be traced to review, prose, and term-signoff artifacts |
| archive drill hash is archived with the inventory | future reader cannot prove the reviewer-style drill transcript matched the inventory |
| `stale` rows keep package, defence-routing crosswalk, and staleness hashes | future readers cannot tell why archived evidence was not quote-ready or which route was audited |
| `blocked` rows carry a caveat and owning plan | open limitations disappear at freeze |
| retired parquet rows keep manifests | retention policy removes replay provenance |
| inventory hash is listed in the top-level README | reviewer cannot discover the L1 defence pack |

This inventory is small enough to archive even when the underlying sample
parquet is retired under the plan-03 Tier C policy. A stale defence package is
archived for provenance, but the inventory status prevents it from being used
as current thesis evidence without the plan-50 staleness summary regenerating
to `current`.


### 1.3 L1 archive pull-and-reproduce drill

Before freeze, the L1 archive inventory is tested with a reviewer-style
pull-and-reproduce drill. The drill does not require full-statistics
regeneration; it proves that the archived package points to the exact
L1 defence evidence and that blocked rows remain visible.

```yaml
l1_archive_drill:
  freeze_id: thesis-freeze-<date>
  reviewer_role: external_examiner
  selected_member: ch10_cutflow
  drill_transcript_hash: sha256:<hash-or-null>
  expected_steps:
    - open_top_level_readme
    - locate_l1_defence_inventory
    - verify_inventory_hash
    - open_plan50_defence_package
    - follow_plan52_rerun_manifest
    - inspect_plan52_execution_transcript
    - inspect_plan52_command_template_verifier
    - verify_review_artifact_hashes
    - inspect_plan53_l1_ci_report
    - compare_plan55_note_annex
    - compare_plan55_split_annex_fixture
    - compare_plan56_glossary_audit
  result: pass | fail
  failure_reason: null
```

Drill review rules:

| Rule | Failure caught |
|---|---|
| drill starts from the top-level README | archive is only navigable by insiders |
| selected member changes across freezes | only the easiest L1 artifact is ever tested |
| blocked rows are included in the drill | archive hides open L1 caveats |
| inventory and package hashes are compared | DOI package and local freeze diverge |
| rerun transcript is inspected after the manifest | archive proves planned reruns but not executed reruns |
| command-template verifier is inspected after the transcript | archive preserves execution output but not the verified command contract |
| refreshed-artifact rows carry verifier hashes and sources | archive trusts a rerun command without A+ command-surface proof |
| review-artifact hashes are checked before the note annex | archive links package prose to stale CI, note, or glossary artifacts |
| CI report and glossary audit are opened explicitly | archive hash comparison passes but reviewer-facing evidence is unreadable |
| note annex is checked against package overlay | thesis prose cannot be traced to evidence |

The drill transcript is archived beside the inventory manifest and is
referenced by the plan-50 overlay roll-up when a quoted result depends on
L1 EM or selection evidence. If the selected member claims refreshed
artifacts, the drill fails unless the plan-52 execution transcript is
archived with matching output hashes, rerun-manifest hash, rerun-transcript
hash, command-template verifier hashes/sources, and review-artifact hashes
for the package, staleness summary, CI report, note annex, archive drill,
and glossary audit.

## 2. Reproducibility container

The container builds from a clean base, fetches pinned dependencies
(Geant4, Arrow, etc.), and runs a smoke sample to confirm the build
works. Recipe target: `containers/Dockerfile`; the file is created before
thesis-freeze.

The container is *not* expected to scale to full statistics on a
single machine; it demonstrates reproducibility, not throughput.
Full-statistics regeneration runs on LUNARC per plan 52.

## 3. Retention policy

Plan 03 §11 retention policy applies. At thesis-freeze:

- *Tier A.* Headline samples (`sig_foil_v3`, `cosmic_cry_*_v1`,
  `beam_neutron_*_v1`) — archived to Zenodo with full statistics.
- *Tier B.* Calibration samples — archived (smaller volume).
- *Tier C.* Study/scan samples (varied parameter scans) — manifests
  archived; underlying parquet may be retired per plan 03.

## 4. RECAST-style preservation

The defence packages (plan 50) plus the container plus the ledger
constitute a RECAST-style preserved analysis: a reviewer can
reproduce a numeric claim by:

1. Pulling the Zenodo DOI.
2. Running the container.
3. Following the `reproducing_command` in the relevant defence
   package.

## 5. Acceptance criteria

- §1 archival package present in `release/` directory at thesis-
  freeze.
- §2 container builds and runs smoke.
- §3 retention policy enforced; manifests retained for retired
  samples.
- §4 a sample reviewer pull-and-reproduce drill is executed once
  before final freeze.
- L1 archive drill in §1.3 passes for at least one EM/selection member
  and records any blocked rows, owner sign-off refs, review-artifact
  hashes, archive-drill hash, and verifier hashes for refreshed rows.

## 6. Dependencies

- **03, 11, 47** — inputs.
- *Consumed by:* thesis-freeze gate.

## 7. References

- Zenodo documentation.
- RECAST framework (Cranmer et al.).
- HEP analysis preservation guidelines (HSF).

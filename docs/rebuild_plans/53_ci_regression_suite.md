---
id: 53_ci_regression_suite
title: CI regression suite — automated tests on every change
version: 0.1
status: draft
owner: Software Quality
depends_on: [00_README, 01_realism_contract, 03_dataset_registry, 19_simulation_validation_suite, 47_reproduction_ledger, 50_reviewer_defense_package, 51_reviewer_question_registry, 52_run_orchestration, 54_open_data_archival, 55_internal_note_template, 56_glossary]
outputs:
  - {path: docs/rebuild_plans/53_ci_regression_suite.md, schema: this file}
  - {path: .github/workflows/ or .gitlab-ci.yml, schema: pipeline definition}
acceptance:
  - {test: realism audit runs on every PR, method: CI log, pass_when: green}
  - {test: registry integrity check runs on every PR touching data/registry, method: CI log, pass_when: green}
  - {test: simulation smoke test runs on every PR touching NNBAR_Detector/, method: CI log, pass_when: green}
  - {test: reconstruction smoke test runs on every PR touching nnbar_reconstruction/, method: CI log, pass_when: green}
  - {test: ledger refresh runs on every PR with code touching ledger-relevant modules, method: CI log, pass_when: green or yellow only}
risks:
  - {risk: CI runtime grows unmanageable, mitigation: §3 selective triggering by path}
estimated_effort: M
last_updated: 2026-05-09
---

# CI regression suite

*Charter.* Every PR runs a tiered set of automated checks. Plan 53
defines the tiers, the triggering rules, and the failure semantics.

## 1. Tiers

### Tier 1 — fast (every PR)

- Lint: pyright / ruff on `nnbar_reconstruction/`; clang-format on
  C++ headers.
- Realism audit (plan 01 §4).
- Registry integrity (plan 03 acceptance §10): hashes match for
  every frozen sample referenced by the PR.
- Reconstruction unit tests (`pytest NNBAR_Detector/tests/`).
- Plan-set audit: every plan file in `docs/rebuild_plans/` has a
  valid YAML header (plan 00 §7).

### Tier 2 — slow (PR + nightly)

- Simulation smoke build for every `WITH_*` permutation (plan 19
  §4).
- Simulation smoke run with 100 events on each build (plan 19 §3).
- Reconstruction smoke on the smoke sample.

### Tier 3 — release (manual + weekly)

- Full plan-47 ledger refresh: re-run reproducing commands for every
  green ledger row.
- Truth-substitution ladder rerun on signal sample (plan 38).
- Sanity plots (plan 19 §2) regenerated and visually compared.

## 2. Triggering

PR diff path determines the tier:

- `nnbar_reconstruction/**` → Tier 1 reconstruction tests.
- `NNBAR_Detector/{src,include,macro,CMakeLists.txt}/**` → Tier 1
  simulation smoke + Tier 2 nightly.
- `data/registry/**` → Tier 1 registry integrity.
- `docs/rebuild_plans/**` → Tier 1 plan-set audit.
- `docs/governance/**` → Tier 1 decision-log integrity.

## 3. Failure semantics

- *Tier 1 failure* blocks merge unconditionally.
- *Tier 2 failure* blocks merge for changes inside Tier 2 trigger
  paths; warns otherwise.
- *Tier 3 failure* opens a tracking issue; never blocks merge but
  changes ledger row status to red until investigated.

## 4. Coverage targets

- Reconstruction module test coverage ≥ 70% line coverage.
- Realism audit coverage = 100% of files under
  `nnbar_reconstruction/` minus test files.
- Plan-file YAML header coverage = 100%.

## 5. L1 defence-package CI checks

Stage E.3 adds plan-set checks that prevent EM/selection reviewer
questions from drifting after plans 50-56 are edited. These are CI audit
requirements, not claims that the final workflow file already exists.

| Check id | Trigger | Assertion | Failure semantics |
|---|---|---|---|
| `l1_defence_overlay_schema` | changes to plans 50, 51, 55, or 56 | every L1 overlay/question/note/glossary term has a stable id and required artifact field, and Plan 50's `required_l1_overlay_ids` set matches all routed L1 overlays | Tier 1 block |
| `l1_review_evidence_links` | changes to plan 50 | package schema exposes overlay roll-up, defence-routing crosswalk, owner sign-off, rerun manifest, rerun transcript, command-template ids, verifier hashes/sources, CI report, archive inventory/drill, note annex, glossary audit, staleness summary, review-artifact hashes, and staleness status | Tier 1 block |
| `l1_question_status_transition` | changes to plan 51 | answered L1 reviewer-question rows carry artifact, overlay, owner sign-off, review-evidence links, review-artifact hashes, and rerun manifest/transcript/template ids plus verifier hash/source when refreshed evidence is claimed | Tier 1 block |
| `l1_wave4_plan_presence` | changes under `docs/rebuild_plans/` | plans 58, 59, 61, and 64 exist and remain between 200 and 300 lines unless a split plan is declared | Tier 1 block |
| `l1_no_stale_cli_or_code_cites` | changes to L1-owned plans | grep for `*.py:<line>` and nnbar module commands, then require the A+ verifier transcript or remove the claim | Tier 1 block |
| `l1_cutflow_identity_guard` | changes to plans 37, 50, 51, or 55 | canonical singular `pass_*` selection columns remain named in defence overlays and note annexes | Tier 1 block |
| `l1_defence_rerun_manifest` | Tier 3 weekly | plan-52 defence rerun bundle has rows for EM chain, selection, pile-up, strange, TOF, Bayesian cross-checks, and unbounded-caveat status | Tier 3 tracking issue if incomplete |
| `l1_overlay_pack_member_parity` | changes to plans 50, 51, 52, 54, 55, or 56 | every plan-50 L1 overlay id maps through a plan-51 question id and to a plan-52 rerun bundle member, a plan-54 archive pack member, a plan-55 note-annex block, and at least one plan-56 glossary term; the defence-routing member covers the full set | Tier 1 block |
| `l1_rerun_transcript_link` | changes to plans 50 or 52 | any ready plan-50 L1 roll-up links both the plan-52 rerun manifest and execution transcript, and plan-52 rows carry review-evidence links plus rerun/verifier review-artifact hashes | Tier 1 block |
| `l1_command_template_registry` | changes to plan 52 | transcript command-template ids are registered, immutable, limited to verified CLI help output or explicit blocked templates, and carry verifier transcripts, hashes, and sources | Tier 1 block |
| `l1_package_staleness_guard` | changes to plans 50-56 | ready plan-50 L1 packages carry `l1_staleness.status: current` against the latest L1 hashes, including plan-54 archive inventory/drill hashes | Tier 1 block |
| `l1_note_package_freshness` | changes to plans 50 or 55 | promoted L1 note annexes quote only current packages or include an explicit stale-package caveat, and carry note/package/rerun/CI/glossary artifact hashes plus staleness id | Tier 1 block |
| `l1_archive_drill_manifest` | thesis-freeze package build | plan-54 L1 archive drill exists, starts from the top-level README, and records blocked rows plus owner sign-off refs, archive-drill hash, rerun hashes, verifier hashes/sources, and review-artifact hashes | Tier 1 block for freeze packages |
| `l1_glossary_signoff` | changes to plans 50, 55, or 56 | plan-56 sign-off rows cover every L1 term used by defence overlays and note annexes | Tier 1 block |

The checks are deliberately text-and-manifest based so they can run
before L3 has implemented every statistics or reconstruction producer. A
missing downstream artifact is represented as a blocked row with a named
owner, not as a skipped CI check.


### 5.1 L1 CI report fixture

The CI implementation writes a compact report for the L1 checks so a
failed run can be triaged without re-running grep by hand. The report is
kept under the normal CI artifact directory and is linked from the plan-50
defence package when a thesis-freeze package is produced.

```yaml
l1_defence_ci_report:
  git_rev: <rev>
  checked_at: <timestamp>
  checks:
    - check_id: l1_wave4_plan_presence
      status: pass | fail | warn
      files_checked:
        - docs/rebuild_plans/58_pileup_at_ess_intensity.md
        - docs/rebuild_plans/59_strange_baryon_contamination.md
        - docs/rebuild_plans/61_time_of_flight_discrimination.md
        - docs/rebuild_plans/64_bayesian_limit_cross_check.md
      evidence:
        line_counts: {58: 284, 59: 290, 61: 272, 64: 249}
        allowed_line_range: [200, 300]
        stale_citation_matches: 0
        owner_signoff_refs_present: true
        review_evidence_link_keys: [overlay_rollup, defence_routing_crosswalk, owner_signoff_refs, rerun_manifest, rerun_transcript, command_template_ids, command_template_verifier_hashes, command_template_verifier_sources, staleness_summary, ci_report, archive_inventory, archive_drill, note_annex, glossary_audit]
        review_artifact_hash_keys: [package, rerun_manifest, rerun_transcript, command_template_verifier, defence_routing_crosswalk, staleness_summary, ci_report, archive_inventory, archive_drill, note_annex, glossary_audit]
        archive_drill_hash_present: true
        command_template_verifier_hashes: [sha256:b3cee4613afed558d4704df3dc5b281271aed768965d79a09603f812496806f0]
      remediation: null
    - check_id: l1_command_template_registry
      status: pass | fail
      files_checked:
        - docs/rebuild_plans/52_run_orchestration.md
      evidence:
        executable_template_ids: [validate_reco_cutflow_v1, validate_reco_allruns_v1]
        blocked_template_ids: [blocked_missing_input_v1]
        verified_command: python -m nnbar_reconstruction.cli validate-reco --help
        verified_options: [--runs, --all-runs, --json]
        verifier_exit_status: 0
        command_template_verifier_hashes: [sha256:b3cee4613afed558d4704df3dc5b281271aed768965d79a09603f812496806f0]
        command_template_verifier_sources: [plan52:validate_reco_cutflow_v1, plan52:validate_reco_allruns_v1]
        immutable_template_policy: true
      remediation: null
    - check_id: l1_archive_drill_manifest
      status: pass | fail
      files_checked:
        - docs/rebuild_plans/54_open_data_archival.md
      evidence:
        expected_pack_members:
          - em_object_chain
          - ch10_cutflow
          - pileup_l11
          - strange_v0
          - tof_timing
          - bayesian_limits
          - unbounded_caveats
          - defence_routing
        inventory_pack_member_count: 8
        top_level_readme_entry_present: true
        blocked_rows_visible: true
        owner_signoff_refs_present: true
        archive_drill_hash_present: true
        review_artifact_hash_keys: [package, rerun_manifest, rerun_transcript, command_template_verifier, defence_routing_crosswalk, staleness_summary, ci_report, archive_inventory, archive_drill, note_annex, glossary_audit]
      remediation: null
    - check_id: l1_glossary_signoff
      status: pass | fail
      files_checked:
        - docs/rebuild_plans/56_glossary.md
      evidence:
        signoff_terms_checked:
          - pass_* columns
          - defence overlay
          - overlay roll-up
          - unbounded caveat status
          - L1 archive pack member
          - defence routing
          - rerun transcript
          - command-template id
          - command-template verifier hash
          - command-template verifier source
          - CLI verifier transcript
          - blocked template
          - review-evidence links
          - review-artifact hashes
          - owner sign-off
          - package freshness
          - stale package
          - stale-package caveat
        required_fields: [defence_package_refs, note_refs, audit_row_ref, thesis_status, approved_by, caveat_text]
        missing_signoff_terms: []
        flagged_delta_rows_have_caveat_text: true
        approved_or_blocked_rows_visible: true
      remediation: null
    - check_id: l1_note_package_freshness
      status: pass | fail
      files_checked:
        - docs/rebuild_plans/50_reviewer_defense_package.md
        - docs/rebuild_plans/55_internal_note_template.md
      evidence:
        promoted_note_rows_checked: <n>
        package_staleness_statuses_allowed: [current, stale-with-caveat]
        staleness_id_present: true
        stale_package_caveat_present_when_needed: true
        review_evidence_link_keys: [overlay_rollup, owner_signoff_refs, rerun_manifest, rerun_transcript, command_template_id, command_template_verifier, staleness_summary, ci_report, archive_inventory, archive_drill, glossary_audit]
        review_artifact_hash_keys: [note_annex, defence_package, staleness_summary, ci_report, rerun_manifest, rerun_transcript, command_template_verifier, archive_inventory, archive_drill, glossary_audit]
      remediation: null
    - check_id: l1_package_staleness_guard
      status: pass | fail
      files_checked:
        - docs/rebuild_plans/50_reviewer_defense_package.md
        - docs/rebuild_plans/51_reviewer_question_registry.md
        - docs/rebuild_plans/52_run_orchestration.md
        - docs/rebuild_plans/53_ci_regression_suite.md
        - docs/rebuild_plans/54_open_data_archival.md
        - docs/rebuild_plans/55_internal_note_template.md
        - docs/rebuild_plans/56_glossary.md
      evidence:
        ready_package_count: <n>
        ready_packages_with_current_staleness: <n>
        checked_hash_inputs: [plan50_overlay_schema, plan51_question_registry, plan52_rerun_manifest, plan52_rerun_transcript, plan52_command_templates, plan52_command_template_verifiers, plan53_ci_report, plan54_archive_inventory, plan54_archive_drill, review_artifact_hashes, plan55_note_annex, plan56_glossary_audit]
        archive_hashes_present: true
        stale_ready_packages: []
      remediation: null
    - check_id: l1_review_evidence_links
      status: pass | fail
      files_checked:
        - docs/rebuild_plans/50_reviewer_defense_package.md
      evidence:
        required_link_keys: [overlay_rollup, defence_routing_crosswalk, owner_signoff_refs, rerun_manifest, rerun_transcript, command_template_ids, command_template_verifier_hashes, command_template_verifier_sources, ci_report, archive_inventory, archive_drill, note_annex, glossary_audit, staleness_summary, staleness_status]
        required_hash_keys: [package, rerun_manifest, rerun_transcript, command_template_verifier, defence_routing_crosswalk, ci_report, note_annex, glossary_audit, staleness_summary, archive_inventory, archive_drill]
        staleness_status_key_present: true
        command_template_verifier_hashes_present: true
      remediation: null
    - check_id: l1_question_status_transition
      status: pass | fail
      files_checked:
        - docs/rebuild_plans/51_reviewer_question_registry.md
      evidence:
        answered_rows_checked: <n>
        required_answer_keys: [artifact, owner_signoff, review_evidence_links, review_artifact_hashes, rerun_manifest_id, rerun_transcript_id]
        required_transition_keys: [old_status, new_status, required_artifact_status, l1_overlay_id]
        refreshed_artifact_keys: [rerun_manifest_id, rerun_transcript_id, rerun_command_template_id, rerun_command_template_verifier_hash, rerun_command_template_verifier_source]
        rerun_manifest_refs_match_plan52: true
        rerun_transcript_refs_present_or_blocked: true
        transition_matrix_checked: true
      remediation: null
    - check_id: l1_defence_overlay_schema
      status: pass | fail
      files_checked:
        - docs/rebuild_plans/50_reviewer_defense_package.md
        - docs/rebuild_plans/51_reviewer_question_registry.md
        - docs/rebuild_plans/55_internal_note_template.md
        - docs/rebuild_plans/56_glossary.md
      evidence:
        overlay_ids_checked: [em_cluster_truth_blindness, pi0_cut_decomposition, selection_cutflow_identity, pileup_l11_status, strange_v0_contamination, tof_timing_resolution, bayesian_prior_sensitivity, unbounded_caveat_status]
        required_l1_overlay_ids_present: true
        required_l1_overlay_ids_match_plan50_table: true
        required_l1_overlay_ids_match_plan51_and_plan55: true
        required_overlay_fields: [overlay_id, applicability, reason, source_plans, required_artifacts, artifact_status, reviewer_question_ids, caveat_text, last_verified]
        question_overlay_links_present: true
        note_overlay_links_present: true
        glossary_refs_present: true
      remediation: null
    - check_id: l1_no_stale_cli_or_code_cites
      status: pass | fail
      files_checked:
        - docs/rebuild_plans/31_subsystem_calorimeter_clustering.md
        - docs/rebuild_plans/32_subsystem_shower_shape.md
        - docs/rebuild_plans/33_subsystem_photon_object.md
        - docs/rebuild_plans/34_subsystem_pi0_pairing.md
        - docs/rebuild_plans/35_subsystem_kinematic_fit.md
        - docs/rebuild_plans/36_subsystem_event_variables.md
        - docs/rebuild_plans/37_subsystem_event_selection.md
        - docs/rebuild_plans/44_background_taxonomy.md
        - docs/rebuild_plans/45_systematics_taxonomy.md
        - docs/rebuild_plans/46_significance_protocol.md
        - docs/rebuild_plans/50_reviewer_defense_package.md
        - docs/rebuild_plans/51_reviewer_question_registry.md
        - docs/rebuild_plans/52_run_orchestration.md
        - docs/rebuild_plans/53_ci_regression_suite.md
        - docs/rebuild_plans/54_open_data_archival.md
        - docs/rebuild_plans/55_internal_note_template.md
        - docs/rebuild_plans/56_glossary.md
        - docs/rebuild_plans/58_pileup_at_ess_intensity.md
        - docs/rebuild_plans/59_strange_baryon_contamination.md
        - docs/rebuild_plans/61_time_of_flight_discrimination.md
        - docs/rebuild_plans/64_bayesian_limit_cross_check.md
      evidence:
        citation_patterns: ['*.py:<line>', 'nnbar module CLI invocation']
        code_citation_matches: <n>
        cli_invocation_matches: <n>
        verified_cli_help_transcripts: <n>
        forbidden_removed_file_matches: 0
      remediation: null
    - check_id: l1_cutflow_identity_guard
      status: pass | fail
      files_checked:
        - docs/rebuild_plans/37_subsystem_event_selection.md
        - docs/rebuild_plans/50_reviewer_defense_package.md
        - docs/rebuild_plans/51_reviewer_question_registry.md
        - docs/rebuild_plans/55_internal_note_template.md
      evidence:
        canonical_cut_columns: [pass_scintillator_energy, pass_tpc_foil_track, pass_pion_count, pass_invariant_mass, pass_sphericity, pass_scintillator_balance]
        final_and_column: passes_preliminary_selection
        defence_overlay_id: selection_cutflow_identity
        note_annex_block: event_variable_and_cutflow_identity
        independent_and_cumulative_counts_required: true
      remediation: null
    - check_id: l1_defence_rerun_manifest
      status: pass | fail | warn
      files_checked:
        - docs/rebuild_plans/52_run_orchestration.md
      evidence:
        expected_bundle_members: [em_object_chain, ch10_cutflow, pileup_l11, strange_v0, tof_timing, bayesian_limits, unbounded_caveats, defence_routing]
        missing_bundle_members: [<member-or-empty>]
        ready_rows_require_source_and_output_hashes: true
        blocked_rows_require_owner_and_blocker: true
        review_evidence_links_required: true
      remediation: null
    - check_id: l1_overlay_pack_member_parity
      status: pass | fail
      files_checked:
        - docs/rebuild_plans/50_reviewer_defense_package.md
        - docs/rebuild_plans/51_reviewer_question_registry.md
        - docs/rebuild_plans/52_run_orchestration.md
        - docs/rebuild_plans/54_open_data_archival.md
        - docs/rebuild_plans/55_internal_note_template.md
        - docs/rebuild_plans/56_glossary.md
      evidence:
        overlay_ids_checked: [em_cluster_truth_blindness, pi0_cut_decomposition, selection_cutflow_identity, pileup_l11_status, strange_v0_contamination, tof_timing_resolution, bayesian_prior_sensitivity, unbounded_caveat_status]
        question_ids_checked: [RQ-L1-EM-P1-CLUSTERING, RQ-L1-EM-P2-DISCRIMINANT, RQ-L1-PI0-CUTS, RQ-L1-SELECTION-CUTFLOW, RQ-L1-PILEUP-L11, RQ-L1-STRANGE-BARYON, RQ-L1-TOF, RQ-L1-BAYES-LIMIT, RQ-L1-UNBOUNDED-CAVEATS]
        pack_members_checked: [em_object_chain, ch10_cutflow, pileup_l11, strange_v0, tof_timing, bayesian_limits, unbounded_caveats, defence_routing]
        overlay_to_pack_member_map:
          em_cluster_truth_blindness: em_object_chain
          pi0_cut_decomposition: em_object_chain
          selection_cutflow_identity: ch10_cutflow
          pileup_l11_status: pileup_l11
          strange_v0_contamination: strange_v0
          tof_timing_resolution: tof_timing
          bayesian_prior_sensitivity: bayesian_limits
          unbounded_caveat_status: unbounded_caveats
        all_pack_members_have_review_evidence_links: true
        crosswalk_glossary_terms_checked: true
        defence_routing_covers_all_overlays: true
        missing_note_annex_blocks: []
      remediation: null
```

Report review rules:

| Rule | Failure caught |
|---|---|
| every §5 check id appears in the report | CI silently skipped an L1 defence guard |
| every failed check has remediation text | reviewer cannot tell which plan/owner must act |
| line-count evidence is numeric, not prose | 500-line and Wave-4 depth gates become auditable |
| stale-citation evidence includes match count | A+ examiner gate is not reduced to a checkbox |
| report git rev matches package git rev | archived defence artifacts and CI evidence diverge |
| archive and glossary checks are present when freeze mode runs | freeze package omits L1 drill, archive-drill hash, owner sign-off refs, review-artifact hashes, or term sign-off evidence |
| rerun transcript check appears with review-evidence links and artifact hashes when roll-up uses refreshed artifacts | package claims rerun evidence without execution proof or artifact parity |
| command-template registry check includes verifier transcript | transcript uses unsupported, unverified, or mutable command surface |
| answered-question transition evidence includes command-template ids and verifier hash | reviewer registry closes a refreshed-evidence question without replay contract or A+ verifier proof |
| answered-question transition evidence includes rerun manifest/transcript ids matching plan 52 | reviewer registry closes a question without a stable rerun row or transcript handoff |
| answered-question transition evidence includes owner sign-off | reviewer registry closes a question without accountable approval |
| answered-question transition evidence includes review-evidence links | reviewer registry answer cannot be traced to package, CI, note, and glossary artifacts |
| answered-question transition evidence includes review-artifact hashes | reviewer registry answer links can drift after artifacts are regenerated |
| staleness guard appears for ready L1 packages and includes archive hashes | stale defence package is promoted as current evidence |
| review-evidence links include package, defence routing, staleness, CI, archive, note, glossary artifacts, and hashes | package has L1 evidence in prose but no machine-readable handoff |
| note freshness check appears for promoted notes with artifact hashes and staleness id | thesis-facing note quotes stale package or unverifiable note evidence as current evidence |
| archive drill report lists the eight plan-54 pack members by stable id | freeze CI checks archive presence but not full L1 evidence-class coverage |
| overlay-to-pack-member parity appears with plan-50, plan-51, plan-52, plan-54, plan-55, and plan-56 evidence | a reviewer question has a defence overlay but no rerun, archive, note, or glossary route |

A warning status is allowed only for Tier 3 weekly checks. Tier 1 L1
checks are pass/fail and block the plan-set edit when they fail.

## 6. Acceptance criteria

- §1 tiers implemented in `.github/workflows/` (or equivalent).
- §2 triggering wired by path filter.
- §3 failure semantics documented and enforced.
- §4 coverage targets met on `main`.
- §5 L1 defence-package CI checks implemented for Stage E.3 plan edits,
  including rerun transcript linkage plus review-artifact parity for refreshed artifacts and
  answered-question transition evidence with command-template ids plus verifier
  hashes, owner sign-off, review-artifact hashes, package staleness guards,
  review-evidence link checks, note freshness checks, and command-template
  registry/verifier checks.
- Freeze-mode L1 CI includes archive-drill, archive-evidence hash,
  owner-signoff, glossary-signoff, and plan-54 pack-member parity checks.
- Stage E.3 overlay parity checks keep plan-50 overlays, plan-52 rerun
  bundle members, plan-54 archive pack members, and plan-55 note annexes
  aligned for every L1 reviewer-question family.

## 7. Risks

- *Risk:* nightly load is heavy; cluster contention.
  *Mitigation:* nightly Tier 2 batches across 24 hours; Tier 3
  weekly.
- *Risk:* smoke samples drift from being representative.
  *Mitigation:* Tier 3 ledger refresh is the production check.

## 8. Dependencies

- **01, 03, 19, 47** — checks consumed by tiers.
- *Consumed by:* every other plan's "CI rule" entry.

## 9. References

- pytest + GitHub Actions standard practice.
- ATLAS / CMS CI conventions.

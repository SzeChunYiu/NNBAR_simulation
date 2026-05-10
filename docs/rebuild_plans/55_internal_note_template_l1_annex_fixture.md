---
id: 55_internal_note_template_l1_annex_fixture
title: Internal-note template — L1 annex fixture
version: 0.1
status: draft
owner: Software Quality
depends_on: [55_internal_note_template, 50_reviewer_defense_package, 51_reviewer_question_registry, 52_run_orchestration]
outputs:
  - {path: docs/rebuild_plans/55_internal_note_template_l1_annex_fixture.md, schema: split L1 annex fixture}
acceptance:
  - {test: fixture annex rows match plan 55 §1.1 block names, method: plan-53 parity check, pass_when: zero missing blocks}
last_updated: 2026-05-10
---

# Internal-note L1 annex fixture

This companion file keeps plan 55 below the 500-line cap while preserving
the machine-readable L1 annex consumed by plans 50, 53, 54, and 56.

### 1.2 Machine-readable L1 note annex fixture

A promoted internal note stores the L1 annex as a structured block so
plan 53 can compare the note, defence package, and reviewer-question
registry without parsing prose. The same block can be rendered in the
Markdown note appendix.

```yaml
l1_note_annex:
  result_id: LIC-CH10-NUM-1
  note_version: v1
  annex_rows:
    - annex_block: em_object_chain
      applicability: applies | not_applicable | blocked
      source_plans: [31, 32, 33, 34, 35]
      defence_overlay_id: em_cluster_truth_blindness
      additional_defence_overlay_ids: [pi0_cut_decomposition]
      reviewer_question_ids: [RQ-L1-EM-P1-CLUSTERING, RQ-L1-EM-P2-DISCRIMINANT, RQ-L1-PI0-CUTS]
      required_contents:
        - P.1-P.7 method ids and closure row ids
        - Class-B drop hash status for production EM decisions
        - selected DEC stubs for clusterer, discriminator, and pi0 cuts
      evidence_refs:
        - p1_p7_closure_rows
        - photon_pi0_response_and_handoff_summary
        - DEC-31-CLUSTERER-CHOICE
        - DEC-32-DISCRIMINANT-CHOICE
        - DEC-34-PI0-CUT-BASELINE
      review_evidence_links:
        overlay_rollup: <plan50-rollup-id>
        defence_routing_crosswalk: <plan50-crosswalk-id-or-null>
        owner_signoff_refs: [RQ-L1-EM-P1-CLUSTERING:<owner-hash-or-null>, RQ-L1-EM-P2-DISCRIMINANT:<owner-hash-or-null>, RQ-L1-PI0-CUTS:<owner-hash-or-null>]
        ci_report: <plan53-l1-report-id>
        rerun_manifest: plan52:EM chain closure
        rerun_transcript: plan52:em_object_chain:transcript-or-null
        command_template_id: validate_reco_allruns_v1
        command_template_verifier: plan52:validate_reco_allruns_v1
        glossary_audit: <plan56-audit-id>
        staleness_summary: <plan50-staleness-id>
        archive_inventory: <plan54-inventory-id-or-null>
        archive_drill: <plan54-drill-id-or-null>
      artifact_hashes:
        note_annex: sha256:<hash>
        note_annex_fixture: sha256:<hash>
        defence_package: sha256:<hash-or-null>
        defence_routing_crosswalk: sha256:<hash-or-null>
        staleness_summary: sha256:<hash-or-null>
        ci_report: sha256:<hash-or-null>
        rerun_manifest: sha256:<hash-or-null>
        rerun_transcript: sha256:<hash-or-null>
        command_template_verifier: sha256:b3cee4613afed558d4704df3dc5b281271aed768965d79a09603f812496806f0
        glossary_audit: sha256:<hash-or-null>
        archive_inventory: sha256:<hash-or-null>
        archive_drill: sha256:<hash-or-null>
      caveat_text: <required when applicability is blocked>
    - annex_block: event_variable_and_cutflow_identity
      applicability: applies | not_applicable | blocked
      source_plans: [36, 37]
      defence_overlay_id: selection_cutflow_identity
      reviewer_question_ids: [RQ-L1-SELECTION-CUTFLOW]
      required_contents:
        - canonical pass_* columns
        - independent and cumulative cut counts
      evidence_refs:
        - <defence package path or ledger key>
      review_evidence_links:
        overlay_rollup: <plan50-rollup-id>
        defence_routing_crosswalk: <plan50-crosswalk-id-or-null>
        owner_signoff_refs: [RQ-L1-SELECTION-CUTFLOW:<owner-hash-or-null>]
        ci_report: <plan53-l1-report-id>
        rerun_manifest: plan52:Ch 10 selection cut-flow
        rerun_transcript: plan52:ch10_cutflow:transcript-or-null
        command_template_id: validate_reco_cutflow_v1
        command_template_verifier: plan52:validate_reco_cutflow_v1
        glossary_audit: <plan56-audit-id>
        staleness_summary: <plan50-staleness-id>
        archive_inventory: <plan54-inventory-id-or-null>
        archive_drill: <plan54-drill-id-or-null>
      artifact_hashes:
        note_annex: sha256:<hash>
        note_annex_fixture: sha256:<hash>
        defence_package: sha256:<hash>
        defence_routing_crosswalk: sha256:<hash-or-null>
        staleness_summary: sha256:<hash>
        ci_report: sha256:<hash>
        rerun_manifest: sha256:<hash-or-null>
        rerun_transcript: sha256:<hash-or-null>
        command_template_verifier: sha256:b3cee4613afed558d4704df3dc5b281271aed768965d79a09603f812496806f0
        glossary_audit: sha256:<hash>
        archive_inventory: sha256:<hash-or-null>
        archive_drill: sha256:<hash-or-null>
      caveat_text: null
    - annex_block: pile_up_caveat
      applicability: applies | not_applicable | blocked
      source_plans: [1, 44, 58]
      defence_overlay_id: pileup_l11_status
      reviewer_question_ids: [RQ-L1-PILEUP-L11]
      required_contents:
        - plan-58 study id and ESS time-model id
        - paired cosmic overlay status
        - occupancy-tail interval and L11 limitation state
      evidence_refs:
        - plan58_pileup_overlay_closure
        - DEC-58-PILEUP-NUISANCE
      review_evidence_links:
        overlay_rollup: <plan50-rollup-id>
        defence_routing_crosswalk: <plan50-crosswalk-id-or-null>
        owner_signoff_refs: [RQ-L1-PILEUP-L11:<owner-hash-or-null>]
        ci_report: <plan53-l1-report-id>
        rerun_manifest: plan52:Pile-up L11 overlay
        rerun_transcript: plan52:pileup_l11:transcript-or-null
        command_template_id: blocked_missing_input_v1
        command_template_verifier: null
        glossary_audit: <plan56-audit-id>
        staleness_summary: <plan50-staleness-id>
        archive_inventory: <plan54-inventory-id-or-null>
        archive_drill: <plan54-drill-id-or-null>
      artifact_hashes:
        note_annex: sha256:<hash>
        note_annex_fixture: sha256:<hash>
        defence_package: sha256:<hash-or-null>
        defence_routing_crosswalk: sha256:<hash-or-null>
        staleness_summary: sha256:<hash-or-null>
        ci_report: sha256:<hash-or-null>
        rerun_manifest: sha256:<hash-or-null>
        rerun_transcript: sha256:<hash-or-null>
        command_template_verifier: null
        glossary_audit: sha256:<hash-or-null>
        archive_inventory: sha256:<hash-or-null>
        archive_drill: sha256:<hash-or-null>
      caveat_text: <required unless applicability is not_applicable>
    - annex_block: strange_background_caveat
      applicability: applies | not_applicable | blocked
      source_plans: [14, 44, 59]
      defence_overlay_id: strange_v0_contamination
      reviewer_question_ids: [RQ-L1-STRANGE-BARYON]
      required_contents:
        - K_S/Lambda/Sigma branching snapshot
        - V0 rejection closure status
        - residual survivor interval and signal-loss interval
      evidence_refs:
        - plan59_lambda_enriched_v0_closure
        - DEC-59-V0-REJECTION
      review_evidence_links:
        overlay_rollup: <plan50-rollup-id>
        defence_routing_crosswalk: <plan50-crosswalk-id-or-null>
        owner_signoff_refs: [RQ-L1-STRANGE-BARYON:<owner-hash-or-null>]
        ci_report: <plan53-l1-report-id>
        rerun_manifest: plan52:Strange V0 contamination
        rerun_transcript: plan52:strange_v0:transcript-or-null
        command_template_id: blocked_missing_input_v1
        command_template_verifier: null
        glossary_audit: <plan56-audit-id>
        staleness_summary: <plan50-staleness-id>
        archive_inventory: <plan54-inventory-id-or-null>
        archive_drill: <plan54-drill-id-or-null>
      artifact_hashes:
        note_annex: sha256:<hash>
        note_annex_fixture: sha256:<hash>
        defence_package: sha256:<hash-or-null>
        defence_routing_crosswalk: sha256:<hash-or-null>
        staleness_summary: sha256:<hash-or-null>
        ci_report: sha256:<hash-or-null>
        rerun_manifest: sha256:<hash-or-null>
        rerun_transcript: sha256:<hash-or-null>
        command_template_verifier: null
        glossary_audit: sha256:<hash-or-null>
        archive_inventory: sha256:<hash-or-null>
        archive_drill: sha256:<hash-or-null>
      caveat_text: <required unless applicability is not_applicable>
    - annex_block: timing_tof_cross_check
      applicability: applies | not_applicable | blocked
      source_plans: [36, 45, 61]
      defence_overlay_id: tof_timing_resolution
      reviewer_question_ids: [RQ-L1-TOF]
      required_contents:
        - TOF method id and E.8 comparison row
        - nonzero timing-resolution budget
        - cal/cosmic closure slices and signal-loss interval
      evidence_refs:
        - DEC-61-TOF-ESTIMATOR
        - DEC-61-RESOLUTION-BUDGET
      review_evidence_links:
        overlay_rollup: <plan50-rollup-id>
        defence_routing_crosswalk: <plan50-crosswalk-id-or-null>
        owner_signoff_refs: [RQ-L1-TOF:<owner-hash-or-null>]
        ci_report: <plan53-l1-report-id>
        rerun_manifest: plan52:TOF timing closure
        rerun_transcript: plan52:tof_timing:transcript-or-null
        command_template_id: blocked_missing_input_v1
        command_template_verifier: null
        glossary_audit: <plan56-audit-id>
        staleness_summary: <plan50-staleness-id>
        archive_inventory: <plan54-inventory-id-or-null>
        archive_drill: <plan54-drill-id-or-null>
      artifact_hashes:
        note_annex: sha256:<hash>
        note_annex_fixture: sha256:<hash>
        defence_package: sha256:<hash-or-null>
        defence_routing_crosswalk: sha256:<hash-or-null>
        staleness_summary: sha256:<hash-or-null>
        ci_report: sha256:<hash-or-null>
        rerun_manifest: sha256:<hash-or-null>
        rerun_transcript: sha256:<hash-or-null>
        command_template_verifier: null
        glossary_audit: sha256:<hash-or-null>
        archive_inventory: sha256:<hash-or-null>
        archive_drill: sha256:<hash-or-null>
      caveat_text: <required unless applicability is not_applicable>
    - annex_block: limit_convention_cross_check
      applicability: applies | not_applicable | blocked
      source_plans: [4, 46, 64]
      defence_overlay_id: bayesian_prior_sensitivity
      reviewer_question_ids: [RQ-L1-BAYES-LIMIT]
      required_contents:
        - plan-46 primary-method dispatch id
        - Jeffreys and flat-prior upper limits
        - prior-sensitivity ratios and status
      evidence_refs:
        - DEC-64-BAYES-CROSSCHECK
        - DEC-64-PRIORS
        - DEC-64-SENSITIVITY-THRESHOLDS
      review_evidence_links:
        overlay_rollup: <plan50-rollup-id>
        defence_routing_crosswalk: <plan50-crosswalk-id-or-null>
        owner_signoff_refs: [RQ-L1-BAYES-LIMIT:<owner-hash-or-null>]
        ci_report: <plan53-l1-report-id>
        rerun_manifest: plan52:Bayesian limit cross-check
        rerun_transcript: plan52:bayesian_limits:transcript-or-null
        command_template_id: blocked_missing_input_v1
        command_template_verifier: null
        glossary_audit: <plan56-audit-id>
        staleness_summary: <plan50-staleness-id>
        archive_inventory: <plan54-inventory-id-or-null>
        archive_drill: <plan54-drill-id-or-null>
      artifact_hashes:
        note_annex: sha256:<hash>
        note_annex_fixture: sha256:<hash>
        defence_package: sha256:<hash-or-null>
        defence_routing_crosswalk: sha256:<hash-or-null>
        staleness_summary: sha256:<hash-or-null>
        ci_report: sha256:<hash-or-null>
        rerun_manifest: sha256:<hash-or-null>
        rerun_transcript: sha256:<hash-or-null>
        command_template_verifier: null
        glossary_audit: sha256:<hash-or-null>
        archive_inventory: sha256:<hash-or-null>
        archive_drill: sha256:<hash-or-null>
      caveat_text: <required unless applicability is not_applicable>
    - annex_block: unbounded_caveat_status
      applicability: applies | not_applicable | blocked
      source_plans: [1, 45, 50]
      defence_overlay_id: unbounded_caveat_status
      reviewer_question_ids: [RQ-L1-UNBOUNDED-CAVEATS]
      required_contents:
        - limitation id and affected result ids
        - reviewer-facing caveat text
        - owner and reopening condition
      evidence_refs:
        - plan45_caveat_or_numeric_bound_row
        - plan50_unbounded_caveat_overlay
      review_evidence_links:
        overlay_rollup: <plan50-rollup-id>
        defence_routing_crosswalk: <plan50-crosswalk-id-or-null>
        owner_signoff_refs: [RQ-L1-UNBOUNDED-CAVEATS:<owner-hash-or-null>]
        ci_report: <plan53-l1-report-id>
        rerun_manifest: plan52:Unbounded caveat status
        rerun_transcript: plan52:unbounded_caveats:transcript-or-null
        command_template_id: blocked_missing_input_v1
        command_template_verifier: null
        glossary_audit: <plan56-audit-id>
        staleness_summary: <plan50-staleness-id>
        archive_inventory: <plan54-inventory-id-or-null>
        archive_drill: <plan54-drill-id-or-null>
      artifact_hashes:
        note_annex: sha256:<hash>
        note_annex_fixture: sha256:<hash>
        defence_package: sha256:<hash-or-null>
        defence_routing_crosswalk: sha256:<hash-or-null>
        staleness_summary: sha256:<hash-or-null>
        ci_report: sha256:<hash-or-null>
        rerun_manifest: sha256:<hash-or-null>
        rerun_transcript: sha256:<hash-or-null>
        command_template_verifier: null
        glossary_audit: sha256:<hash-or-null>
        archive_inventory: sha256:<hash-or-null>
        archive_drill: sha256:<hash-or-null>
      caveat_text: <required unless applicability is not_applicable>
    - annex_block: defence_routing
      applicability: applies | blocked
      source_plans: [50, 51, 52, 53, 54, 56]
      defence_overlay_id: em_cluster_truth_blindness
      additional_defence_overlay_ids: [pi0_cut_decomposition, selection_cutflow_identity, pileup_l11_status, strange_v0_contamination, tof_timing_resolution, bayesian_prior_sensitivity, unbounded_caveat_status]
      reviewer_question_ids: [RQ-L1-EM-P1-CLUSTERING, RQ-L1-EM-P2-DISCRIMINANT, RQ-L1-PI0-CUTS, RQ-L1-SELECTION-CUTFLOW, RQ-L1-PILEUP-L11, RQ-L1-STRANGE-BARYON, RQ-L1-TOF, RQ-L1-BAYES-LIMIT, RQ-L1-UNBOUNDED-CAVEATS]
      required_contents: [plan-50 overlay ids match plan-51 questions, plan-52 bundle ids match plan-54 archive pack members, plan-53 report id and plan-56 glossary audit id are current]
      evidence_refs: [l1_defence_routing_crosswalk]
      review_evidence_links: {overlay_rollup: <plan50-rollup-id>, defence_routing_crosswalk: <plan50-crosswalk-id-or-null>, owner_signoff_refs: [L1-routing-owner:<owner-hash-or-null>], ci_report: <plan53-l1-report-id>, rerun_manifest: plan52:Defence routing, rerun_transcript: plan52:defence_routing:transcript-or-null, command_template_id: blocked_missing_input_v1, command_template_verifier: null, glossary_audit: <plan56-audit-id>, staleness_summary: <plan50-staleness-id>, archive_inventory: <plan54-inventory-id-or-null>, archive_drill: <plan54-drill-id-or-null>}
      artifact_hashes: {note_annex: sha256:<hash>, note_annex_fixture: sha256:<hash>, defence_package: sha256:<hash-or-null>, defence_routing_crosswalk: sha256:<hash-or-null>, staleness_summary: sha256:<hash-or-null>, ci_report: sha256:<hash-or-null>, rerun_manifest: sha256:<hash-or-null>, rerun_transcript: sha256:<hash-or-null>, command_template_verifier: null, glossary_audit: sha256:<hash-or-null>, archive_inventory: sha256:<hash-or-null>, archive_drill: sha256:<hash-or-null>}
      caveat_text: <required when any routing fixture hash drifts>
```

Review rules:

| Rule | Failure caught |
|---|---|
| annex row names match the §1.1 blocks | note drifts from defence package taxonomy |
| every `applies` row names a defence overlay id | note has no machine-readable package handoff |
| every thesis-facing row exposes review-evidence links plus note-annex and split-fixture artifact hashes | note cannot be reconciled with package, split fixture, staleness, CI, archive, and glossary evidence |
| every `blocked` row carries `caveat_text` | hidden missing evidence in reviewer-facing prose |
| every low-count note includes the limit-convention row | Bayesian prior sensitivity omitted from sparse-count claims |
| every L11 note includes the pile-up caveat row | independent-event limitation omitted from acceptance claims |
| every unbounded limitation includes the unbounded-caveat row | caveat-only systematics are hidden as if they were zero-width nuisances |

The note author may add prose after the structured annex, but the structured row is the reviewable source of truth for CI and plan-50 package regeneration.

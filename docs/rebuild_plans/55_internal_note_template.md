---
id: 55_internal_note_template
title: Internal-note template — ATLAS INT-style format
version: 0.1
status: draft
owner: Software Quality
depends_on: [00_README]
outputs:
  - {path: docs/rebuild_plans/55_internal_note_template.md, schema: this file}
  - {path: docs/notes/_template.md, schema: blank template}
acceptance:
  - {test: every plan-set deliverable has a corresponding INT note when promoted to thesis-quote, method: per-result review, pass_when: full coverage}
  - {test: notes follow §1 sectioning, method: lint, pass_when: zero deviations}
risks:
  - {risk: notes duplicate the plan body, mitigation: §2 separation rule}
estimated_effort: S
last_updated: 2026-05-09
---

# Internal-note template — ATLAS INT-style

*Charter.* The format every long-form result document uses. Plans
describe the *plan*; notes describe the *result*. They share
provenance but serve different audiences.

## 1. Sections

```
# <Title>

## Abstract
<2-3 sentences>

## 1. Motivation
Why we measured this.

## 2. Method
What we did. Cite plan(s) and DEC entries.

## 3. Sample
Cite registry id from plan 03.

## 4. Result
The number / plot. Quote uncertainty per plan 04.

## 5. Cross-checks
Closure, ladder, fast-MC sanity (plans 38, 39, 40).

## 6. Systematic uncertainties
Cite nuisances from plan 45.

## 7. Conclusion
Summary; pointer to the ledger row in plan 47.

## 8. Reviewer notes
Open questions; foreseeable counter-arguments.

## 9. References
```


### 1.1 L1 EM/selection annex for reviewer-facing notes

Any internal note that quotes an EM-object, event-selection, or low-count
limit result must include the following annex after §8. The annex keeps
Stage E.3 aligned with the plan-50 defence overlays and the plan-51 L1
reviewer-question seeds. Rows may be marked `not_applicable`, but only
with a result-specific reason and a pointer to the affected plan-24
leaf or plan-44 background node.

| Annex block | Applies to | Required contents | Source plans |
|---|---|---|---|
| EM object chain | photon, pi0, or calorimeter result | P.1-P.7 method ids, Class-B drop hash status, closure row ids, selected DEC stubs | 31, 32, 33, 34, 35 |
| Event-variable and cut-flow identity | Ch 10 selection or event-shape result | E.1-E.9 event-variable method id, canonical `pass_*` columns, independent and cumulative cut counts | 36, 37 |
| Pile-up caveat | any result carrying L11 or rate/occupancy language | plan-58 study id, ESS time-model id, paired cosmic overlay status, occupancy-tail interval | 01, 44, 58 |
| Strange-background caveat | beam-neutron or EM-fake background result | K_S/Lambda/Sigma branch snapshot, V0 rejection closure, residual survivor interval | 14, 44, 59 |
| Timing/TOF cross-check | cosmic rejection or timing-result note | TOF method id, nonzero resolution budget, cal/cosmic closure slices, comparison to E.8 | 36, 45, 61 |
| Limit-convention cross-check | low-count limit or zero-survivor row | plan-46 primary method, Jeffreys and flat prior limits, prior-sensitivity status | 04, 46, 64 |
| Unbounded-caveat status | any EM/selection result with a limitation that lacks a numeric nuisance bound | limitation id, affected result ids, caveat text, owner, and reopening condition | 01, 45, 50 |

The annex is not a substitute for the defence package. It is the note
reader's compact route map to the exact package fields that answer the
foreseeable EM/selection examiner questions.


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
        package_rollup: <plan50-rollup-id>
        ci_report: <plan53-l1-report-id>
        command_template_verifier: plan52:validate_reco_cutflow_v1
        glossary_audit: <plan56-audit-id>
        staleness_summary: <plan50-staleness-id>
        archive_inventory: <plan54-inventory-id-or-null>
        archive_drill: <plan54-drill-id-or-null>
      artifact_hashes:
        note_annex: sha256:<hash>
        defence_package: sha256:<hash>
        staleness_summary: sha256:<hash>
        ci_report: sha256:<hash>
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
        package_rollup: <plan50-rollup-id>
        ci_report: <plan53-l1-report-id>
        rerun_manifest: plan52:Pile-up L11 overlay
        glossary_audit: <plan56-audit-id>
        staleness_summary: <plan50-staleness-id>
        archive_inventory: <plan54-inventory-id-or-null>
        archive_drill: <plan54-drill-id-or-null>
      artifact_hashes:
        note_annex: sha256:<hash>
        defence_package: sha256:<hash-or-null>
        staleness_summary: sha256:<hash-or-null>
        ci_report: sha256:<hash-or-null>
        rerun_manifest: sha256:<hash-or-null>
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
        package_rollup: <plan50-rollup-id>
        ci_report: <plan53-l1-report-id>
        rerun_manifest: plan52:Strange V0 contamination
        glossary_audit: <plan56-audit-id>
        staleness_summary: <plan50-staleness-id>
        archive_inventory: <plan54-inventory-id-or-null>
        archive_drill: <plan54-drill-id-or-null>
      artifact_hashes:
        note_annex: sha256:<hash>
        defence_package: sha256:<hash-or-null>
        staleness_summary: sha256:<hash-or-null>
        ci_report: sha256:<hash-or-null>
        rerun_manifest: sha256:<hash-or-null>
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
        package_rollup: <plan50-rollup-id>
        ci_report: <plan53-l1-report-id>
        rerun_manifest: <plan52-tof-row-id-or-blocker>
        glossary_audit: <plan56-audit-id>
        staleness_summary: <plan50-staleness-id>
        archive_inventory: <plan54-inventory-id-or-null>
        archive_drill: <plan54-drill-id-or-null>
      artifact_hashes:
        note_annex: sha256:<hash>
        defence_package: sha256:<hash-or-null>
        staleness_summary: sha256:<hash-or-null>
        ci_report: sha256:<hash-or-null>
        rerun_manifest: sha256:<hash-or-null>
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
        package_rollup: <plan50-rollup-id>
        ci_report: <plan53-l1-report-id>
        glossary_audit: <plan56-audit-id>
        staleness_summary: <plan50-staleness-id>
      artifact_hashes:
        note_annex: sha256:<hash>
        defence_package: sha256:<hash-or-null>
        staleness_summary: sha256:<hash-or-null>
        ci_report: sha256:<hash-or-null>
        glossary_audit: sha256:<hash-or-null>
      caveat_text: <required unless applicability is not_applicable>
```

Review rules:

| Rule | Failure caught |
|---|---|
| annex row names match the §1.1 blocks | note drifts from defence package taxonomy |
| every `applies` row names a defence overlay id | note has no machine-readable package handoff |
| every thesis-facing row exposes review-evidence links and artifact hashes | note cannot be reconciled with package, staleness, CI, archive, and glossary evidence |
| every `blocked` row carries `caveat_text` | hidden missing evidence in reviewer-facing prose |
| every low-count note includes the limit-convention row | Bayesian prior sensitivity omitted from sparse-count claims |
| every L11 note includes the pile-up caveat row | independent-event limitation omitted from acceptance claims |
| every unbounded limitation includes the unbounded-caveat row | caveat-only systematics are hidden as if they were zero-width nuisances |

The note author may add prose after the structured annex, but the
structured row is the reviewable source of truth for CI and plan-50
package regeneration.


### 1.3 L1 annex completeness checklist

Before a note is promoted to thesis-quote status, the L1 annex is checked
against the reviewer-question registry and the defence package. The check
is a small matrix, not a prose judgement, so omissions are visible in CI.

| Checklist item | Applies when | Required evidence |
|---|---|---|
| reviewer question coverage | any annex row has `applicability: applies` | at least one plan-51 question id is listed |
| defence package handoff | any note quotes a final EM/selection number | plan-50 overlay id, package revision, and owner sign-off status are recorded |
| package freshness | any note quotes a final EM/selection number | plan-50 staleness status is `current` or the note carries the stale-package caveat |
| rerun reproducibility | any note says an artifact was refreshed | plan-52 rerun manifest row id, execution transcript row id, command-template id, command-template verifier hash, and output hash are recorded |
| CI transcript | any note is promoted after Stage E.3 starts | plan-53 L1 report id is recorded |
| glossary consistency | any annex introduces shorthand | plan-56 glossary audit row is recorded |
| review evidence reconciliation | any annex row supports thesis-facing prose | plan-50 roll-up id, staleness id, plan-53 report id, plan-54 archive ids, plan-56 audit id, and note/package/staleness/CI/archive/glossary hashes are recorded |

The note may still be circulated internally with incomplete rows, but it
cannot be used as thesis evidence until every applicable checklist item
is either satisfied or explicitly blocked with the same blocker text used
in the plan-50 defence package. When a note says an artifact was refreshed,
the annex must point to the intended rerun manifest, the execution
transcript, command-template id, and command-template verifier hash so
readers can distinguish planned coverage, completed work, and the verified
command contract used for replay.
A note may cite a stale package only as historical provenance; thesis-facing
numeric claims require a current package or an explicit stale-package caveat
in §8 Reviewer notes.

## 2. Plan vs note separation

- A *plan* describes intent, gates, ownership, acceptance criteria.
  Long-lived; revised as the rebuild evolves.
- A *note* describes a finished result. Frozen at the time of
  writing; updates trigger a v2 note.

A note that re-derives plan content is duplicative; instead, notes
cite plans by ID.

## 3. Acceptance criteria

- §1 template target path is `docs/notes/_template.md`, created before
  the first note is promoted.
- First three notes drafted: licentiate Ch 6 reproduction, Ch 8 π⁰
  reproduction, Ch 10 selection reproduction.
- Stage E.3 notes that quote L1 EM, selection, timing, pile-up,
  strange-background, or Bayesian-limit evidence satisfy the §1.3
  checklist, including rerun transcript, command-template links, and
  verifier hashes for refreshed artifacts, owner sign-off, and package
  freshness evidence for quoted numbers.
- Thesis-facing L1 annex rows expose review-evidence links and artifact
  hashes so plan 53 can reconcile notes against the package, staleness,
  CI, archive, and glossary evidence before promotion.

## 4. Dependencies

- **00_README** — plan space.
- *Consumed by:* every result-quoting deliverable; thesis chapter
  drafting.

## 5. References

- ATLAS internal-note format precedent.

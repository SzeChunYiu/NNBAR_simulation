---
id: 56_glossary
title: Glossary — terms maintained alongside code
version: 0.1
status: draft
owner: Software Quality
depends_on: [00_README, 50_reviewer_defense_package, 51_reviewer_question_registry, 52_run_orchestration, 53_ci_regression_suite, 54_open_data_archival, 55_internal_note_template]
outputs:
  - {path: docs/rebuild_plans/56_glossary.md, schema: this file}
  - {path: docs/glossary.md, schema: living glossary}
acceptance:
  - {test: every plan-set acronym and shorthand is defined here, method: cross-reference scan, pass_when: zero undefined}
  - {test: terms match thesis Ch 14 glossary; deltas are flagged, method: comparison, pass_when: zero unflagged divergences}
risks:
  - {risk: thesis edits change a term; glossary lags, mitigation: §3 review on every thesis-freeze}
estimated_effort: S
last_updated: 2026-05-10
---

# Glossary

*Charter.* Single source of truth for every term used in the rebuild
plan-set, code, and ledger. Supersedes thesis Ch 14 glossary for
code-level usage; deltas are flagged.

## 1. Core terms

| Term | Definition |
|---|---|
| **NNBAR** | Neutron-antineutron oscillation experiment at ESS |
| **HIBEAM** | High Intensity Baryon Extraction And Measurement; the upstream phase of NNBAR |
| **TPC** | Time Projection Chamber; the tracking detector |
| **PMT** | Photomultiplier Tube |
| **MCPL** | Monte Carlo Particle List; the file format for primary particles |
| **CRY** | Cosmic-Ray Shower library (LLNL) |
| **SD** | Sensitive Detector (Geant4 class) |
| **POG** | Physics Object Group (working group structure) |
| **CP** | Combined Performance (working group) |
| **WG** | Working Group |
| **DAG** | Directed Acyclic Graph |
| **DEC-YYYY-MM-DD-N** | decision-log entry (plan 05) |
| **gate** | sign-off boundary (plan 06) |
| **leaf** | irreducible reconstruction decision (plan 24) |
| **ladder** | truth-substitution validation instrument (plan 38) |
| **ledger** | thesis reproduction ledger (plan 47) |
| **registry** | dataset registry (plan 03) or reviewer-question registry (plan 51) |
| **Class A** | experiment-equivalent column (plan 01 §2.1) |
| **Class B** | truth-only column (plan 01 §2.2) |
| **Class C** | MC-tuned calibration constant (plan 01 §2.3) |
| **digitisation seam** | the future-realism interface (plan 02) |
| **W-value** | mean energy per electron-ion pair (plan 17 §3) |
| **realism contract** | plan 01 |
| **fiducial volume** | detector region accepted by acceptance gate (plan 43) |
| **F-C** | Feldman-Cousins (plan 04 §5) |
| **CLs** | confidence-level method (plan 46 §2) |
| **N-1 plot** | distribution of variable C with all other cuts applied (plan 41) |
| **ROC curve** | signal acceptance vs background rejection (plan 41) |
| **IBU** | Iterative Bayesian Unfolding (plan 42) |



### 1.1 L1 EM/selection and defence-package terms

| Term | Definition |
|---|---|
| **`pass_*` columns** | Canonical singular event-selection booleans used by plan 37 for the Ch 10 cut-flow; plural aliases may be derived but do not replace them. |
| **pile-up / L11** | Limitation category for simultaneous or time-correlated signal, cosmic, and beam-induced activity not modelled by independent events; plan 58 owns the first overlay closure. |
| **V0 topology** | Displaced neutral-particle decay topology reconstructed from charged or charged-plus-neutral daughters; plan 59 uses it for K_S, Lambda, and Sigma contamination checks. |
| **K_S** | Short-lived neutral kaon used in plan 59 as a strange-background benchmark with charged- and neutral-pion decay modes. |
| **Lambda** | Strange baryon used in plan 59's Lambda-enriched beam-neutron closure slice. |
| **Sigma** | Strange-baryon family used in plan 59 to test gamma, neutron, and pion contamination paths. |
| **TOF** | Time of flight; plan 61's timing discriminator formed from TPC time anchors, scintillator hit times, and reconstructed path lengths. |
| **TOF sidecar** | Candidate table that stores TOF scores and validity reasons without changing the canonical plan-37 selection columns. |
| **Jeffreys prior** | Bayesian prior proportional to the square root of Fisher information; plan 64 applies it to the total Poisson mean for low-count limit cross-checks. |
| **flat prior** | Bayesian cross-check prior uniform in non-negative signal mean; plan 64 compares it against the Jeffreys-prior result and the plan-46 primary limit. |
| **prior sensitivity** | Difference between Bayesian limits under approved priors, reported as a reviewer caveat when it exceeds plan-64 thresholds. |
| **defence overlay** | Extra plan-50 package block that must be present when a result depends on L1 EM, selection, timing, pile-up, strange-background, or Bayesian-limit evidence. |
| **unbounded caveat status** | Plan-50 overlay state for EM/selection assumptions that cannot yet be assigned a numeric nuisance; it keeps the limitation visible until plan 45 or the owning study supplies a bound. |
| **overlay roll-up** | Plan-50 compact status block summarising all L1 defence overlays, blockers, required review links, and current/stale package state for one quoted result. |
| **review-evidence links** | Plan-50 and plan-51 machine-readable pointers from an L1 answer to the overlay roll-up, CI, note-annex, glossary-audit, rerun, archive, and staleness artifacts. |
| **review-artifact hashes** | Stable digests carried by plans 50, 51, 52, 53, 54, and 55 for package, CI report, note-annex, glossary-audit, rerun, and staleness artifacts that support an L1 defence answer. |
| **L1 archive pack member** | Stable plan-54 evidence-class id in the thesis-freeze archive inventory; plan 53 checks that every EM/selection defence class remains represented before freeze. |
| **defence routing** | Stable L1 crosswalk tying reviewer-question ids, overlay ids, rerun bundle members, archive pack members, note annex rows, and glossary audit rows; plans 52 and 54 store it as `defence_routing`. |
| **owner sign-off** | Plan-51 accountable approval recorded before an L1 reviewer-question answer can stop blocking a thesis-facing result. |
| **rerun transcript** | Plan-52 execution record proving which reviewer-triggered rerun rows actually ran, with input hashes, output hashes, environment identity, and pass/fail/block status. |
| **command-template id** | Stable plan-52 identifier for the verified rerun command contract used by a transcript row; it records replay semantics without depending on prose. |
| **command-template verifier hash** | Stable digest of the plan-52 CLI verifier transcript proving the command-template surface was checked before a refreshed L1 artifact was trusted. |
| **command-template verifier source** | Stable plan-52 verifier row id that produced the command-template verifier hash, such as `plan52:validate_reco_cutflow_v1`, so hashes can be traced back to the checked command surface. |
| **CLI verifier transcript** | Plan-52 evidence record containing the checked help command, exit status, supported flags, and digest for an executable command template. |
| **blocked template** | Plan-52 command-template row used when no execution command is valid because a required input or artifact is missing. |
| **package freshness** | Plan-50 state in which the L1 defence package staleness summary is `current` against the latest question registry, rerun manifest, rerun transcript, CI report, archive inventory/drill, note annex, glossary audit, and review-artifact hashes. |
| **stale package** | Archived defence package whose evidence is retained for provenance but is not acceptable as current thesis evidence until the plan-50 staleness summary, archive inventory/drill links, and review-artifact hashes are regenerated. |
| **stale-package caveat** | Plan-55 reviewer-note language that explicitly warns when a note cites stale L1 package evidence as historical provenance rather than current numerical support. |

## 2. Geant4 / Hep terms

| Term | Definition |
|---|---|
| **FTFP_BERT** | Geant4 hadronic physics list (Fritiof + Bertini cascade) |
| **HP** | High-Precision neutron data (G4NDL) |
| **dE/dx** | mean energy loss per unit length |
| **MIP** | Minimum-Ionising Particle |
| **X₀** | radiation length |
| **λ_I** | nuclear interaction length |
| **PDG** | Particle Data Group |
| **G4** | Geant4 |
| **CMS PF** | CMS Particle Flow algorithm |
| **PandoraPFA** | Pandora Particle Flow Algorithm |
| **ACTS** | A Common Tracking Software toolkit |
| **GPS** | General Particle Source (Geant4) |

## 3. Update protocol

- New terms added on first use in any plan or code.
- Definitions cite the originating plan / paper.
- Thesis Ch 14 (overleaf-hibeam-thesis `14_HIBEAM_NNBAR_glossary.tex`)
  is the user-facing version; this glossary is the code-facing
  version. Differences are flagged and reconciled at thesis-freeze.


### 3.1 L1 glossary audit fixture

The L1 defence package treats glossary coverage as evidence, not prose.
Each EM/selection term added in §1.1 is represented in an audit fixture
that can be regenerated during thesis-freeze checks.

```yaml
l1_glossary_audit:
  audit_version: 1
  scope: EM-selection-defence
  terms:
    - term: pass_* columns
      defined_in_section: "1.1"
      source_plans: [37, 50, 51, 55]
      required_contexts:
        - cutflow_identity_guard
        - reviewer_question_registry
      thesis_delta: none | flagged
      owner: L1
    - term: command-template verifier hash
      defined_in_section: "1.1"
      source_plans: [51, 52, 53, 54, 55]
      required_contexts:
        - reviewer_question_registry
        - rerun_command_template_registry
        - defence_ci_report
        - archive_inventory
        - note_annex
      canonical_hashes:
        - sha256:b3cee4613afed558d4704df3dc5b281271aed768965d79a09603f812496806f0
      thesis_delta: none | flagged
      owner: L1
    - term: review-evidence links
      defined_in_section: "1.1"
      source_plans: [50, 51, 52, 53, 54, 55]
      required_contexts:
        - l1_overlay_rollup
        - reviewer_question_registry
        - rerun_manifest
        - defence_ci_report
        - archive_inventory
        - note_annex
      required_link_keys:
        - overlay_rollup
        - owner_signoff_refs
        - rerun_manifest
        - rerun_transcript
        - command_template_ids
        - command_template_verifier_hashes
        - command_template_verifier_sources
        - staleness_summary
        - ci_report
        - archive_inventory
        - archive_drill
        - note_annex
        - glossary_audit
        - staleness_status
      thesis_delta: none | flagged
      owner: L1
    - term: review-artifact hashes
      defined_in_section: "1.1"
      source_plans: [50, 51, 52, 53, 54, 55]
      required_contexts:
        - l1_overlay_rollup
        - reviewer_question_registry
        - rerun_manifest
        - defence_ci_report
        - archive_inventory
        - note_annex
      required_hash_keys:
        - package
        - staleness_summary
        - ci_report
        - archive_inventory
        - archive_drill
        - note_annex
        - glossary_audit
        - rerun_manifest
        - rerun_transcript
        - command_template_verifier
      thesis_delta: none | flagged
      owner: L1
    - term: owner sign-off
      defined_in_section: "1.1"
      source_plans: [50, 51, 55]
      required_contexts:
        - defence_overlay
        - reviewer_question_registry
        - note_annex
      required_fields:
        - owner_signoff_ref
        - owner_signoff
        - defense_package_updated
      thesis_delta: none | flagged
      owner: L1
    - term: package freshness
      defined_in_section: "1.1"
      source_plans: [50, 53, 54, 55]
      required_contexts:
        - staleness_summary
        - defence_ci_report
        - archive_inventory
        - archive_drill
        - note_annex
      required_status_values:
        - current
        - stale
        - blocked
      thesis_delta: none | flagged
      owner: L1
    - term: stale-package caveat
      defined_in_section: "1.1"
      source_plans: [50, 53, 54, 55]
      required_contexts:
        - staleness_summary
        - defence_ci_report
        - archive_inventory
        - note_annex
      required_when:
        - note cites stale package as historical provenance
        - package staleness status is not current
      thesis_delta: none | flagged
      owner: L1
    - term: unbounded caveat status
      defined_in_section: "1.1"
      source_plans: [45, 50, 51, 55]
      required_contexts:
        - defence_overlay
        - reviewer_question_registry
        - note_annex
      thesis_delta: none | flagged
      owner: L1
    - term: L1 archive pack member
      defined_in_section: "1.1"
      source_plans: [53, 54, 55]
      required_contexts:
        - archive_inventory
        - archive_drill
        - defence_ci_report
        - note_annex
      expected_member_ids:
        - em_object_chain
        - ch10_cutflow
        - pileup_l11
        - strange_v0
        - tof_timing
        - bayesian_limits
        - unbounded_caveats
        - defence_routing
      thesis_delta: none | flagged
      owner: L1
    - term_group: physics-study shorthand
      defined_in_section: "1.1"
      terms: [pile-up / L11, V0 topology, K_S, Lambda, Sigma, TOF, TOF sidecar, Jeffreys prior, flat prior, prior sensitivity]
      source_plans: [50, 55, 58, 59, 61, 64]
      required_contexts: [defence_overlay, note_annex, glossary_audit]
      thesis_delta: none | flagged
      owner: L1
    - term_group: defence-workflow shorthand
      defined_in_section: "1.1"
      terms: [defence overlay, overlay roll-up, rerun transcript, command-template id, command-template verifier source, CLI verifier transcript, blocked template, stale package, defence routing]
      source_plans: [50, 51, 52, 53, 54, 55]
      required_contexts: [l1_overlay_rollup, reviewer_question_registry, rerun_transcript, command_template_registry, archive_inventory, note_annex]
      thesis_delta: none | flagged
      owner: L1
```

Audit review rules:

| Rule | Failure caught |
|---|---|
| every §1.1 term appears in the fixture as either a `term` row or a `term_group` member | glossary entry cannot be traced into defence evidence |
| every fixture term has at least one source plan | term is defined without an accountable plan owner |
| every `thesis_delta: flagged` row names a reviewer note | thesis-facing language diverges without explanation |
| `pass_* columns` always lists plan 37 | cut-flow terminology drifts away from the canonical selection plan |
| L1 terms list owner L1 | another lane accidentally owns EM/selection terminology |
| freshness and staleness terms cite plans 50, 53, 54, and 55 | package-state language drifts across defence, CI, archive, and note surfaces |
| L1 archive pack member row lists the same eight ids as plan 54 | glossary and CI describe a different freeze-package evidence set |
| command-template and verifier-hash terms cite plans 52 and 51 | reviewer answers drift away from the verified command registry |
| review-evidence and review-artifact terms cite plans 50, 51, 52, 53, 54, and 55 | machine-readable handoff language drifts across package, registry, rerun, CI, archive, and note surfaces |
| owner sign-off term cites plans 50, 51, and 55 | accountability language drifts between registry, package, and note surfaces |

The fixture is consumed by the plan-53 L1 CI checks and by the plan-55
internal note annex. A glossary change that updates prose but not this
fixture is treated as an incomplete defence-package edit.


### 3.2 L1 thesis-freeze term sign-off

At thesis freeze, L1 terms receive an explicit sign-off row so reviewer
language, internal-note language, and defence-package language stay
synchronized.

| Sign-off field | Meaning |
|---|---|
| `term` | exact glossary spelling used in §1.1 |
| `defence_package_refs` | plan-50 overlay ids that use the term |
| `note_refs` | plan-55 annex rows that expose the term to readers |
| `thesis_status` | `same`, `translated`, or `flagged_delta` |
| `approved_by` | L1 owner or Methodology Council delegate |

A `flagged_delta` is acceptable only when the plan-55 note annex carries
the same caveat text and the plan-50 overlay roll-up is not marked
`ready` without that caveat.

```yaml
l1_glossary_signoff:
  freeze_id: <thesis-freeze-id>
  selection_defence_refs: &selection_defence_refs [selection_cutflow_identity]
  selection_note_refs: &selection_note_refs [event_variable_and_cutflow_identity]
  l1_defence_refs: &l1_defence_refs [em_cluster_truth_blindness, pi0_cut_decomposition, selection_cutflow_identity, pileup_l11_status, strange_v0_contamination, tof_timing_resolution, bayesian_prior_sensitivity, unbounded_caveat_status]
  l1_note_refs: &l1_note_refs [em_object_chain, event_variable_and_cutflow_identity, pile_up_caveat, strange_background_caveat, timing_tof_cross_check, limit_convention_cross_check, unbounded_caveat_status, defence_routing]
  rows:
    - {term: pass_* columns, defence_package_refs: *selection_defence_refs, note_refs: *selection_note_refs, audit_row_ref: "l1_glossary_audit:pass_* columns", thesis_status: same | translated | flagged_delta, approved_by: <L1-owner-or-null>, caveat_text: <required when thesis_status is flagged_delta>}
    - {term: defence overlay, defence_package_refs: *l1_defence_refs, note_refs: *l1_note_refs, audit_row_ref: l1_glossary_audit:defence overlay, thesis_status: same | translated | flagged_delta, approved_by: <L1-owner-or-null>, caveat_text: <required when thesis_status is flagged_delta>}
    - {term: overlay roll-up, defence_package_refs: *l1_defence_refs, note_refs: *l1_note_refs, audit_row_ref: l1_glossary_audit:overlay roll-up, thesis_status: same | translated | flagged_delta, approved_by: <L1-owner-or-null>, caveat_text: <required when thesis_status is flagged_delta>}
    - {term: unbounded caveat status, defence_package_refs: [unbounded_caveat_status], note_refs: [unbounded_caveat_status], audit_row_ref: l1_glossary_audit:unbounded caveat status, thesis_status: same | translated | flagged_delta, approved_by: <L1-owner-or-null>, caveat_text: <required when thesis_status is flagged_delta>}
    - {term: L1 archive pack member, defence_package_refs: *l1_defence_refs, note_refs: *l1_note_refs, audit_row_ref: l1_glossary_audit:L1 archive pack member, thesis_status: same | translated | flagged_delta, approved_by: <L1-owner-or-null>, caveat_text: <required when thesis_status is flagged_delta>}
    - {term: defence routing, defence_package_refs: *l1_defence_refs, note_refs: [defence_routing], audit_row_ref: l1_glossary_audit:defence routing, thesis_status: same | translated | flagged_delta, approved_by: <L1-owner-or-null>, caveat_text: <required when thesis_status is flagged_delta>}
    - {term: rerun transcript, defence_package_refs: *l1_defence_refs, note_refs: *l1_note_refs, audit_row_ref: l1_glossary_audit:rerun transcript, thesis_status: same | translated | flagged_delta, approved_by: <L1-owner-or-null>, caveat_text: <required when thesis_status is flagged_delta>}
    - {term: command-template id, defence_package_refs: [em_cluster_truth_blindness, selection_cutflow_identity], note_refs: [em_object_chain, event_variable_and_cutflow_identity], audit_row_ref: l1_glossary_audit:command-template id, thesis_status: same | translated | flagged_delta, approved_by: <L1-owner-or-null>, caveat_text: <required when thesis_status is flagged_delta>}
    - {term: command-template verifier hash, defence_package_refs: [em_cluster_truth_blindness, selection_cutflow_identity], note_refs: [em_object_chain, event_variable_and_cutflow_identity], audit_row_ref: l1_glossary_audit:command-template verifier hash, thesis_status: same | translated | flagged_delta, approved_by: <L1-owner-or-null>, caveat_text: <required when thesis_status is flagged_delta>}
    - {term: command-template verifier source, defence_package_refs: [em_cluster_truth_blindness, selection_cutflow_identity], note_refs: [em_object_chain, event_variable_and_cutflow_identity], audit_row_ref: l1_glossary_audit:command-template verifier source, thesis_status: same | translated | flagged_delta, approved_by: <L1-owner-or-null>, caveat_text: <required when thesis_status is flagged_delta>}
    - {term: CLI verifier transcript, defence_package_refs: [em_cluster_truth_blindness, selection_cutflow_identity], note_refs: [em_object_chain, event_variable_and_cutflow_identity], audit_row_ref: l1_glossary_audit:CLI verifier transcript, thesis_status: same | translated | flagged_delta, approved_by: <L1-owner-or-null>, caveat_text: <required when thesis_status is flagged_delta>}
    - {term: blocked template, defence_package_refs: [pileup_l11_status, strange_v0_contamination, tof_timing_resolution, bayesian_prior_sensitivity, unbounded_caveat_status], note_refs: [pile_up_caveat, strange_background_caveat, timing_tof_cross_check, limit_convention_cross_check, unbounded_caveat_status], audit_row_ref: l1_glossary_audit:blocked template, thesis_status: same | translated | flagged_delta, approved_by: <L1-owner-or-null>, caveat_text: <required when thesis_status is flagged_delta>}
    - {term: review-evidence links, defence_package_refs: *l1_defence_refs, note_refs: *l1_note_refs, audit_row_ref: l1_glossary_audit:review-evidence links, thesis_status: same | translated | flagged_delta, approved_by: <L1-owner-or-null>, caveat_text: <required when thesis_status is flagged_delta>}
    - {term: review-artifact hashes, defence_package_refs: *l1_defence_refs, note_refs: *l1_note_refs, audit_row_ref: l1_glossary_audit:review-artifact hashes, thesis_status: same | translated | flagged_delta, approved_by: <L1-owner-or-null>, caveat_text: <required when thesis_status is flagged_delta>}
    - {term: owner sign-off, defence_package_refs: *l1_defence_refs, note_refs: *l1_note_refs, audit_row_ref: l1_glossary_audit:owner sign-off, thesis_status: same | translated | flagged_delta, approved_by: <L1-owner-or-null>, caveat_text: <required when thesis_status is flagged_delta>}
    - {term: package freshness, defence_package_refs: *l1_defence_refs, note_refs: *l1_note_refs, audit_row_ref: l1_glossary_audit:package freshness, thesis_status: same | translated | flagged_delta, approved_by: <L1-owner-or-null>, caveat_text: <required when thesis_status is flagged_delta>}
    - {term: stale package, defence_package_refs: *l1_defence_refs, note_refs: *l1_note_refs, audit_row_ref: l1_glossary_audit:stale package, thesis_status: same | translated | flagged_delta, approved_by: <L1-owner-or-null>, caveat_text: <required when thesis_status is flagged_delta>}
    - {term: stale-package caveat, defence_package_refs: *l1_defence_refs, note_refs: *l1_note_refs, audit_row_ref: l1_glossary_audit:stale-package caveat, thesis_status: same | translated | flagged_delta, approved_by: <L1-owner-or-null>, caveat_text: <required when thesis_status is flagged_delta>}
```

## 4. Acceptance criteria

- Every shorthand or acronym in the active plan set is defined, including
  L1 additions 58, 59, 61, and 64.
- §3 reconciliation with thesis glossary done at thesis-freeze.
- L1 terms receive the §3.2 sign-off row before a defence package is
  marked ready.
- Package freshness and stale-package caveat terms are covered by the
  glossary audit before any L1 note is promoted.
- Owner sign-off terminology is covered before a reviewer-question answer
  is marked answered.
- Review-evidence link terminology is covered before a package or registry
  answer is promoted as machine-readable.
- Review-artifact hash terminology is covered before rerun transcripts,
  CI reports, archive inventories, or note annexes are promoted.
- Command-template and verifier-hash terms are covered before any L1 rerun
  transcript is archived or cited by a reviewer-question answer.

## 5. Dependencies

- **00_README** — plan space.
- *Consumed by:* every plan, every note, every ledger row.

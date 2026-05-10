---
id: 24_reconstruction_question_tree
title: Reconstruction fundamental question tree
version: 0.1
status: draft
owner: Methodology Council
depends_on: [00_README, 01_realism_contract, 07_simulation_atomic_walkthrough, 08_reconstruction_atomic_walkthrough, 09_io_schema_data_dictionary]
inputs:
  - {path: docs/detector_fundamental_question_tree.md, schema: detector-side companion}
  - {path: NNBAR_Detector/docs/reconstruction.md, schema: implementation reference}
outputs:
  - {path: docs/rebuild_plans/24_reconstruction_question_tree.md, schema: this file}
  - {path: docs/reconstruction_fundamental_question_tree.md, schema: living tree (mirror)}
acceptance:
  - {test: every leaf has the answer-now / deeper-question / next-measurement triplet, method: tree review, pass_when: all leaves complete}
  - {test: every leaf names its inputs (Class A columns), decision rule, allowed truth use, outputs, downstream consumers, method: per-leaf review, pass_when: full coverage}
  - {test: every subsystem plan 25-37 cites the leaf identities defined here, method: cross-reference, pass_when: zero unmatched}
risks:
  - {risk: leaves get renamed during subsystem-plan writing → cascading rework, mitigation: this plan is signed before 25-37 start (00_README §2)}
  - {risk: tree completeness can never be proven, only refuted, mitigation: §10 reviewer challenge inviting new branches}
estimated_effort: L
last_updated: 2026-05-09
---

# Reconstruction fundamental question tree

*Charter.* Mirror `docs/detector_fundamental_question_tree.md` for
the reconstruction side. Decompose the reconstruction recursively
from the root question down to irreducible decisions ("leaves"). Every
subsystem plan 25–37 takes its scope from the leaves named here.

The tree is *prescriptive* about decomposition and *descriptive* about
the current code. Improvements live in the subsystem plans, scored
against the truth-substitution ladder (plan 38).

This plan also establishes the convention that no leaf may consume a
Class B (truth) column in its decision path (plan 01). Migration of
the existing Class B reads (plan 08 §3.7) is tracked as a per-leaf
exit criterion.

## 1. Root question

**Can this reconstruction prove an antineutron annihilation candidate
from detector observables alone, without using simulation truth?**

Answer now: not yet. The current code reads truth in several decision
paths (plan 08 §3.7). The licentiate-grade selection achieves about
70% signal acceptance with finite-sample zero cosmic survival, but
this rests on truth-aware reconstruction in places. Plan 47 ledger
must reproduce the licentiate first (with truth allowed where the
licentiate allowed it) and then re-quote with the truth-leakage
audit (plan 01) green.

Deeper question: which observables are essential rather than
convenient? Tree branches §2–§7 enumerate them.

## 2-6. Branch files

Detailed per-leaf branches are split out to keep plan 24 under the
500-line cap. The split files inherit the truth-leakage gate in §7,
the visual summary in §8, and the acceptance/dependency sections below.

| Branch | Leaves | Split file |
|---|---|---|
| §2 Vertex | V.1-V.5 | `docs/rebuild_plans/24_reconstruction_question_tree/24_2_vertex.md` |
| §3 Charged objects | C.1-C.6 | `docs/rebuild_plans/24_reconstruction_question_tree/24_3_charged.md` |
| §4 Photon / π⁰ | P.1-P.7 | `docs/rebuild_plans/24_reconstruction_question_tree/24_4_photon_pi0.md` |
| §5 Event variables | E.1-E.9 | `docs/rebuild_plans/24_reconstruction_question_tree/24_5_event_variables.md` |
| §6 Selection | S.1-S.6 | `docs/rebuild_plans/24_reconstruction_question_tree/24_6_selection.md` |

## 7. Truth-leakage gate (recursive predicate)

At every leaf in §2–§6, the audit asks:

> *Does this decision depend on a Class B column?*

The acceptable answers are:

- *No.* Production-ready leaf.
- *Yes, only inside a `@validation_only` decorated function.*
  Acceptable for scoring, never for selection.
- *Yes, but only as a sparse-table fallback when Class A inputs
  are unavailable.* Acceptable temporarily; tracked as a migration
  item.
- *Yes, in a production decision path.* **Audit failure.** The leaf
  is not signed off until it migrates.

Plan 01 §4 implements the audit. Plan 08 §3.7 lists the current
violations. Each violation has an exit criterion in the owning
subsystem plan.

## 8. Visualisation

```
Root: Can reconstruction prove n̄ annihilation from observables alone?
  ├── §2 Vertex                 (V.1 hits→tracks, V.2 direction,
  │                              V.3 foil projection, V.4 aggregation,
  │                              V.5 acceptance)              → plan 25
  ├── §3 Charged objects        (C.1 cand, C.2 dE/dx, C.3 range,
  │                              C.4 scint match, C.5 π/p decision,
  │                              C.6 rejection)               → plans 25, 27, 28, 29
  ├── §4 Photon / π⁰            (P.1 cluster, P.2 ch/n test,
  │                              P.3 direction, P.4 energy,
  │                              P.5 pairing, P.6 accidental,
  │                              P.7 kinematic fit)           → plans 31, 32, 33, 34, 35
  ├── §5 Event variables        (E.1-E.9)                     → plan 36
  ├── §6 Selection              (S.1-S.6)                     → plan 37
  └── §7 Truth-leakage gate     (recursive at every leaf)     → plan 01 audit
```

(Per 00_README §4.7 numbering: plan 31 is cluster, 32 shower shape,
33 photon object, 34 π⁰ pairing, 35 kinematic fit, 36 event
variables, 37 event selection.)

## 9. Acceptance criteria

- §2–§7 are populated with the leaf identities listed.
- Subsystem plans 25–37 cite the leaf identities (V.1, C.2, P.5,
  …) verbatim and their per-leaf input/output/decision schemas
  populate the templates here.
- Plan 38 truth-substitution ladder uses the leaf identities as
  rungs.
- Plan 47 reproduction ledger cites leaf identities in its method
  column.

## 10. Reviewer challenge

This tree is signed off only after a reviewer has tried to find a
reconstruction decision that does not fit any leaf above. New leaves
identified by review become signed §2–§6 revision additions.

## 11. Risks and mitigations

- *Risk:* leaf renames after subsystem plans land cascade rework.
  *Mitigation:* this plan is signed before 25–37 start; renames
  require a paired DEC entry and revisions to all citing plans.
- *Risk:* tree drifts from code as reconstruction.py evolves.
  *Mitigation:* plan 53 CI rule: edits to public reconstruction
  functions trigger a check that this tree is updated.
- *Risk:* truth-leakage audit becomes too strict and breaks legacy
  studies.
  *Mitigation:* §7 acceptable-answers ladder; sparse-table
  fallbacks remain allowed during migration.

## 12. Dependencies

- **00_README** — plan space.
- **01_realism_contract** — Class A/B/C scheme; §7 audit gate.
- **07, 08** — simulation/reconstruction baselines.
- **09** — column classifications used in per-leaf input lists.
- *Consumed by:* plans 25, 27–37, 38 (rungs), 47 (ledger method),
  50 (defence package).

## 13. References

- `docs/detector_fundamental_question_tree.md` — direct template.
- `NNBAR_Detector/docs/reconstruction.md` — implementation reference
  this tree decomposes.

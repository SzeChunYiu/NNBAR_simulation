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

The annex is not a substitute for the defence package. It is the note
reader's compact route map to the exact package fields that answer the
foreseeable EM/selection examiner questions.

## 2. Plan vs note separation

- A *plan* describes intent, gates, ownership, acceptance criteria.
  Long-lived; revised as the rebuild evolves.
- A *note* describes a finished result. Frozen at the time of
  writing; updates trigger a v2 note.

A note that re-derives plan content is duplicative; instead, notes
cite plans by ID.

## 3. Acceptance criteria

- §1 template lives at `docs/notes/_template.md`.
- First three notes drafted: licentiate Ch 6 reproduction, Ch 8 π⁰
  reproduction, Ch 10 selection reproduction.

## 4. Dependencies

- **00_README** — plan space.
- *Consumed by:* every result-quoting deliverable; thesis chapter
  drafting.

## 5. References

- ATLAS internal-note format precedent.

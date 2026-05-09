---
id: 51_reviewer_question_registry
title: Reviewer-question registry — living, append-only
version: 0.1
status: draft
owner: Reproducibility WG
depends_on: [00_README, 50_reviewer_defense_package]
outputs:
  - {path: docs/rebuild_plans/51_reviewer_question_registry.md, schema: this file}
  - {path: docs/reviewer_question_registry.md, schema: living registry}
acceptance:
  - {test: each question has owner, status, mapped gate(s), date asked, asker, method: registry review, pass_when: full coverage}
  - {test: every question that affects an existing result triggers a defence-package update, method: §3 cross-check, pass_when: zero stale packages}
risks:
  - {risk: questions accumulate without resolution, mitigation: §4 escalation policy}
estimated_effort: S
last_updated: 2026-05-09
---

# Reviewer-question registry

*Charter.* Append-only list of every question asked by supervisors,
examiners, collaborators, and referees. Each question routes to the
gate(s) that should already have answered it, or motivates a new
gate. The registry is the operational definition of "leave no
question to ask."

## 1. Entry schema

```yaml
- id: RQ-YYYY-MM-DD-N
  asked_by: <name or role>
  asked_on: YYYY-MM-DD
  question: <verbatim>
  category: realism | reproducibility | systematics | physics | method | scope | other
  affects_results: [LIC-CH10-NUM-1, ...]   # ledger rows
  routes_to_gate: [01 (realism), 38 (ladder), 47 (ledger), ...]
  status: open | answered | clarified | rejected
  answer:
    summary: <one paragraph>
    artifact: <path to defence package or new plan section>
  defense_package_updated: [LIC-CH10-NUM-1, ...]
  resolved_on: YYYY-MM-DD
```

## 2. Seed entries (v0.1)

If the user has written feedback from the licentiate defence, those
become the seed entries verbatim. Pending the user's input on
00_README §11 open question 1.

Stub entries (codex-supervisor populates as the registry grows):

```
RQ-2026-05-09-1: How is "no surviving cosmic" interpreted as a rate?
  → routed to plan 04 §5, plan 21 §4. Answered: F-C 90% C.L. upper limit.
RQ-2026-05-09-2: Why FTFP_BERT without _HP for the signal sample?
  → routed to plan 12 §2. Answered: HP slows down a lot; not relevant
    at signal scale; HP retained for cosmic/beam-neutron samples.
RQ-2026-05-09-3: Why W-value 23.6 eV when reference is 26-27.4 eV?
  → routed to plan 17 §3. Answered pending DEC.
```

## 3. Update protocol

1. New question logged.
2. Routed to existing gate or new plan section.
3. Plan section updated if the question reveals a gap.
4. Defence packages affected (per §1 `affects_results`) are
   regenerated.
5. Status flipped to `answered` only after the asker confirms
   resolution.

## 4. Escalation

A question open for > 30 days without progress is escalated to the
Methodology Council monthly review (plan 06 §5). Council ranks
questions by impact (results affected × asker authority) and assigns
an owner.

## 5. Acceptance criteria

- §1 schema instantiated.
- §2 seed entries (or licentiate-feedback verbatim if available).
- §3 update protocol implemented; plan 53 CI regenerates affected
  defence packages on registry edit.
- §4 escalation tracked in plan 06 meeting log.

## 6. Risks

- *Risk:* questions go stale silently.
  *Mitigation:* §4 30-day escalation; monthly council review.
- *Risk:* registry becomes a critique journal, not an action list.
  *Mitigation:* §1 `routes_to_gate` field forces every entry to be
  actionable.

## 7. Dependencies

- **50** — defence packages updated by registry events.
- *Consumed by:* plan 06 (governance escalation), every plan that
  receives a routed question.

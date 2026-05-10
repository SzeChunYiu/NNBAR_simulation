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


### 2.1 L1 EM/selection A+ seed entries

Wave-4 L1 adds the following anticipated examiner questions so the
defence package can route EM-object, event-selection, pile-up, strange,
TOF, and Bayesian-limit challenges before a reviewer asks them. These
entries are seed rows for the living registry; each one must become a
full YAML row under `docs/reviewer_question_registry.md` when a concrete
ledger result cites the affected plan.

| Seed id | Anticipated question | Category | Routes to gate | Required answer artifact | Initial status |
|---|---|---|---|---|---|
| `RQ-L1-EM-P1-CLUSTERING` | How do we know the neutral-shower clusterer is not using truth Track_ID grouping? | realism | plans 31, 38, 57 | Class-B drop hash plus P.1 closure rows | open until measured |
| `RQ-L1-EM-P2-DISCRIMINANT` | Is the charged/neutral discriminator calibrated, or just a hard-cone reproduction rule? | method | plans 32, 38, 57 | ROC/AUC bundle, threshold DEC, and calibration artifact | open until closure |
| `RQ-L1-PI0-CUTS` | Are the six pi0 selection cuts decomposed into individual pass columns? | reproducibility | plans 34, 37, 47 | per-cut fixture and Ch 8/Ch 10 ledger row | answered by plan schema, pending data |
| `RQ-L1-SELECTION-CUTFLOW` | Does the Ch 10 cut-flow use the current canonical singular `pass_*` columns? | reproducibility | plans 37, 47 | cut-flow identity table and cumulative-count artifact | answered by plan 37, pending ledger |
| `RQ-L1-PILEUP-L11` | Can signal plus cosmic or beam pile-up change the quoted acceptance? | systematics | plans 01, 58, 44, 45 | paired overlay closure and L11 caveat status | open until plan 58 closure |
| `RQ-L1-STRANGE-BARYON` | Could K_S, Lambda, or Sigma production in beam-neutron material fake the signal? | physics | plans 14, 22, 44, 59 | Lambda-enriched V0 rejection closure and residual interval | open until enriched slice exists |
| `RQ-L1-TOF` | Does timing add real cosmic rejection once detector resolution is included? | method | plans 36, 41, 45, 61 | TOF ROC, nonzero resolution budget, and signal-loss interval | open until closure |
| `RQ-L1-BAYES-LIMIT` | Are low-count limits stable under Jeffreys vs flat Bayesian priors? | method | plans 04, 46, 64 | prior-sensitivity table and plan-46 comparison ratios | open until statistics code lands |
| `RQ-L1-UNBOUNDED-CAVEATS` | Which EM/selection claims still depend on unbounded limitations rather than numeric nuisances? | systematics | plans 01, 45, 50 | defence-package caveat block per affected result | open until plan 50 packages exist |

A seed row is not considered answered merely because a plan mentions it.
It is answered only when the required artifact exists, cites the relevant
ledger row, and the defence package records the same status.

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

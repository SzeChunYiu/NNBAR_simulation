---
id: 49_targeted_improvements
title: Targeted improvements — protocol and selection
version: 0.1
status: draft
owner: Methodology Council
depends_on: [00_README, 38_truth_substitution_ladder, 47_reproduction_ledger, 48_prior_art_survey]
outputs:
  - {path: docs/rebuild_plans/49_targeted_improvements.md, schema: this file}
acceptance:
  - {test: improvement proposals cite a leaf, a prior-art candidate, and an expected ladder delta, method: per-proposal review, pass_when: signed by Methodology Council}
  - {test: every accepted improvement is scored on the ladder before/after, method: plan 38 matrix delta, pass_when: matrix entry recorded}
  - {test: no accepted improvement regresses any green ledger row, method: plan 47 cross-check, pass_when: zero regressions}
risks:
  - {risk: improvement proposals proliferate, mitigation: §2 prioritisation by ladder dominance}
  - {risk: improvement breaks reproduction of a thesis number, mitigation: §3 ledger non-regression rule}
estimated_effort: M
last_updated: 2026-05-09
---

# Targeted improvements protocol

*Charter.* Improvements to the reconstruction are not free-form. Each
proposal must cite a leaf identified by the ladder as a dominant
contributor, propose a method (often from plan 48), be scored
before/after on the same ladder, and not regress any green row in
plan 47. This plan is the gate.

## 1. Proposal template

```yaml
id: IMP-2026-XX-XX-N
proposed_by: <author>
target_leaf: V.4   # or P.4, S.6, etc.
ladder_dominance: <IV(L) value from plan 38 matrix>
proposed_method: <name; cite plan 48 if borrowed>
expected_ladder_delta: <projected IV(L) reduction>
implementation_plan: <which plan(s) get edited; new file paths>
risk: <what could regress>
acceptance:
  - ladder IV(L) reduces by ≥ X
  - plan 47 ledger zero red rows
status: draft | accepted | rejected | implemented
decision_log: [DEC-YYYY-MM-DD-N]
```

## 2. Prioritisation

Improvements are ranked by `IV(L)` from the ladder (plan 38). The
top three IV(L) leaves are the priority queue.

If two leaves are tied, prefer the one closer to the analysis output
(downstream) because its improvement has fewer cascading consequences.

## 3. Non-regression rule

An accepted improvement must:

1. Pass plan 38 ladder rerun: `IV(L)` after ≤ `IV(L)` before − Δ
   (the proposed reduction).
2. Pass plan 47 ledger rerun: zero green rows turn red. Yellow rows
   may stay yellow (the improvement must not increase the drift).
3. Pass plan 53 CI: no test regressions.

A failure on any of (1)–(3) reverts the change.

## 4. Acceptance criteria

- §1 template exists; first three improvements drafted (vertex
  fit, photon kinematic fit, charged PID likelihood per plan 24's
  expected dominance).
- §2 priority queue refreshed on every plan-38 ladder run.
- §3 non-regression enforced by plan 53 CI.

## 5. Risks

- *Risk:* proposals based on conjecture not on ladder evidence.
  *Mitigation:* §1 `ladder_dominance` field is mandatory; proposals
  without ladder support are rejected without review.

## 6. Dependencies

- **38, 47, 48** — inputs.
- *Consumed by:* every improvement-class plan revision.

# Paper section 9 — Conclusion and future work evidence plan

Status: **BLOCKED**

This specification defines how the conclusion and future-work section must stay
bounded by measured evidence and documented blockers.

## Section purpose

Section 9 summarizes verified outcomes, negative results, and future directions
without upgrading L0/L1 scaffolds into measured claims.

## Required evidence before prose can be drafted

- The conclusion lists only results with claim levels supported elsewhere in the
  paper.
- Negative, neutral, and parity-fail outcomes are acknowledged.
- Future work references planned phases, scope-extension specs, or blocker rows.
- No future-work item is described as already achieved unless the corresponding
  MASTER_PLAN row and harness evidence support it.

## Figures and tables

- Table 9.1: milestone gate status at paper freeze.
- Table 9.2: future-work items with prerequisite evidence and expected claim
  level.

## Current gaps

- OPEN: `milestone_gates_open` — all paper-methodology milestone gates remain
  unchecked.
- OPEN: `future_work_scope_unranked` — Phase 6/7/8/9/10 and competitor baselines
  are not ranked by evidence readiness.
- OPEN: `negative_results_summary_missing` — neutral/regression/parity-fail rows
  do not exist yet.

## Acceptance checklist

- [ ] Conclusions cite only supported claim levels.
- [ ] Negative and blocked results are summarized fairly.
- [ ] Future work maps to explicit specs or MASTER_PLAN rows.

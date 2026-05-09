---
id: 41_n_minus_1_and_roc_studies
title: N-1 plots and ROC studies for selection optimisation
version: 0.1
status: draft
owner: Analysis WG
depends_on: [00_README, 04_statistical_uncertainty, 36_subsystem_event_variables, 37_subsystem_event_selection]
outputs:
  - {path: docs/rebuild_plans/41_n_minus_1_and_roc_studies.md, schema: this file}
  - {path: output/studies/n_minus_1/, schema: per-cut N-1 plots}
  - {path: output/studies/roc/, schema: per-variable ROC plots}
acceptance:
  - {test: N-1 plot produced for every cut in plan 37 §1, method: per-cut review, pass_when: full coverage}
  - {test: ROC produced for every continuous variable in plan 36 §2, method: per-variable review, pass_when: full coverage}
  - {test: optimal-cut suggestion produced with explicit objective, method: §3 deliverable, pass_when: signed in DEC}
risks:
  - {risk: optimisation overfits to the regenerated sample's statistical fluctuation, mitigation: §3 train/validation/test split per plan 04}
estimated_effort: M
last_updated: 2026-05-09
---

# N-1 plots and ROC studies for selection optimisation

*Charter.* For every selection cut and every continuous selection
variable, produce the standard discrimination diagnostics. These
feed plan 37 (selection) reproduction and any future cut-optimisation
proposal.

## 1. N-1 plots

For every cut C in plan 37 §1:

1. Apply all *other* cuts.
2. Plot the distribution of the variable C operates on, for signal
   sample (plan 20) and each background (cosmic plan 21, beam
   neutron plan 22).
3. Annotate the cut value and the resulting acceptance / rejection.

N-1 plots reveal which cut does the heaviest lifting and which is
nearly redundant given the others.

## 2. ROC curves

For every continuous variable V in plan 36 §2:

1. Vary V's threshold across its support.
2. Plot signal acceptance vs background rejection (per background
   sample).
3. Compute the AUC.
4. Mark the licentiate cut value on the curve.

ROC curves reveal whether the licentiate's hand-tuned cut sits at the
ROC's knee or could be relaxed/tightened.

## 3. Optimal cut search

A cut tuple `(t_1, …, t_n)` is "optimal" only relative to an
objective. Plan 41 names the objective in a DEC entry:

| Candidate objective | Definition |
|---|---|
| **Significance Z₀** | `s / √b` over the signal box |
| **F1** | balanced precision/recall |
| **Punzi figure** | `s / (a/2 + √b)` for a target Z = a |
| **Fixed acceptance** | maximise rejection at fixed signal acceptance |

Search uses train/validation/test split (plan 04 §2): tune on
validation, freeze, evaluate on test. Reporting the test-set value
is the only valid quote.

## 4. Acceptance criteria

- §1 N-1 plots complete for plan 37 cuts.
- §2 ROC curves complete for plan 36 continuous variables.
- §3 objective signed in DEC; optimal tuple reported on test set.

## 5. Risks and mitigations

- *Risk:* the licentiate cuts are already near-optimal; the
  optimisation reports a ≤ 1% gain that statistical fluctuation
  obscures.
  *Mitigation:* report bootstrap uncertainty (plan 04 §2) on the
  optimum so improvements within statistical noise are not promoted.

## 6. Dependencies

- **04** — uncertainty machinery.
- **36, 37** — variables and cuts.
- *Consumed by:* plan 37 (cut tuning), plan 47 (ledger), plan 50.

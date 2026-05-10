---
id: 49_targeted_improvements
title: Targeted improvements — protocol and selection
version: 0.2
status: draft
owner: Methodology Council
depends_on: [00_README, 01_realism_contract, 02_digitization_seam, 38_truth_substitution_ladder, 47_reproduction_ledger, 48_prior_art_survey, 57_mva_method_protocol]
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
last_updated: 2026-05-10
---

# Targeted improvements protocol

*Charter.* Improvements to the reconstruction are not free-form. Each
proposal must cite a leaf identified by the ladder as a dominant
contributor, propose a method from plan 48 or a named realism upgrade,
be scored before/after on the same ladder, and not regress any green
row in plan 47. This plan is the gate that turns the rebuild from
thesis reproduction into controlled post-thesis improvement.

The default answer to an improvement request is **not accepted yet**.
A proposal becomes accepted only after the Methodology Council records
the leaf, source method, closure dataset, expected ladder delta,
non-regression guard, and decision-log entry.

## 1. Proposal schema

Each proposal is stored as a small YAML/Markdown block in the decision
packet that approves it. The schema below is normative; all fields are
required unless explicitly marked optional.

```yaml
id: IMP-YYYY-MM-DD-N
status: draft | accepted | rejected | implemented | retired
proposed_by: <author or lane>
owner_wg: <Tracking POG | Charged-PID POG | EM-Object POG | Combined Performance | Analysis WG | Sim Production | Software Quality>
target_leaf: <plan-24 leaf id, e.g. V.4, C.5, S.6>
upgrade_class: algorithm | digitisation_realism | simulation_realism | analysis_cross_check | software_quality
source_method: <plan-48 row, realism limitation, or named follow-up plan>
source_citation: <plan id / prior-art key / limitations-registry id>
current_baseline: <the frozen reproduction method or limitation being improved>
expected_ladder_delta: <qualitative until plan 38 has numeric IV(L) rows>
closure_dataset: <dataset id from plan 03 or named calibration slice>
closure_observable: <single observable or artifact row>
pass_criterion: <numerical criterion or named closure-table row>
production_truth_boundary: <none | validation_only | diagnostic_only | labeling>
ledger_guard: <plan-47 row(s) that must not regress>
ci_guard: <plan-53 job or explicit verifier>
decision_log: [DEC-YYYY-MM-DD-N]
rollback_rule: <what reverts the improvement>
```

### 1.1 Review checklist

1. The target leaf appears in plan 24 and has a plan 38 ladder row.
2. The source method is listed in plan 48 or the upgrade maps to a
   named limitation in plan 01 §6.
3. The closure dataset and observable are already owned by a plan, or
   the proposal is rejected as premature.
4. The proposal declares whether it touches reconstruction algorithms,
   digitisation, simulation, analysis-only cross-checks, or CI.
5. The proposal records a plan 05 decision before any implementation
   patch lands.
6. The proposal records a rollback rule before any implementation patch
   lands.

## 2. Prioritisation and acceptance gates

Improvements are ranked by `IV(L)` from the ladder in plan 38. The top
three dominant leaves are the default queue. If two leaves are tied,
prefer the one closer to the final analysis output because downstream
improvements usually expose fewer hidden dependencies.

A proposal may bypass the top-three queue only when one of the following
A+ gates applies:

| Gate | When it applies | Required evidence |
|---|---|---|
| reproduction blocker | a plan 47 row cannot turn green without the upgrade | failed ledger row plus minimal diff plan |
| realism blocker | plan 01 §6 limitation dominates a quoted result | limitations ID, affected result, and digitisation/simulation owner |
| safety blocker | current method risks truth leakage or non-reproducibility | realism audit finding or plan 38 C.1/C.2 failure |
| reviewer blocker | plan 50 reviewer defence needs an explicit cross-check | reviewer question ID and analysis-only artifact |

Accepted improvements are implemented one at a time. Bundling is
allowed only when the same patch produces the same closure artifact and
rollback unit.

## 3. Non-regression rule

An accepted improvement must pass all of the following before promotion:

1. **Ladder delta.** The target `IV(L)` after the change is no worse
   than before and meets the proposal's declared expected delta.
2. **Ledger guard.** No green plan-47 reproduction row turns red. Yellow
   rows may stay yellow, but their drift must not increase.
3. **Closure guard.** The named closure observable passes the pass
   criterion in the proposal packet.
4. **CI guard.** Plan 53 CI and any proposal-specific verifier pass.
5. **Decision-log guard.** The decision-log entry states whether the
   improvement is promoted, rejected, or held as analysis-only.

A failure on any guard reverts or quarantines the improvement. A
quarantined method may remain as a study artifact, but it cannot change
production reconstruction or quoted thesis numbers.

## 4. Post-thesis upgrade catalogue

The rebuild enables upgrades that were not safe to do in the original
thesis workflow because the old code mixed reconstruction, truth labels,
and analysis bookkeeping. The catalogue below names the upgrades that
are now explicitly allowed to compete for proposal status.

| Upgrade | Class | Primary leaves / plans | What the rebuild enables | First gate before acceptance |
|---|---|---|---|---|
| TPC position/timing/energy realism | digitisation_realism | V.1-V.5, C.1-C.3, P.3-P.4; plans 01/02 | plan 02 seam can inject smearing, jitter, thresholds, non-linearity, dead channels, gain dispersion, and optical-photon response without editing reconstruction algorithms | choose one plan-01 limitation L1-L4/L10/L12 and close it with identity-vs-realism hashes plus closure tables |
| MCPL beam ingestion | simulation_realism | sample-generation and beam-interface plans, plus S.6/43 | a registered external beam particle list can become a frozen sample input instead of a hand-written generator assumption | dataset registry entry, generator hash, and plan 43 efficiency comparison against the current beam model |
| Trigger / DAQ realism | simulation_realism | S.1, S.6, plans 01/02/53 | plan 01 L5 names DAQ dead-time/buffer/trigger absence; plan 02 keeps it outside digitisation so it can be added as a simulation-side stage | a separate trigger/DAQ plan with live-time denominator and no reconstruction-side shortcuts |
| Pile-up overlay | simulation_realism | all object leaves plus S.6; plan 58 | plan 58 defines overlay timing, occupancy, and acceptance-shift closure instead of treating pile-up as prose | paired signal/cosmic overlay closure and explicit plan 45 nuisance row |
| MVA discriminants | algorithm | C.5/C.6, P.2/P.6, S.6; plan 57 | plan 57 supplies feature-schema, train/validation/test, overtraining, and inference-schema gates | feature schema DEC entry plus frozen test split and calibration curve |
| Strange-baryon contamination controls | analysis_cross_check | V.4, C.5/C.6, S.2/S.6; plan 59 | plan 59 defines displaced-V0 and contamination-yield checks for beam-neutron interactions | Lambda-enriched closure slice and contamination summary artifact |
| Time-of-flight discrimination | algorithm | E.8, S.1/S.6; plan 61 | plan 61 turns timing into an explicit score with invalid-case handling | timing-resolution budget and cosmic-vs-signal closure |
| Bayesian limit cross-check | analysis_cross_check | S.6, plan 64 | plan 64 provides an independent low-count result check without changing the primary frequentist quote | prior-sensitivity table and agreement/disagreement policy |
| Adaptive vertex fit | algorithm | V.4/V.5; plans 30/48 | plan 48 identifies adaptive vertex fitting as a weighted aggregation candidate | vertex residual closure on signal and calibration slices |
| dE/dx truncated mean / PID likelihood | algorithm | C.2/C.5/C.6; plans 27/29/48/57 | plan 48 names robust dE/dx and classifier families while plan 57 prevents truth leakage | Bethe-Bloch closure plus PID calibration and no-regression cut-flow |

## 5. Seed proposal queue

The entries below are **draft seeds**, not accepted improvements. They
exist so the Methodology Council can choose the first real proposal
without re-discovering the upgrade space.

| Seed id | Target leaf | Candidate | Source | Expected gain | Blocking evidence needed |
|---|---|---|---|---|---|
| IMP-SEED-TPC-REALISM | V.1-V.5 / C.2 / P.4 | one digitisation plug-in for L1/L2/L3/L4/L10/L12 | plans 01/02 | converts exact-MC observables into versioned realism systematics | choose a single limitation and produce identity-vs-plug-in closure |
| IMP-SEED-MCPL-BEAM | S.6 / plan 43 | MCPL beam-particle ingestion | sample-generation plans plus plan 43 | replaces hand-coded beam assumptions with registered beam input | dataset registry row and efficiency comparison |
| IMP-SEED-DAQ | S.1/S.6 | trigger/readout/dead-time model | plan 01 L5; plan 02 out-of-scope boundary | exposes live-time denominator and high-rate failure modes | new simulation-side plan and DQM interface |
| IMP-SEED-PILEUP | all object leaves / S.6 | cosmic+signal overlay | plan 58 | quantifies ESS-intensity occupancy and acceptance shift | paired overlay closure artifact |
| IMP-SEED-MVA-PID | C.5/C.6 | calibrated PID score | plans 48/57 | may reduce truth-substitution and threshold brittleness | fixed feature schema, no-truth inference audit, test-split calibration |
| IMP-SEED-TOF | E.8/S.6 | time-of-flight discriminator | plan 61 | rejects cosmic-like timing with explicit invalid-state handling | timing-resolution budget and closure table |
| IMP-SEED-V0 | C.6/S.2/S.6 | strange-baryon V0 veto | plan 59 | protects against beam-neutron strange-baryon contamination | Lambda-enriched closure and systematics row |
| IMP-SEED-BAYES | S.6/reporting | Bayesian limit cross-check | plan 64 | strengthens reviewer defence without changing primary selection | prior-sensitivity table and comparison note |

## 6. Decision packet template

When a seed becomes a real proposal, the decision packet must contain:

1. **Problem statement.** One paragraph naming the result, leaf, and
   limitation/ladder entry that motivates the work.
2. **Baseline artifact.** Hash or manifest of the current reproduction
   output to protect plan 47.
3. **Method source.** Plan 48 prior-art row, plan 01 limitation, or the
   dedicated follow-up plan that defines the method.
4. **Implementation scope.** Exact owner lane/repo and disjoint writable
   files. If it crosses lane boundaries, the proposal waits for human
   coordination.
5. **Validation artifact.** Closure dataset, observable, fitter or
   estimator, and pass/fail criterion.
6. **Promotion rule.** What changes if the method passes; what remains
   analysis-only if it fails.
7. **Rollback rule.** How to revert the change without corrupting
   registry, ledger, or decision-log state.

## 7. Governance boundaries

- **Digitisation realism** closes plan 01 limitations through plan 02's
  seam and must preserve a no-op default configuration.
- **Simulation realism** changes generator, beam, DAQ, or pile-up inputs
  and therefore must update the dataset registry before reconstruction
  consumes new samples.
- **Algorithmic reconstruction** changes a plan-24 leaf implementation
  and must rerun the leaf closure plus downstream ledger guard.
- **MVA upgrades** are algorithmic upgrades with extra plan 57 lifecycle
  gates. They are not allowed to become opaque replacements for the
  cut-based reproduction baseline.
- **Analysis cross-checks** may add reviewer confidence but cannot
  silently change the primary quoted result.

## 8. Acceptance criteria

- §1 schema and §6 packet template are complete enough to review a real
  improvement without extra process design.
- §4 explicitly lists the post-thesis upgrades enabled by the rebuild:
  TPC realism, MCPL beam ingestion, DAQ realism, pile-up overlay, and
  MVA discriminants.
- §4 and §5 cross-reference plan 01 §6 limitations, plan 02's
  digitisation seam, plan 57's MVA protocol, and plans 58/59/61/64.
- Every accepted future improvement has a plan 05 decision-log entry,
  a plan 38 ladder comparison, a plan 47 no-regression guard, and a
  rollback rule.

## 9. Risks

- *Risk:* proposals based on conjecture, not evidence. *Mitigation:* the
  ladder/limitation field is mandatory and proposals without evidence
  are rejected before implementation.
- *Risk:* realism work bypasses reconstruction audits. *Mitigation:*
  digitisation and simulation realism have separate classes and owners.
- *Risk:* an MVA outperforms only on a validation split. *Mitigation:*
  plan 57 requires frozen train/validation/test splits and calibration
  checks before promotion.
- *Risk:* analysis cross-checks drift into primary results. *Mitigation:*
  §7 says cross-checks are reviewer support unless a decision packet
  explicitly promotes them through all gates.

## 10. Dependencies

- **01** — limitations L1-L12 define realism blockers.
- **02** — digitisation seam and plug-in slots.
- **38** — ladder dominance and before/after scoring.
- **47** — reproduction ledger non-regression guard.
- **48** — prior-art source catalogue.
- **57** — MVA feature-schema and lifecycle discipline.
- **58, 59, 61, 64** — named post-thesis upgrade/cross-check plans.
- *Consumed by:* every improvement-class plan revision and plan 50
  reviewer-defence updates.

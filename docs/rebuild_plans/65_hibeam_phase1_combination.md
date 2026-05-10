---
id: 65_hibeam_phase1_combination
title: HIBEAM Phase-1 combination — vertex-only result and NNBAR joint limit
version: 0.1
status: draft
owner: Analysis WG
depends_on: [04_statistical_uncertainty, 16_geometry_and_alignment, 17_field_calibration, 43_signal_efficiency, 45_systematics_taxonomy, 46_significance_protocol, 47_reproduction_ledger, 63_calibration_drift_monitoring]
inputs:
  - {path: docs/rebuild_plans/43_signal_efficiency.md, schema: signal-efficiency factorisation}
  - {path: docs/rebuild_plans/45_systematics_taxonomy.md, schema: nuisance/correlation registry}
  - {path: docs/rebuild_plans/46_significance_protocol.md, schema: limit/significance convention}
  - {path: docs/rebuild_plans/63_calibration_drift_monitoring.md, schema: calibration-drift contract}
outputs:
  - {path: docs/rebuild_plans/65_hibeam_phase1_combination.md, schema: this file}
  - {path: data/registry/combination/phase1_phase2_<tag>.yml, schema: planned combination registry}
acceptance:
  - {test: Phase-1 result format is explicit and vertex-only, method: §1 schema review, pass_when: no calorimeter/PID fields are required}
  - {test: Phase-1/Phase-2 combination likelihood separates shared and unshared nuisances, method: §3 table, pass_when: every nuisance has a correlation class}
  - {test: blinding rule prevents Phase-2 tuning on Phase-1 observed counts, method: §4 review, pass_when: observed fields are sealed until freeze}
  - {test: no Phase-1 data file is hallucinated, method: §8 verifier, pass_when: Phase-1 inputs are schema targets until supplied}
risks:
  - {risk: Phase-1 vertex-only result is over-weighted relative to Phase-2 full detector, mitigation: likelihood uses per-phase efficiencies and nuisance correlations}
  - {risk: shared beam/systematic assumptions cause double counting, mitigation: §3 correlation classes and plan 45 single-source rule}
estimated_effort: L
last_updated: 2026-05-10
---

# HIBEAM Phase-1 combination

*Charter.* Define how a HIBEAM Phase-1 vertex-only result can be
reported by itself and later combined with a Phase-2 NNBAR result. The
plan is intentionally schema-first because no source-backed Phase-1
result file is present in this repository today.

The combination must not let Phase-1 observed counts tune Phase-2
selections. Phase-1 can constrain shared nuisances only through a
pre-declared likelihood and a signed unblinding protocol.

## 0.1 Wave 6 derivation — joint likelihood and blinding

### Physics derivation

**What is physically measured.** The Phase-1/Phase-2 combination
measures one common neutron-antineutron signal-strength parameter using
two detector configurations with different efficiency, background, and
calibration information. Phase 1 contributes a vertex-only TPC count
experiment; Phase 2 contributes the fuller NNBAR detector result. The
ground-truth statistical object is the per-phase likelihood plus the
nuisance correlation model, not a merged event sample.

**Estimator rationale.** A product likelihood is the appropriate
combination estimator because Phase-1 and Phase-2 observations are
statistically distinct while some nuisance parameters are shared
`\cite{Cowan:2011Likelihood}`. Shared beam flux and annihilation-model
terms should be represented once; detector-specific efficiencies and
calibrations should remain phase-specific or partially correlated.
Blinding protects the estimator from selection bias: observed counts
are sealed until selections, nuisance classes, and method-dispatch
rules are frozen.

**Statistical character.** Expected limits depend on efficiency,
background, exposure, and nuisance priors. Observed limits add
Poisson/counting variance and are valid only after unblinding. The main
systematic risk is correlation misclassification: treating a shared
nuisance as independent double-counts information, while treating
phase-specific detector effects as shared can over-constrain the joint
limit.

### Logic gaps

- **Confidence levels 90% and 95%.** Grounding: §1/§2 follow plan 46
  conventions. `OPEN:` ensure plan 46 carries the final Feldman-Cousins
  or likelihood-reference citation and method dispatch before quoting a
  combined observed limit; target resolution date 2026-06-22.
- **Low-count dispatch threshold (`n_obs <= 5` or `b <= 5`).**
  Grounding: registry schema mirrors plan 46. `OPEN:` lock the
  threshold in plan 46/05 before a real Phase-1 packet is combined;
  target resolution date 2026-06-22.
- **Nuisance correlation classes.** Grounding: §3 table is the v0.1
  policy. `OPEN:` validate every nuisance id against plan 45 and add
  correlation coefficients or shared-prior definitions where "partially
  shared" is used; target resolution date 2026-06-29.
- **Blinding state.** Grounding: §4 requires sealed observed counts
  until freeze. `OPEN:` attach Methodology Council freeze/unblind DEC
  ids to the registry before any observed limit is reported; target
  resolution date 2026-06-29.
- **Missing Phase-1 packet.** Grounding: §8 verifier finds no
  source-backed data packet. `OPEN:` require a hashed Phase-1 result
  packet and schema validation before plan-47 rows can quote more than
  expected limits; target resolution date 2026-06-29.

### Closure test for the derivation

1. Build two toy packets: Phase 1 vertex-only and Phase 2 full-detector,
   both with expected counts and sealed observed counts.
2. Validate that the combination registry rejects Phase-2-only detector
   fields in the Phase-1 packet and rejects any nuisance lacking a
   correlation class.
3. Compute expected limits with shared and unshared nuisance settings,
   verifying that shared nuisance priors are applied once in the joint
   likelihood.
4. Attempt an observed-limit calculation with `n_observed: sealed` and
   require failure. Only after a freeze/unblind decision can observed
   counts propagate to plan 47.

## 1. Phase-1 result format

Phase-1 is treated as a vertex-only TPC search result. Its minimal
result packet is:

```yaml
phase: HIBEAM_PHASE1
result_tag: <tag>
exposure:
  protons_on_target: null
  live_time_seconds: null
  neutron_flux_integral: null
selection:
  topology: vertex_only_tpc
  fiducial_volume: null
  blind_region_definition: null
counts:
  n_observed: sealed
  b_expected: null
  b_uncertainty: null
signal:
  efficiency: null
  efficiency_uncertainty: null
nuisances: []
method_dispatch:
  convention: plan_46
  confidence_level: 0.90
```

Required omissions are as important as required fields:

- No scintillator PID term.
- No lead-glass photon-clustering term.
- No π⁰ pairing or kinematic-fit term.
- No Phase-2-only MVA score.

Those omissions prevent accidental reuse of Phase-2 detector power in a
Phase-1-only result.

## 2. Standalone Phase-1 limit

The standalone Phase-1 result uses plan 46:

1. Build `s_expected`, `b_expected`, and `n_observed` from the Phase-1
   result packet.
2. Apply plan 45 nuisances that are valid for Phase-1 only.
3. Use Feldman-Cousins for zero/near-zero counts per plan 46 §3.
4. Report 90% C.L. primary and 95% C.L. comparison if the input packet
   carries enough information.

If `n_observed` remains sealed, only expected limits may be reported.
Observed limits require the unblinding state in §4.

The result packet writes both:

- a human-readable table for the thesis/reviewer package, and
- a machine-readable registry row under the planned combination
  registry.

## 3. Phase-1 + Phase-2 joint likelihood

The joint likelihood is a product of per-phase likelihood terms with a
shared nuisance model:

```text
L_joint(mu, theta_shared, theta_p1, theta_p2)
  = L_p1(data_p1 | mu, theta_shared, theta_p1)
    × L_p2(data_p2 | mu, theta_shared, theta_p2)
    × pi(theta_shared, theta_p1, theta_p2)
```

Where:

- `mu` is the common neutron-antineutron signal-strength parameter.
- `theta_shared` are correlated nuisance parameters.
- `theta_p1` and `theta_p2` are phase-specific nuisance parameters.

Correlation classes:

| Nuisance | Correlation class | Source plan | Rule |
|---|---|---|---|
| Beam flux normalisation | shared | plan 45 | one nuisance if the same ESS flux model is used |
| n̄ annihilation branching | shared | plan 13/45 | one nuisance for common signal physics |
| TPC W-value | partially shared | plan 17/63 | shared prior, phase-specific drift term |
| TPC alignment | partially shared | plan 16/45 | shared engineering prior, phase-specific survey/drift |
| Phase-1 vertex efficiency | Phase-1 only | plan 43-style packet | no Phase-2 constraint unless same selection is used |
| Phase-2 scintillator/lead-glass calibration | Phase-2 only | plans 18/63 | absent from Phase-1 result format |
| Beam-neutron background | model-dependent | plans 22/45 | shared only if the same source DEC and geometry are used |
| Cosmic background | phase-specific | plan 21/44 | separate unless exposure and shielding model are identical |

The combination registry records the correlation class for every
nuisance id. A nuisance without a class is treated as uncorrelated and
blocks A+ promotion until reviewed.

## 4. Blinding protocol

The combination has two freezes:

1. **Analysis freeze.** Phase-1 and Phase-2 selections, nuisance
   classes, and method-dispatch rules are frozen using expected counts
   only.
2. **Observed-count unblind.** Observed counts are copied into the
   result packet after Methodology Council sign-off.

Rules:

- Phase-1 observed counts cannot be inspected while tuning Phase-2
  selection thresholds.
- Phase-2 observed counts cannot be inspected while deciding whether to
  include Phase-1 in the combination.
- If a post-unblind bug is found, the combination moves to `invalidated`
  until a DEC records the fix and both phases are refrozen.
- Expected limits may be shown before unblinding; observed limits may
  not.

The `n_observed: sealed` literal in §1 is intentional. Any non-sealed
observed value in a pre-freeze packet is a blocking review failure.

## 5. Registry schema

```yaml
id: phase1_phase2_<tag>
status: draft | frozen_expected | unblinded | invalidated
phase1_packet: null
phase2_packet: null
method_dispatch:
  source_plan: 46
  low_count_rule: "n_obs <= 5 or b <= 5"
nuisance_correlation:
  - nuisance_id: beam_flux
    class: shared
    source_plan: 45
outputs:
  expected_limit_90: null
  expected_limit_95: null
  observed_limit_90: sealed
audit:
  freeze_decision: null
  unblind_decision: null
  ledger_rows: []
```

The registry is append-only. A corrected combination supersedes the old
tag rather than rewriting it.

## 6. Interaction with the thesis ledger

Plan 47 rows that quote Phase-1, Phase-2, or combined limits must carry:

- the combination registry id,
- the method selected by plan 46,
- the nuisance ids and correlation classes used,
- the blinding state at the time the number was produced, and
- the drift-monitoring tag from plan 63 for any Class C calibration
  nuisance.

If the Phase-1 packet is missing or still sealed, ledger rows may quote
only expected limits and must not claim observed agreement.

## 7. Implementation notes

This plan does not require a new CLI surface. L3 may later implement the
combination in `nnbar_reconstruction/statistics/`, but the current A+
artifact is the schema, correlation policy, and blinding contract.

Recommended implementation order:

1. Add the registry schema and static validators.
2. Add expected-limit fixtures using plan 46 examples.
3. Add nuisance-correlation validation against plan 45 ids.
4. Add unblind-state validation.
5. Only then ingest a real Phase-1 packet.

## 8. A+ verifier transcript

Re-run before changing path or existence claims:

```bash
ls docs/rebuild_plans/43_signal_efficiency.md \
   docs/rebuild_plans/45_systematics_taxonomy.md \
   docs/rebuild_plans/46_significance_protocol.md \
   docs/rebuild_plans/47_reproduction_ledger.md \
   docs/rebuild_plans/63_calibration_drift_monitoring.md
find data -maxdepth 3 -type f \\( -iname '*phase1*' -o -iname '*hibeam*' \\)
```

Current 2026-05-10 evidence: the referenced local plans exist. The
repository does not provide a source-backed Phase-1 result packet in
the checked `data/` tree, so Phase-1 inputs are schema targets until a
real packet is supplied and hashed.

## 9. Acceptance criteria

- §1 Phase-1 packet is vertex-only and has no Phase-2 detector fields.
- §3 assigns every nuisance a correlation class.
- §4 prevents observed-count leakage into selection tuning.
- §6 defines exactly what plan 47 rows must carry for any combined
  limit.

## 10. Dependencies

- **04** — intervals and low-count uncertainty conventions.
- **43** — signal efficiency payload shape.
- **45** — nuisance ids and correlations.
- **46** — significance/limit method dispatch.
- **47** — ledger rows for limits.
- **63** — calibration-drift tags for Class C nuisances.

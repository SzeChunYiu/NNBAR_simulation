---
id: 57_mva_method_protocol
title: MVA / ML method protocol — when, how, with what discipline
version: 0.1
status: draft
owner: Software Quality + Combined Performance
depends_on: [00_README, 04_statistical_uncertainty, 23_sample_calibration_aux, 24_reconstruction_question_tree, 38_truth_substitution_ladder, 49_targeted_improvements]
outputs:
  - {path: docs/rebuild_plans/57_mva_method_protocol.md, schema: this file}
  - {path: nnbar_reconstruction/mva/, schema: shared MVA utilities}
acceptance:
  - {test: every MVA discriminant follows §1 lifecycle, method: per-MVA review, pass_when: signed by Council}
  - {test: feature-schema is decision-logged before training, method: §2 review, pass_when: DEC entry per MVA}
  - {test: inference-time feature schema audit matches training schema, method: §3 audit, pass_when: zero mismatches}
  - {test: overtraining test passes; calibration monotonicity verified, method: §4 closure, pass_when: pass}
risks:
  - {risk: MVA upgrade outperforms baseline only on the validation set, mitigation: §1 train/validation/test split with seed and scope}
  - {risk: feature schema changes silently between training and inference, mitigation: §3 audit}
estimated_effort: M
last_updated: 2026-05-09
---

# MVA / ML method protocol

*Charter.* Cross-cutting plan covering every multivariate /
machine-learning discriminant in the rebuild. Adopted by plans 29
(charged PID), 32 (shower shape), 37 (event selection), and any
future MVA upgrade.

The protocol exists because MVAs are easy to misuse; HIBEAM's PhD
reproducibility appendix explicitly flags "TrackGNN feature schema"
as a load-bearing decision (DEC-2026-05-08-1).

## 1. Lifecycle

1. *Baseline gate.* No MVA is trained on a leaf until the cut-based
   baseline reproduces the thesis number for that leaf (plan 47
   green row).
2. *Feature schema decision.* Authoring WG names the features,
   their classes (must be Class A only — plan 01), their sources.
   Decision-logged (plan 05).
3. *Train / validation / test split.* Seed and scope per plan 04.
   Scope is per-event, not per-track or per-cluster (events are the
   independent unit). Test set never seen by anything except the
   final reporting.
4. *Training.* Library and hyperparameters recorded. Training script
   committed.
5. *Overtraining check.* Train vs validation performance gap < 5%
   (or stated tolerance).
6. *Calibration monotonicity.* The classifier output should be a
   monotonic function of true class probability — verify on
   validation set.
7. *Ladder benchmark.* Score against cut-based baseline on plan 38
   ladder.
8. *Acceptance.* Council signs off based on (5), (6), (7) plus
   non-regression on plan 47.

## 2. Feature schema discipline

```yaml
# nnbar_reconstruction/mva/<discriminant>/schema.yml
discriminant_id: charged_pid_likelihood_v1
features:
  - {name: dedx, source: plan 27, class: A}
  - {name: scintillator_range, source: plan 28, class: A}
  - {name: scintillator_energy, source: plan 18, class: A}
  - {name: track_length, source: plan 26, class: A}
  - {name: leadglass_leakage, source: plan 33, class: A}
labels:
  - {name: truth_pid, source: Particle.Name, class: B, decorator: @labeling}
splits:
  scope: per-event
  seed: <derived per plan 04>
  fractions: {train: 0.6, validation: 0.2, test: 0.2}
training:
  library: scikit-learn / xgboost / pytorch (chosen at plan stage)
  hyperparameters: <recorded YAML>
overtraining_tolerance: 5%
```

The schema is a versioned artifact. Changing a feature creates a new
schema (with bumped version) and a new DEC entry. Inference-time
code reads `schema.yml` to confirm the inputs match.

## 3. Inference-vs-training schema audit

A model loaded at inference time *must* present the same feature
schema it was trained with. Plan 53 CI runs an audit:

```
python -m nnbar_reconstruction.mva.audit_schema \
    --model models/charged_pid_likelihood_v1.pkl \
    --schema schemas/charged_pid_likelihood_v1.yml \
    --code-path nnbar_reconstruction/charged_pid_likelihood.py
```

Mismatch is a hard fail. Mirrors HIBEAM's `DEC-2026-05-08-1` lesson.

## 4. Overtraining and calibration monotonicity

- *Overtraining.* Compute the chosen metric (e.g. AUC) on train and
  validation. Gap > tolerance → reject.
- *Calibration monotonicity.* Bin validation events by classifier
  output decile; compute true-class fraction per decile; verify
  monotonic. Non-monotonic regions flagged and either retrained
  with regularisation or post-hoc Platt scaling applied.

## 5. Reporting

For each MVA in the rebuild, the reporting block includes:

- Schema version + hash.
- Train / validation / test split sizes.
- Seed.
- Library + hyperparameters.
- Overtraining gap.
- Calibration monotonicity check pass.
- Ladder IV(L) before / after.
- Test-set metric (the headline number).

## 6. Acceptance criteria

- §1 lifecycle followed for every MVA.
- §2 feature schema YAML present per MVA.
- §3 audit green in CI.
- §4 overtraining and calibration checks documented.

## 7. Risks

- *Risk:* MVA learns truth-leakage features (e.g. a Class A feature
  that is correlated with the label only via a Class B path).
  *Mitigation:* §2 schema review by Methodology Council; ladder
  benchmark catches "too good to be true" results.
- *Risk:* test set leaks into training via repeated re-tuning.
  *Mitigation:* §1 step 3 — test set is sealed; re-tuning requires
  council sign-off.

## 8. Dependencies

- **04** — splits and seeds.
- **23** — calibration training samples.
- **24** — leaf identity for benchmarking.
- **38** — ladder.
- **49** — improvement protocol the MVA proposal flows through.
- *Consumed by:* plans 29, 32, 37.

## 9. References

- HIBEAM PhD reproducibility appendix `DEC-2026-05-08-1`.
- Standard MVA discipline (TMVA, scikit-learn documentation).
- ATLAS / CMS multivariate analysis guidelines.

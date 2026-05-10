---
id: 40_closure_and_pulls
title: Per-leaf closure tests and pull distributions
version: 0.2
status: draft
owner: Combined Performance
depends_on: [00_README, 04_statistical_uncertainty, 24_reconstruction_question_tree, 38_truth_substitution_ladder, 39_fast_mc_sanity_check]
inputs:
  - {path: nnbar_reconstruction/closure/runner.py, schema: L3 closure runner API}
  - {path: tests/test_closure.py, schema: L3 regression fixtures}
outputs:
  - {path: docs/rebuild_plans/40_closure_and_pulls.md, schema: this file}
  - {path: output/closure/<dataset_id>/<leaf_id>/closure_report.json, schema: ClosureReport.as_dict()}
  - {path: output/closure/<dataset_id>/<leaf_id>/metrics.csv, schema: one row per ClosureMetric}
acceptance:
  - {test: every fitted quantity reports pull mean near zero, method: ClosureMetric.pull_mean, pass_when: leaf band satisfied}
  - {test: every fitted quantity reports pull width near one, method: ClosureMetric.pull_width and bootstrap uncertainty, pass_when: leaf band satisfied}
  - {test: reco-vs-truth distributions are not visibly incompatible, method: K-S statistic and p-value, pass_when: ks_pvalue above leaf band}
  - {test: every leaf has a closure schedule, method: §4 schedule, pass_when: full coverage or explicit blocked reason}
risks:
  - {risk: pull width > 1 indicates underestimated uncertainties, mitigation: §8 escalation procedure}
  - {risk: plans cite a non-existent closure CLI, mitigation: §3 uses the verified Python API only}
estimated_effort: M
last_updated: 2026-05-10
---

# Per-leaf closure tests and pull distributions

*Charter.* Plan 38 asks how much each truth leaf moves the final
analysis when inserted into the reconstruction ladder. Plan 39 asks
whether an independently smeared truth distribution can mimic the
reco-only distribution. Plan 40 is the fitted-quantity closure layer:
for each leaf with an estimator and an uncertainty, compute pull means,
pull widths, reduced chi2, and a reco-vs-truth compatibility check. A
closure failure blocks plan 47 thesis reproduction for the affected row
until the row records the responsible leaf and mitigation.

This plan does **not** cite a plan-40 command-line interface. The current
L3 surface is the Python module `nnbar_reconstruction/closure/runner.py`;
the runnable snippets below import that API directly. If L3 later adds a
CLI, update §11 only after a help command proves that the surface exists.

## 0.1 Wave 6 derivation — pull closure and uncertainty calibration

### Physics derivation

**What is physically measured.** Pull closure measures whether a
reconstructed estimator is unbiased relative to validation truth and
whether its reported uncertainty has the correct scale. The measured
ground-truth quantity is the truth value for a leaf-specific observable;
the closure observables are pull mean, pull width, reduced chi2, and
shape compatibility between reconstructed and truth distributions.

**Estimator rationale.** If an estimator is centred and its uncertainty
model is correct, `(reco - truth) / sigma` should be distributed with
mean near zero and width near one for the fitted quantities that plan 40
owns. A nonzero mean indicates bias or a calibration offset; a pull
width above one indicates underestimated uncertainty or unmodelled
tails; a pull width below one indicates overestimated uncertainty or
over-regularisation. K-S shape compatibility protects against a
pathological case where moments look acceptable but the distribution
shape is wrong.

**Statistical character.** Pull statistics carry finite-sample
uncertainty and bootstrap covariance, but systematic effects dominate
defence-critical failures. Calibration constants, alignment,
material-budget approximations, physics-list alternatives, and sample
mode differences can all shift pulls coherently. Closure bands must be
bound before reading the row's result; otherwise a pass can be created
by post-hoc tolerance tuning.

### Logic gaps

- **Pull-mean and pull-width bands.** Grounding: §4 and §6 record
  current leaf-specific bands. `OPEN:` derive each band from the
  target thesis observable's allowed bias and uncertainty budget before
  final defence use; target resolution date 2026-06-22.
- **K-S p-value >0.01.** Grounding: current leaf-band shape guard.
  `OPEN:` validate the false-fail/false-pass behaviour with toys and
  bootstrap covariance at the expected row counts; target resolution
  date 2026-06-29.
- **Bootstrap interval stability.** Grounding: plan 04 supplies the
  deterministic bootstrap convention. `OPEN:` define the minimum event
  count or resampling budget for each leaf so the conclusion cannot flip
  under the 68% interval; target resolution date 2026-06-22.
- **Explicit column maps outside V.4.** Grounding: §1 states only V.4
  has default runner support today. `OPEN:` either add tested defaults
  in L3 or require each non-V.4 ledger row to carry its column map;
  target resolution date 2026-06-15.
- **Classification/count leaves.** Grounding: §4 removes the fake-pull
  placeholder for non-fitted leaves. `OPEN:` bind PID, selection, and
  count leaves to their native closure metrics in plans 29, 37, and
  47; target resolution date 2026-06-29.

### Closure test for the derivation

1. For one ledger row and leaf, join reco, truth, and sigma columns by
   event id; stop if the event coverage or sigma validity is not exact
   enough for the row's declared band.
2. Run `run_closure` with the pre-bound `ClosureBand` and persist
   `closure_report.json` plus `metrics.csv`.
3. Interpret failures by metric: pull mean routes to estimator bias,
   pull width routes to uncertainty modelling, chi2/dof routes to
   outliers or tails, and K-S failure routes to shape/model mismatch.
4. Copy the metrics into plan 47 and keep the row `mismatch` until the
   responsible leaf either closes or the residual is explicitly carried
   as a plan-45 systematic.

## 1. Verified implementation surface

Current L3 files:

| Path | Lines | Role |
|---|---:|---|
| `nnbar_reconstruction/closure/__init__.py` | 5 | package export surface |
| `nnbar_reconstruction/closure/runner.py` | 323 | closure bands, pull metrics, report objects, event joins |
| `tests/test_closure.py` | 69 | unbiased, deterministic, and biased-fail fixtures |

Current public objects in `runner.py`:

| Object | Type | Plan role |
|---|---|---|
| `ClosureBand` | dataclass | stores max absolute pull mean, pull-width band, and K-S p-value floor |
| `ClosureMetric` | dataclass | stores one quantity's pull mean, width, chi2/dof, bootstrap uncertainty, K-S result, and pass/fail |
| `ClosureReport` | dataclass | groups all metrics for one leaf and dataset |
| `run_closure` | validation-only function | computes the closure report from reco and truth tables |
| `closure_band_for_leaf` | function | supplies default V.4, V.2, P.3, P.4, and E.7 bands |

The runner currently auto-discovers V.4 vertex columns and also supports a
generic table with `reco`, `truth`, and `sigma` columns. Any other leaf
must pass an explicit `column_map` until L3 adds a default map. This is an
important A+ boundary: a plan 47 row may not claim a P.4 or E.7 closure
used default columns unless the row's log shows the explicit map or a new
verified L3 default.

## 2. Pull and compatibility metrics

For a fitted quantity with reconstructed value `x_fit`, validation truth
`x_true`, and fitted standard deviation `sigma_fit`, the pull is:

```text
pull = (x_fit - x_true) / sigma_fit
```

A closed estimator should have pull mean near zero and pull width near
one. Plan 40 records more than these two numbers because A+ review must
separate bias, uncertainty underestimation, and shape mismatch:

- `pull_mean`: signed average pull; nonzero values indicate estimator
  bias or a mis-centred calibration constant.
- `pull_width`: RMS width around the pull mean; values above one point
  to underestimated uncertainty or unmodelled tails.
- `chi2_per_dof`: sum of squared pulls divided by the number of finite
  pulls; this gives a reviewer-readable goodness-of-fit scale.
- `pull_mean_uncertainty` and `pull_width_uncertainty`: plan-04
  deterministic bootstrap half-widths.
- `ks_pvalue`: two-sample K-S compatibility between reco and truth
  values; this catches shape disagreement even when pulls happen to be
  centred.

Rows with missing `sigma_fit`, non-positive `sigma_fit`, or no finite
joined entries fail closed. They are `mismatch` or `blocked-no-sample`
rows in plan 47, not reproduced rows.

## 3. Runnable procedure using the verified API

For a real row, materialise reco and truth tables first, then run a
row-specific Python invocation from the L3 worktree. Replace the paths,
leaf id, and column map with the plan 47 row under study.

```bash
cd /Volumes/MyDrive/nnbar/nnbar/NNBAR_Detector-L3
python3 - <<'PY'
from pathlib import Path
import json
import pandas as pd

from nnbar_reconstruction.closure.runner import run_closure

reco_path = Path('/path/to/reco_vertices.parquet')
truth_path = Path('/path/to/truth_vertices.parquet')
out_dir = Path('/Volumes/MyDrive/nnbar/nnbar/simulation-L2/output/closure/<dataset_id>/V.4')
out_dir.mkdir(parents=True, exist_ok=True)

reco = pd.read_parquet(reco_path)
truth = pd.read_parquet(truth_path)
report = run_closure({'vertices': reco}, truth, 'V.4', n_boot=200, dataset_id='<dataset_id>')

(out_dir / 'closure_report.json').write_text(json.dumps(report.as_dict(), indent=2))
pd.DataFrame([metric.as_dict() for metric in report.metrics.values()]).to_csv(out_dir / 'metrics.csv', index=False)
print(json.dumps(report.as_dict(), indent=2))
PY
```

For an immediately runnable smoke without sample files:

```bash
cd /Volumes/MyDrive/nnbar/nnbar/NNBAR_Detector-L3
python3 - <<'PY'
import pandas as pd
from nnbar_reconstruction.closure.runner import run_closure

truth_values = [100.0 + index for index in range(40)]
truth = pd.DataFrame({
    'event_id': list(range(40)),
    'vertex_x_truth': truth_values,
    'vertex_y_truth': truth_values,
    'vertex_z_truth': truth_values,
})
reco = pd.DataFrame({
    'event_id': list(range(40)),
    'vertex_x': [value + error for value, error in zip(truth_values, [-1.0, 1.0] * 20)],
    'vertex_y': [value + error for value, error in zip(truth_values, [-1.0, 1.0] * 20)],
    'vertex_z': [value + error for value, error in zip(truth_values, [-1.0, 1.0] * 20)],
    'vertex_x_sigma': [1.0] * 40,
    'vertex_y_sigma': [1.0] * 40,
    'vertex_z_sigma': [1.0] * 40,
})
report = run_closure({'vertices': reco}, truth, 'V.4', n_boot=50, dataset_id='plan40-smoke')
print(report.as_dict())
PY
```

The smoke must pass and report `pull_mean = 0`, `pull_width = 1`, and
`chi2_per_dof = 1` for each vertex component. A deliberately shifted
fixture must fail; `tests/test_closure.py` is the regression guard for
that negative control.

## 4. Per-leaf closure schedule

| Leaf | Quantity | Truth source | Required uncertainty | Band (mean / width / K-S) | Frequency | Current runner support |
|---|---|---|---|---|---|---|
| V.4 | event vertex x,y,z | `Particle_output` vertex coordinates or plan-30 truth vertex table | vertex covariance or component sigma | `|mu| < 0.1`, width `[0.9,1.1]`, p > 0.01 | every signal-sample freeze | default V.4 map |
| V.2 | track direction residuals | production momentum direction | angular-fit covariance | `|mu| < 0.05`, width `[0.9,1.1]`, p > 0.01 | every signal-sample freeze | explicit `column_map` |
| C.2 | dE/dx estimator | truth charged species and deposited energy | truncated-mean dE/dx sigma | `|mu| < 0.1`, width `[0.9,1.2]`, p > 0.01 | every charged calibration refresh | explicit `column_map`; W-value failures cite DEC-2026-05-10-5 |
| C.5 | proton/pi PID | validation-only truth `Name`/PDG label | classifier score calibration | accuracy/ROC row, not a pull | per calibration sample | use plan 29 PID scan, not `run_closure` |
| P.3 | photon direction | truth gamma momentum | angular covariance | `|mu| < 0.05`, width `[0.9,1.2]`, p > 0.01 | per `cal_singlegamma` sample | explicit `column_map` |
| P.4 | photon energy | truth gamma kinetic energy | calorimeter energy sigma | `|mu| < 0.05`, width `[0.9,1.2]`, p > 0.01 | per photon calibration sample | explicit `column_map` |
| P.5 | pi0 mass | PDG pi0 mass after photon-pair fit | fit mass sigma | `|delta_m| < 1 MeV`, width `[0.9,1.2]`, p > 0.01 | per signal sample | explicit `column_map` |
| E.7 | visible invariant mass | truth four-vectors after Class-A selection | propagated event-mass sigma | `|delta_m| < 50 MeV`, width `[0.8,1.2]`, p > 0.01 | every signal-sample freeze | explicit `column_map` |

The `(others)` placeholder from v0.1 is removed. Leaves without a fitted
uncertainty are routed to their own validation metric (classification,
rank, efficiency, or count closure) rather than forced into a fake pull.

## 5. Numbered closure workflow

1. **Bind one row.** Start from a single plan 47 ledger id and one leaf.
   The output directory is `output/closure/<dataset_id>/<leaf_id>/`.
2. **Materialise inputs.** Store reco, truth, and sigma columns in tables
   whose event ids can be joined. If the row lacks the truth table or
   sigma column, mark it `blocked-no-sample` or `mismatch` with the
   missing column named.
3. **Choose the band before looking.** Use `closure_band_for_leaf` when
   it exists; otherwise record the explicit `ClosureBand` in the ledger
   note and plan-05/DEC trail if it changes a threshold.
4. **Run `run_closure`.** Persist `closure_report.json` and
   `metrics.csv`. The ledger `reproduced_value` must include `n_events`,
   `pull_mean`, `pull_width`, `chi2_per_dof`, `ks_pvalue`, and `passed`.
5. **Classify the row.** If all quantities pass and the row checks a
   numerical thesis value, `status: reproduced` is allowed. If any
   quantity fails, use `status: mismatch` with a `delta` field naming the
   failing metric and leaf.
6. **Attach an explanation.** A mismatch note must hypothesise the cause:
   W-value bias, non-HP physics-list limitation, fast-vs-optical mode
   mismatch, redesigned reconstruction method, sample-regeneration gap,
   or unexplained human-review item.
7. **Escalate.** Closure failures open a plan 51 reviewer question or a
   plan 05 DEC only when the fix changes a method, threshold, feature, or
   systematic model.

## 6. Acceptance bands and pass/fail semantics

A pass requires all of the following for every quantity in the report:

- `abs(pull_mean) < max_abs_pull_mean`;
- `pull_width_range[0] <= pull_width <= pull_width_range[1]`;
- `ks_pvalue > min_ks_p`;
- bootstrap uncertainty is finite and small enough that the conclusion
  would not flip under the 68% interval.

When a band is revised, the plan body may carry a DEC stub, but the
production result cannot be cited until the decision log entry is
approved. That mirrors the A+ rule for thresholds and avoids silent
post-hoc tuning.

## 7. Relationship to plans 38 and 39

- Plan 38 truth-substitution failures identify which reconstruction leaf
  moves the final observable.
- Plan 39 fast-MC failures identify whether independent detector-response
  smearing can reproduce the reco-only distribution.
- Plan 40 closure failures identify whether a fitted estimator is biased
  or has a miscalibrated uncertainty.

A defence-quality row should carry all applicable artifacts. If plan 38
and plan 39 pass but plan 40 fails, prioritise the covariance model. If
plan 40 passes but plan 39 fails, prioritise detector-response constants.
If all fail, treat the thesis row as unreproduced until the leaf-level
implementation and sample provenance are re-audited.

## 8. Escalation when closure fails

1. **Stat-only diagnosis.** Bootstrap the failing metric using plan 04.
   If the failure is compatible with low statistics, increase the sample
   size before changing code or thresholds.
2. **Bias diagnosis.** Plot pull vs calibration constants: TPC W-value,
   scintillator yield, lead-glass calibration, alignment scenario, and
   material-budget bracket.
3. **Systematic diagnosis.** Compare physics-list alternatives from plan
   12 and signal/background model alternatives from plans 13 and 14.
4. **Mode diagnosis.** Compare fast-mode vs optical-mode samples before
   interpreting scintillator or photon-yield discrepancies.
5. **Code-bug diagnosis.** Run the realism audit from plan 01 and the
   leaf's L3 regression test. A Class-B leak or post-selection join bug
   can make pulls look artificially good or bad.

The output of this escalation is a concrete action, not a prose-only
excuse: update a plan 47 row, add a plan 51 reviewer question, or prepare
a DEC entry if the method itself changes.

## 9. CI and ledger integration

Plan 53 should run `tests/test_closure.py` on every closure-relevant PR.
Full sample closures are heavier and belong to the reproduction ledger:
plan 47 rows link to `closure_report.json` and copy the summary metrics
into `data/ledger/rows.yml`. A green unit test proves the runner works;
it does not prove a thesis figure has been reproduced.

## 10. Risks and mitigations

- *Risk:* only V.4 has a default column map today. *Mitigation:* ledger
  rows for other leaves must provide `column_map` explicitly until L3
  extends `_default_column_map` and tests it.
- *Risk:* pull bands are tuned after seeing the data. *Mitigation:* any
  band change is a method-threshold decision under plan 05.
- *Risk:* K-S p-values are over-interpreted at low N. *Mitigation:* quote
  `n_events`, bootstrap intervals, and plan-04 small-sample caveats.
- *Risk:* classification leaves are squeezed into pull logic. *Mitigation:*
  route PID, selection, and count leaves to their native metrics.

## 11. A+ verifier transcript

Run these before editing any file/function/CLI claim in this plan:

```bash
cd /Volumes/MyDrive/nnbar/nnbar/NNBAR_Detector-L3
rtk ls nnbar_reconstruction/closure/__init__.py \
   nnbar_reconstruction/closure/runner.py \
   tests/test_closure.py
rtk wc -l nnbar_reconstruction/closure/__init__.py \
      nnbar_reconstruction/closure/runner.py \
      tests/test_closure.py
rtk grep -n -E "^(def|class) ClosureBand" nnbar_reconstruction/closure/runner.py
rtk grep -n -E "^(def|class) ClosureMetric" nnbar_reconstruction/closure/runner.py
rtk grep -n -E "^(def|class) ClosureReport" nnbar_reconstruction/closure/runner.py
rtk grep -n -E "^    def as_dict" nnbar_reconstruction/closure/runner.py
rtk grep -n -E "^def run_closure" nnbar_reconstruction/closure/runner.py
rtk grep -n -E "^def closure_band_for_leaf" nnbar_reconstruction/closure/runner.py
rtk grep -n -E "^def test_run_closure" tests/test_closure.py
rtk proxy python3 -m nnbar_reconstruction.cli --help
rtk pytest tests/test_closure.py -q
```

On 2026-05-10 these checks resolved: the files existed, line counts were
5/323/69, the listed objects were present in `runner.py`, `cli --help`
listed only `summarize`, `scan-pid`, `response-matrix`, `cutflow`, `dqm`,
and `validate-reco`, and `tests/test_closure.py` passed. Because no
closure CLI is listed, this plan uses the Python API rather than citing
an invented command.

## 12. Dependencies

- **04** — bootstrap intervals, deterministic seeds, and small-sample
  interpretation.
- **09** — event id and table/column provenance.
- **18** — calibration constants that explain bias trends.
- **24** — leaf ids and ownership.
- **38** — truth-substitution companion artifact.
- **39** — independent fast-MC companion artifact.
- **47** — thesis ledger status, reproduced values, and deltas.
- *Consumed by:* plans 25–37, plan 47, plan 50, plan 51, and plan 53.

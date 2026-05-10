---
id: 39_fast_mc_sanity_check
title: Fast-MC inverse closure check
version: 0.2
status: draft
owner: Combined Performance
depends_on: [00_README, 04_statistical_uncertainty, 24_reconstruction_question_tree, 38_truth_substitution_ladder, 40_closure_and_pulls]
inputs:
  - {path: nnbar_reconstruction/fast_mc/closure_test.py, schema: L3 fast-MC smearing/comparison API}
  - {path: tests/test_fast_mc.py, schema: L3 regression fixtures}
outputs:
  - {path: docs/rebuild_plans/39_fast_mc_sanity_check.md, schema: this file}
  - {path: output/fast_mc/<dataset_id>/<observable>/report.json, schema: FastMCClosureReport.as_dict()}
  - {path: output/fast_mc/<dataset_id>/<observable>/smeared.parquet, schema: truth columns plus smeared columns}
acceptance:
  - {test: smear-truth distributions match reco-only distributions within stated tolerance, method: per-observable closure report, pass_when: tolerance met for visible_invariant_mass, pi0_mass_peak, sphericity, and total_calorimeter_energy}
  - {test: deliberate reco bias fails, method: test_fast_mc_closure_flags_deliberate_bias_fixture, pass_when: report.passed is false}
risks:
  - {risk: closure passes but reco code has a bias the smearing model also has, mitigation: §5 independent constants and plan 40 pull cross-check}
  - {risk: users invent a non-existent fast-MC CLI, mitigation: §3 records the current no-CLI verifier and uses the verified Python API}
estimated_effort: M
last_updated: 2026-05-10
---

# Fast-MC inverse closure check

*Charter.* Plan 38 validates reconstruction by substituting truth into
selected ladder leaves and running the downstream chain. That is powerful
but not independent: the truth-at-L and reco-only rungs can still share a
bias in the same reconstruction code. Plan 39 is the independent
cross-check. It smears truth observables with parameterised detector
resolutions and compares the resulting fast-MC distribution to the
reco-only distribution. Any large disagreement becomes a plan 40 closure
failure and a plan 47 ledger blocker until the responsible leaf explains
it.

This plan is intentionally conservative about executable surface. The current L3 implementation exposes a Python API under
`nnbar_reconstruction/fast_mc/closure_test.py`. No current fast-MC
package CLI is cited in this plan; the runnable commands below therefore
use the verified API directly and write the same artifacts a future CLI
should produce.

## 0.1 Wave 6 derivation — smearing closure as bias detector

### Physics derivation

**What is physically measured.** Fast-MC closure measures whether truth
observables, after applying detector-resolution smearing fixed outside
the row under study, reproduce the reconstructed observable
distribution. The ground-truth quantity is the row-aligned truth
observable; the measured closure outputs are mean bias, RMS ratio, and
distributional compatibility between smeared truth and reco-only data.

**Estimator rationale.** A detector response matrix can be approximated
locally by smearing truth with resolution parameters when the dominant
effect is measurement resolution rather than selection migration. If
the smeared-truth distribution matches reco, the reconstruction behaves
like the independent resolution model for that observable. If it fails,
the discrepancy isolates either an under-modelled detector response, a
row-alignment/selection mismatch, or a biased reconstruction leaf. The
K-S comparison is useful here because it detects shape differences
without assuming the observable is Gaussian, while mean and RMS metrics
retain interpretable bias and resolution checks.

**Statistical character.** The smearing seed introduces Monte Carlo
variance, and finite row counts broaden the K-S and moment estimates.
The dominant risk is systematic leakage: constants tuned on the same
reco distribution would make the closure circular. Therefore every
smearing constant must come from plan 18, plan 04, external detector
requirements, or a prior registry entry before the row is evaluated.

### Logic gaps

- **Default smearing constants.** Grounding: §6 assigns v0.2 constants
  to leaf owners. `OPEN:` replace each placeholder by a plan-18
  calibration result, external requirement, or plan-09 Class C registry
  row before using it in a thesis equality claim; target resolution
  date 2026-06-22.
- **Bias tolerances and RMS-ratio bands.** Grounding: §7 records
  current plan-level thresholds. `OPEN:` derive each threshold from the
  corresponding thesis observable's sensitivity or plan-40 pull
  tolerance; target resolution date 2026-06-22.
- **K-S p-value >0.01.** Grounding: current distribution-shape guard.
  `OPEN:` validate the false-fail rate with toys at the expected row
  counts and with bootstrapped covariance; target resolution date
  2026-06-29.
- **Row-alignment tolerance 0.5%.** Grounding: §4 fail-closed join
  guard. `OPEN:` replace with exact event-key equality once plan 09
  manifests guarantee one event id per row across truth and reco
  tables; target resolution date 2026-06-15.
- **Energy-dependent smearing.** Grounding: §9 states that the current
  scalar API cannot natively express all detector response functions.
  `OPEN:` either precompute per-row sigmas or extend L3 with a tested
  transform rule before applying photon-energy or calorimeter-energy
  closure to defence-critical rows; target resolution date 2026-06-29.

### Closure test for the derivation

1. Choose one plan-47 row and one observable, materialise row-aligned
   truth and reco tables, and verify exact event-key coverage.
2. Bind the smearing constants and random seed from plan-04/plan-18
   provenance before reading the reco distribution for that row.
3. Run `smear_truth` and `compare_distributions`, persist
   `smeared.parquet` and `report.json`, and copy mean bias, RMS ratio,
   K-S statistic, and pass/fail into the ledger row.
4. If closure fails, route to plan 40 and the owning leaf. A pass is
   only an independence check; it does not override the plan-47 figure
   equality protocol.

## 1. Verified implementation surface

Current L3 files:

| Path | Lines | Role |
|---|---:|---|
| `nnbar_reconstruction/fast_mc/__init__.py` | 5 | package export surface |
| `nnbar_reconstruction/fast_mc/closure_test.py` | 275 | smearing, tolerance, K-S comparison, report objects |
| `tests/test_fast_mc.py` | 71 | deterministic smearing, biased-fail, unbiased-pass fixtures |

Current public objects in `closure_test.py`:

| Object | Type | Plan role |
|---|---|---|
| `ClosureTolerance` | dataclass | stores maximum absolute bias, RMS-ratio band, and minimum K-S p-value |
| `FastMCClosureReport` | dataclass | JSON-serialisable report for one observable |
| `smear_truth` | function | copies a truth table and appends smeared output columns |
| `compare_distributions` | function | computes mean offset, RMS ratio, K-S statistic, and pass/fail |
| `tolerance_for_observable` | function | supplies the plan-39 default tolerances |

Current regression fixtures in `tests/test_fast_mc.py` check that fixed
seeds are deterministic, that a deliberately shifted reco distribution
fails, and that identical distributions pass. Those tests are necessary
but not sufficient for thesis reproduction; the production procedure in
§3 binds them to real reco outputs and plan 47 rows.

## 2. Inputs and table contract

The fast-MC job consumes two table families:

1. **Truth table.** A row-aligned table with one truth column per
   observable. The source is the same run manifest used by plan 38, but
   only Class B / validation-only values are read. Example columns:
   `visible_invariant_mass_truth`, `pi0_mass_truth`, `sphericity_truth`,
   and `total_calorimeter_energy_truth`.
2. **Reco table.** A row-aligned reco-only table with the matching
   reconstructed observable. Example columns:
   `visible_invariant_mass`, `pi0_mass_peak`, `sphericity`, and
   `total_calorimeter_energy`.

The row key is the event identifier from plan 09. If row alignment is
ambiguous, the fast-MC job must stop and mark the plan 47 row
`mismatch`, not silently compare differently selected event sets.

## 3. Runnable procedure using the verified API

Until L3 adds a dedicated CLI, run a row-specific Python API invocation
from the L3 worktree. Replace the dataset paths and column names with the
plan 47 row under study.

```bash
cd /Volumes/MyDrive/nnbar/nnbar/NNBAR_Detector-L3
python3 - <<'PY'
from pathlib import Path
import json
import pandas as pd

from nnbar_reconstruction.fast_mc.closure_test import (
    compare_distributions,
    smear_truth,
)

truth_path = Path("/path/to/truth_observables.parquet")
reco_path = Path("/path/to/reco_observables.parquet")
out_dir = Path("/Volumes/MyDrive/nnbar/nnbar/simulation-L2/output/fast_mc/<dataset_id>/visible_invariant_mass")
out_dir.mkdir(parents=True, exist_ok=True)

truth = pd.read_parquet(truth_path)
reco = pd.read_parquet(reco_path)

smeared = smear_truth(
    truth,
    {
        "seed": 0,
        "rules": {
            "visible_invariant_mass_truth": {
                "distribution": "gaussian",
                "sigma": 50.0,
                "output": "visible_invariant_mass_smeared",
            }
        },
    },
)
report = compare_distributions(
    reco["visible_invariant_mass"],
    smeared["visible_invariant_mass_smeared"],
    observable="visible_invariant_mass",
)

smeared.to_parquet(out_dir / "smeared.parquet", index=False)
(out_dir / "report.json").write_text(json.dumps(report.as_dict(), indent=2))
print(json.dumps(report.as_dict(), indent=2))
PY
```

For an immediately runnable smoke without sample files:

```bash
cd /Volumes/MyDrive/nnbar/nnbar/NNBAR_Detector-L3
python3 - <<'PY'
import pandas as pd
from nnbar_reconstruction.fast_mc.closure_test import compare_distributions, smear_truth

truth = pd.DataFrame({"visible_invariant_mass_truth": [100.0, 101.0, 102.0, 103.0]})
reco = pd.Series([100.5, 101.5, 102.5, 103.5])
smeared = smear_truth(truth, {
    "seed": 3901,
    "rules": {
        "visible_invariant_mass_truth": {
            "distribution": "gaussian",
            "sigma": 1.0,
            "output": "visible_invariant_mass_smeared",
        }
    },
})
report = compare_distributions(
    reco,
    smeared["visible_invariant_mass_smeared"],
    observable="visible_invariant_mass",
)
print(report.as_dict())
PY
```

The command is intentionally explicit: it records the truth input, reco
input, smearing rule, output directory, and report JSON in the shell log.
A future `fast-mc` CLI may wrap this API, but plans must not cite that
CLI until L3 exposes it and a help check resolves.

## 4. Numbered closure workflow

For each plan 47 row that invokes plan 39:

1. **Select one observable.** Use exactly one row id and one observable
   per run. Do not combine visible mass and π⁰ mass in one ledger row.
2. **Materialise truth and reco inputs.** Record the two input paths in
   the row notes. If either table is absent, mark the row
   `blocked-no-sample`.
3. **Check row alignment.** Join on event id and fail closed if the
   joined count differs from either input count by more than 0.5%.
4. **Choose the smearing rule.** Use the table in §6. Constants must be
   fixed before looking at the reco distribution for this row.
5. **Run `smear_truth`.** Persist the smeared table under
   `output/fast_mc/<dataset_id>/<observable>/smeared.parquet`.
6. **Run `compare_distributions`.** Persist `report.json` and copy the
   key fields into `data/ledger/rows.yml`: `reproduced_value` contains
   `n_reco`, `n_smeared`, `mean_offset`, `rms_ratio`, and `ks_pvalue`;
   `delta` explains any failure against §7.
7. **Route failures.** If `passed` is false, open a plan 40 pull/closure
   row for the responsible leaf and keep the plan 47 status `mismatch`.
8. **Record provenance.** The ledger note must state whether the row was
   run through the API above or through a future verified CLI.

## 5. Independence guardrails

The smearing constants are independent only if they are fixed before the
reco-only distribution is inspected. The following guardrails are
mandatory:

- Tune constants from plan 18 calibration runs, external detector
  requirements, or plan 04 statistical conventions — never from the row
  being checked.
- Do not reuse plan 38 truth-substitution outputs as smearing targets;
  plan 38 and plan 39 must fail independently.
- Keep the random seed in the command or row metadata. Default seed `0`
  is acceptable for one-off diagnostics, but thesis rows should use the
  plan 04 binding `sha256(dataset_id || observable || "fast_mc")[:8]`.
- Treat a passing fast-MC row as an independence cross-check, not as a
  replacement for the plan 40 pull test.

## 6. Smearing parameters and ownership

| Leaf | Observable | Default smearing rule | Constant owner | Notes |
|---|---|---|---|---|
| V.4 | vertex z | Gaussian σ = 5 mm | plan 18 MIP closure | Use event vertex truth, not reconstructed TPC seed. |
| V.4 | vertex radius | Gaussian σ = 5 mm | plans 15 and 18 | Pad pitch and material multiple-scattering prior. |
| P.3 | photon direction | Gaussian σθ = 30 mrad | plan 32 | Convert to angular residual before comparing. |
| P.4 | photon energy | Gaussian relative σ = 5%/√E | plan 18 | The current API supports `relative_sigma`; energy-dependent √E scaling needs precomputed per-row σ or a future rule. |
| C.2 | charged dE/dx | Gaussian relative σ = 10% | plan 27 | W-value mismatch routes to DEC-2026-05-10-5. |
| C.3 | scintillator range | Gaussian σ = 10 mm | plan 28 | Saturate at non-negative range after smearing in a future transform hook. |
| E.2 | total calorimeter energy | Gaussian absolute σ = 50 MeV for current row-level checks | plans 18 and 36 | Split lead-glass and scintillator components before defense. |

Every new constant added here must also be registered in plan 09 as a
Class C parameter and cited by the plan 47 row that uses it.

## 7. Acceptance criteria per observable

`compare_distributions` applies the default tolerances below when called
with the canonical observable name. A noncanonical observable falls back
to zero bias tolerance, RMS-ratio range `[0.8, 1.2]`, and K-S p-value
`> 0.01`; do not use that fallback for thesis rows.

| Observable | Bias tolerance | RMS-ratio range | K-S p-value | Ledger pass/fail action |
|---|---:|---:|---:|---|
| `visible_invariant_mass` | ≤ 50 MeV | [0.7, 1.3] | > 0.01 | `reproduced` only if all three pass; otherwise `mismatch` with report fields |
| `pi0_mass_peak` | ≤ 5 MeV | [0.7, 1.3] | > 0.01 | route to P.4/P.5 closure before changing π⁰ cuts |
| `sphericity` | ≤ 0.05 | [0.7, 1.3] | > 0.01 | route to E.4 event-shape closure |
| `total_calorimeter_energy` | ≤ 50 MeV | [0.7, 1.3] | > 0.01 | route to plan 18 lead-glass/scint intercalibration |

The `reproduced` status is allowed only when the row directly checks a
numerical thesis value. Figure-level rows generally remain `mismatch`
until the visual/bin-by-bin equality protocol from plan 47 is satisfied,
even if the fast-MC report itself passes.

## 8. Relationship to plans 38 and 40

- **Plan 38** answers: how much does each truth leaf move the final
  observable when inserted into the real reconstruction chain?
- **Plan 39** answers: can an independently smeared truth distribution
  reproduce the reco-only distribution within fixed detector-resolution
  tolerances?
- **Plan 40** answers: for fitted quantities, are the pulls centred at
  zero with unit width, and do closure failures have an escalation path?

A robust defence row should have all three artifacts when applicable:
`output/ladder/...` from plan 38, `output/fast_mc/.../report.json` from
this plan, and `output/closure/...` from plan 40. If plan 38 and plan 39
agree but plan 40 fails, prioritise uncertainty modelling. If plan 38
fails but plan 39 passes, prioritise reconstruction leaf coupling. If
plan 39 fails alone, prioritise detector-response constants or row
alignment.

## 9. Risks and mitigations

- *Risk:* no dedicated CLI exists, so operators copy an API snippet
  incorrectly. *Mitigation:* keep this plan's snippet executable, and add
  a CLI only after an L3 test covers `--help` and a minimal report run.
- *Risk:* energy-dependent smearing is more complex than the current
  scalar `relative_sigma` API. *Mitigation:* precompute row-specific
  smeared columns for defence-critical rows or extend L3 with a tested
  transform rule.
- *Risk:* a fast-MC pass is over-interpreted as full reproduction.
  *Mitigation:* plan 47 still owns thesis figure equality, and plan 40
  still owns pull closure.

## 10. Dependencies

- **04** — seed binding, bootstrap, K-S reporting conventions.
- **09** — Class B truth columns and Class C smearing constants.
- **18** — calibration constants used by the smearing table.
- **24** — leaf ids used to route failures.
- **38** — truth-substitution ladder companion artifact.
- **40** — pull and closure escalation companion artifact.
- *Consumed by:* plans 25–37, plan 47, plan 50.

## 11. A+ verifier transcript

Run these from `/Volumes/MyDrive/nnbar/nnbar/NNBAR_Detector-L3`
before editing any file/function/CLI claim in this plan:

```bash
rtk ls nnbar_reconstruction/fast_mc/__init__.py \
   nnbar_reconstruction/fast_mc/closure_test.py \
   tests/test_fast_mc.py
rtk wc -l nnbar_reconstruction/fast_mc/__init__.py \
      nnbar_reconstruction/fast_mc/closure_test.py \
      tests/test_fast_mc.py
rtk grep -n -E "^(def|class) ClosureTolerance" nnbar_reconstruction/fast_mc/closure_test.py
rtk grep -n -E "^(def|class) FastMCClosureReport" nnbar_reconstruction/fast_mc/closure_test.py
rtk grep -n -E "^    def as_dict" nnbar_reconstruction/fast_mc/closure_test.py
rtk grep -n -E "^def smear_truth" nnbar_reconstruction/fast_mc/closure_test.py
rtk grep -n -E "^def compare_distributions" nnbar_reconstruction/fast_mc/closure_test.py
rtk grep -n -E "^def tolerance_for_observable" nnbar_reconstruction/fast_mc/closure_test.py
rtk proxy python3 -m nnbar_reconstruction.cli --help
rtk pytest tests/test_fast_mc.py -q
```

On 2026-05-10 the file/function checks resolved, and `cli --help` listed
`summarize`, `scan-pid`, `response-matrix`, `cutflow`, `dqm`, and
`validate-reco`. Because no fast-MC CLI is listed, this plan uses the
Python API rather than citing an invented CLI.

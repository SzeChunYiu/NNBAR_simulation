---
id: 08_6_validation
title: Reconstruction atomic walkthrough — validation public surface
version: 0.1
status: draft
owner: Reproducibility WG
depends_on: [08_reconstruction_atomic_walkthrough, 01_realism_contract, 09_io_schema_data_dictionary]
inputs:
  - {path: NNBAR_Detector/nnbar_reconstruction/validation.py, schema: source file}
outputs:
  - {path: docs/rebuild_plans/08_reconstruction_atomic_walkthrough/08_6_validation.md, schema: split walkthrough section}
last_updated: 2026-05-10
---

# Validation public surface — split from plan 08

This split file preserves and deepens plan 08 §6 so the main walkthrough
stays below the 500-line cap while validation receives function-level detail.

## 6. Validation (validation.py, 204 lines)

`validation.py` is a truth-aware reporting module, not a reconstruction
decision module. Its public functions consume reconstructed tables after
`reconstruct_run` and truth/provenance columns carried for diagnostics.
Class B reads here are validation-only and must not be interpreted as
permission for reconstruction decision paths to read truth columns.

### 6.1 Private metric helpers used by the public surface

- `_charged_pid_truth(name)` (`validation.py:14–20`) maps Class B
  `truth_name` values from `charged.csv` (plan 09 §14.2, lines
  274–280) into validation labels: exact `"proton"` ⇒ `proton`;
  `"pi+"`, `"pi-"`, or `"charged_pion"` ⇒ `charged_pion`; anything
  else is ignored.
- `_photon_charge_truth(name)` (`validation.py:23–42`) maps Class B
  photon `truth_name` diagnostics from `photons.csv` (plan 09 §14.4,
  lines 288–293) into validation labels. The hardcoded charged set is
  `{e+, e-, mu+, mu-, pi+, pi-, proton, antiproton, deuteron, alpha}`;
  the hardcoded neutral set is `{gamma, neutron, pi0, opticalphoton}`.
- `_binary_report(...)` (`validation.py:45–83`) computes TP/FP/TN/FN,
  class counts, accuracy, positive precision/recall, negative recall,
  and balanced F1. `usable` is hardcoded to require at least one truth
  positive and one truth negative (`validation.py:69–83`).
- `_empty_binary_report(...)` (`validation.py:86–101`) returns the same
  metric keys with zero counts, zero scores, and `usable: false`.

### 6.2 `evaluate_reconstruction_truth(result)`

**Source:** `NNBAR_Detector/nnbar_reconstruction/validation.py:104–146`.

**Inputs:** a reconstruction result dictionary. The function reads only
`charged` and `photons` tables from the dict (`validation.py:107–108`).
For `charged`, it requires `truth_name` and `pid_guess`
(`validation.py:110`): `truth_name` is Class B diagnostic provenance in
plan 09 §14.2 (lines 274–280), while `pid_guess` is the reconstructed
PID output derived from the charged-object rules in plan 08 §3.4. For
`photons`, it requires `truth_name` and `has_tpc_track`
(`validation.py:126`): `truth_name` is Class B diagnostic provenance,
while `has_tpc_track` is the reconstructed charged/neutral match output
from plan 09 §14.4 (lines 288–293).

**Decision rule:** missing/empty required tables yield empty reports
(`validation.py:110–117`, `126–133`). Otherwise charged rows are copied,
truth labels are produced with `_charged_pid_truth`, non-π/p labels are
dropped, and predicted positives are rows where `pid_guess == "proton"`
(`validation.py:113–124`). Photon rows are copied, truth charge labels
are produced with `_photon_charge_truth`, unlabelled names are dropped,
and predicted positives are `has_tpc_track.astype(bool)`
(`validation.py:129–140`). Each side is reduced by `_binary_report`; the
top-level `overall_usable` is true only when both charged PID and photon
charged-match reports are usable (`validation.py:142–145`).

**Outputs:** a dict with `charged_pid`, `photon_charged_match`, and
`overall_usable` (`validation.py:142–146`). Each report contains the
metric keys listed in §6.1.

**Truth reads:** Class B `truth_name` from reconstructed charged/photon
diagnostic columns. This is expected validation-only truth use, not a
reconstruction decision-path read under plan 08 §3.7.

### 6.3 `aggregate_reconstruction_truth(results)`

**Source:** `NNBAR_Detector/nnbar_reconstruction/validation.py:149–164`.

**Inputs:** a list of reconstruction result dictionaries. Inputs are the
same reconstructed tables required by `evaluate_reconstruction_truth`
after aggregation; no parquet columns are read directly by this function.

**Decision rule:** collect the union of table keys across all result
dicts (`validation.py:152–154`), concatenate all present non-empty
DataFrames for each key with `ignore_index=True`, and use an empty
DataFrame when no non-empty table exists (`validation.py:156–163`). The
combined dict is passed to `evaluate_reconstruction_truth`
(`validation.py:164`). There are no hardcoded numerical thresholds.

**Outputs:** the same validation report schema as
`evaluate_reconstruction_truth`.

**Truth reads:** none directly; Class B truth diagnostics are consumed
only by the delegated `evaluate_reconstruction_truth` call.

### 6.4 `assess_validation_readiness(report, *, min_class_count=1, min_accuracy=0.0, min_balanced_f1=0.0)`

**Source:** `NNBAR_Detector/nnbar_reconstruction/validation.py:167–204`.
The CLI exposes the same defaults as `--min-class-count 1`,
`--min-accuracy 0.0`, and `--min-balanced-f1 0.0` (`cli.py:261–270`);
`reconstruction.md:117–125` describes the JSON readiness block.

**Inputs:** a validation report dict, not raw parquet tables. The report
is expected to contain `charged_pid` with `true_proton`/`true_pion`, and
`photon_charged_match` with `true_charged`/`true_neutral`
(`validation.py:176–179`).

**Decision rule:** for each section, fail if `usable` is false, any
required class count is below `min_class_count`, `accuracy` is below
`min_accuracy`, or `balanced_f1` is below `min_balanced_f1`
(`validation.py:180–194`). Failure messages include the exact metric,
observed value, and threshold.

**Outputs:** a dict with `passed`, `failed_requirements`, and a
`requirements` echo of the three thresholds cast to `int`/`float`
(`validation.py:196–204`).

**Truth reads:** none. Truth dependence is already summarized into the
input validation report.

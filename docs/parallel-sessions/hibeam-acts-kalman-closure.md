# Lane: hibeam-acts-kalman-closure

## Goal

Add a fail-closed audit that proves every HIBEAM TPC tracking method family in
`acts_tracking/` (Kalman, CKF, vertex fits) reports the evidence the HIBEAM GNN
Overleaf article requires before any thesis use: pinned dataset id, truth
source, split, sigma_r, epsilon, and deployable/oracle status. No model
training, no SLURM, no edits to existing tracking or article source — only a
new audit helper plus tests that emit structured blockers when evidence is
missing.

## Files

- Prefer creating: `nnbar_reconstruction/analysis/hibeam_acts_audit.py` (<=500 lines)
- Test: `tests/test_hibeam_acts_audit.py`
- Read-only references:
  - `acts_tracking/INTEGRATION_GUIDE.md`
  - `acts_tracking/` source/configs (do not edit)
  - `docs/parallel-sessions/hibeam-gnn-feature-contract.md` (prior fail-closed pattern)
  - `docs/parallel-sessions/hibeam-vertex-method-closure.md` (prior fail-closed pattern)
- Update: `docs/parallel-sessions/MASTER_PLAN.md` status/notes only (row
  `HIBEAM ACTS/Kalman baseline integration closure` in PROPOSED TASKS — promote
  to a `NEXT`/`DONE` row in the NNBAR Reconstruction table on completion)

Do not edit C++, the HIBEAM Overleaf article, `acts_tracking/` production code,
or submit SLURM jobs. Do not retrain or rerun any tracking model.

## Implementation steps

1. Re-read `docs/parallel-sessions.md`, this spec, `CODING_STANDARDS.md`,
   `docs/parallel-sessions/hibeam-gnn-feature-contract.md`, and
   `docs/parallel-sessions/hibeam-vertex-method-closure.md` for the prior
   fail-closed audit pattern.
2. Enumerate the HIBEAM tracking method families from `acts_tracking/`
   (e.g. Kalman fit, CKF combinatorial finder, vertex fitter, ambiguity
   resolution stages). Treat the family list as data, not code paths.
3. For each family, require the following evidence keys:
   `dataset_id` (pinned), `truth_source` (oracle vs. deployable), `split`
   (train/val/test), `sigma_r`, `epsilon`, and `deployable_or_oracle` status.
   Missing/placeholder values must be reported as structured blockers
   (`missing_dataset_id`, `missing_truth_source`, `missing_split`,
   `missing_sigma_r`, `missing_epsilon`, `missing_status`, `todo_marker`).
4. Write failing tests first: a synthetic evidence dict per family that is
   complete should report zero blockers; one with a `TODO` marker or absent
   field should surface the matching structured blocker enum. Cover the case
   where `acts_tracking/INTEGRATION_GUIDE.md` is unavailable (skip-safe).
5. Implement the audit helper as pure-Python data inspection only. No
   imports from `acts_tracking/`, no subprocess calls, no network/SLURM, no
   model loading.
6. Run focused and full pytest; confirm every touched source/test file is
   <=500 lines.
7. Update this lane's `MASTER_PLAN.md` row to `DONE` only after focused and
   full tests pass and blocker categories are documented in the row notes.

## Verification

Run:

```bash
rtk python -m pytest tests/test_hibeam_acts_audit.py -q
rtk zsh -lc 'python -m pytest tests/ -x -q 2>&1 | tail -20'
rtk wc -l nnbar_reconstruction/analysis/hibeam_acts_audit.py tests/test_hibeam_acts_audit.py docs/parallel-sessions/MASTER_PLAN.md
rtk proxy bash -lc 'grep -nE "from acts_tracking|import acts_tracking" nnbar_reconstruction/analysis/hibeam_acts_audit.py tests/test_hibeam_acts_audit.py || echo OK_NO_PRODUCTION_IMPORT'
```

Expected: focused tests pass; full test command exits 0; touched files
<=500 lines; no production `acts_tracking` imports leak into the audit
module or its tests; current audit remains intentionally fail-closed
because dataset id / sigma_r / epsilon evidence is not yet pinned.

## Stop condition

Stop after one compact audit-helper + tests + MASTER_PLAN row update is
committed. Do not extend into model training, dataset staging, or
modifications to `acts_tracking/` source.

# Lane: rfc-feature-provenance

## Goal

Close the RFC feature provenance gap: the classifier input columns must either
come from canonical Ch. 9 event-variable outputs and documented cosmic weights,
or fail closed with explicit blockers. This lane should add contract tests and a
small audit/helper layer before any broad RFC refactor.

## Files

- Prefer creating: `nnbar_reconstruction/analysis/rfc_feature_provenance.py`
- Modify only if needed and under cap: `nnbar_reconstruction/ml/feature_extraction.py`
- Test: `tests/test_rfc_feature_provenance.py` or focused additions to
  `tests/test_rfc.py`
- Read-only references:
  - `nnbar_reconstruction/analysis/event_variables.py`
  - `nnbar_reconstruction/data_pipeline/cosmic_weights.py`
  - `nnbar_reconstruction/ml/rfc_classifier.py`
- Update: `docs/parallel-sessions/MASTER_PLAN.md` status/notes only

Do not retrain models, edit binary model artifacts, or run simulations/SLURM jobs.

## Implementation steps

1. Re-read `docs/parallel-sessions.md`, this spec, and `CODING_STANDARDS.md`.
2. Write failing tests for RFC provenance checks that distinguish:
   - canonical event-variable columns produced from `EventVariables.to_dict()`;
   - hit-level fallback columns in `extract_rfc_features` that need provenance;
   - cosmic-weight availability via `get_weight` or a supplied weight column;
   - missing provenance/weight evidence as explicit blockers.
3. Implement a compact audit/helper that reports per-feature status for every
   `RFC_FEATURE_COLUMNS` entry without changing classifier hyperparameters.
4. If a minimal `extract_rfc_features` adjustment is required, keep it small and
   preserve existing tests; otherwise leave production extraction unchanged and
   document the blocker in the audit result.
5. Update this lane's `MASTER_PLAN.md` row to `DONE` only for the completed
   provenance contract and tests; leave any larger feature-extraction rewrite as
   a named blocker.

## Verification

Run:

```bash
rtk python -m pytest tests/test_rfc.py tests/test_rfc_feature_provenance.py -q
rtk zsh -lc 'python -m pytest tests/ -x -q 2>&1 | tail -20'
rtk wc -l nnbar_reconstruction/analysis/rfc_feature_provenance.py nnbar_reconstruction/ml/feature_extraction.py tests/test_rfc.py tests/test_rfc_feature_provenance.py docs/parallel-sessions/MASTER_PLAN.md
```

Expected: focused tests pass; full test command exits 0; every touched source
and test file is <=500 lines.

## Stop condition

Stop after one compact provenance-contract unit and the `MASTER_PLAN.md` status
update are committed. Do not bundle model training or broad feature rewrites.

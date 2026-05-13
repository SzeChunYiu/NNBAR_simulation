# Lane: cosmic-background-rate-audit

## Goal

Implement a fail-closed audit for the Ch. 9 cosmic-background rate estimate and
its 27-bin CRY combination evidence.

## Files to create/edit

- Create `nnbar_reconstruction/analysis/cosmic_background_rate_audit.py`
- Create `tests/test_cosmic_background_rate_audit.py`
- Read `scripts/combine_cosmic_background.py` and
  `nnbar_reconstruction/data_pipeline/cosmic_weights.py` before choosing input
  contracts.

Do not run simulations or submit SLURM jobs.

## Implementation steps

1. Check that all 27 CRY particle/energy bins are represented by non-stub output
   or an explicit documented shard/root-stub blocker.
2. Verify weighted-sum normalization, livetime scaling, and output rate columns
   are present and numeric.
3. Treat known gamma-bin4 shard-vs-root-stub evidence as a documented blocker
   unless a merge artifact exists.
4. Add synthetic tests for all bins present, missing-bin blockers, and invalid
   normalization/livetime fields.

## Test command

```bash
rtk proxy python -m pytest tests/test_cosmic_background_rate_audit.py -q
```

## Stop condition

Commit when the focused tests pass, touched files are below 500 lines, and the
audit fails closed for missing or nonnumeric cosmic-rate evidence.

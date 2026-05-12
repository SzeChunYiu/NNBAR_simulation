# Lane: pi0-multiplicity-response-audit

## Goal

Implement a fail-closed audit for multi-π0 response studies covering 1, 2, and
3 π0 events at the same nominal energy.

## Files to create/edit

- Create `nnbar_reconstruction/analysis/pi0_multiplicity_response_audit.py`
- Create `tests/test_pi0_multiplicity_response_audit.py`
- Read the neutral π0 response audit and pi0 reconstruction helpers before
  choosing column names.

Do not run simulations or submit SLURM jobs.

## Implementation steps

1. Require one evidence table per multiplicity with event count, reco efficiency,
   invariant-mass confusion rate, and opening-angle separation summaries.
2. Return blockers for missing samples, missing response columns, or nonnumeric
   metrics.
3. Add synthetic pileup tests for green one/two/three-π0 inputs and missing
   multi-π0 sample blockers.

## Test command

```bash
rtk proxy python -m pytest tests/test_pi0_multiplicity_response_audit.py -q
```

## Stop condition

Commit when focused tests pass, touched files are below 500 lines, and the audit
has no side effects beyond reading provided evidence files.

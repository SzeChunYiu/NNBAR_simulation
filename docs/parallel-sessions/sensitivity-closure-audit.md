# Lane: sensitivity-closure-audit

## Goal

Implement a fail-closed sensitivity closure audit for the Ch. 9/10 sensitivity
calculation. The audit must report structured blockers unless every ingredient
needed for the sensitivity estimate is evidence-backed.

## Files to create/edit

- Create `nnbar_reconstruction/analysis/sensitivity_closure_audit.py`
- Create `tests/test_sensitivity_closure_audit.py`
- Read existing `nnbar_reconstruction/analysis/sensitivity.py` before choosing
  formulas or column names.

Do not run simulations or submit SLURM jobs.

## Implementation steps

1. Define a small dataclass result with `ready`, `blockers`, and per-ingredient
   evidence fields.
2. Check for signal efficiency, cosmic rate, beam-background rate, livetime, and
   zero-survivor Poisson-limit inputs in explicit columns or registry records.
3. Return blockers for each missing or nonnumeric ingredient; never invent
   defaults.
4. Add focused tests for all-missing input, a fully populated synthetic green
   input, and one partial-input blocker case.

## Test command

```bash
rtk proxy python -m pytest tests/test_sensitivity_closure_audit.py -q
```

## Stop condition

Commit when the focused tests pass, touched files are below 500 lines, and the
audit fails closed on missing sensitivity ingredients without side effects.

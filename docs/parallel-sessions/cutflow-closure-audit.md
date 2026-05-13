# Lane: cutflow-closure-audit

## Goal

Implement a fail-closed audit proving the thesis Table 9.1 event-selection
cutflow is represented in the Python event-selection path with the expected
observable names, thresholds, and order.

## Files to create/edit

- Create `nnbar_reconstruction/analysis/cutflow_closure_audit.py`
- Create `tests/test_cutflow_closure_audit.py`
- Read `nnbar_reconstruction/analysis/event_selection.py` and existing cutflow
  tests before deciding the audit surface.

Do not run simulations or submit SLURM jobs.

## Implementation steps

1. Encode the required Table 9.1 cut names/order as audit expectations, with
   references to existing constants instead of duplicating values when possible.
2. Verify every required observable exists and every threshold is numeric and
   provenance-tagged.
3. Return structured blockers for missing cuts, wrong order, missing observable
   names, or missing provenance.
4. Add tests covering a complete synthetic cutflow and individual failure modes.

## Test command

```bash
rtk proxy python -m pytest tests/test_cutflow_closure_audit.py -q
```

## Stop condition

Commit when focused tests pass, touched files are below 500 lines, and the audit
can fail closed without altering production selection behaviour.

# Lane: photon-conversion-fraction-mismatch

## Goal

Diagnose the remaining photon-conversion map blocker after the Interaction
parquet audit fix: the staged `photon_100MeV_conversion` sample now has real
conversion-volume fractions, but several detector fractions differ from the
thesis targets at tolerance 0.010.

## Files to create/edit

- Create `docs/reports/photon_conversion_fraction_mismatch.md`
- Read-only: `nnbar_reconstruction/analysis/photon_conversion_audit.py`
- Read-only: staged local sample under
  `build_lunarc/output/photon_100MeV_conversion/`
- Update `docs/parallel-sessions/MASTER_PLAN.md` row status/evidence only

Do not run simulations, submit SLURM jobs, retune physics constants, or change
production reconstruction code in this lane.

## Implementation steps

1. Re-run the photon conversion audit on the staged local sample and capture the
   exact totals/fractions/blockers.
2. Inspect the conversion-volume labels used by the audit: raw `Current_Vol`
   counts, canonical detector mapping counts, and any unmapped labels.
3. Compare the audited fractions against the thesis target table already
   encoded in the audit module; identify whether the mismatch is due to sample
   statistics, volume canonicalization, geometry/material setup, or an
   unresolved physics/modeling difference.
4. Write a fail-closed report with evidence, tables, and a short recommended
   next action. If the cause is still unknown, leave an `OPEN:` blocker with the
   exact missing evidence needed.
5. Update the MASTER_PLAN photon conversion rows only with the compact outcome.

## Test command

```bash
rtk proxy python -m pytest tests/test_photon_conversion_audit.py -q
rtk proxy bash scripts/validate-csup-queues.sh
```

## Stop condition

Commit when the report exists, the focused test and queue validator pass, line
caps are respected, and no production code or simulation output was changed.

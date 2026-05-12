# Paper section 6 — Physics parity evidence plan

Status: **BLOCKED**

This specification defines the evidence required before the paper can claim that
an optimized Geant4/G4GPU path preserves physics observables. It binds section 6
to the KS-test parity gate in `docs/specs/paper-methodology.md` and to the
`benchmarks/harness/parity.py` contract in `docs/specs/benchmark-harness.md`.

## Section purpose

Section 6 reports whether each optimized result is statistically compatible with
vanilla Geant4 for the fixed workload, physics-list, seed, and hardware matrix.
It is the approval gate for moving measured speedups into the main results
section. A performance win with failed parity remains a negative result and must
not be promoted as a physics-preserving acceleration.

## Required evidence before prose can be drafted

- Vanilla and optimized per-seed observable arrays exist for every cited row.
- The seed list is identical between vanilla and optimized samples.
- KS p-values are recorded for `Edep_total`, `step_count`,
  `secondary_multiplicity`, `first_step_length`, and `neutron_capture_rate` for
  W4 where applicable.
- `parity_pass` is true only when every required observable has p-value > 0.05.
- Any failed observable is named in the harness row and appears in a parity-fail
  table.
- The reference dataset manifest and hardware evidence are frozen before parity
  interpretation.

## Figures and tables

- Table 6.1: parity coverage matrix by optimization, workload, and physics list.
- Table 6.2: minimum KS p-value per observable group for L3 rows.
- Figure 6.1: vanilla-vs-optimized observable distributions for representative
  passing rows.
- Figure 6.2: failed-observable diagnostics for `PARITY_FAIL` rows.
- Supplementary Table S2: all parity-fail rows with row IDs, failing observable,
  p-value, and linked harness artifacts.

## Current gaps

- OPEN: `parity_module_missing` — `benchmarks/harness/parity.py` is absent.
- OPEN: `schema_module_missing` — `benchmarks/harness/schema.py` is absent, so
  parity row fields are not yet centralized.
- OPEN: `reference_samples_missing` — vanilla reference Parquet samples and the
  SHA-256 manifest are absent.
- OPEN: `results_rows_missing` — no `benchmarks/results/results.parquet` rows
  exist for parity interpretation.
- OPEN: `workload_matrix_unmeasured` — W1--W6 physics-list parity coverage is
  not populated.

## Acceptance checklist

- [ ] `benchmarks/harness/parity.py` implements the KS gate with focused tests.
- [ ] Harness rows contain all parity p-values and failing-observable metadata.
- [ ] Every L3 result has matching vanilla and optimized seed sets.
- [ ] Every `PARITY_FAIL` row is retained and documented.
- [ ] Section 5 speedup tables reference only rows with passing parity.

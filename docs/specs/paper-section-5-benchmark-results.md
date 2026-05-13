# Paper section 5 — Benchmark results evidence plan

Status: **BLOCKED**

This specification defines the evidence required before the paper's benchmark
results section can cite any Geant4/G4GPU speedup. It implements the claim
rules from `docs/specs/paper-methodology.md` and the harness contract in
`docs/specs/benchmark-harness.md`.

## Section purpose

Section 5 reports measured wall-clock and per-step performance for the fixed
W1--W6 workload matrix. It must separate main-table L3 results from L2 smoke
measurements and L1 estimates, and it must include neutral, regression, and
parity-failure outcomes in supplementary material rather than silently dropping
them.

## Required evidence before prose can be drafted

- `benchmarks/results/results.parquet` exists and is append-only.
- Every cited optimization row includes `opt_id`, `workload_id`,
  `physics_list`, `hw_id`, `n_seeds`, seed list, `speedup_mean`,
  `speedup_ci95_lo`, `speedup_ci95_hi`, `claim_level`, `result_tag`, and
  `parity_pass`.
- Main-result rows are at claim level L3 or higher. L2 rows may appear only in a
  validation or methods paragraph, never in the main speedup table.
- Reference datasets are pinned by `benchmarks/reference/MANIFEST.sha256`.
- Hardware and build evidence exist for every row under
  `benchmarks/hardware_evidence/` and `benchmarks/build_logs/`.
- The row's optimized commit or branch is traceable to an isolated G4GPU worktree
  and does not imply NNBAR production has switched away from vanilla Geant4.

## Figures and tables

- Table 5.1: workload and physics-list coverage by optimization ID.
- Table 5.2: L3 speedup results with 95% confidence intervals.
- Figure 5.1: speedup CI bars grouped by workload and hardware.
- Figure 5.2: per-step or steps-per-event comparison for performance attribution.
- Supplementary Table S1: `NEUTRAL` and `REGRESSION` rows.
- Supplementary Table S2: `PARITY_FAIL` rows with failing observables.

## Current gaps

- OPEN: `harness_modules_missing` — `benchmarks/harness/schema.py`,
  `parity.py`, `builder.py`, `runner.py`, `hardware.py`, and `run.py` are not
  present in this checkout.
- OPEN: `results_parquet_missing` — `benchmarks/results/results.parquet` is not
  present, so no measured row can be cited.
- OPEN: `reference_manifest_missing` — the vanilla reference manifest is absent.
- OPEN: `hardware_matrix_missing` — no H1/H2/H3/H4 coverage rows exist.
- OPEN: `competitor_baseline_missing` — Celeritas/AdePT comparison rows are not
  measured for this section.

## Acceptance checklist

- [ ] Harness modules 1--6 from `docs/specs/benchmark-harness.md` are present and
      have focused tests.
- [ ] Reference generation is approved and manifest-pinned.
- [ ] Every W1--W6 result row has the required seed, build, hardware, and commit
      evidence.
- [ ] Every main-table row is L3+ with `parity_pass = True`.
- [ ] Negative and parity-fail outcomes are represented in supplementary tables.
- [ ] Captions cite the exact harness row filters and commit IDs.

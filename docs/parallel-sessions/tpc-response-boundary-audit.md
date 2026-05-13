# Lane: tpc-response-boundary-audit

## Goal

Make the TPC response and digitization boundary explicit, machine-readable, and
tested. The lane should separate the thesis first-order electron-count response
from advanced drift, pad, gain, diffusion, field-map, Garfield, or GPU paths so
future reconstruction claims cannot mix evidence levels silently.

## Writable scope

- Create: `nnbar_reconstruction/analysis/tpc_response_boundary.py`
- Create: `tests/test_tpc_response_boundary.py`
- Modify only for lane status: `docs/parallel-sessions/MASTER_PLAN.md`

Forbidden:

- Do not edit C++ simulation, CUDA/GPU, SLURM, or LUNARC files.
- Do not change the production TPC W-value policy; that is owned by
  `tpc-w-value-policy-audit`.
- Do not add a new CLI command in this iteration.
- Do not cite unverified line numbers, non-existent files, or unsupported
  `python -m nnbar_reconstruction.*` commands.

## Required reading

1. `docs/parallel-sessions.md`
2. `docs/parallel-sessions/MASTER_PLAN.md`
3. `CODING_STANDARDS.md`
4. `docs/rebuild_plans/09_io_schema_data_dictionary.md`
5. `docs/rebuild_plans/17_field_calibration.md`
6. `docs/rebuild_plans/45_systematics_taxonomy.md`
7. `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/5_Detector_simulation.tex`
8. `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/7_Reconstruction.tex`

Before committing any file, function, path, or command claim, apply the verifier
rules in `docs/parallel-sessions.md`.

## One compact-safe iteration

1. Claim the lane by changing its MASTER_PLAN row from `NEXT` to `RUNNING` and
   committing that status-only change.
2. Build a small data model that records each TPC response surface as one of:
   `thesis_first_order`, `production_schema`, `advanced_non_thesis`, or
   `missing_or_unverified`.
3. Record the thesis first-order contract after verifying the required reading:
   Poisson ionisation-electron counts, segment/cell dimensions, required parquet
   columns, and the evidence source for each item.
4. Record advanced paths only as non-authoritative or missing unless the worker
   verifies local source evidence. Do not infer Garfield/GPU drift support from
   comments or stale docs.
5. Add pure audit helpers that can classify a schema or config dictionary without
   reading local absolute paths.
6. Add tests with toy inputs for:
   - thesis electron-count schema accepted;
   - missing `electrons` column rejected or downgraded;
   - advanced drift/gain/diffusion flags classified as non-thesis evidence;
   - no absolute paths are required.
7. Add one integration-style test against the current repo config or schema docs
   only if it remains deterministic and does not need sample parquet files.
8. Mark the MASTER_PLAN row `DONE` only after focused/full pytest and file-cap
   checks pass.

## Verification command

```bash
rtk python -m pytest tests/test_tpc_response_boundary.py -q
rtk proxy zsh -lc "python -m pytest tests/ -x -q 2>&1 | tail -20"
rtk proxy wc -l nnbar_reconstruction/analysis/tpc_response_boundary.py tests/test_tpc_response_boundary.py
```

## Stop condition

Stop after the boundary audit module/tests are committed, touched files remain
under 500 lines, and MASTER_PLAN states which TPC response surface is
thesis-authoritative versus non-thesis or still unverified.

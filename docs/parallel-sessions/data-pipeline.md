# Lane: data-pipeline

## Goal

Create the `nnbar_reconstruction/data_pipeline/` Python package from scratch.

## Worktree

`/Volumes/MyDrive/nnbar/nnbar/simulation-data-pipeline` (branch: `lane/data-pipeline`)

## Writable Targets

- `nnbar_reconstruction/data_pipeline/__init__.py` (new)
- `nnbar_reconstruction/data_pipeline/load_simulation_data.py` (new)
- `nnbar_reconstruction/data_pipeline/run_clustering_pipeline.py` (new)
- `nnbar_reconstruction/data_pipeline/prepare_gnn_training_data.py` (new)

Do NOT touch any other files.

## Full Spec

Read the complete spec at:
`nnbar_reconstruction/data_pipeline/SPEC.md`

It contains exact function signatures, column names, feature definitions,
and output formats. Follow it exactly.

## Reference Code

Read before writing anything:
- `nnbar_reconstruction/tracking/clustering.py` — style reference, existing DBSCAN logic
- `nnbar_reconstruction/IMPROVEMENT_TASK.md` — background context and data format

## Test Data

A small real dataset (one run, ~few events) is at:
`/Volumes/MyDrive/nnbar/nnbar/simulation/NNBAR_Detector/output/`

Use this to verify your code loads without error. Do not hardcode this path.

## Iteration Cycle

One file per iteration:
1. Re-read `docs/parallel-sessions.md` and this file.
2. Create one file per the spec.
3. Syntax check: `python3 -m py_compile <file>`
4. Quick smoke test loading the test data (print shape, first rows).
5. `git add nnbar_reconstruction/data_pipeline/<file>` and commit.
6. Continue to next file.

## Commit Format

```
feat(data-pipeline): <description>

Lane: data-pipeline
```

## Stop Condition

All four files created, syntax-checked, and committed.

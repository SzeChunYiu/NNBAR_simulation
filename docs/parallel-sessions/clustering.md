# Lane: clustering

## Goal

Enhance `nnbar_reconstruction/tracking/clustering.py` and create
`nnbar_reconstruction/tracking/clustering_config.yaml`.

## Worktree

`/Volumes/MyDrive/nnbar/nnbar/simulation-clustering` (branch: `lane/clustering`)

## Writable Targets

- `nnbar_reconstruction/tracking/clustering.py` (modify in place)
- `nnbar_reconstruction/tracking/clustering_config.yaml` (new)

Do NOT touch any other files.

## Full Spec

Read the complete spec at:
`docs/specs/clustering-enhancements.md`

It lists exactly what functions to add, what to change, and what the YAML must contain.

## Critical Rule

**ALL existing public function signatures must remain identical.**
This is additive only — new functions and new top-level definitions.
Do not rename, reorder, or change any existing function.

## Iteration Cycle

One enhancement per iteration:
1. Re-read `docs/parallel-sessions.md` and this file.
2. Read the full spec at `docs/specs/clustering-enhancements.md`.
3. Add one enhancement (e.g. `load_clustering_config`, or `cluster_with_hdbscan`).
4. Syntax check: `python3 -m py_compile nnbar_reconstruction/tracking/clustering.py`
5. `git add` and commit.
6. Continue to next enhancement.

Create `clustering_config.yaml` as its own commit after all function additions are done.

## Commit Format

```
feat(clustering): <description>

Lane: clustering
```

## Stop Condition

All four enhancements committed + `clustering_config.yaml` created and committed.
File stays under 1000 lines (original was ~831; additions should be ~150 lines).

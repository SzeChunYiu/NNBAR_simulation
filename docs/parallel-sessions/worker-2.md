# Lane: worker-2 (Python / Analysis worker — secondary)

## Scope

Same scope as worker-1: Python code in `nnbar_reconstruction/`, analysis scripts,
classifiers, cuts, weights, data pipeline, pytest tests, Parquet I/O.

It does NOT write C++, CUDA, or LUNARC infrastructure (that is pane 0's scope).
It does NOT compete with worker-1 — all tasks are assigned via the queue file
`codex-tasks/worker-2.txt` by the planner to prevent MASTER_PLAN race conditions.

## Every iteration

### Step 1 — Check queue

Read `codex-tasks/worker-2.txt`. If the file is non-empty, the first line is
your goal. Pop it and proceed directly to Step 3.

If the file is empty, go to Step 2.

### Step 2 — Check MASTER_PLAN for unassigned NEXT tasks

Read `docs/parallel-sessions/MASTER_PLAN.md`. Look for tasks with status `NEXT`
that match this pane's scope AND are not already being handled by worker-1 (i.e.
not in `codex-tasks/worker-1.txt`).

If a matching NEXT task exists with a spec file, claim it (Step 3).

If nothing is available:
```
WORKER-2 IDLE: no queued or NEXT tasks available
```
Then stop.

### Step 3 — Claim and implement

1. Update MASTER_PLAN.md: change task status from `NEXT` → `RUNNING`
2. Commit: `git commit -m "wip: mark <task> RUNNING"`
3. Read the task's spec file from `docs/parallel-sessions/<name>.md`
4. Implement the task fully per the spec
5. Run verification: `python -m pytest tests/ -x -q 2>&1 | tail -20`
6. Commit the implementation
7. Update MASTER_PLAN.md: `RUNNING` → `DONE`
8. Commit: `git commit -m "feat(<lane>): <description>"`

### Step 4 — Stop condition

After marking DONE, **stop**. The supervisor will resend this prompt and you
will pick the next queued task automatically.

## Scope keywords (any of these = pane 2 territory)

- Python, `.py`, pytest, `nnbar_reconstruction/`
- HIBEAM GNN, TrackGNN, VertexGNN, vertex method
- RFC, classifier, sklearn, random forest
- π⁰ cuts, pi0, diphoton, invariant mass
- cosmic weights, `w_{i,j}`, `combine_cosmic_background`
- data pipeline, Parquet, clustering, feature extraction
- analysis, reconstruction, cutflow, sensitivity
- thesis reproduction ledger, geometry constants, W-value

## Important constraints

- Only write files inside `nnbar_reconstruction/` or `tests/` or `docs/`
- Do NOT touch C++ files or LUNARC infrastructure (pane 0's scope)
- Do NOT claim tasks already in worker-1.txt (check before claiming)
- Working directory: `/Volumes/MyDrive/nnbar/nnbar/simulation/`
- Run tests with: `python -m pytest tests/ -x -q`

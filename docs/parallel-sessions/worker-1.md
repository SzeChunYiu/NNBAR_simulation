# Lane: worker-1 (Python / Analysis worker)

## Scope

This pane handles: Python code in `nnbar_reconstruction/`, analysis scripts,
classifiers, cuts, weights, data pipeline, pytest tests, Parquet I/O.

It does NOT write C++, CUDA, or LUNARC infrastructure (that is pane 0's scope).

## Every iteration

### Step 1 — Check for a running task

Read `docs/parallel-sessions/MASTER_PLAN.md`. If any task is marked `RUNNING`
and falls within this pane's scope (Python/analysis), continue that task first
before picking a new one.

### Step 2 — Pick the next task

Find the first row in MASTER_PLAN.md with status `NEXT` that matches this
pane's scope. Tasks with an explicit spec file in `docs/parallel-sessions/`
take priority.

**Scope keywords (any of these = pane 1 territory):**
- Python, `.py`, pytest, `nnbar_reconstruction/`
- RFC, classifier, sklearn, random forest
- π⁰ cuts, pi0, diphoton, invariant mass
- cosmic weights, `w_{i,j}`, `combine_cosmic_background`
- data pipeline, Parquet, clustering, feature extraction
- analysis, reconstruction, cutflow

### Step 3 — Claim and implement

1. Update MASTER_PLAN.md: change task status from `NEXT` → `RUNNING`
2. Commit: `git commit -m "wip: mark <task> RUNNING"`
3. Read the task's spec file (e.g. `docs/parallel-sessions/cosmic-weight-analysis.md`)
4. Implement the task fully per the spec
5. Run verification: `python -m pytest tests/ -x -q 2>&1 | tail -20`
6. Commit the implementation
7. Update MASTER_PLAN.md: `RUNNING` → `DONE`
8. Commit: `git commit -m "feat(<lane>): <description>"`

### Step 4 — Stop condition

After marking DONE, **stop**. The supervisor will resend this prompt and you
will pick the next NEXT task automatically.

If no NEXT task matches this pane's scope, write to stdout:
```
WORKER-1 IDLE: no matching NEXT tasks in MASTER_PLAN.md
```
Then stop. The supervisor will resend this prompt when new tasks are added.

## Important constraints

- Only write files inside `nnbar_reconstruction/` or `tests/`
- Do NOT touch C++ files or LUNARC infrastructure (pane 0's scope)
- Working directory: `/Volumes/MyDrive/nnbar/nnbar/simulation/`
- Run tests with: `python -m pytest tests/ -x -q 2>&1 | tail -20`
- **Local resource policy**: pytest unit tests are acceptable locally. Do NOT
  run large data pipelines, ML training, or SLURM jobs locally. Training,
  large-scale inference, and data generation go to LUNARC.

# Lane: worker-2 (legacy Python / analysis worker — secondary)

> **Migration note (2026-05-13):** the flat local queue
> `codex-tasks/worker-2.txt` is inactive. The active supervisor topology is the
> five-session LUNARC layout in `docs/parallel-sessions.md` and
> `docs/parallel-sessions/MASTER_PLAN.md`; for the current recon PANE 2 launch
> prompt, use `docs/parallel-sessions/rfc-feature-provenance.md` and the active
> queue directory named in `codex-prompts-recon.txt`.

## Scope

Same scope as worker-1: Python code in `nnbar_reconstruction/`, analysis scripts,
classifiers, cuts, weights, data pipeline, pytest tests, Parquet I/O.

It does NOT write C++, CUDA, or LUNARC infrastructure (that is pane 0's scope).
It does NOT compete with worker-1 — active tasks are assigned by the current
session queue files under `codex-tasks/{recon,sim,g4gpu,review,meta}/` and by
`MASTER_PLAN.md`, not by the migrated flat queue file.

## Every iteration

### Step 0 — Resolve the active lane

1. Re-read `docs/parallel-sessions.md` first.
2. Check the relevant prompt file (`codex-prompts-recon.txt` for Python/recon
   PANE 2) and follow the lane-specific markdown named there.
3. Treat this file as a legacy compatibility note unless the prompt file or
   `MASTER_PLAN.md` explicitly points back to it.

### Step 1 — Check active queue

Do **not** pop from `codex-tasks/worker-2.txt` when it contains the `MIGRATED`
banner. Use the active queue file named by the current prompt/lane instead
(for example `codex-tasks/recon/worker-2.txt` for recon PANE 2).

If the file is empty, go to Step 2.

### Step 2 — Check MASTER_PLAN for unassigned NEXT tasks

Read `docs/parallel-sessions/MASTER_PLAN.md`. Look for tasks with status `NEXT`
that match this pane's scope AND are not already queued or handled by the
corresponding active worker-1 lane (for recon, check
`codex-tasks/recon/worker-1.txt`).

If a matching NEXT task exists with a spec file, claim it (Step 3).

If nothing is available:
```
WORKER-2 IDLE: no queued or NEXT tasks available
```
Then follow the shared `docs/parallel-sessions.md` "Never idle" fallback: take
one compact-safe plan-audit or gap-scan task inside this lane's writable scope.

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
- Do NOT claim tasks already in the active worker-1 queue (check before
  claiming)
- Working directory: `/Volumes/MyDrive/nnbar/nnbar/simulation/`
- Run tests with: `rtk python3 -m pytest tests/ -x -q 2>&1 | tail -20`
- **Local resource policy**: pytest unit tests are acceptable locally. Do NOT
  run large data pipelines, ML training, or SLURM jobs locally. Training,
  large-scale inference, and data generation go to LUNARC.

# Lane: worker-4 (G4GPU source-code review + research, isolated)

## Scope

This pane reads Geant4 source code line by line, identifies concrete
optimization opportunities, and produces written reports that feed the
implementation work in worker-3. It does NOT modify NNBAR or production
G4GPU code — it produces analyses, surveys, and recommendations.

Same isolation policy as worker-3: nothing under `NNBAR_Detector/`,
`nnbar_reconstruction/`, `scripts/`, `lunarc/`, `slurm/`, or `macro/` is
touched. See `docs/policies/g4gpu-isolation.md`.

## Why this lane exists

The user has directed us to "review the Geant4 source code line by line."
Implementation (worker-3) and source review/research (worker-4) are
independent activities that benefit from parallel execution. Splitting
them also keeps each iteration tight and compact-safe.

## Every iteration

### Step 1 — Check queue

Read `codex-tasks/worker-4.txt`. If non-empty, the first line is your goal.

If empty, go to Step 2.

### Step 2 — Pick a source-review or survey task

Read `docs/parallel-sessions/MASTER_PLAN.md` G4GPU section. Look for
`NEXT` rows in the survey / source-review / research category. If none,
write `WORKER-4 IDLE: no queued or NEXT survey/research tasks` and stop.

### Step 3 — Execute the research task

For source-review tasks specifically:
1. Locate the Geant4 source on LUNARC:
   ```bash
   rtk proxy bash -lc 'ssh -O check lunarc 2>/dev/null && echo "Connected" || /Users/billy/lunarc-init.sh'
   rtk proxy ssh lunarc 'find /sw/pkg/geant4* /usr/local/geant4* /projects -name "*.cc" -path "*/source/*" 2>/dev/null | head -3'
   rtk proxy ssh lunarc 'echo $G4INSTALL; geant4-config --prefix 2>/dev/null'
   ```
2. Read the specific hot-path source files identified in the task spec
3. Identify concrete optimization opportunities — for each, record:
   - Exact file + line range
   - Current code snippet
   - What's slow (cache miss, branch, divisions, allocations, etc.)
   - Proposed optimization (with reference if standard CS technique)
   - Expected speedup
   - Validation strategy (how to prove the optimization preserves physics)
4. Write findings to `docs/reports/g4_source_review_<topic>.md`
5. Commit on a feature branch
6. Update MASTER_PLAN if a new G4GPU implementation task should be queued for
   worker-3

For ML / algorithm survey tasks: produce the report per the relevant spec.

### Step 4 — Stop

After committing the report, stop.

## Scope keywords (any of these = worker-4 territory)

- Geant4 source review, line-by-line Geant4 review
- Hot-path identification, profiling analysis
- Quasi-Monte Carlo, SAH-BVH, JIT specialization research
- Algorithm surveys for G4GPU
- Literature surveys for HEP simulation acceleration
- `docs/specs/g4gpu-line-by-line-acceleration.md`

## Important constraints

### Isolation

Same hard rule as worker-3: never edit NNBAR_Detector/, nnbar_reconstruction/,
scripts/, lunarc/, slurm/, macro/. Only edit:
- `docs/reports/g4_*.md`, `docs/reports/g4gpu_*.md`, `docs/reports/ml_*.md`
- `docs/specs/g4gpu-*.md`
- `docs/parallel-sessions/g4gpu-*.md`, `docs/parallel-sessions/worker-4.md`
- `docs/parallel-sessions/MASTER_PLAN.md` (status updates only)
- `codex-tasks/worker-4.txt`

### Resource policy

- No local builds or simulations
- Web search / WebFetch is fine
- pytest is only allowed for any test scripts you produce alongside reports
- LUNARC SSH for reading source files: yes, after the socket guard

### Outputs

- Every report you produce must include exact file paths + line numbers for
  any optimization opportunity flagged
- Citations for any standard CS technique you reference (paper + year)
- A "validation strategy" subsection per recommendation
- Concrete next-step proposal: which G4GPU task this would unblock

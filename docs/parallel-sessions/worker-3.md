# Lane: worker-3 (G4GPU dedicated — C++/CUDA, isolated)

## Scope

This pane owns the **G4GPU R&D project only**. It works exclusively in
`/Volumes/MyDrive/nnbar/geant4-gpu/` (locally) and
`/projects/hep/fs10/shared/nnbar/billy/geant4-gpu/` (LUNARC).

It does NOT touch `NNBAR_Detector/`, `nnbar_reconstruction/`, `scripts/`,
`lunarc/`, `slurm/`, or `macro/` — those are NNBAR thesis-production
territory and are isolated from G4GPU by policy
(`docs/policies/g4gpu-isolation.md`).

## Why this lane exists

G4GPU is exploratory. Mixing its work with NNBAR thesis-production work
risks accidental coupling. Giving G4GPU its own lane enforces isolation
by construction: worker-3 simply has no business writing under
`NNBAR_Detector/` or `nnbar_reconstruction/`, so it won't.

## Every iteration

### Step 1 — Check queue

Read `codex-tasks/worker-3.txt`. If the file is non-empty, the first line is
your goal. Pop it and proceed to Step 3.

If empty, go to Step 2.

### Step 2 — Check MASTER_PLAN for G4GPU NEXT tasks

Read `docs/parallel-sessions/MASTER_PLAN.md` G4GPU section. Pick the first
G4GPU-prefixed task with status `NEXT`. If none:

```
WORKER-3 IDLE: no queued or NEXT G4GPU tasks
```

Then stop.

### Step 3 — Claim and implement

1. Update MASTER_PLAN.md: change G4GPU task status from `NEXT` → `RUNNING`
2. Commit (in `nnbar/simulation`): `rtk git commit -m "wip: mark <task> RUNNING"`
3. Read the spec file (e.g. `docs/parallel-sessions/g4gpu-phase5.md`)
4. Implement in `/Volumes/MyDrive/nnbar/geant4-gpu/` on the appropriate
   `lane/g4gpu-<phase>` branch
5. **All builds and tests on LUNARC, never locally** — see Constraints
6. Commit on the G4GPU branch, push to GitHub
7. Update MASTER_PLAN.md (in `nnbar/simulation`): `RUNNING` → `DONE`
8. Commit: `rtk git commit -m "feat(g4gpu-<phase>): <description>"`

### Step 4 — Stop condition

After marking DONE, stop. Supervisor will resend this prompt.

## Scope keywords (any of these = worker-3 territory)

- G4GPU, geant4-gpu, libG4GPU
- VoxelGeometry, RTXGeometry, MuonStepKernel, EMStepKernel, NeutronStepKernel
- OptiX, CUDA, RT cores, Tensor cores, CUDA core kernels
- Phase 3 / 4 / 5 / 6 / 7 / 8 / 9 / 10 of the G4GPU acceleration plan
- Quasi-Monte Carlo, SAH-BVH, JIT specialization (LLVM ORC), cuckoo hashing
- Benchmark suite for G4GPU, perf profiling, ncu/Nsight reports
- `docs/specs/g4gpu-line-by-line-acceleration.md`

## Important constraints

### Isolation (overrides everything)

- **Never** edit anything under `NNBAR_Detector/`, `nnbar_reconstruction/`,
  `scripts/`, `lunarc/`, `slurm/`, or `macro/` in this lane.
- **Never** add G4GPU includes or links to NNBAR_Detector CMake.
- **Never** modify any SLURM script that feeds the NNBAR production pipeline.
- The only files in `nnbar/simulation` you may touch are:
  - `docs/parallel-sessions/MASTER_PLAN.md` (status updates)
  - `docs/parallel-sessions/g4gpu-*.md` (lane specs you authored)
  - `docs/specs/g4gpu-*.md` (your strategy docs)
  - `docs/reports/g4gpu_*.md` (your reports)
  - `docs/blockers/optix-*.md` (your blocker notes)
  - `codex-tasks/worker-3.txt` (popping from your queue)

### Resource policy

- **NEVER** run cmake, make, g++, or nvcc locally. All builds on LUNARC.
- **NEVER** run a Geant4 / G4GPU executable locally. All runs on LUNARC.
- Code-editing, git commits, doc updates are local-only.
- LUNARC build pattern:
  ```bash
  rtk proxy bash -lc 'ssh -O check lunarc 2>/dev/null && echo "Connected" || /Users/billy/lunarc-init.sh'
  rtk proxy rsync -av /Volumes/MyDrive/nnbar/geant4-gpu/ lunarc:/projects/hep/fs10/shared/nnbar/billy/geant4-gpu/
  rtk proxy ssh lunarc "cd /projects/hep/fs10/shared/nnbar/billy/geant4-gpu && cmake --build build -j8 && ctest --test-dir build --output-on-failure"
  ```

### LUNARC

- SSH socket guard before any LUNARC call:
  ```bash
  rtk proxy bash -lc 'ssh -O check lunarc 2>/dev/null && echo "Connected" || /Users/billy/lunarc-init.sh'
  ```
- SLURM account: `lu2026-2-51` | partition: `gpua40` for GPU, `lu48` for CPU
- All G4GPU SLURM jobs use the G4GPU build tree, never the NNBAR build tree

### Validation

Every kernel you add must:
- Pass a Geant4-reference regression test (or a clearly-flagged stub if the
  reference isn't yet implementable)
- Be reproducible under fixed seeds
- Have its expected speedup documented in the commit message
- Be incapable of being called from NNBAR_Detector (compile-time
  isolation — separate library, separate header tree)

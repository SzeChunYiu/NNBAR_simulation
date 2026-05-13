# Lane: worker-3 (G4GPU dedicated — C++/CUDA, isolated)

## Scope

This pane owns the **Geant4 acceleration project** — work intended to make
Geant4 itself faster for every user (HEP experiments, medical physics, space
radiation, etc.), not just NNBAR. The work splits in two channels:

1. **Upstreamable patches against Geant4 source** — non-GPU optimizations
   that benefit every user immediately. These are submitted as MRs against
   `gitlab.cern.ch/geant4/geant4` once validated.
2. **`libG4Accel` library** in `/Volumes/MyDrive/nnbar/geant4-gpu/` —
   GPU kernels and non-trivially-different algorithms that opt-in through
   Geant4's existing extension points (fast simulation, task system,
   process manager).

Locally the work happens in `/Volumes/MyDrive/nnbar/geant4-gpu/`; on LUNARC
in `/projects/hep/fs10/shared/nnbar/billy/geant4-gpu/`. A separate fork of
Geant4 (cloned from gitlab.cern.ch/geant4/geant4 at the v11.2.2 tag) sits at
`/Volumes/MyDrive/nnbar/geant4-fork/` locally and on LUNARC at
`/projects/hep/fs10/shared/nnbar/billy/geant4-fork/` — that is where upstream
patches are developed.

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

- Geant4 acceleration, libG4Accel, libG4GPU
- Upstream Geant4 patches (against gitlab.cern.ch/geant4/geant4)
- `geant4-fork` repo on local and LUNARC
- VoxelGeometry, RTXGeometry, MuonStepKernel, EMStepKernel, NeutronStepKernel
- OptiX, CUDA, RT cores, Tensor cores, CUDA core kernels
- Phase 3 / 4 / 5 / 6 / 7 / 8 / 9 / 10 of the acceleration plan
- Quasi-Monte Carlo, SAH-BVH, JIT specialization (LLVM ORC), cuckoo hashing
- Benchmark suite (canonical G4 examples: BasicExample, Hadr01, TestEm0,
  OpNovice2, etc.) + perf profiling, ncu/Nsight reports
- `docs/specs/g4gpu-line-by-line-acceleration.md`

## Output channels

Every implementation choice goes to one of two places:

| If the optimization... | Goes into | Validated against |
|------------------------|-----------|-------------------|
| Requires only CPU + standard C++ | `geant4-fork`, prepared as upstream MR | Canonical Geant4 examples, bit-exact under fixed seeds |
| Requires CUDA / RTX / GPU runtime | `libG4Accel` in `geant4-gpu` repo | Canonical examples via opt-in flag + NNBAR-equivalent events |
| Is risky / not yet upstreamable | `libG4Accel` first, then re-propose as MR after months of bake-in | Same as above |

Never put a CPU-only optimization solely in `libG4Accel`. CPU wins belong
upstream where every user benefits without compiling against the library.

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

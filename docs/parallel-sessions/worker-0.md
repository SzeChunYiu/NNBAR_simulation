# Lane: worker-0 (C++ / GPU / LUNARC worker)

## Scope

This pane handles: C++ code, CUDA kernels, LUNARC builds, SLURM scripts,
G4GPU phases, CRY integration, detector simulation infrastructure.

It does NOT write Python analysis code (that is pane 1's scope).

## Every iteration

### Step 1 — Check for a running task

Read `docs/parallel-sessions/MASTER_PLAN.md`. If any task is marked `RUNNING`
and falls within this pane's scope (C++/GPU/LUNARC), check whether it is:

- **Blocked on external work** (e.g. SLURM jobs running on LUNARC, jobs in queue,
  waiting for hardware): update the Notes field with current status, commit with
  `rtk git commit -m "docs(worker-0): refresh <task> blockers"`, then **proceed to
  Step 2** and pick a NEXT task from a different lane (do not idle).
- **Actionable** (there is code to write, a build to run, a script to fix): finish
  it, mark DONE, stop.

Never spend more than one commit updating a blocked task's notes — that is not
progress. Move on to real implementation work immediately.

### Step 2 — Pick the next task

Find the first row in MASTER_PLAN.md with status `NEXT` that matches this
pane's scope. Tasks with an explicit spec file in `docs/parallel-sessions/`
take priority.

**Scope keywords (any of these = pane 0 territory):**
- C++, CUDA, `.cu`, `.cc`, `.hh`, CMakeLists
- LUNARC, SLURM, build, rsync, guarded LUNARC SSH
- G4GPU, geant4-gpu, VoxelGeometry, MuonKernel, RTX, OptiX, optical photon
- CRY, cosmic generator, binary rebuild
- `NNBAR_Detector/`, `geant4-gpu/`

### Step 3 — Claim and implement

1. Update MASTER_PLAN.md: change task status from `NEXT` → `RUNNING`
2. Commit: `rtk git commit -m "wip: mark <task> RUNNING"`
3. Read the task's spec file (e.g. `docs/parallel-sessions/g4gpu-phase1.md`)
4. Implement the task fully per the spec
5. Run any required verification — **ALL builds and tests must run on LUNARC,
   not locally** (see constraints below)
6. Commit the implementation
7. Update MASTER_PLAN.md: `RUNNING` → `DONE`
8. Commit: `rtk git commit -m "feat(<lane>): <description>"`

### Step 4 — Stop condition

After marking DONE, **stop**. The supervisor will resend this prompt and you
will pick the next NEXT task automatically.

If no NEXT task matches this pane's scope, write to stdout:
```
WORKER-0 IDLE: no matching NEXT tasks in MASTER_PLAN.md
```
Then stop. The supervisor will resend this prompt when new tasks are added.

## Important constraints

### G4GPU isolation (overrides everything)

The NNBAR simulation is thesis-critical. G4GPU is exploratory R&D. They are
**entirely separate projects** and must not share code, builds, binaries, or
data provenance.

- **Never** add a G4GPU include, link, or `find_package(G4GPU)` to anything
  under `NNBAR_Detector/`, `nnbar_reconstruction/`, `scripts/`, `lunarc/`,
  `slurm/`, or `macro/`.
- **Never** swap a G4GPU kernel for a Geant4 process in the NNBAR pipeline,
  even for testing. G4GPU prototypes run in their own tree at
  `/Volumes/MyDrive/nnbar/geant4-gpu/` and on LUNARC at
  `/projects/hep/fs10/shared/nnbar/billy/geant4-gpu/`.
- **Never** submit a SLURM job that uses a G4GPU binary in the NNBAR
  production pipeline.
- All NNBAR-thesis production data must carry `simulator=geant4-11.2.2-...`
  provenance in Parquet metadata; G4GPU benchmark outputs stay in the
  G4GPU tree and never get copied into `results/`.

Full rationale and the physics-parity gate are in
`docs/policies/g4gpu-isolation.md`. If a task you are about to do appears to
violate this rule, refuse it and write a note in MASTER_PLAN.md.

### Resource policy — no heavy local work
- **NEVER run cmake, make, g++, nvcc, or any C++/CUDA compiler locally.**
  This machine is memory-constrained (190 MB free RAM). ALL compilation goes to
  LUNARC via SSH.
- **NEVER run SLURM simulations locally.** Use `sbatch` on LUNARC.
- **NEVER run large data-processing scripts locally.** Run on LUNARC.
- Python `pytest` (unit tests only, < 30 s) is acceptable locally.
- Code-editing, git commits, MASTER_PLAN.md updates are always fine locally.

Build pattern (always SSH to LUNARC):
```bash
# Sync source first, then build on LUNARC:
rtk proxy rsync -av /Volumes/MyDrive/nnbar/geant4-gpu/ lunarc:/projects/hep/fs10/shared/nnbar/billy/geant4-gpu/
rtk proxy ssh lunarc "cd /projects/hep/fs10/shared/nnbar/billy/geant4-gpu && cmake --build build -j8 2>&1 | tail -30"
```

- Only write files inside the task's specified writable scope
- Do NOT touch Python files in `nnbar_reconstruction/` (pane 1's scope)
- Before any LUNARC command, check or initialize the multiplexed socket:
  ```bash
  rtk proxy bash -lc "ssh -O check lunarc 2>/dev/null && echo Connected || /Users/billy/lunarc-init.sh"
  ```
- Run LUNARC SSH commands through RTK after the guard, for example:
  ```bash
  rtk proxy ssh lunarc "squeue -u scyiu -o '%.10i %.18j %.8T %.10M'"
  ```
- SLURM account: `lu2026-2-51` | partition: `lu48` (CPU), `gpua40` (GPU)
- geant4-gpu repo: `/Volumes/MyDrive/nnbar/geant4-gpu/`
- NNBAR_Detector on LUNARC: `/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/`

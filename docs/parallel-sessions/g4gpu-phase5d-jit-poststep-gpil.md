# Lane: g4gpu-phase5d-jit-poststep-gpil

## Goal

Start the highest-ranked follow-up from the structured Geant4 PIL/geometry
review: de-risk the BD-geant4-032/035 PostStep GPIL dispatch/thunk-table idea
with one compact, isolated Geant4-GPU prototype or guarded scaffold.

This is a compact-safe first implementation unit. It should prove semantics on
a small representative harness before any broad upstream Geant4 patch is
attempted.

## Required reading

1. `docs/parallel-sessions.md`
2. `docs/parallel-sessions/MASTER_PLAN.md`
3. `docs/reports/g4_bottleneck_database_pil_geometry.md` entries
   BD-geant4-032 and BD-geant4-035, plus the ranked next-implementation list
4. `docs/specs/g4gpu-line-by-line-acceleration.md`
5. `docs/policies/g4gpu-isolation.md`

## Writable scope

Primary worktree:

- `/Volumes/MyDrive/nnbar/geant4-gpu/`

Allowed changes there:

- A new branch or continuation branch for this lane.
- Minimal prototype/scaffold source, tests, CMake wiring, and short docs needed
  for the dispatch-table proof.
- Keep changes isolated from NNBAR production simulation and reconstruction.

Simulation checkout changes allowed only for handoff/status:

- `docs/parallel-sessions/MASTER_PLAN.md`
- this lane spec, if it needs a brief clarification
- the matching active queue file, only to pop/claim this queued task if the
  local/LUNARC queue protocol requires it

Forbidden paths:

- `NNBAR_Detector/`
- `nnbar_reconstruction/`
- production simulation macros, SLURM job scripts, and data artifacts in this
  repository
- any Geant4 source checkout outside the isolated Geant4-GPU worktree, unless
  used read-only for source comparison

## One-iteration task

1. Check the Geant4-GPU worktree status. If another pane has uncommitted Phase 5
   edits in the same files you would modify, do not overwrite them; stop with a
   blocker note in the handoff.
2. Create or update the smallest isolated prototype/scaffold that models the
   current process-vector GPIL dispatch and an optimized dispatch/thunk table.
3. Cover at least these semantic cases in tests or a verifier:
   - common non-forced process selection chooses the same process and proposed
     step as the vanilla loop;
   - forced/exclusive behavior remains a slow-path/fallback, not silently
     optimized away;
   - mutation or unsupported process state falls back rather than changing
     physics semantics.
4. Do not claim a physics speedup from the prototype. It may report expected
   future speedup only by citing BD-geant4-032/035.
5. Commit only your own Geant4-GPU changes. If you update this simulation
   checkout for status, stage explicit paths only.

## Verification

Run the smallest relevant local checks in the Geant4-GPU worktree, then use the
LUNARC guard before any remote build:

```bash
rtk proxy bash -lc 'ssh -O check lunarc 2>/dev/null && echo "Connected" || /Users/billy/lunarc-init.sh'
```

Minimum acceptable verification for this compact unit:

```bash
rtk proxy bash -lc 'cd /Volumes/MyDrive/nnbar/geant4-gpu && cmake --build build --target G4GPU'
rtk proxy bash -lc 'cd /Volumes/MyDrive/nnbar/geant4-gpu && ctest --test-dir build --output-on-failure -R "gpil|dispatch|process|stub"'
```

If the current build tree is absent or stale, configure/build in the manner
already used by the Geant4-GPU repo and record the exact commands in the
handoff. If build/test is blocked by another pane's in-flight Phase 5 changes,
record that blocker instead of force-cleaning or resetting.

## Stop condition

Stop after one bounded prototype/scaffold plus its verification or a concrete
blocker. Update `MASTER_PLAN.md` from `NEXT` to `RUNNING`/`DONE` only with
artifact evidence, and include:

- branch/commit path;
- changed files;
- verification commands and results;
- whether any unsupported GPIL behavior intentionally falls back;
- next recommended implementation step.

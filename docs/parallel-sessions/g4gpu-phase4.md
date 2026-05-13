# Lane: g4gpu-phase4 (Opticks integration boundary)

## Role

You are an isolated G4GPU worker. Keep all implementation work in the
`geant4-gpu` side project; do not touch NNBAR production simulation,
reconstruction, data, macros, or SLURM output paths.

## Goal

Refresh Phase 4 from a custom optical-photon OptiX rewrite into a fail-closed
Opticks integration boundary. The compact first unit is **not** to claim optical
transport speedup. It is to make G4GPU able to discover, document, and call an
Opticks bridge when available, while preserving a clean `G4GPU_WITH_OPTICKS=OFF`
build when Opticks is absent.

## Repo and branch

Work in the isolated repo:

```text
/Volumes/MyDrive/nnbar/geant4-gpu/
```

Use branch:

```text
lane/g4gpu-phase4-opticks
```

If a matching LUNARC worktree is required, create/use it under an isolated
`/projects/hep/fs10/shared/nnbar/billy/geant4-gpu-*` path. Do not copy code into
`NNBAR_Detector` or the thesis-production simulation checkout.

## Required reading

- `docs/parallel-sessions/MASTER_PLAN.md` — current G4GPU status.
- `docs/specs/g4gpu-line-by-line-acceleration.md` — Phase 4 policy: ship optical
  by wrapping Opticks rather than rebuilding it.
- In the isolated `geant4-gpu` repo: `docs/SPEC.md`, `docs/VALIDATION.md`,
  existing `cmake/`, `include/g4gpu/`, `src/`, and `tests/` layout.
- If Opticks source or install is available locally/LUNARC, inspect only enough to
  identify the public entry points and cite exact paths in the report.

## Writable scope

Only the isolated `geant4-gpu` worktree and these coordination files if needed:

- `docs/parallel-sessions/MASTER_PLAN.md`
- `docs/reports/phase4_opticks_bridge_*.md`

Do not edit NNBAR production code, production data, or active SLURM job files.

## Compact iteration

1. Check whether Opticks is available locally or on LUNARC. If using LUNARC, first
   run the socket guard from `MASTER_PLAN.md`; use read-only discovery commands.
2. Add a guarded G4GPU build option such as `G4GPU_WITH_OPTICKS` that defaults
   `OFF`.
3. Add a small bridge/interface scaffold only if it can compile without Opticks
   when the option is `OFF`. Prefer an adapter boundary over copied Opticks code.
4. Add a smoke test or configure test that proves the default build remains
   fail-closed without Opticks.
5. Write `docs/reports/phase4_opticks_bridge_YYYYMMDD.md` with:
   - what was discovered about Opticks availability,
   - exact files changed in the isolated repo,
   - what is still blocked before any optical-speedup claim,
   - verification commands and outputs.
6. Update the Phase 4 row in `MASTER_PLAN.md` only with verified evidence.

## Verification

Run the smallest relevant checks in the isolated `geant4-gpu` worktree, for
example:

```bash
cmake --build build --target G4GPU -j2
ctest --test-dir build --output-on-failure -R "opticks|optical|stub"
```

If no build tree exists, run configure/build commands consistent with the repo's
current docs and record the exact command. If Opticks is absent, the expected
green path is the default `G4GPU_WITH_OPTICKS=OFF` build plus a report explaining
the missing dependency.

## Stop condition

Stop after one bounded Opticks-bridge scaffold or availability/blocker report is
committed in the isolated `geant4-gpu` repo and summarized in the local
coordination docs. Do not submit SLURM jobs unless the lane needs a short build
verification and the command is explicitly build/test only. Never claim optical
physics parity or speedup until a later validation lane compares against Opticks
reference output.

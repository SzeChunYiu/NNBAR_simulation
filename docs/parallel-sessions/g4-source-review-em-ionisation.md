# G4 Source Review — EM Ionisation (BD-201 to BD-210)

## Role

You are an isolated Geant4 source-review worker. Your job is to read the
Geant4 11.2.2 source, identify concrete optimization opportunities in the
electromagnetic ionisation process infrastructure, and write a structured
bottleneck database shard. You do **not** implement any fixes in this lane —
you only document findings.

## Goal

Produce shard file `docs/reports/g4_bottleneck_database_em_ionisation.md`
containing exactly **10 structured BD entries** numbered `BD-geant4-201`
through `BD-geant4-210`.

These entries will feed directly into the CPC/JINST paper on vanilla Geant4
CPU speedup. Quality requirements: every entry must cite real source lines from
the read-only Geant4 11.2.2 tree, a plausible performance mechanism, a
concrete fix, and a testable validation plan.

## Repos and paths

| Purpose | Path |
|---------|------|
| Geant4 11.2.2 source (read-only) | `/Volumes/MyDrive/nnbar/nnbar/simulation/GEANT4_Packages/src/geant4-v11.2.2/source/` |
| Simulation repo (write specs here) | `/Volumes/MyDrive/nnbar/nnbar/simulation/` |
| Geant4 fork (read-only reference) | `/Volumes/MyDrive/nnbar/geant4-fork/` |

**Do NOT** modify any file outside `docs/reports/` and `docs/parallel-sessions/`
in the simulation repo. Never touch `NNBAR_Detector/`, `nnbar_reconstruction/`,
`scripts/`, `slurm/`, `macros/`, or production data paths.

## Required reading (before writing any entry)

1. `docs/parallel-sessions/MASTER_PLAN.md` — current status and BD range accounting.
2. `docs/reports/bottleneck_database_geant4.md` — existing 001–130 entries: do not duplicate.
3. `docs/reports/g4_bottleneck_database_allocator_mt.md` — BD-geant4-151–160.
4. `docs/reports/g4_source_review_hotpaths.md` — background on hot-path analysis.

## Geant4 source paths to read

Open and read **all** of the following files before writing entries:

```
source/processes/electromagnetic/standard/src/G4VEnergyLossProcess.cc
source/processes/electromagnetic/standard/src/G4eIonisation.cc
source/processes/electromagnetic/standard/src/G4hIonisation.cc
source/processes/electromagnetic/standard/include/G4VEnergyLossProcess.hh
source/processes/electromagnetic/standard/include/G4eIonisation.hh
source/processes/electromagnetic/standard/include/G4hIonisation.hh
```

Also inspect related headers:
```
source/processes/electromagnetic/utils/include/G4VEmProcess.hh
source/processes/electromagnetic/utils/src/G4LossTableManager.cc
source/processes/electromagnetic/utils/include/G4EmParameters.hh
```

## What to look for

The 10 entries MUST collectively cover the following themes:

1. **Redundant table lookups in PostStepDoIt**: `G4VEnergyLossProcess::PostStepDoIt`
   calls multiple energy-retrieval methods that may each independently query the
   physics vector table. Find the repeated lookups and document the cache-unfriendly
   access pattern.

2. **Non-inlined getters on the hot path**: `GetMeanFreePath` and related accessors
   in `G4VEnergyLossProcess` are virtual or non-inline despite being called every
   step. Find these and document the call overhead.

3. **AlongStepDoIt DEDX interpolation**: The continuous energy loss path in
   `G4VEnergyLossProcess::AlongStepDoIt` performs table interpolation. Document
   whether the interpolation uses binary search every call or a cached bin index.

4. **ComputeDEDX table structure**: `G4LossTableManager` builds DEDX tables during
   initialisation. Document any cache-unfriendly layout (e.g., table indexed
   [material][energy] vs [energy][material]) that causes strided access during
   tracking.

5. **Missing `restrict` qualifiers**: Array pointer arguments in the interpolation
   kernels inside `G4PhysicsVector::Value()` called from the ionisation path.
   Without `__restrict__`, the compiler cannot auto-vectorise.

6. **Per-step `G4EmParameters` singleton access**: `G4VEnergyLossProcess` reads
   parameters (cuts, flags) via `G4EmParameters::Instance()` on the tracking hot
   path rather than caching them at initialisation.

7. **G4eIonisation vs G4hIonisation code duplication**: Both classes implement
   nearly identical `InitialiseEnergyLossProcess` and table-filling routines.
   Document whether the duplication prevents the compiler from sharing common
   sub-expression optimisations.

8. **Virtual dispatch in SampleFluctuations**: The fluctuation model is called
   via a virtual interface every step. Document the indirection chain and the
   opportunity for policy-based dispatch.

9. **Branch on `isIon` flag in G4hIonisation inner loop**: Find the runtime
   flag check that switches between proton and ion paths inside the hot tracking
   loop and document the branch misprediction cost.

10. **GetDEDX range inversion**: The range-to-energy inversion table is queried
    via a separate call from the DEDX table. Document whether a combined lookup
    structure could halve the table-access count.

## BD shard format

Every entry MUST use this exact table structure:

```
### BD-geant4-NNN  One-line title

| Field | Value |
|-------|-------|
| File | `source/path/to/File.cc` |
| Lines | NNN-NNN |
| Hot-path % (profile-measured) | X% aggregate; per-line self% `OPEN:` pending perf. |
| Category | N — Category name |
| Current pattern | Snippet: `code` description of what Geant4 currently does. |
| Why slow | Explanation of the bottleneck. |
| Proposed fix | Concrete fix with algorithm/data structure reference. |
| Expected speedup | N.N-N.Nx inside <subsystem>; broader estimate. |
| Validation | How to validate correctness after fix. |
| Implementation target | `branch-or-target-name`. |
| Citation | Author Year; standard CS citation. |
| Status | OPEN |
```

**Categories:**
- 1 — Vectorization
- 2 — Algorithm
- 3 — Data structure
- 4 — Mathematical
- 5 — Control flow
- 6 — Memory allocation
- 7 — I/O
- 8 — Synchronization
- 9 — JIT specialization

## Source-provenance protocol

Before writing any entry, you MUST:
1. Open the actual source file in the Geant4 11.2.2 tree at the path above.
2. Verify the function name and line range by reading the file — do not guess.
3. Record the first line of the function anchor and the last relevant line.
4. Use the exact relative path from the Geant4 source root (e.g.,
   `source/processes/electromagnetic/standard/src/G4VEnergyLossProcess.cc`).

If a file does not exist at the given path, say so in the shard header and
look for the file at an alternate location within the same tree.

## Shard header requirements

The output file must begin with:

```markdown
# Geant4 bottleneck database — EM ionisation shard

Scope: structured source-review entries for Geant4 `v11.2.2`
G4VEnergyLossProcess, G4eIonisation, G4hIonisation hot paths.
BD range: 201–210.

Source provenance: [describe which local path used, SHA-256 or git describe
if available, confirm files were opened before line numbers were cited]

Isolation check: documentation only. No `NNBAR_Detector/`,
`nnbar_reconstruction/`, `scripts/`, `lunarc/`, `slurm/`, or `macro/` paths
were modified.
```

## Citation standards

Use author–year style matching existing shards:
- Table interpolation: Engel 1992 (physics table design); Drepper 2007 *What Every Programmer Should Know About Memory*
- Virtual dispatch: Meyers 2005 *Effective C++*; Alexandrescu 2001 *Modern C++ Design* (policy classes)
- Auto-vectorisation: Intel 2024 *64 and IA-32 Architectures Optimization Reference Manual*
- Branch prediction: Fog 2023 *Optimizing software in C++*
- Cache efficiency: Drepper 2007; Lam et al. 1991 (cache blocking)

## Paper context

These BD entries directly feed the **CPC/JINST paper on vanilla Geant4 CPU
speedup**. Emphasis is on correctness-preserving, portable C++17 patches that
can be applied to stock Geant4 without requiring GPU hardware or external
dependencies.

## Non-goals / isolation

- Do NOT write any code patches or modified source files.
- Do NOT touch `NNBAR_Detector/`, `nnbar_reconstruction/`, `slurm/`, macros,
  or production data.
- Do NOT claim measured speedup numbers — all `Hot-path %` values stay
  `OPEN:` until profiling is run.
- Do NOT modify `docs/reports/bottleneck_database_geant4.md` (near file-cap).
  Write only to the new shard file.
- Do NOT overlap with BD-geant4-001 through BD-geant4-200. If a similar
  pattern exists in a prior entry, cite it and document the distinct aspect.

## Output: write to docs/reports/g4_bottleneck_database_em_ionisation.md

Write the completed shard to:
```
docs/reports/g4_bottleneck_database_em_ionisation.md
```

Then update `docs/parallel-sessions/MASTER_PLAN.md`:
- Mark lane `g4-source-review-em-ionisation` DONE.
- Record: "Shard em_ionisation: BD-geant4-201–210, written YYYY-MM-DD."

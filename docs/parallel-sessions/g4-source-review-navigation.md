# G4 Source Review — Navigation (BD-231 to BD-240)

## Role

You are an isolated Geant4 source-review worker. Your job is to read the
Geant4 11.2.2 source, identify concrete optimization opportunities in the
geometry navigation infrastructure, and write a structured bottleneck database
shard. You do **not** implement any fixes in this lane — you only document
findings.

## Goal

Produce shard file `docs/reports/g4_bottleneck_database_navigation.md`
containing exactly **10 structured BD entries** numbered `BD-geant4-231`
through `BD-geant4-240`.

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
3. `docs/reports/g4_bottleneck_database_pil_geometry.md` — BD-geant4-032–050 (geometry entries already covered).
4. `docs/reports/g4_source_review_hotpaths.md` — background on hot-path analysis.

## Geant4 source paths to read

Open and read **all** of the following files before writing entries:

```
source/geometry/navigation/src/G4Navigator.cc
source/geometry/navigation/src/G4NormalNavigation.cc
source/geometry/navigation/src/G4VoxelNavigation.cc
source/geometry/navigation/src/G4VoxelSafety.cc
```

Also inspect related headers:
```
source/geometry/navigation/include/G4Navigator.hh
source/geometry/navigation/include/G4VoxelNavigation.hh
source/geometry/navigation/include/G4VoxelSafety.hh
source/geometry/volumes/include/G4SmartVoxelHeader.hh
source/geometry/volumes/include/G4SmartVoxelNode.hh
```

## What to look for

The 10 entries MUST collectively cover the following themes:

1. **Redundant transform recomputation in LocateGlobalPointAndSetup**: Each
   call to `G4Navigator::LocateGlobalPointAndSetup` recomputes the local
   coordinate transform from the global point even when the track has not left
   the current volume. Find the transform computation and document the
   redundancy relative to the cached `fLastLocatedPointLocal`.

2. **Non-cached surface normals in G4NormalNavigation**: `G4NormalNavigation::ComputeStep`
   calls `SurfaceNormal` on the solid at each boundary crossing. Document
   whether the result is cached between the `ComputeStep` and the subsequent
   `GetLocalExitNormal` call in the same step.

3. **Excessive virtual calls in voxel traversal**: `G4VoxelNavigation` calls
   `solid->DistanceToIn` via a virtual pointer inside the voxel-traversal loop.
   Count the virtual calls per step and document the overhead versus a
   type-dispatched version.

4. **G4VoxelNavigation inner loop allocation**: Find any `std::vector::push_back`
   or temporary object construction inside the `G4VoxelNavigation` candidate-
   voxel traversal loop that triggers heap activity per step.

5. **CheckNextStep redundant volume relocation**: `G4Navigator::CheckNextStep`
   may call `LocateGlobalPointAndSetup` defensively even when the navigator
   state is already valid. Document the condition that triggers the redundant
   relocation.

6. **Voxel boundary list sorted-search vs cached cursor**: `G4SmartVoxelHeader`
   uses a sorted `G4SmartVoxelProxy` list. The voxel-entry lookup performs a
   linear or binary search per axis per step. Document whether a cached
   cursor index (updated by delta) would reduce the search cost for straight tracks.

7. **G4VoxelSafety recomputation of the same voxel for coincident boundaries**:
   When a track exits two voxel boundaries simultaneously, `G4VoxelSafety` may
   be called twice for overlapping nodes. Find and document.

8. **Transform stack depth in deeply-nested geometry**: `G4Navigator` maintains
   a history stack (`G4NavigationHistory`) whose depth increases with the
   nesting level. Document the stack operations (push/pop) cost and the memory
   layout of the history array for deeply-nested NNBAR-style geometries.

9. **G4NormalNavigation missing short-circuit for known-inside tracks**: After
   entering a daughter volume, the next `ComputeStep` call re-tests `Inside`
   on the mother solid unnecessarily. Document the condition and the cost.

10. **ComputeSafety repeated solid distance calls**: `G4Navigator::ComputeSafety`
    may call `DistanceToOut` on multiple solids in the history stack. Document
    whether the per-solid results are cached across consecutive safety queries
    at the same point.

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
4. Use the exact relative path from the Geant4 source root.

If a file does not exist at the given path, say so in the shard header and
look for the file at an alternate location within the same tree.

## Shard header requirements

The output file must begin with:

```markdown
# Geant4 bottleneck database — navigation shard

Scope: structured source-review entries for Geant4 `v11.2.2`
G4Navigator, G4NormalNavigation, G4VoxelNavigation, G4VoxelSafety hot paths.
BD range: 231–240.

Source provenance: [describe which local path used, SHA-256 or git describe
if available, confirm files were opened before line numbers were cited]

Isolation check: documentation only. No `NNBAR_Detector/`,
`nnbar_reconstruction/`, `scripts/`, `lunarc/`, `slurm/`, or `macro/` paths
were modified.
```

## Citation standards

Use author–year style matching existing shards:
- Spatial indexing: de Berg et al. 2008 *Computational Geometry: Algorithms and Applications*
- Cache-oblivious traversal: Frigo et al. 1999
- Virtual dispatch elimination: Alexandrescu 2001 *Modern C++ Design*
- Memory layout: Drepper 2007 *What Every Programmer Should Know About Memory*

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
- Do NOT overlap with BD-geant4-001 through BD-geant4-230, especially
  BD-geant4-032–050 which already cover geometry topics.

## Output: write to docs/reports/g4_bottleneck_database_navigation.md

Write the completed shard to:
```
docs/reports/g4_bottleneck_database_navigation.md
```

Then update `docs/parallel-sessions/MASTER_PLAN.md`:
- Mark lane `g4-source-review-navigation` DONE.
- Record: "Shard navigation: BD-geant4-231–240, written YYYY-MM-DD."

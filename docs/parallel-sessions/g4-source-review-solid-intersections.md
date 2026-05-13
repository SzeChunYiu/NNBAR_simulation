# G4 Source Review — Solid Intersections (BD-241 to BD-250)

## Role

You are an isolated Geant4 source-review worker. Your job is to read the
Geant4 11.2.2 source, identify concrete optimization opportunities in the
CSG and Boolean solid distance/intersection routines, and write a structured
bottleneck database shard. You do **not** implement any fixes in this lane —
you only document findings.

## Goal

Produce shard file `docs/reports/g4_bottleneck_database_solid_intersections.md`
containing exactly **10 structured BD entries** numbered `BD-geant4-241`
through `BD-geant4-250`.

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
3. `docs/reports/g4_bottleneck_database_pil_geometry.md` — BD-geant4-032–050 (prior geometry entries).
4. `docs/reports/g4_source_review_hotpaths.md` — background on hot-path analysis.

## Geant4 source paths to read

Open and read **all** of the following files before writing entries:

```
source/geometry/solids/CSG/src/G4Box.cc
source/geometry/solids/CSG/src/G4Tubs.cc
source/geometry/solids/CSG/src/G4Sphere.cc
source/geometry/solids/Boolean/src/G4BooleanSolid.cc
source/geometry/solids/Boolean/src/G4SubtractionSolid.cc
```

Also inspect related headers:
```
source/geometry/solids/CSG/include/G4Box.hh
source/geometry/solids/CSG/include/G4Tubs.hh
source/geometry/solids/Boolean/include/G4BooleanSolid.hh
source/geometry/solids/Boolean/include/G4SubtractionSolid.hh
```

## What to look for

The 10 entries MUST collectively cover the following themes:

1. **Missing SIMD vectorization of G4Box distance formulas**: `G4Box::DistanceToIn`
   and `G4Box::DistanceToOut` perform per-axis slab tests using scalar arithmetic.
   These are direct SIMD candidates (3 independent axis tests). Document the
   scalar code and the SSE/AVX upgrade path.

2. **Redundant sqrt in G4Tubs DistanceToIn**: `G4Tubs::DistanceToIn(p, v)`
   calls `std::sqrt` to compute the radial distance from the axis despite some
   branches only needing the squared value. Find and count all `std::sqrt` calls.

3. **Non-inlined trivial G4Box::Inside cases**: `G4Box::Inside` first tests
   whether the point is clearly inside all three half-extents before testing
   surfaces. Document whether the fast path is inlined into the caller or forces
   a function call.

4. **Excessive branching in G4Tubs::Inside**: `G4Tubs::Inside` tests phi range,
   radial range, and z range with separate if-chains. Document the branch tree
   depth and whether predication or a combined bitmask test would reduce
   misprediction.

5. **G4BooleanSolid double DistanceToIn evaluation**: `G4BooleanSolid::DistanceToIn`
   evaluates both constituent solids even when the first result is sufficient to
   classify the point. Find the Boolean logic and document the early-exit
   opportunity.

6. **G4SubtractionSolid redundant Inside calls**: `G4SubtractionSolid::DistanceToOut`
   calls `Inside` on the subtracted solid to determine if a candidate exit point
   is real. Document the redundancy when the subtracted solid is small relative
   to the primary solid.

7. **G4Sphere trigonometric calls in DistanceToIn**: `G4Sphere::DistanceToIn`
   for partial-sphere solids with phi/theta cuts calls `std::atan2`, `std::acos`,
   or `std::sin`/`std::cos`. Find and document each transcendental function call
   on the hot path.

8. **Missing __restrict__ in G4Box/G4Tubs hot functions**: The distance and
   Inside functions take `const G4ThreeVector&` arguments that alias no internal
   state. Document whether the missing `__restrict__` on the argument prevents
   auto-vectorisation.

9. **G4BooleanSolid virtual dispatch chain depth**: A nested Boolean tree
   (e.g., subtraction of subtraction) issues virtual calls at each level of the
   tree per step. Document the maximum observed tree depth in typical NNBAR
   geometry and the per-level overhead.

10. **G4Tubs DistanceToOut normal computation duplication**: `G4Tubs::DistanceToOut(p, v, calcNorm, validNorm, n)`
    recomputes which surface was hit to fill the normal vector after already
    computing the exit distance. Document the duplicated surface-id logic and
    the opportunity to combine both into a single pass.

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
# Geant4 bottleneck database — solid intersections shard

Scope: structured source-review entries for Geant4 `v11.2.2`
G4Box, G4Tubs, G4Sphere, G4BooleanSolid, G4SubtractionSolid hot paths.
BD range: 241–250.

Source provenance: [describe which local path used, SHA-256 or git describe
if available, confirm files were opened before line numbers were cited]

Isolation check: documentation only. No `NNBAR_Detector/`,
`nnbar_reconstruction/`, `scripts/`, `lunarc/`, `slurm/`, or `macro/` paths
were modified.
```

## Citation standards

Use author–year style matching existing shards:
- SIMD ray-box intersection: Williams et al. 2005 *An Efficient and Robust Ray-Box Intersection Algorithm*
- Ray-cylinder intersection: Pharr et al. 2016 *Physically Based Rendering*
- Branch elimination: Fog 2023 *Optimizing software in C++*
- Intel SIMD: Intel 2024 *64 and IA-32 Architectures Optimization Reference Manual*

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
- Do NOT overlap with BD-geant4-001 through BD-geant4-240.

## Output: write to docs/reports/g4_bottleneck_database_solid_intersections.md

Write the completed shard to:
```
docs/reports/g4_bottleneck_database_solid_intersections.md
```

Then update `docs/parallel-sessions/MASTER_PLAN.md`:
- Mark lane `g4-source-review-solid-intersections` DONE.
- Record: "Shard solid_intersections: BD-geant4-241–250, written YYYY-MM-DD."

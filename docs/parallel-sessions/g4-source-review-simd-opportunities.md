# G4 Source Review — SIMD Opportunities (BD-281 to BD-290)

## Role

You are an isolated Geant4 source-review worker. Your job is to read the
Geant4 11.2.2 source, identify concrete SIMD vectorization opportunities
across G4AffineTransform, G4EmCalculator, and G4MaterialPropertiesTable, and
write a structured bottleneck database shard. You do **not** implement any
fixes in this lane — you only document findings.

## Goal

Produce shard file `docs/reports/g4_bottleneck_database_simd_opportunities.md`
containing exactly **10 structured BD entries** numbered `BD-geant4-281`
through `BD-geant4-290`.

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
3. `docs/reports/g4_source_review_hotpaths.md` — background on hot-path analysis.

## Geant4 source paths to read

Open and read **all** of the following files before writing entries:

```
source/geometry/management/src/G4AffineTransform.cc
source/processes/electromagnetic/utils/src/G4EmCalculator.cc
source/materials/src/G4MaterialPropertiesTable.cc
```

Also inspect related headers:
```
source/geometry/management/include/G4AffineTransform.hh
source/processes/electromagnetic/utils/include/G4EmCalculator.hh
source/materials/include/G4MaterialPropertiesTable.hh
source/geometry/management/include/G4ThreeVector.hh
source/global/HEPGeometry/include/CLHEP/Vector/ThreeVector.h
```

## What to look for

The 10 entries MUST collectively cover the following themes:

1. **G4AffineTransform rotation matrix × vector scalar loops**: The
   `G4AffineTransform::TransformPoint` and `TransformAxis` methods apply a 3×3
   rotation matrix to a 3-vector using 9 scalar multiply-adds. Find these loops
   and document the SSE/AVX 128-bit or 256-bit replacement (padding to 4-wide).

2. **G4AffineTransform AOS layout blocking batch SIMD**: `G4AffineTransform`
   stores one transform per object (Array-of-Structures). When transforming
   many points (e.g., in navigation), the transforms cannot be batched into
   SIMD registers. Document the Structure-of-Arrays refactor for batch transform.

3. **G4AffineTransform missing __restrict__ on point and matrix pointers**:
   The transform methods take `const G4ThreeVector&` arguments. The compiler
   cannot prove the output does not alias the rotation matrix, preventing
   auto-vectorisation of the 9-multiply accumulation. Document the fix.

4. **G4EmCalculator per-call material property lookup**: `G4EmCalculator::ComputeDEDX`
   and related methods perform repeated `GetMaterial`, `GetElement`, and table
   lookups on every call rather than caching the resolved pointers. Find the
   lookup chain and document the per-call overhead.

5. **G4EmCalculator virtual process iteration**: `G4EmCalculator` iterates over
   the process manager's process list via virtual dispatch to find the relevant
   EM process. Document the iteration depth and the cached-process-pointer upgrade.

6. **G4MaterialPropertiesTable std::map lookup per photon step**: In optical
   photon simulation, `G4MaterialPropertiesTable::GetProperty` performs a
   `std::map<G4String, G4MaterialPropertyVector*>` lookup by string key for
   every photon step. Document the hash-map or enum-key alternative.

7. **G4MaterialPropertiesTable string-keyed map cache miss**: String comparison
   in `std::map` is O(length) and causes branch mispredicts on key prefixes.
   Find the comparison function used and document the integer-enum keying
   approach already partially present in newer Geant4 versions.

8. **G4ThreeVector 3-vector arithmetic missing SIMD width**: CLHEP `ThreeVector`
   arithmetic operators (+=, -=, cross product) operate on x, y, z as three
   separate `double` operations. Document the 4-wide SSE2 opportunity (store z
   and a zero in lane 3) used in e.g. Intel Embree.

9. **Rotation matrix inverse computed redundantly**: In `G4AffineTransform`,
   both the forward and inverse rotation are sometimes stored, but the inverse
   is recomputed via transpose rather than read from a cached field. Find any
   recomputation in the navigation hot path and document the caching fix.

10. **G4EmCalculator cross-section interpolation repeated per particle type**:
    `G4EmCalculator::ComputeCrossSectionPerVolume` resolves the particle
    definition and material on every call. In shower simulation with many
    particles of the same type, the resolution is repeated identically.
    Document the batch or memoisation approach.

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
   `source/geometry/management/src/G4AffineTransform.cc`).

If a file does not exist at the given path, say so in the shard header and
look for the file at an alternate location within the same tree.

## Shard header requirements

The output file must begin with:

```markdown
# Geant4 bottleneck database — SIMD opportunities shard

Scope: structured source-review entries for Geant4 `v11.2.2`
G4AffineTransform, G4EmCalculator, G4MaterialPropertiesTable cross-cutting
SIMD vectorization opportunities. BD range: 281–290.

Source provenance: [describe which local path used, SHA-256 or git describe
if available, confirm files were opened before line numbers were cited]

Isolation check: documentation only. No `NNBAR_Detector/`,
`nnbar_reconstruction/`, `scripts/`, `lunarc/`, `slurm/`, or `macro/` paths
were modified.
```

## Citation standards

Use author–year style matching existing shards:
- SSE/AVX matrix–vector multiply: Intel 2024 *64 and IA-32 Architectures Optimization Reference Manual*; Fog 2023 *Optimizing software in C++*
- AOS vs SOA layout: Drepper 2007 *What Every Programmer Should Know About Memory*; Pharr et al. 2018 *Physically Based Rendering*
- Auto-vectorisation blockers (__restrict__): Agner Fog 2023; GCC 2024 auto-vectorisation documentation
- String key overhead: Alexandrescu 2001 *Modern C++ Design* (type-indexed dispatch); Josuttis 2012 *The C++ Standard Library*
- Batch transform: Wald et al. 2014 (Embree ray tracing kernels, SIMD packet transform)

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
- Do NOT overlap with BD-geant4-001 through BD-geant4-280. If a similar
  pattern exists in a prior entry, cite it and document the distinct aspect.

## Output: write to docs/reports/g4_bottleneck_database_simd_opportunities.md

Write the completed shard to:
```
docs/reports/g4_bottleneck_database_simd_opportunities.md
```

Then update `docs/parallel-sessions/MASTER_PLAN.md`:
- Mark lane `g4-source-review-simd-opportunities` DONE.
- Record: "Shard simd_opportunities: BD-geant4-281–290, written YYYY-MM-DD."

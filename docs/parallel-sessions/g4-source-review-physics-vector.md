# G4 Source Review — Physics Vector (BD-271 to BD-280)

## Role

You are an isolated Geant4 source-review worker. Your job is to read the
Geant4 11.2.2 source, identify concrete optimization opportunities in the
physics table and vector lookup infrastructure, and write a structured
bottleneck database shard. You do **not** implement any fixes in this lane —
you only document findings.

## Goal

Produce shard file `docs/reports/g4_bottleneck_database_physics_vector.md`
containing exactly **10 structured BD entries** numbered `BD-geant4-271`
through `BD-geant4-280`.

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
source/global/management/src/G4PhysicsVector.cc
source/global/management/src/G4PhysicsLogVector.cc
source/global/management/src/G4PhysicsTable.cc
```

Also inspect related headers:
```
source/global/management/include/G4PhysicsVector.hh
source/global/management/include/G4PhysicsLogVector.hh
source/global/management/include/G4PhysicsTable.hh
source/global/management/include/G4PhysicsOrderedFreeVector.hh
```

## What to look for

The 10 entries MUST collectively cover the following themes:

1. **Linear search fallback in G4PhysicsVector::FindBin**: `G4PhysicsVector`
   has a `FindBin` or equivalent that falls back to a linear scan when the
   cached last-bin hint misses. Find the fallback path and document the worst-
   case scan length for typical physics table sizes (hundreds of bins).

2. **Non-inlined G4PhysicsVector::Value accessor called in tight loops**: The
   `Value()` and `GetValue()` methods are called millions of times per event
   from energy-loss and cross-section lookups. Document whether they are marked
   `inline` or inlined by the compiler, and whether the virtual base prevents
   inlining.

3. **Branch on log vs linear interpolation inside every Value() call**:
   `G4PhysicsLogVector::Value` and `G4PhysicsVector::Value` each check at
   runtime whether the vector type uses log or linear energy bins. Find the
   branch, document its frequency, and describe the template specialisation
   that would eliminate it.

4. **G4PhysicsTable vector-of-pointers memory layout**: `G4PhysicsTable` stores
   a `std::vector<G4PhysicsVector*>`. Iteration over table entries for all
   materials forces pointer chasing (one cache miss per material). Document the
   layout and the SOA (struct-of-arrays) alternative.

5. **G4PhysicsLogVector bin-index computation log call**: `G4PhysicsLogVector`
   computes the bin index via `std::log(energy / emin) / binWidth`. Document
   whether `std::log` is called on every bin lookup or whether the inverse bin
   width is pre-multiplied to reduce it to a multiply.

6. **ComputeValue virtual dispatch per table entry**: `G4PhysicsVector::ComputeValue`
   is virtual. It is called during table fill (initialisation), but also
   potentially at tracking time for on-the-fly vectors. Find any tracking-time
   calls and document the overhead.

7. **Energy() accessor overhead for inverse table lookups**: `G4PhysicsVector::Energy()`
   retrieves the energy axis value for a given index and is used in range-to-
   energy inversion. Document whether repeated calls with the same bin index
   can be eliminated.

8. **G4PhysicsTable::RetrievePhysicsTable disk I/O format**: The ASCII
   serialisation format used by `RetrievePhysicsTable` and `StorePhysicsTable`
   parses floating-point text on startup. Document the I/O time relative to
   table computation and the binary-cache alternative.

9. **Thread-local table replication in MT mode**: Under MT, each worker thread
   holds its own copy of cross-section tables. Document the per-thread memory
   footprint, the initialisation time, and whether read-only tables could be
   shared via `const` pointers.

10. **Bin-index cache invalidation on material change**: `G4PhysicsVector` caches
    the last-used bin index. When the material changes between consecutive steps,
    the cache is always cold. Document the cache-miss rate for a detector with
    many alternating materials (e.g., NNBAR scintillator/iron sandwich).

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
# Geant4 bottleneck database — physics vector shard

Scope: structured source-review entries for Geant4 `v11.2.2`
G4PhysicsVector, G4PhysicsLogVector, G4PhysicsOrderedFreeVector,
G4PhysicsTable lookup and interpolation hot paths. BD range: 271–280.

Source provenance: [describe which local path used, SHA-256 or git describe
if available, confirm files were opened before line numbers were cited]

Isolation check: documentation only. No `NNBAR_Detector/`,
`nnbar_reconstruction/`, `scripts/`, `lunarc/`, `slurm/`, or `macro/` paths
were modified.
```

## Citation standards

Use author–year style matching existing shards:
- Binary search: Knuth 1997 *The Art of Computer Programming Vol. 3*
- Cache-efficient table layout: Drepper 2007 *What Every Programmer Should Know About Memory*
- Template specialisation for branch elimination: Alexandrescu 2001 *Modern C++ Design*
- Log interpolation: Press et al. 2007 *Numerical Recipes*
- MT read-only sharing: Williams 2012 *C++ Concurrency in Action*

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
- Do NOT overlap with BD-geant4-001 through BD-geant4-270.

## Output: write to docs/reports/g4_bottleneck_database_physics_vector.md

Write the completed shard to:
```
docs/reports/g4_bottleneck_database_physics_vector.md
```

Then update `docs/parallel-sessions/MASTER_PLAN.md`:
- Mark lane `g4-source-review-physics-vector` DONE.
- Record: "Shard physics_vector: BD-geant4-271–280, written YYYY-MM-DD."

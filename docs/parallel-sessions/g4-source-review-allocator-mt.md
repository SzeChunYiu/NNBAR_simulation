# Lane: g4-source-review-allocator-mt

## Role

You are an isolated Geant4 source-review worker. Your job is to read the
Geant4 11.2.2 source, identify concrete optimization opportunities in the
allocator and multi-threading infrastructure, and write a structured bottleneck
database shard. You do **not** implement any fixes in this lane — you only
document findings.

## Goal

Produce shard file `docs/reports/g4_bottleneck_database_allocator_mt.md`
containing exactly **10 structured BD entries** numbered `BD-geant4-151`
through `BD-geant4-160`.

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
3. `docs/reports/g4_bottleneck_database_pil_geometry.md` — BD-geant4-032–050.
4. `docs/reports/g4_bottleneck_database_process_manager.md` — BD-geant4-131–140.
5. `docs/reports/g4gpu_bottleneck_gap_scan_20260512.md` — confirmed next free block is 151.
6. `docs/reports/g4_source_review_hotpaths.md` — background on hot-path analysis.

## Source files to inspect

Open and read **all** of the following files before writing entries:

```
source/global/management/include/G4Allocator.hh
source/global/management/include/G4AutoLock.hh
source/global/management/include/G4Threading.hh
source/tracking/src/G4TrackingManager.cc        (G4Allocator usage)
source/event/src/G4EventManager.cc              (G4AutoLock patterns)
source/global/management/src/G4StateManager.cc
```

Also inspect related headers:
```
source/global/management/include/G4AllocatorPool.hh
source/global/management/include/G4ThreadLocalSingleton.hh
source/global/management/include/G4MTRunManagerKernel.hh   (if present)
```

## Focus themes

The 10 entries MUST collectively cover the following themes (not necessarily
one entry per theme — some themes may spawn two entries):

1. **Thread-local pool exhaustion fallback**: When `G4Allocator` thread-local
   pool is exhausted, it falls back to the global mutex-protected pool. Find
   the guard in `G4AllocatorPool` and the fallback path. Document the
   contention risk in high-track-count MT events.

2. **False sharing in G4Allocator pool headers**: Pool chunk headers are
   allocated per-thread but may land on shared cache lines when pool pages are
   adjacent. Find structure sizes, alignment, and `G4CACHE_LINE_SIZE` usage (or
   lack thereof).

3. **G4AutoLock overhead in hot event paths**: Find every `G4AutoLock` or
   `G4MutexLock` call inside `G4EventManager.cc` and `G4StateManager.cc` that
   executes on the tracking hot path (not just initialization). Document lock
   granularity vs. the data it protects.

4. **G4ThreadLocalSingleton initialization races**: Look for double-checked
   locking or spin patterns in `G4ThreadLocalSingleton` that re-execute on
   every thread per run (not just first access). Document if there is
   unnecessary per-event overhead.

5. **G4TrackingManager allocator usage**: Find where `G4TrackingManager.cc`
   calls `new`/`delete` for track objects (or delegates to `G4Allocator`).
   Document per-track allocation rate and the pool miss penalty.

6. **Global mutex in G4StateManager**: `G4StateManager::SetNewState()` and
   `GetCurrentState()` may hold a mutex during hot-path transitions. Find and
   document.

7. **Lock-free upgrade opportunities**: Where `std::mutex` or
   `G4MUTEXLOCK`/`G4MUTEXUNLOCK` wraps read-dominated data, document atomic
   upgrade path using `std::atomic` or `std::shared_mutex`.

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
   `source/global/management/include/G4Allocator.hh`).

If a file does not exist at the given path, say so in the shard header and
look for the file at an alternate location within the same tree.

## Shard header requirements

The output file must begin with:

```markdown
# Geant4 bottleneck database — allocator and MT infrastructure shard

Scope: structured source-review entries for Geant4 `v11.2.2` allocator pool,
AutoLock, and multi-threading initialization paths. BD range: 151–160.

Source provenance: [describe which local path used, SHA-256 or git describe
if available, confirm files were opened before line numbers were cited]

Isolation check: documentation only. No `NNBAR_Detector/`,
`nnbar_reconstruction/`, `scripts/`, `lunarc/`, `slurm/`, or `macro/` paths
were modified.
```

## Citation standards

Use author–year style matching existing shards:
- Memory allocation: Berger et al. 2000 (Hoard), Lea 2000 (dlmalloc)
- False sharing: Boehm 2005, Drepper 2007 *What Every Programmer Should Know About Memory*
- Lock-free: Herlihy and Shavit 2012 *The Art of Multiprocessor Programming*
- Thread-local: Williams 2012 *C++ Concurrency in Action*
- Intel cache: Intel 2024 *64 and IA-32 Architectures Optimization Reference Manual*

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
- Do NOT overlap with BD-geant4-001 through BD-geant4-150. If a similar
  pattern exists in a prior entry, cite it and document the distinct aspect.

## Output

Write the completed shard to:
```
docs/reports/g4_bottleneck_database_allocator_mt.md
```

Then update `docs/parallel-sessions/MASTER_PLAN.md`:
- Mark lane `g4-source-review-allocator-mt` DONE.
- Record: "Shard allocator_mt: BD-geant4-151–160, written YYYY-MM-DD."

# Lane: g4-source-review-event-stack

## Role

You are an isolated Geant4 source-review worker. Your job is to read the
Geant4 11.2.2 event management, stack management, and track-stack sources,
identify concrete optimization opportunities, and write a structured bottleneck
database shard. You do **not** implement any fixes in this lane — you only
document findings.

## Goal

Produce shard file `docs/reports/g4_bottleneck_database_event_stack.md`
containing exactly **10 structured BD entries** numbered `BD-geant4-191`
through `BD-geant4-200`.

These entries feed the CPC/JINST paper on vanilla Geant4 CPU speedup.
Every entry must cite real source lines, a plausible performance mechanism,
a concrete fix, and a testable validation plan.

## Repos and paths

| Purpose | Path |
|---------|------|
| Geant4 11.2.2 source (read-only) | `/Volumes/MyDrive/nnbar/nnbar/simulation/GEANT4_Packages/src/geant4-v11.2.2/source/` |
| Simulation repo (write here) | `/Volumes/MyDrive/nnbar/nnbar/simulation/` |

**Do NOT** touch `NNBAR_Detector/`, `nnbar_reconstruction/`, `scripts/`,
`slurm/`, `macros/`, or production data paths.

## Required reading (before writing any entry)

1. `docs/parallel-sessions/MASTER_PLAN.md` — current BD range accounting.
2. `docs/reports/bottleneck_database_geant4.md` — existing 001–130 entries.
3. `docs/reports/g4_bottleneck_database_tracking_manager.md` — entries covering
   `G4TrackingManager`; do not duplicate those specific findings.
4. `docs/reports/g4_bottleneck_database_hits_sd.md` — entries for SD/stack if any.
5. Any existing entries for `G4StackManager` in the root database; confirm none
   in BD-geant4-001..190 before writing 191–200.

## Source files to inspect

Open and read **all** of the following files before writing entries:

```
source/event/src/G4EventManager.cc
source/event/src/G4StackManager.cc
source/event/src/G4TrackStack.cc
source/tracking/src/G4TrackingManager.cc
source/event/include/G4TrackStack.hh
source/event/include/G4StackManager.hh
```

Also inspect related headers:
```
source/event/include/G4StackedTrack.hh
source/event/include/G4SmartTrackStack.hh   (if present)
source/event/src/G4SmartTrackStack.cc        (if present)
source/track/include/G4Track.hh
```

## Focus themes

The 10 entries MUST collectively cover the following themes (not necessarily
one entry per theme — some themes warrant two entries):

1. **Heap allocation per track object**: Each secondary track created during
   stepping is typically heap-allocated via `new G4Track(...)`. Find the
   allocation site(s) in `G4TrackingManager.cc` or `G4StackManager.cc`.
   Document the per-event allocation count and pool-miss rate.

2. **`std::stack` vs. ring-buffer for the track stack**: `G4TrackStack` uses
   a dynamic `G4StackedTrack` container (likely a `std::vector` or deque-backed
   LIFO). Find the push/pop hot spots. Contrast with a pre-allocated ring-buffer
   or fixed-capacity `std::array`-backed stack.

3. **Secondary track sorting overhead**: `G4SmartTrackStack` (if present) or
   `G4StackManager` may sort secondaries by kinetic energy or particle type to
   improve cache locality. Find the sort call, identify its complexity, and
   assess whether an insertion-sorted or bucket-sorted structure would be better.

4. **Urgent / waiting / postpone queue management**: `G4StackManager` maintains
   three separate queues (urgent, waiting, postpone). Find the dispatch logic
   that promotes tracks between queues. Document unnecessary copying or
   reallocation at queue transitions.

5. **`G4StackedTrack` object layout**: Inspect the `G4StackedTrack` struct
   (track pointer + trajectory container). Document padding, alignment gaps, and
   whether converting to a SoA (pointer array separate from trajectory-pointer
   array) would improve prefetch behavior.

6. **`G4EventManager` stack-manager call overhead**: Every `ProcessOneEvent()`
   iteration calls through virtual or indirect dispatch to move tracks from the
   waiting stack to the tracking manager. Count the indirections and document
   devirtualization opportunities.

7. **`G4TrackingManager` per-track overhead**: `G4TrackingManager::ProcessOneTrack()`
   calls trajectory management, stepping, and cleanup. Find memory-management
   calls that happen on every track (not just on allocation). Document
   unnecessary null checks, redundant pointer resetting, or repeated method
   dispatch.

8. **Postponed-track re-injection**: When postponed tracks are re-queued at the
   start of a new event, find the loop in `G4StackManager` that moves them.
   Document whether the loop copies objects or just re-queues pointers, and
   whether the transfer is cache-friendly.

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
   `source/event/src/G4StackManager.cc`).

If a file does not exist at the given path, say so in the shard header and
look for the file at an alternate location within the same tree.

## Shard header requirements

The output file must begin with:

```markdown
# Geant4 bottleneck database — event and track-stack management shard

Scope: structured source-review entries for Geant4 `v11.2.2` event manager,
stack manager, and track-stack infrastructure. BD range: 191–200.

Source provenance: [describe which local path used, SHA-256 or git describe
if available, confirm files were opened before line numbers were cited]

Isolation check: documentation only. No `NNBAR_Detector/`,
`nnbar_reconstruction/`, `scripts/`, `lunarc/`, `slurm/`, or `macro/` paths
were modified.
```

## Citation standards

Use author–year style matching existing shards:
- Memory allocation / pool: Berger et al. 2000 (Hoard), Lea 2000 (dlmalloc)
- Cache-friendly containers: Stroustrup 2012, Intel 2024 *Optimization Reference Manual*
- LIFO vs. ring buffers: Knuth 1998 *The Art of Computer Programming* Vol. 1
- AoS-to-SoA: Drepper 2007 *What Every Programmer Should Know About Memory*
- Lock-free queues: Herlihy and Shavit 2012 *The Art of Multiprocessor Programming*
- Sorting: Williams 2012; Sedgewick and Wayne 2011 *Algorithms* 4th ed.

## Paper context

These BD entries directly feed the **CPC/JINST paper on vanilla Geant4 CPU
speedup**. Emphasis is on correctness-preserving, portable C++17 patches that
can be applied to stock Geant4 without requiring GPU hardware or external
dependencies. Track-stack management contributes roughly 10–15% of total
Geant4 event-loop time in complex hadronic events; improvements here
compound with primary tracking speedups.

## Non-goals / isolation

- Do NOT write any code patches or modified source files.
- Do NOT touch `NNBAR_Detector/`, `nnbar_reconstruction/`, `slurm/`, macros,
  or production data.
- Do NOT claim measured speedup numbers — all `Hot-path %` values stay
  `OPEN:` until profiling is run.
- Do NOT modify `docs/reports/bottleneck_database_geant4.md` (near file-cap).
  Write only to the new shard file.
- Do NOT overlap with BD-geant4-001 through BD-geant4-190. If a similar
  pattern exists in a prior entry, cite it and document the distinct aspect.

## Output

Write the completed shard to:
```
docs/reports/g4_bottleneck_database_event_stack.md
```

Then update `docs/parallel-sessions/MASTER_PLAN.md`:
- Mark lane `g4-source-review-event-stack` DONE.
- Record: "Shard event_stack: BD-geant4-191–200, written YYYY-MM-DD."

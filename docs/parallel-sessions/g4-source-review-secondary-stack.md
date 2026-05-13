# G4 Source Review — Secondary Stack (BD-291 to BD-300)

## Role

You are an isolated Geant4 source-review worker. Your job is to read the
Geant4 11.2.2 source, identify concrete optimization opportunities in the
secondary particle stack and particle-change infrastructure, and write a
structured bottleneck database shard. You do **not** implement any fixes in
this lane — you only document findings.

## Goal

Produce shard file `docs/reports/g4_bottleneck_database_secondary_stack.md`
containing exactly **10 structured BD entries** numbered `BD-geant4-291`
through `BD-geant4-300`.

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
source/tracking/src/G4VParticleChange.cc
source/processes/electromagnetic/utils/src/G4ParticleChangeForGamma.cc
source/event/src/G4StackManager.cc
source/tracking/src/G4Track.cc
```

Also inspect related headers:
```
source/tracking/include/G4VParticleChange.hh
source/processes/electromagnetic/utils/include/G4ParticleChangeForGamma.hh
source/event/include/G4StackManager.hh
source/tracking/include/G4Track.hh
source/tracking/include/G4Allocator.hh
source/global/management/include/G4Allocator.hh
```

## What to look for

The 10 entries MUST collectively cover the following themes:

1. **Per-secondary heap allocation bypassing G4Allocator in AddSecondary**:
   `G4VParticleChange::AddSecondary` calls `new G4Track(...)` for each
   secondary particle. Find whether this allocation goes through the
   `G4Allocator` pool or falls through to the system allocator, and document
   the pool-bypass rate for high-multiplicity events.

2. **Secondary vector resize in G4VParticleChange::AddSecondary**: The
   secondaries are stored in a `std::vector<G4Track*>` that grows dynamically.
   Find the `push_back` or `emplace_back` call, document when reallocation
   occurs, and describe the `reserve(maxExpectedSecondaries)` fix.

3. **G4ParticleChangeForGamma unnecessary copy of G4DynamicParticle**: When
   `G4ParticleChangeForGamma` creates a secondary (e.g., a Compton electron),
   it constructs a new `G4DynamicParticle` by copying from a local stack-
   allocated instance. Find the copy constructor call and document the
   move-construction or in-place construction upgrade.

4. **G4StackManager lock contention in MT mode**: In multi-threaded Geant4,
   `G4StackManager::PushOneTrack` and `PopNextTrack` may acquire a mutex
   protecting the stack. Find the lock scope, document the lock duration
   relative to the track-processing time, and describe the per-thread stack
   sharding approach.

5. **G4StackManager urgent/waiting stack O(N) pop**: `G4StackManager` maintains
   urgent and waiting stacks. `PopNextTrack` searches for the highest-priority
   track. Find the search strategy (linear scan vs. priority queue) and document
   the priority-queue upgrade for high-occupancy stacks.

6. **G4Track construction overhead — redundant field initialisation**: `G4Track`
   has a large number of data members initialised to default values in its
   constructor. Find the constructor body, count the zero-initialised fields
   that are overwritten immediately after construction, and document the
   placement-new or lazy-init alternative.

7. **G4VParticleChange::Initialize redundant copy of G4Track state**: At the
   start of each `DoIt`, `G4VParticleChange::Initialize` copies fields from
   the current `G4Track` into the particle-change object. Find the copy loop
   and document which fields are always overwritten before use.

8. **G4ParticleChangeForGamma ProposeLocalEnergyDeposit branch per step**:
   `G4ParticleChangeForGamma` stores a `localEnergyDeposit` updated via
   `ProposeLocalEnergyDeposit`. Find whether the update includes a branch
   (e.g., checking for negative deposit) and document the branchless
   accumulation fix.

9. **G4StackManager stacking-action virtual call per track**: For every track
   pushed, `G4StackManager` calls the user stacking action via a virtual
   `ClassifyNewTrack` method. Find the call site and document the cost of one
   virtual dispatch per secondary in a 100-secondary hadronic shower.

10. **G4Track::GetKineticEnergy redundant recomputation**: `G4Track` may recompute
    kinetic energy from momentum and mass on access if the momentum representation
    is the canonical form. Find any such lazy recomputation in the accessor and
    document the cached-value approach.

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
   `source/tracking/src/G4VParticleChange.cc`).

If a file does not exist at the given path, say so in the shard header and
look for the file at an alternate location within the same tree.

## Shard header requirements

The output file must begin with:

```markdown
# Geant4 bottleneck database — secondary stack shard

Scope: structured source-review entries for Geant4 `v11.2.2`
G4VParticleChange, G4ParticleChangeForGamma, G4Track, G4StackManager
secondary particle handling hot paths. BD range: 291–300.

Source provenance: [describe which local path used, SHA-256 or git describe
if available, confirm files were opened before line numbers were cited]

Isolation check: documentation only. No `NNBAR_Detector/`,
`nnbar_reconstruction/`, `scripts/`, `lunarc/`, `slurm/`, or `macro/` paths
were modified.
```

## Citation standards

Use author–year style matching existing shards:
- Memory pooling (G4Allocator): Berger et al. 2000 (Hoard); Lea 2000 (dlmalloc)
- Move semantics: Meyers 2014 *Effective Modern C++*; Stroustrup 2013 *The C++ Programming Language*
- Priority queue for event scheduling: Cormen et al. 2009 *Introduction to Algorithms*
- Lock contention in MT particle stacks: Williams 2012 *C++ Concurrency in Action*
- Virtual dispatch cost per secondary: Meyers 2005 *Effective C++*; Fog 2023 *Optimizing software in C++*

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
- Do NOT overlap with BD-geant4-001 through BD-geant4-290. If a similar
  pattern exists in a prior entry, cite it and document the distinct aspect.

## Output: write to docs/reports/g4_bottleneck_database_secondary_stack.md

Write the completed shard to:
```
docs/reports/g4_bottleneck_database_secondary_stack.md
```

Then update `docs/parallel-sessions/MASTER_PLAN.md`:
- Mark lane `g4-source-review-secondary-stack` DONE.
- Record: "Shard secondary_stack: BD-geant4-291–300, written YYYY-MM-DD."

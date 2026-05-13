# G4 Source Review — Hadronic Cascade (BD-251 to BD-260)

## Role

You are an isolated Geant4 source-review worker. Your job is to read the
Geant4 11.2.2 source, identify concrete optimization opportunities in the
hadronic cascade model infrastructure, and write a structured bottleneck
database shard. You do **not** implement any fixes in this lane — you only
document findings.

## Goal

Produce shard file `docs/reports/g4_bottleneck_database_hadronic_cascade.md`
containing exactly **10 structured BD entries** numbered `BD-geant4-251`
through `BD-geant4-260`.

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
source/processes/hadronic/models/coherent_elastic/src/G4HadronElastic.cc
source/processes/hadronic/models/binary_cascade/src/G4BinaryCascade.cc
source/processes/hadronic/models/cascade/cascade/src/G4CascadeInterface.cc
source/processes/hadronic/models/binary_cascade/src/G4FieldPropagation.cc
```

Also inspect related headers:
```
source/processes/hadronic/models/binary_cascade/include/G4BinaryCascade.hh
source/processes/hadronic/models/cascade/cascade/include/G4CascadeInterface.hh
source/processes/hadronic/util/include/G4ReactionProduct.hh
source/processes/hadronic/util/include/G4HadronicInteraction.hh
```

## What to look for

The 10 entries MUST collectively cover the following themes:

1. **Per-event STL vector allocation in G4BinaryCascade**: `G4BinaryCascade`
   maintains particle lists as `std::vector` or `std::list` that are cleared
   and repopulated for every event. Find the `clear()`/`push_back()` patterns
   inside `ApplyYourself` and document the heap churn.

2. **std::list usage in G4BinaryCascade propagateParticle inner loop**: Linked-list
   traversal prevents SIMD and cache-efficient access. Find `std::list` member
   declarations, identify the inner-loop traversal, and document the
   `std::vector`-with-swap-removal upgrade.

3. **Redundant Lorentz boosts in G4BinaryCascade**: The binary cascade boosts
   particles to and from the nucleus rest frame multiple times during
   propagation. Find the boost calls per cascade step and document whether any
   can be deferred or batched.

4. **BuildTargetList heap allocation per cascade**: `G4BinaryCascade::BuildTargetList`
   constructs the target nucleon list with `new G4KineticTrack` per nucleon.
   Document the per-nucleon allocation rate and the pool-allocation upgrade path.

5. **G4CascadeInterface (Bertini) per-collision particle construction**: Inside
   `G4CascadeInterface::ApplyYourself`, secondary particles are created via
   `new G4ReactionProduct`. Find and document the per-secondary allocation.

6. **G4HadronElastic final-state construction overhead**: `G4HadronElastic::ApplyYourself`
   constructs the `G4HadFinalState` and fills it with secondaries using the
   standard heap path. Document the allocation chain.

7. **Repeated nucleus density sampling**: `G4BinaryCascade` samples the nuclear
   density profile (Woods-Saxon or similar) multiple times per cascade. Find the
   sampling calls and document whether a pre-sampled nucleon position table would
   reduce transcendental function calls.

8. **G4FieldPropagation per-step heap activity**: `G4FieldPropagation` in the
   binary cascade propagates particles through the nuclear potential field.
   Find any `new`/`delete` inside the step loop and document pooling options.

9. **Sorted insertion of cascade particles**: `G4BinaryCascade` may insert
   collision products into a time-ordered priority structure. Find the insertion
   sort or `std::multimap` usage and document the O(N log N) cost versus a
   bucket-sorted approach for typical cascade sizes.

10. **G4CascadeInterface model-selection branch per hadron type**: At entry to
    `ApplyYourself`, `G4CascadeInterface` dispatches on particle type via a
    chain of if/else or switch. Document the branch depth and the table-dispatch
    alternative.

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
# Geant4 bottleneck database — hadronic cascade shard

Scope: structured source-review entries for Geant4 `v11.2.2`
G4HadronElastic, G4BinaryCascade, G4CascadeInterface (Bertini) hot paths.
BD range: 251–260.

Source provenance: [describe which local path used, SHA-256 or git describe
if available, confirm files were opened before line numbers were cited]

Isolation check: documentation only. No `NNBAR_Detector/`,
`nnbar_reconstruction/`, `scripts/`, `lunarc/`, `slurm/`, or `macro/` paths
were modified.
```

## Citation standards

Use author–year style matching existing shards:
- Memory allocation: Berger et al. 2000 (Hoard); Lea 2000 (dlmalloc)
- STL container performance: Josuttis 2012 *The C++ Standard Library*
- Lorentz boost batching: Agostinelli et al. 2003 (Geant4 NIM paper)
- Priority queue: Cormen et al. 2009 *Introduction to Algorithms*

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
- Do NOT overlap with BD-geant4-001 through BD-geant4-250.

## Output: write to docs/reports/g4_bottleneck_database_hadronic_cascade.md

Write the completed shard to:
```
docs/reports/g4_bottleneck_database_hadronic_cascade.md
```

Then update `docs/parallel-sessions/MASTER_PLAN.md`:
- Mark lane `g4-source-review-hadronic-cascade` DONE.
- Record: "Shard hadronic_cascade: BD-geant4-251–260, written YYYY-MM-DD."

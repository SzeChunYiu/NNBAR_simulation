# Lane: g4-source-review-nuclear-startup

## Role

You are an isolated Geant4 source-review worker. Your job is to read the
Geant4 11.2.2 nuclear data loading and startup parsing sources, identify
optimization opportunities, and write a structured bottleneck database shard.
You do **not** implement any fixes in this lane.

## Goal

Produce shard file `docs/reports/g4_bottleneck_database_nuclear_startup.md`
containing exactly **10 structured BD entries** numbered `BD-geant4-181`
through `BD-geant4-190`.

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

## Required reading

1. `docs/parallel-sessions/MASTER_PLAN.md` — current status and BD range.
2. `docs/reports/bottleneck_database_geant4.md` — existing entries; do not duplicate.
3. `docs/reports/g4_bottleneck_database_neutron_hp.md` — BD-071–080.
4. `docs/reports/g4gpu_bottleneck_gap_scan_20260512.md` — range accounting.
5. `docs/reports/g4_source_review_hotpaths.md` — prior analysis.

## Source files to inspect

Open and read **all** of the following files:

```
source/processes/hadronic/util/src/G4NuclearLevelData.cc
source/processes/hadronic/util/include/G4NuclearLevelData.hh
source/processes/hadronic/models/photon_evaporation/src/G4PhotonEvaporation.cc
source/processes/hadronic/util/src/G4NucleiProperties.cc
```

Also inspect if present:
```
source/processes/hadronic/models/photon_evaporation/src/G4NuclearLevelStore.cc
source/processes/hadronic/models/photon_evaporation/include/G4NuclearLevelStore.hh
source/processes/decay/src/G4RadioactiveDecay.cc
source/processes/hadronic/util/include/G4NuclearLevel.hh
source/processes/hadronic/models/photon_evaporation/include/G4PhotonEvaporation.hh
```

## Focus themes

The 10 entries MUST collectively cover:

1. **ENSDF text parsing at startup**: `G4NuclearLevelData` reads nuclear level
   data from ENSDF-format text files at run initialization. Find the file-open
   and line-by-line parsing loop. Document: number of files opened, total lines
   parsed, use of `sscanf`/`strtod`/`istringstream`, and whether binary
   pre-compiled data could replace text parsing.

2. **Repeated file I/O for the same nucleus**: Does `G4NuclearLevelData` cache
   level data in memory after first load, or does it re-read files on
   successive worker-thread initialization? Find the per-thread vs. shared
   data structure and document any redundant I/O.

3. **Sorted vector vs unordered_map for level lookup**: After parsing, nuclear
   levels are stored in some container. Find the actual container type used
   in `G4NuclearLevelData` or `G4NuclearLevelStore`. Document the lookup
   complexity for gamma-emission level selection and propose `std::lower_bound`
   on a sorted vector if levels are sorted by energy.

4. **Lazy initialization race in MT**: In multi-threaded Geant4, if
   `G4NuclearLevelData::GetLevelManager()` uses a lazy `if(!ptr) Load()`
   pattern, there is a data race unless protected by a mutex. Find the guard
   and document its granularity (per-nuclide or global lock).

5. **G4PhotonEvaporation startup model construction**: Find where
   `G4PhotonEvaporation` is constructed (likely in physics-list setup) and
   how many level managers it loads eagerly at construction time. Document
   whether the load is deferred until first use.

6. **G4NucleiProperties table size and layout**: `G4NucleiProperties.cc`
   provides nuclear binding energies. Find the underlying table (array or map),
   its size, and whether lookup is O(1) array index or O(log n) map. Document
   alignment and cache-line utilization.

7. **G4RadioactiveDecay startup ENSDF parse**: If `G4RadioactiveDecay.cc`
   parses its own isotope database at startup, find the parsing loop and
   document the overhead for simulations that enable radioactive decay but
   simulate only a small subset of isotopes. Propose selective/deferred loading.

8. **Gamma-cascade level selection inner loop**: In `G4PhotonEvaporation`,
   find the loop that selects the next nuclear level from available transitions.
   Document whether it scans all transitions linearly or uses a pre-normalized
   CDF, and propose alias-method sampling.

9. **Level-manager per-(Z,A) allocation pattern**: Does each nuclide
   instantiate its own level-manager object, leading to many small heap
   allocations? Find the allocation site in `G4NuclearLevelData` and document
   whether a pool allocator or flat array of level records would reduce
   allocation overhead.

10. **Binary data format opportunity**: Geant4 ships G4ENSDFSTATEDATA in text
    format. Document the load-time cost (file size, parse time estimate based
    on line count) and the well-known approach of building a binary-format
    G4NuclearLevelData cache file at first load (similar to HDF5 or ROOT
    serialization) that would reduce subsequent startup by 5–20×.

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

## Source-provenance protocol

1. Open each source file before citing line numbers.
2. Verify function anchor and last relevant line by reading the file.
3. Use the exact relative path from the source root.
4. If a file is missing, search the tree and document the actual path.

## Shard header

```markdown
# Geant4 bottleneck database — nuclear data startup shard

Scope: structured source-review entries for Geant4 `v11.2.2` nuclear level
data loading, ENSDF parsing, and photon evaporation initialization. BD range:
181–190.

Source provenance: [describe path used, git describe or SHA, confirm files
opened before line numbers cited]

Isolation check: documentation only. No NNBAR production paths modified.
```

## Citation standards

- Evaluated Nuclear Structure Data File (ENSDF) documentation, BNL/NNDC
- Vose 1991 alias tables; Walker 1977
- Cormen et al. 2009 sorted-vector binary search
- Drepper 2007 *What Every Programmer Should Know About Memory* (I/O cache)
- HDF5 group 2023 (binary format precedent); ROOT team 2003 (TTree serialization)
- Williams 2012 *C++ Concurrency in Action* (MT lazy init)

## Paper context

Nuclear data startup cost directly affects time-to-first-event in batch
production and re-initialization cost in multi-run workflows. These BD entries
feed the **CPC/JINST paper on vanilla Geant4 CPU speedup**.

## Non-goals

- Do NOT write code patches.
- Do NOT touch NNBAR production paths.
- Do NOT claim measured numbers.
- Do NOT modify `docs/reports/bottleneck_database_geant4.md`.
- Do NOT duplicate BD-geant4-001 through BD-geant4-180.

## Output

Write to:
```
docs/reports/g4_bottleneck_database_nuclear_startup.md
```

Update `docs/parallel-sessions/MASTER_PLAN.md`:
- Mark lane `g4-source-review-nuclear-startup` DONE.
- Record: "Shard nuclear_startup: BD-geant4-181–190, written YYYY-MM-DD."

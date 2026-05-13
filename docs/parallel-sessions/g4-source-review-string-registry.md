# Lane: g4-source-review-string-registry

## Role

You are an isolated Geant4 source-review worker. Your job is to read the
Geant4 11.2.2 particle/process registry and string-key lookup sources,
identify concrete optimization opportunities, and write a structured bottleneck
database shard. You do **not** implement any fixes in this lane.

## Goal

Produce shard file `docs/reports/g4_bottleneck_database_string_registry.md`
containing exactly **10 structured BD entries** numbered `BD-geant4-171`
through `BD-geant4-180`.

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

1. `docs/parallel-sessions/MASTER_PLAN.md` — current status and BD range.
2. `docs/reports/bottleneck_database_geant4.md` — existing entries; do not duplicate.
3. `docs/reports/g4_bottleneck_database_process_manager.md` — BD-131–140.
4. `docs/reports/g4gpu_bottleneck_gap_scan_20260512.md` — range accounting.
5. `docs/reports/g4_source_review_hotpaths.md` — prior analysis.

## Source files to inspect

Open and read **all** of the following files before writing entries:

```
source/particles/management/src/G4ParticleTable.cc
source/processes/management/src/G4ProcessManager.cc
source/processes/management/src/G4ProcessTable.cc
source/processes/management/src/G4VProcess.cc
source/materials/src/G4Material.cc
```

Also inspect these headers:
```
source/particles/management/include/G4ParticleTable.hh
source/processes/management/include/G4ProcessTable.hh
source/processes/management/include/G4VProcess.hh
source/materials/include/G4Material.hh
```

And look for the G4String definition in one of:
```
source/global/management/include/G4String.hh
source/global/HEPNumerics/include/G4String.hh
```
(check both paths; use whichever exists)

## Focus themes

The 10 entries MUST collectively cover:

1. **G4ParticleTable O(n) string scan**: `G4ParticleTable::FindParticle(const
   G4String&)` may use a `std::map<G4String, G4ParticleDefinition*>` or a
   linear scan. Find the actual lookup structure and document the cost of
   string comparison (null-terminator scan + locale) versus an integer hash
   lookup.

2. **G4ProcessTable string-keyed lookups**: `G4ProcessTable::FindProcess()`
   and related methods search by process name. Document whether the lookup is
   O(n) linear, O(log n) map, or hash-map, and the calling frequency from the
   tracking loop.

3. **GetProcessName() in hot loops**: Find where `G4VProcess::GetProcessName()`
   is called during step execution (not just initialization). Every call to
   `GetProcessName()` that triggers a std::string copy in the step loop is
   wasteful — document each hot-path call site.

4. **G4String copy cost in process selection**: When `G4ProcessManager`
   selects the winning process and stores the name for the step record, does
   it copy a `G4String`? Document any `std::string` heap allocation in the
   step-record path (lines involving `fpStepPoint->SetProcessDefinedStep`
   or equivalent).

5. **std::map<G4String, ...> vs unordered_map**: `G4ParticleTable` and
   `G4ProcessTable` use ordered or linear data structures. Document the
   iteration cost for particle/process registration at startup and the lookup
   cost per step for name-keyed tables. Note the absence of
   `std::unordered_map` with a good hash.

6. **G4Material name lookup**: `G4Material::GetMaterial(const G4String& name)`
   performs a string scan over the material table. Find the loop, document the
   frequency it is called from physics-list construction and process
   initialization, and propose hashing.

7. **Process-name-to-index cache absence**: When physics assigns cross-section
   tables per process name, repeated `FindProcess()` calls are not cached.
   Find a concrete call site that repeats the lookup across events or steps,
   and document the fix (build a name→index cache at run initialization).

8. **G4String operator== and locale overhead**: If `G4String` is a thin
   `std::string` wrapper, `operator==` uses `std::char_traits<char>::compare`
   which handles locale. Document the hot-path implication and propose compile-
   time or `string_view` comparison.

9. **G4VProcess name stored as std::string member**: Every `G4VProcess`
   subclass carries a `theProcessName` std::string. In MT, each worker thread
   has its own process objects. Document whether the string data is effectively
   read-only after construction (it is) and whether `std::string_view` or
   `const char*` lookup tables would eliminate copies.

10. **ProcessVector GetPhysIntVector lazy name matching**: If any GPIL or DoIt
    selection path matches processes by comparing names at runtime, document
    the exact call chain and propose an integer-ID substitution (assign a
    stable enum or process ID at registration time).

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
3. Use the exact relative path from the Geant4 source root.
4. If a file is missing, search the tree and document the actual path.

## Shard header

```markdown
# Geant4 bottleneck database — string and registry shard

Scope: structured source-review entries for Geant4 `v11.2.2` particle/process
registry and string-key lookup paths. BD range: 171–180.

Source provenance: [describe path used, SHA or git describe, confirm files
opened]

Isolation check: documentation only. No NNBAR production paths modified.
```

## Citation standards

- Knuth 1998 *The Art of Computer Programming Vol. 3* (hashing)
- Cormen et al. 2009 hash tables, open addressing
- Stroustrup 2012 `std::unordered_map` design and string_view rationale
- C++17 `std::string_view` paper (P0254R2, Yasskin and Wakely 2016)
- Drepper 2007 *What Every Programmer Should Know About Memory*

## Paper context

These BD entries feed the **CPC/JINST paper on vanilla Geant4 CPU speedup**.
String-keyed lookups in the registry layer accumulate over millions of steps;
replacing them with integer-ID dispatch is a broadly applicable, low-risk
optimization.

## Non-goals

- Do NOT write code patches.
- Do NOT touch NNBAR production paths.
- Do NOT claim measured numbers.
- Do NOT modify `docs/reports/bottleneck_database_geant4.md`.
- Do NOT duplicate BD-geant4-001 through BD-geant4-170.

## Output

Write to:
```
docs/reports/g4_bottleneck_database_string_registry.md
```

Update `docs/parallel-sessions/MASTER_PLAN.md`:
- Mark lane `g4-source-review-string-registry` DONE.
- Record: "Shard string_registry: BD-geant4-171–180, written YYYY-MM-DD."

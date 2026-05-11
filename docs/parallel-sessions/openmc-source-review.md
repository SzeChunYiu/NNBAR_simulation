# Lane: openmc-source-review (OpenMC hot-path source-code review)

## Goal

Apply the bottleneck-hunting methodology from
`docs/specs/mcaccel-bottleneck-methodology.md` to OpenMC. Output: entries
in `docs/reports/bottleneck_database_openmc.md`.

OpenMC is the second-target MC code. Reviewing it in parallel with Geant4
serves two purposes:
1. Independent attack on a different MC code → more total throughput.
2. Cross-code pattern recognition: bottlenecks that appear in BOTH Geant4
   AND OpenMC are candidates for universal fixes in `core/`.

## Mandatory reading

- `docs/specs/mcaccel-bottleneck-methodology.md` (database format, 10
  categories, profile-first rule)
- `docs/specs/g4gpu-line-by-line-acceleration.md` (architecture)
- `docs/policies/g4gpu-isolation.md` (isolation, no NNBAR touch)

## Locate OpenMC source

```bash
rtk proxy bash -lc 'ssh -O check lunarc 2>/dev/null && echo "Connected" || /Users/billy/lunarc-init.sh'
rtk proxy ssh lunarc 'ls /projects/hep/fs10/shared/nnbar/billy/openmc 2>/dev/null || git clone https://github.com/openmc-dev/openmc /projects/hep/fs10/shared/nnbar/billy/openmc'
```

If the clone is needed, do it on LUNARC (not locally) to avoid filling
local disk. Pin to the latest stable tag.

## Hot paths to review

OpenMC's structure differs from Geant4 (no virtual-call-heavy process
hierarchy; written in C++17 with cleaner abstractions). The hot paths
identified by published profiling (OpenMC's own GTC tutorial slides and
Romano et al. ANE 2015):

### 1. Cross-section lookup and interpolation (~35-50%)

Files to read:
- `src/cross_sections.cpp`
- `src/material.cpp::sample_*`
- `include/openmc/cross_sections.h`
- `src/secondary_*.cpp` (each reaction product sampler)

Targets: hash-based lookup vs. linear search, table compression, QMC for
sampling.

### 2. Geometry tracking (~20-25%)

Files to read:
- `src/geometry.cpp`
- `src/surface.cpp` (CSG surfaces — fewer than Geant4's solids)
- `src/cell.cpp` (and tally cells)

Targets: SAH-BVH for cell-region location, branchless surface tests,
cache layout for the constructive solid geometry tree.

### 3. Tallies / scoring (~10-15%)

Files to read:
- `src/tallies/tally.cpp`
- `src/tallies/tally_scoring.cpp`

Targets: hash-based filter dispatch, vectorized accumulation.

### 4. RNG and event scheduling (~5-10%)

Files to read:
- `src/random_lcg.cpp` (the default RNG — small, simple, replaceable)
- `src/event.cpp` (event-based transport infrastructure)

Targets: drop-in QMC, batched sampling.

## Iteration cycle

1. Mark `openmc-source-review` RUNNING in MASTER_PLAN.md
2. Pick one hot path (start with 1: cross-section lookup)
3. Annotate ≥ 10 bottlenecks per iteration using the database format
4. Commit
5. Note cross-code patterns: if a bottleneck mirrors a Geant4 database
   entry, add a cross-reference field linking the two IDs
6. Stop after committing

## Important

- All builds and runs on LUNARC
- The review reads source — it does not modify OpenMC. Worker-3 implements;
  worker-4 reviews.
- License: OpenMC is MIT; our annotations and any later fork-patches are
  fine to publish.

## Acceptance (cumulative)

- All four hot paths annotated with ≥ 10 database entries each (target 40+
  total)
- ≥ 5 cross-references to Geant4 database entries (the universal-fix
  candidates)

## Stop condition

After committing the current iteration's hot-path section, stop.

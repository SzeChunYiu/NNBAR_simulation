# Lane: g4-source-review (Geant4 hot-path source-code review)

## Goal

Read Geant4 11.2.2 source line by line in its profiled hot 20% and emit
entries into the bottleneck database
`docs/reports/bottleneck_database_geant4.md` per the methodology in
`docs/specs/mcaccel-bottleneck-methodology.md`.

This is the empirical foundation for *every* Phase 5+ implementation task.
Without this review, optimizations are speculative. After this review,
every implementation task on worker-3's queue cites a specific Geant4
source line and a database entry ID as its target.

**Mandatory reading before iterating:**
- `docs/specs/mcaccel-bottleneck-methodology.md` (the loop and the 10
  categories — every annotation must use this format)
- `docs/specs/g4gpu-line-by-line-acceleration.md` (broader strategy)
- `docs/policies/g4gpu-isolation.md` (what is in scope for review vs. what
  is off limits)

Progress note (2026-05-11): the legacy free-form report
`docs/reports/g4_source_review_hotpaths.md` already covers hot path 1 (PIL)
and hot path 2 (geometry navigation). Do not repeat those sections in the
next compact iteration. From the next iteration onward, create/append
structured entries in `docs/reports/bottleneck_database_geant4.md`, starting
with hot path 3 (physics sampling / DoIt), unless the queue explicitly asks
for a separate legacy-entry conversion pass.

## Locate Geant4 source

```bash
rtk proxy bash -lc 'ssh -O check lunarc 2>/dev/null && echo "Connected" || /Users/billy/lunarc-init.sh'

# Find the Geant4 install used by NNBAR
rtk proxy ssh lunarc 'geant4-config --prefix 2>&1 ; echo --- ; \
  module avail geant4 2>&1 | head -20'

# Find the source tarball or extracted tree
rtk proxy ssh lunarc 'find /sw /usr/local /projects -maxdepth 6 -iname "geant4*src*" -o -iname "geant4-v11*" 2>/dev/null | head -20'

# If only the built tree is available, source may be in the source/ subdir of
# the install prefix, or we may need to download geant4-11.2.2.tar.gz.
```

If no source tree is available, document the blocker in
`docs/blockers/geant4-source-not-available.md` and propose the download
URL: https://gitlab.cern.ch/geant4/geant4 (tag `v11.2.2`).

## Hot paths to review

For each, read the named files top to bottom, annotate optimization
opportunities, and quantify expected impact. Hot-path identification is
based on published Geant4 profiling work (Apostolakis et al. CHEP 2021,
Bandieramonte et al. EPJ 2024) and our own intuition from the strategy doc.

### 1. PIL — Physics Interaction Length (~30% of CPU)

Files to read:
- `source/processes/management/src/G4VProcess.cc`
- `source/processes/management/src/G4ProcessManager.cc`
- `source/tracking/src/G4SteppingManager.cc` (the inner step loop; Geant4
  11.2.2 does not contain `G4SteppingManager2.cc`)
- `source/processes/electromagnetic/utils/src/G4VEnergyLossProcess.cc`
- `source/global/management/src/G4PhysicsVector.cc` and
  `source/global/management/include/G4PhysicsVector.icc` (cross-section
  interpolation — the hot inner loop)

Annotate:
- Every virtual call that could be devirtualized via JIT
- Every binary search that could be perfect-hashed
- Every branch in the inner loop
- Every `new`/`delete` in the hot loop

### 2. Geometry navigation (~25% of CPU)

Files to read:
- `source/geometry/navigation/src/G4Navigator.cc`
- `source/geometry/management/src/G4SmartVoxelHeader.cc`
- `source/geometry/navigation/src/G4VoxelNavigation.cc`
- `source/geometry/management/include/G4VTouchable.hh`,
  `source/geometry/management/src/G4TouchableHistory.cc`, and
  `source/geometry/management/include/G4TouchableHistory.icc`
- `source/geometry/management/src/G4VPhysicalVolume.cc`
- `source/geometry/solids/CSG/src/G4Box.cc::DistanceToIn/Out` (representative
  surface tests)
- `source/geometry/solids/CSG/src/G4Tubs.cc::DistanceToIn/Out`

Annotate:
- Voxel descent loops — replaceable by SAH-BVH
- Touchable history copies — replaceable by persistent data structures
- Branchy surface tests — replaceable by branchless SIMD intrinsics
- Transformation cascades — could be flattened at build time

### 3. Physics sampling — DoIt (~20%)

Files to read:
- `source/processes/electromagnetic/standard/src/G4MollerBhabhaModel.cc`
- `source/processes/electromagnetic/standard/src/G4SeltzerBergerModel.cc`
- `source/processes/hadronic/models/parton_string/diffraction/src/G4FTFModel.cc`
- `source/processes/hadronic/models/cascade/cascade/src/G4CascadeInterface.cc`
- Random sampling utilities: `source/externals/clhep/src/JamesRandom.cc`
  and `source/externals/clhep/include/CLHEP/Random/JamesRandom.h`
- `source/track/src/G4ParticleChange.cc` (allocation churn)

Annotate:
- Tabulated cross-section interpolation patterns (apply QMC?)
- Secondary allocation pattern (replace with pool?)
- Hadronic cascade branching (a survey target for QMC variance reduction)
- HepJamesRandom: drop-in PCG/xoshiro candidate?

### 4. Track / Step / Stack management (~15%)

Files to read:
- `source/track/src/G4Track.cc`
- `source/track/src/G4Step.cc`
- `source/tracking/src/G4TrackingManager.cc`
- `source/event/src/G4StackManager.cc`
- `source/event/include/G4StackedTrack.hh`

Annotate:
- AoS-vs-SoA opportunities
- Allocator hot spots
- Stack ordering policies (currently last-in-first-out; could be per-species
  queues)

### 5. Hit collection / SD (~10%)

Files to read:
- `source/digits_hits/detector/src/G4SDManager.cc`
- `source/digits_hits/detector/src/G4VSensitiveDetector.cc`
- `source/digits_hits/hits/src/G4HCofThisEvent.cc`

Annotate:
- `std::map<G4String, G4HCofThisEvent*>` lookups (perfect-hash candidate)
- Virtual SD dispatch (specialize at runtime via JIT?)

## Output format

**The output is the bottleneck database** (one file per code), not a
free-form report. Append entries to
`docs/reports/bottleneck_database_geant4.md` using the exact format from
`docs/specs/mcaccel-bottleneck-methodology.md`. Each entry has a unique
ID `BD-geant4-NNN` and the ten required fields (File, Lines, Hot-path %,
Category, Current pattern, Why slow, Proposed fix, Expected speedup,
Validation, Implementation target).

Legacy free-form output:

```
## 1. PIL

### source/tracking/src/G4SteppingManager.cc:449-512 — virtual call cascade
**Current**: every step iterates over all processes via virtual call
**Optimization**: JIT-specialize the loop for the current particle's
process list, eliding never-active processes
**Expected speedup**: 1.5-2x on the step loop dispatch overhead
**Validation**: bit-exact output for fixed seeds (no algorithm change)
**Proposed task**: g4gpu-phase5d-jit-step-loop
**Standard technique**: partial evaluation, Futamura projection
**Reference**: Futamura 1971; LLVM ORC tutorial
```

Repeat for every annotated opportunity (target: 50+ entries across the
five hot paths).

End with a "Next implementations" section listing the top 10 by
(speedup × validatability / effort), each with a proposed Phase 5d/6/8
task name.

## Iteration cycle

1. Read this spec, the strategy doc, the isolation policy
2. Mark `g4-source-review` RUNNING in MASTER_PLAN.md
3. Locate Geant4 source; if blocked, write blocker note and stop
4. Read the next uncovered hot path and annotate ~10 opportunities
5. Commit the partial report
6. Stop and let the next iteration cover hot path 2, etc.

This is intentionally split across multiple iterations — each iteration
covers one hot path, keeps the worker compact-safe, and produces a usable
partial report.

## Acceptance (cumulative across iterations)

- All five hot paths covered
- ≥ 50 file:line-cited optimization opportunities
- Each entry has all six fields: current code / opt / speedup / validation /
  proposed task / reference
- "Next implementations" section ranks the top 10

## Stop condition

After committing the current iteration's hot-path section, stop. The
report continues across iterations.

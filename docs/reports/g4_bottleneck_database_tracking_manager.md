# Geant4 tracking-manager bottleneck database shard

Scope: additional structured source-review entries for Geant4 `v11.2.2`
tracking-manager, trajectory, and step state-management paths. This shard adds
`BD-geant4-101`--`BD-geant4-110`; it intentionally does not repeat the earlier
tracking/step/stack entries `BD-geant4-014`--`023`, the completed shards
through `BD-geant4-080`, or the reserved charged-transport/decay slots
`BD-geant4-081`--`100`.

Source provenance: local Geant4 fork `/Volumes/MyDrive/nnbar/geant4-fork`
reports `git describe --tags --always --dirty` = `v11.2.2` and short commit
`f840b5da3a`. Line anchors below were verified against that tree before this
report was written. No speedup or priority promotion is claimed here; every
`Hot-path %` remains `OPEN:` until tracking, visualization, or secondary-heavy
benchmarks assign measured self-time.

## Entries

### BD-geant4-101  TrackingManager deletes the previous track secondary bucket one pointer at a time

| Field | Value |
|-------|-------|
| File | `source/tracking/src/G4TrackingManager.cc` |
| Lines | 61-75 |
| Hot-path % (profile-measured) | Secondary cleanup at track handoff: per-line self% `OPEN:` pending shower/allocation profile. |
| Category | 6 -- Memory allocation |
| Current pattern | Snippet: `ProcessOneTrack` loops over `*GimmeSecondaries()`, executes `delete itr` for every carried secondary, and then clears the vector before installing the next track. |
| Why slow | Secondary-rich showers pay serialized heap destruction and pointer chasing exactly at the track handoff boundary; allocator cost is separated from the physics process that created the tracks, making ownership harder to batch. |
| Proposed fix | Add an opt-in secondary-track recycle list/arena owned by the event stack handoff, so the common Geant4-owned secondary objects are bulk-reset while preserving the existing delete path for user-owned or externally transferred tracks. |
| Expected speedup | 1.05-1.25x in secondary-heavy tracking sections if allocation traces show this cleanup in the hot path; negligible when few secondaries are produced. |
| Validation | Fixed-seed shower replay must preserve secondary IDs, parent IDs, statuses, creator process pointers, and stack insertion order; ASan/Valgrind traces must show no leaks or double frees in default and user-stacking modes. |
| Implementation target | `geant4-fork:g4-tracking-secondary-recycle`. |
| Citation | Berger et al. 2000 Hoard allocator; Stroustrup 2012 resource ownership. |
| Status | OPEN |

### BD-geant4-102  Standard trajectory construction heap-allocates both the point container and first point

| Field | Value |
|-------|-------|
| File | `source/tracking/src/G4Trajectory.cc` |
| Lines | 56-70 |
| Hot-path % (profile-measured) | Trajectory-enabled track setup: per-line self% `OPEN:` pending visualization/debug trajectory profile. |
| Category | 6 -- Memory allocation |
| Current pattern | Snippet: the constructor copies static track metadata, allocates `new G4TrajectoryPointContainer()`, then pushes `new G4TrajectoryPoint(aTrack->GetPosition())` for the initial point. |
| Why slow | Even the first stored point requires two heap objects and a pointer-vector indirection; trajectory-heavy debug/visualization runs therefore amplify allocator traffic before any per-step points are appended. |
| Proposed fix | Store the first point inline and allocate a trajectory-point arena or small-vector only when additional points are appended; retain the existing `G4VTrajectoryPoint*` ABI through a compatibility view. |
| Expected speedup | 1.1-1.4x in trajectory-construction allocation samples; no production gain when trajectory storage is disabled. |
| Validation | Compare stored particle metadata, first position, `GetPointEntries()`, and visualization output for default, smooth, and rich trajectory modes under fixed seeds. |
| Implementation target | `geant4-fork:g4-trajectory-small-storage`. |
| Citation | Stroustrup 2012 contiguous containers; Berger et al. 2000 allocator locality. |
| Status | OPEN |

### BD-geant4-103  Trajectory copy construction deep-copies every recorded point through the heap

| Field | Value |
|-------|-------|
| File | `source/tracking/src/G4Trajectory.cc` |
| Lines | 72-87 |
| Hot-path % (profile-measured) | Trajectory copy/merge path: per-line self% `OPEN:` pending event-merging and visualization profile. |
| Category | 6 -- Memory allocation |
| Current pattern | Snippet: the copy constructor allocates a fresh `G4TrajectoryPointContainer`, then iterates over `right.positionRecord` and pushes `new G4TrajectoryPoint(*rightPoint)` for each stored point. |
| Why slow | Copying long trajectories is O(points) heap allocation with virtual-point indirection; it can dominate debug output, event merging, or user actions that clone trajectories. |
| Proposed fix | Reserve the destination size and clone from a per-event trajectory-point arena, or represent standard trajectory points as value records with a lazy pointer facade for legacy APIs. |
| Expected speedup | 1.2-2x for long stored trajectories during copy-heavy workflows; memory footprint should also shrink by removing per-point allocator headers. |
| Validation | Copy a suite of trajectories with zero, one, and many points; require point coordinates, particle metadata, and ownership/destruction behavior to match the current implementation. |
| Implementation target | `geant4-fork:g4-trajectory-arena-clone`. |
| Citation | Lam, Rothberg, and Wolf 1991 locality optimization; Stroustrup 2012 value semantics. |
| Status | OPEN |

### BD-geant4-104  Trajectory destruction walks the point vector and deletes each point separately

| Field | Value |
|-------|-------|
| File | `source/tracking/src/G4Trajectory.cc` |
| Lines | 89-98 |
| Hot-path % (profile-measured) | Trajectory teardown: per-line self% `OPEN:` pending trajectory-enabled teardown profile. |
| Category | 6 -- Memory allocation |
| Current pattern | Snippet: the destructor tests `positionRecord`, deletes every stored point, clears the vector, and then deletes the container. |
| Why slow | Long visualized tracks pay one virtual/object destruction path per point and do not benefit from bulk release; teardown latency can appear at end-of-event boundaries. |
| Proposed fix | Allocate standard trajectory points from a monotonic per-event trajectory arena and bulk-release it after all trajectory consumers finish; fall back to per-point deletion for user-derived point types. |
| Expected speedup | 1.1-1.8x in trajectory teardown for long tracks; biggest impact in optical or low-energy EM visualization samples with many steps. |
| Validation | Leak/double-free tests across normal deletion, copied trajectories, merged trajectories, and user-derived trajectory classes; event visual outputs must remain unchanged. |
| Implementation target | `geant4-fork:g4-trajectory-bulk-release`. |
| Citation | Berger et al. 2000 allocator design; Stroustrup 2012 RAII. |
| Status | OPEN |

### BD-geant4-105  Trajectory attribute export allocates a vector and stringifies every field on demand

| Field | Value |
|-------|-------|
| File | `source/tracking/src/G4Trajectory.cc` |
| Lines | 152-178 |
| Hot-path % (profile-measured) | Trajectory attribute export: per-line self% `OPEN:` pending visualization/UI profile. |
| Category | 3 -- Data structure |
| Current pattern | Snippet: `CreateAttValues` creates `new std::vector<G4AttValue>` and pushes converted ID, parent, particle, charge, PDG, energy, momentum, and point-count values on every call. |
| Why slow | Attribute queries rebuild short-lived heap containers and repeat unit/string conversions even when the trajectory metadata is immutable after construction. |
| Proposed fix | Cache immutable attribute strings in the trajectory or fill a caller-provided small buffer; invalidate only if future APIs allow metadata mutation. |
| Expected speedup | 1.2-2x in visualization attribute export; no effect on physics stepping. |
| Validation | UI/visualization tests compare every emitted `G4AttValue` name, value, and unit for representative particle types and energies. |
| Implementation target | `geant4-fork:g4-trajectory-attribute-cache`. |
| Citation | Cormen et al. 2009 memoization/table lookup; Stroustrup 2012 small containers. |
| Status | OPEN |

### BD-geant4-106  AppendStep allocates one trajectory point for every stored step

| Field | Value |
|-------|-------|
| File | `source/tracking/src/G4Trajectory.cc` |
| Lines | 181-184 |
| Hot-path % (profile-measured) | Trajectory-enabled step loop: per-line self% `OPEN:` pending stored-trajectory stepping profile. |
| Category | 6 -- Memory allocation |
| Current pattern | Snippet: `AppendStep` pushes `new G4TrajectoryPoint(aStep->GetPostStepPoint()->GetPosition())` into the trajectory point container. |
| Why slow | A trajectory-enabled run turns every simulation step into at least one heap allocation plus vector growth checks, which is expensive for optical photons and other fine-step workloads. |
| Proposed fix | Reserve or grow trajectory storage in chunks per track and store standard point coordinates as contiguous values, exposing `G4VTrajectoryPoint*` only through a stable compatibility layer. |
| Expected speedup | 1.3-3x in trajectory point recording; wall-clock impact depends on the fraction of runs with `G4_STORE_TRAJECTORY` enabled. |
| Validation | Compare point count and all post-step positions against the current implementation for straight, curved, boundary-heavy, and secondary-rich tracks. |
| Implementation target | `geant4-fork:g4-trajectory-point-buffer`. |
| Citation | Stroustrup 2012 vector growth/locality; Berger et al. 2000 allocation overhead. |
| Status | OPEN |

### BD-geant4-107  MergeTrajectory pointer-splices point records without reserving destination capacity

| Field | Value |
|-------|-------|
| File | `source/tracking/src/G4Trajectory.cc` |
| Lines | 191-203 |
| Hot-path % (profile-measured) | Trajectory merge path: per-line self% `OPEN:` pending event-merging/visualization profile. |
| Category | 3 -- Data structure |
| Current pattern | Snippet: `MergeTrajectory` casts the second trajectory, pushes each point pointer from index 1 onward, deletes the second initial point, and clears the source container. |
| Why slow | The destination vector may reallocate repeatedly while moving many point pointers, and ownership transfer is encoded through manual deletion/clear operations rather than a bulk move. |
| Proposed fix | Reserve `positionRecord->size() + ent - 1` before transfer and use an explicit move/append helper that records ownership transfer; combine with the trajectory point-buffer work for value-backed points. |
| Expected speedup | 1.1-1.6x in trajectory merge hot spots; also lowers risk of future ownership mistakes. |
| Validation | Merge empty, single-point, and long second trajectories; require point order, deletion behavior, and final source/destination counts to match current semantics. |
| Implementation target | `geant4-fork:g4-trajectory-merge-reserve`. |
| Citation | Cormen et al. 2009 amortized dynamic arrays; Stroustrup 2012 move semantics. |
| Status | OPEN |

### BD-geant4-108  G4Step assignment rebuilds owned step points and secondary vectors

| Field | Value |
|-------|-------|
| File | `source/track/src/G4Step.cc` |
| Lines | 106-166 |
| Hot-path % (profile-measured) | Step copy-assignment path: per-line self% `OPEN:` pending stepping/user-copy allocation profile. |
| Category | 6 -- Memory allocation |
| Current pattern | Snippet: `operator=` deletes current pre/post step points, allocates replacement `G4StepPoint` objects, clears/deletes `fSecondary`, copies or creates a `G4TrackVector`, then recreates `secondaryInCurrentStep`. |
| Why slow | Any step assignment pays multiple heap operations and pointer-vector churn; this is a separate copy-assignment cost not captured by the earlier constructor/copy-constructor storage entry. |
| Proposed fix | Move pre/post step points and the current-secondary view into stable inline storage, and make assignment reuse existing buffers when capacities and ownership are compatible. |
| Expected speedup | 1.1-1.5x in copy-assignment profiles and lower allocator noise in user code that snapshots steps. |
| Validation | Regression tests compare all scalar fields, pre/post step-point fields, secondary-vector contents, auxiliary-point pointer behavior, and self-assignment semantics. |
| Implementation target | `geant4-fork:g4-step-assignment-buffer-reuse`. |
| Citation | Stroustrup 2012 copy/move semantics; Intel 2024 cache/locality guidance. |
| Status | OPEN |

### BD-geant4-109  CopyPostToPreStepPoint copies the full endpoint object at every step boundary

| Field | Value |
|-------|-------|
| File | `source/track/include/G4Step.icc` |
| Lines | 142-150 |
| Hot-path % (profile-measured) | Per-step endpoint rollover: per-line self% `OPEN:` pending Track/Step perf profile. |
| Category | 3 -- Data structure |
| Current pattern | Snippet: `CopyPostToPreStepPoint` assigns `*(fpPreStepPoint) = *(fpPostStepPoint)`, resets the post-step status, and records `nSecondaryByLastStep = fSecondary->size()`. Related endpoint assignment in `source/track/src/G4StepPoint.cc` lines 34-60 copies every position, time, material, process, charge, and weight field. |
| Why slow | The rollover is an AoS copy of many fields even when only a subset changed; it also couples endpoint state update to secondary-boundary bookkeeping. |
| Proposed fix | Add a compact step-state rollover path with dirty-field masks or SoA-friendly endpoint storage, while keeping the current full-copy path for ABI compatibility and rare extension mutations. |
| Expected speedup | 1.05-1.25x inside the stepping loop if endpoint copies show in profiles; larger when combined with Phase 6 SoA track packets. |
| Validation | Field-by-field dumps before and after rollover must match current Geant4 for geometry, EM, optical, and secondary-producing steps; secondary suffix boundaries must remain identical. |
| Implementation target | `g4gpu-phase6-step-endpoint-rollover`. |
| Citation | Lam, Rothberg, and Wolf 1991 locality optimization; Intel 2024 structure layout guidance. |
| Status | OPEN |

### BD-geant4-110  InitializeStep and UpdateTrack bounce state between G4Track, G4DynamicParticle, and G4StepPoint

| Field | Value |
|-------|-------|
| File | `source/track/include/G4Step.icc` |
| Lines | 169-250 |
| Hot-path % (profile-measured) | Track/step state copy-in and copy-out: per-line self% `OPEN:` pending Track/Step perf profile. |
| Category | 5 -- Control flow |
| Current pattern | Snippet: `InitializeStep` copies weight, position, times, dynamic-particle state, touchable/material/cuts/sensitive-detector pointers, and velocity into the pre/post step points; `UpdateTrack` copies post-step state back into the track and dynamic particle. |
| Why slow | The scalar API preserves clear ownership boundaries but creates repeated copy-in/copy-out traffic across pointer-rich objects, blocking direct SoA/GPU handoff and adding cache misses around every step. |
| Proposed fix | Introduce an internal step-state adapter that can expose the legacy `G4StepPoint`/`G4Track` API while allowing optimized builds to keep hot fields in a compact packet until a legacy observer forces materialization. |
| Expected speedup | 1.1-1.4x in Track/Step overhead after packetization; also a prerequisite for CPU SIMD and GPU kernels to share one state layout. |
| Validation | Fixed-seed step dumps compare all copied fields before/after `InitializeStep`, after every process update, and after `UpdateTrack`; legacy observers must see identical values at all public API boundaries. |
| Implementation target | `g4gpu-phase6-step-state-adapter`. |
| Citation | Martin Thompson 2011 mechanical sympathy; Stroustrup 2012 abstraction and layout. |
| Status | OPEN |

## Next implementations after this shard

1. `g4gpu-phase6-step-state-adapter` from BD-geant4-109/110: highest leverage
   for the Phase 6 SoA track-packet redesign because it reduces the current
   copy-in/copy-out boundary.
2. `geant4-fork:g4-trajectory-point-buffer` from BD-geant4-102/106: compact,
   trajectory-only upstreamable storage improvement with clear visual-output
   validation.
3. `geant4-fork:g4-tracking-secondary-recycle` from BD-geant4-101: should be
   tested with the existing track-pool and stack-fast-path proposals before any
   ownership-changing MR.
4. `geant4-fork:g4-step-assignment-buffer-reuse` from BD-geant4-108: narrower
   ABI-aware cleanup for user code that snapshots or assigns `G4Step` objects.
5. `geant4-fork:g4-trajectory-merge-reserve` from BD-geant4-107: low-risk
   reserve/move helper after trajectory storage tests are in place.

# Geant4 bottleneck database — event and track-stack management shard

Scope: structured source-review entries for Geant4 `v11.2.2` event manager, stack manager, and track-stack infrastructure. BD range: 191–200.

Source provenance: inspected read-only local Geant4 checkout at `/Volumes/MyDrive/nnbar/nnbar/simulation/GEANT4_Packages/src/geant4-v11.2.2/`. Required files were opened before citing line numbers: `source/event/src/G4EventManager.cc` (SHA-256 `5ae0c0c25f48efef3f628243ab07091567d14aee165520d65f608b2f90a00c17`), `source/event/src/G4StackManager.cc` (`688a198f2745c9711b55255857c03426ffeef8b4137f85c425495a3261ad6d95`), `source/event/src/G4TrackStack.cc` (`b2adffc6ed56818bad286db24f26b8ebd939528c28741410adc72baf5f775a70`), `source/tracking/src/G4TrackingManager.cc` (`05e0682cacda97c359d7c3e3b0579b5f811e39320a547f58ca4623e57aef769c`), `source/event/include/G4TrackStack.hh` (`f32f2362ccd7ad3dd89d6d5c687a5d9b79b1a9a58d313a2f2d0cc9ec91bd8eee`), `source/event/include/G4StackManager.hh` (`791f6aa98984fc751637d1d314c2cf6fe3ad2236956aee11905c5c3b5eb87adc`), `source/event/include/G4StackedTrack.hh` (`3b586d3e508b564c1363d7343941e452b3569bb1b5c84f5aee4f26e23ef91201`), `source/event/include/G4SmartTrackStack.hh` (`2ed41f6e12de94b0275f778090678f2a8c5498cd123b98456be183c91aa23c78`), `source/event/src/G4SmartTrackStack.cc` (`c3b94f3316059d167a6ca4297841a2e84ade96ecf5a1acadf980965648a2dddc`), `source/track/include/G4Track.hh` (`32ff58a3598d5a30e3ce06e69e2633248155a3bc3219d56b2bc1a99d89e01f63`), `source/track/include/G4Track.icc` (`622998137628e00653f6e319c2c4f32e7ee86dbf1d9657a7d70f9912e7a09557`), and `source/track/src/G4ParticleChange.cc` (`c35311466feb29c4fa4c2b177cb495f8055f5ec10e0a1702c846ec056e9ceb5f`). Existing BD-geant4-001--190 stack/secondary-adjacent entries were checked; entries below target distinct event-stack mechanics or explicitly narrow the follow-up aspect.

Isolation check: documentation only. No `NNBAR_Detector/`, `nnbar_reconstruction/`, `scripts/`, `lunarc/`, `slurm/`, `macro/`, source, build, benchmark-result, or production data paths were modified.

### BD-geant4-191  Secondary `G4Track` allocation is pooled but still one wrapper allocation per produced track

| Field | Value |
|-------|-------|
| File | `source/track/src/G4ParticleChange.cc`; `source/track/include/G4Track.icc` |
| Lines | `G4ParticleChange.cc`: 44-58, 62-77, 81-95; `G4Track.icc`: 41-52 |
| Hot-path % (profile-measured) | OPEN: pending perf aggregate; per-line self% `OPEN:` pending perf. |
| Category | 6 — Memory allocation |
| Current pattern | Snippet: `new G4Track(aParticle, GetGlobalTime(), ...)` creates one `G4Track` wrapper per secondary and `G4Track::operator new` lazily creates/uses `G4Allocator<G4Track>`. |
| Why slow | The pool avoids general `malloc`, but every secondary still pays allocator metadata, constructor initialization, later stack wrapper insertion, and a separate dynamic-particle lifetime. Distinct from secondary-stack BD-geant4-291, this entry is the generic particle-change AddSecondary path feeding the event stack. |
| Proposed fix | Add a per-event secondary-track arena with an emplace API that batches `G4Track` wrapper allocation and exports allocation-count/pool-miss telemetry before replacing the legacy pointer path. |
| Expected speedup | 1.05-1.25x in secondary creation and stack handoff; broader event gain depends on secondary multiplicity. |
| Validation | Fixed-seed comparisons of secondary order, IDs, parent IDs, touchables, creator process/model, dynamic-particle kinematics, and allocator telemetry for pool misses and live-object count. |
| Implementation target | `g4-event-stack-secondary-track-arena` |
| Citation | Berger et al. 2000; Lea 2000; Drepper 2007. |
| Status | OPEN |

### BD-geant4-192  `G4TrackStack` is a `std::vector` LIFO with fixed reserve guesses rather than a measured ring buffer

| Field | Value |
|-------|-------|
| File | `source/event/include/G4TrackStack.hh`; `source/event/src/G4StackManager.cc` |
| Lines | `G4TrackStack.hh`: 44-64; `G4StackManager.cc`: 48-60 |
| Hot-path % (profile-measured) | OPEN: pending perf aggregate; per-line self% `OPEN:` pending perf. |
| Category | 3 — Data structure |
| Current pattern | Snippet: `class G4TrackStack : public std::vector<G4StackedTrack>` reserves constructor guesses (`5000`, `1000`) and implements LIFO as `push_back`, `back`, `pop_back`. |
| Why slow | Vector LIFO is good for contiguous storage, but peak occupancy above reserve reallocates and copies wrappers, while low-occupancy events carry over-sized capacity. There is no event-profiled capacity policy or fixed ring segment sized from observed stack depth. |
| Proposed fix | Add stack-depth telemetry and a preallocated segmented ring-buffer/fixed-vector policy keyed by physics list and event class, falling back to vector only when occupancy exceeds the profiled envelope. |
| Expected speedup | 1.05-1.20x inside stack push/pop under bursty shower occupancy; also reduces memory spikes from reserve misses. |
| Validation | Compare pop order, max-depth counters, vector-reallocation counters, and fixed-seed event records across ordinary, smart-stack, waiting, and postponed configurations. |
| Implementation target | `g4-track-stack-profiled-ring-buffer` |
| Citation | Knuth 1998; Stroustrup 2012; Intel 2024 Optimization Reference Manual. |
| Status | OPEN |

### BD-geant4-193  Bulk stack transfers copy every `G4StackedTrack` instead of swapping contiguous segments

| Field | Value |
|-------|-------|
| File | `source/event/src/G4TrackStack.cc`; `source/event/src/G4StackManager.cc` |
| Lines | `G4TrackStack.cc`: 51-66; `G4StackManager.cc`: 176-199, 503-517 |
| Hot-path % (profile-measured) | OPEN: pending perf aggregate; per-line self% `OPEN:` pending perf. |
| Category | 2 — Algorithm |
| Current pattern | Snippet: `for(auto & i : *this) { aStack->push_back(i); } clear();` copies wrappers from source to destination; smart-stack transfer repeatedly pops and re-pushes. |
| Why slow | Waiting-to-urgent and explicit transfer operations are O(N) wrapper-copy loops before processing can resume. Prior BD-geant4-020 records the broad transfer issue; this entry narrows the implementation target to segment swapping/splicing in the concrete `TransferTo` overloads. |
| Proposed fix | Represent each stack as a deque of contiguous segments and transfer by moving segment descriptors or swapping backing buffers when destination ordering permits; retain element-wise reclassification only for smart-stack rebucketing. |
| Expected speedup | 1.10-1.40x during stage transitions and user-driven stack transfers with high occupancy; negligible when no waiting/postponed tracks exist. |
| Validation | Exhaustive tests for LIFO order, `GetNTrack`/`GetMaxNTrack`, trajectory pointer ownership, additional-waiting cascade order, and smart-stack species ordering. |
| Implementation target | `g4-track-stack-segment-transfer` |
| Citation | Sutter 2005; Drepper 2007; Knuth 1998. |
| Status | OPEN |

### BD-geant4-194  `G4StackedTrack` keeps an AoS pair of pointers that forces wrapper copies on stack traffic

| Field | Value |
|-------|-------|
| File | `source/event/include/G4StackedTrack.hh`; `source/event/include/G4TrackStack.hh` |
| Lines | `G4StackedTrack.hh`: 39-55; `G4TrackStack.hh`: 58-64 |
| Hot-path % (profile-measured) | OPEN: pending perf aggregate; per-line self% `OPEN:` pending perf. |
| Category | 3 — Data structure |
| Current pattern | Snippet: `G4StackedTrack` stores `G4Track* track` and `G4VTrajectory* trajectory`; push/pop copies the two-pointer wrapper by value. |
| Why slow | The AoS wrapper is small, but every transfer/pop touches both track and trajectory pointer lanes even when trajectories are disabled or uniformly null. It also prevents prefetching track pointers independently from cold trajectory ownership. |
| Proposed fix | Split track and trajectory storage into parallel arrays or a nullable sidecar trajectory vector, allowing track-pointer-only hot pops and optional trajectory-side prefetch/merge when trajectory recording is compiled in. |
| Expected speedup | 1.03-1.12x in stack traffic, higher in no-trajectory builds with large transfer bursts. |
| Validation | ABI audit for public wrapper use, fixed-seed trajectory/no-trajectory event comparisons, sanitizer ownership checks, and cache-miss counters for stack pop/transfer loops. |
| Implementation target | `g4-stacked-track-soa-storage` |
| Citation | Drepper 2007; Stroustrup 2012; Intel 2024 Optimization Reference Manual. |
| Status | OPEN |

### BD-geant4-195  Smart-stack scheduling scans bucket state and energy counters instead of using a compact non-empty mask

| Field | Value |
|-------|-------|
| File | `source/event/src/G4SmartTrackStack.cc`; `source/event/include/G4SmartTrackStack.hh` |
| Lines | `G4SmartTrackStack.cc`: 73-93, 101-137; `G4SmartTrackStack.hh`: 67-77 |
| Hot-path % (profile-measured) | OPEN: pending perf aggregate; per-line self% `OPEN:` pending perf. |
| Category | 5 — Control flow |
| Current pattern | Snippet: `while (true)` probes `stacks[fTurn]->GetNTrack()` and rotates `fTurn`; push uses a PDG-code branch ladder plus per-bucket energy/safety checks. |
| Why slow | There is no `std::sort` call in this checkout; secondary ordering is a five-bucket heuristic. Empty-bucket probes and repeated energy updates add predictable control-flow overhead that can be replaced by a non-empty bitmask and table-driven bucket metadata. |
| Proposed fix | Maintain a five-bit non-empty mask plus table-mapped particle-code bucket, update energy counters only for buckets that need the heuristic, and pick the next bucket with bit operations rather than repeated empty probes. |
| Expected speedup | 1.05-1.20x inside smart-stack push/pop; broader impact depends on `G4_USESMARTSTACK` adoption and secondary species mix. |
| Validation | Compare smart-stack pop order, `fTurn` evolution, energy counters, max-track statistics, and shower observables for neutron/electron/gamma/positron-heavy events. |
| Implementation target | `g4-smart-stack-bucket-mask` |
| Citation | Sedgewick and Wayne 2011; Intel 2024 Optimization Reference Manual; Drepper 2007. |
| Status | OPEN |

### BD-geant4-196  Additional waiting stacks are heap-owned vectors with cascade promotion cost

| Field | Value |
|-------|-------|
| File | `source/event/src/G4StackManager.cc`; `source/event/include/G4StackManager.hh` |
| Lines | `G4StackManager.cc`: 176-199, 409-417; `G4StackManager.hh`: 167-171 |
| Hot-path % (profile-measured) | OPEN: pending perf aggregate; per-line self% `OPEN:` pending perf. |
| Category | 6 — Memory allocation |
| Current pattern | Snippet: `auto* newStack = new G4TrackStack; additionalWaitingStacks.push_back(newStack);` and empty-urgent promotion cascades each additional stack through the previous stack. |
| Why slow | Optional waiting stages allocate separate stack objects and stage advancement copies each occupied stage down one level. This is distinct from BD-geant4-295's ordinary waiting-to-urgent trigger: it targets the multi-stage heap-pointer layout and cascade policy. |
| Proposed fix | Store additional stages in an inline `std::vector<G4TrackStack>` or segment queue with whole-stage rotation, so advancing stages swaps stage descriptors instead of copying all `G4StackedTrack` wrappers. |
| Expected speedup | 1.10-1.50x for applications using multiple waiting stages; zero or minimal impact for default single-stage workloads. |
| Validation | Unit tests for every `G4ClassificationOfNewTrack` additional-stack ID, exact stage order under repeated `NewStage`, and leak/sanitizer checks for stage resize up/down. |
| Implementation target | `g4-additional-waiting-stage-rotation` |
| Citation | Knuth 1998; Stroustrup 2012; Herlihy and Shavit 2012. |
| Status | OPEN |

### BD-geant4-197  Postponed-track re-injection uses a temporary stack and reclassifies every track at event start

| Field | Value |
|-------|-------|
| File | `source/event/src/G4StackManager.cc` |
| Lines | 270-330 |
| Hot-path % (profile-measured) | OPEN: pending perf aggregate; per-line self% `OPEN:` pending perf. |
| Category | 2 — Algorithm |
| Current pattern | Snippet: `postponeStack->TransferTo(&tmpStack)` followed by a loop that pops, re-runs default/user classification, rewrites parent/track IDs, and `SortOut`s each postponed track. |
| Why slow | Cross-event postponed tracks pay a full copy-to-temp plus per-track classification pass before the first new-event track can run. If most postponed tracks remain urgent/default, the pass is bookkeeping-heavy and cache-unfriendly. |
| Proposed fix | Keep postponed tracks in a dedicated segment with a deferred ID-rewrite cursor and classify lazily only when a user stacking policy or non-default status requires it. |
| Expected speedup | 1.05-1.30x in workloads using `fPostponeToNextEvent`; no direct impact when postpone stack is empty. |
| Validation | Fixed-seed comparisons for postponed track order, negative ID assignment, parent-ID rewrite, user stacking classifications, trajectory ownership, and event boundary reproducibility. |
| Implementation target | `g4-postponed-track-lazy-reinjection` |
| Citation | Cormen et al. 2009; Drepper 2007. |
| Status | OPEN |

### BD-geant4-198  Custom tracking-manager flush set hashes manager pointers during the event loop

| Field | Value |
|-------|-------|
| File | `source/event/src/G4EventManager.cc` |
| Lines | 170-199, 285-290 |
| Hot-path % (profile-measured) | OPEN: pending perf aggregate; per-line self% `OPEN:` pending perf. |
| Category | 3 — Data structure |
| Current pattern | Snippet: `std::unordered_set<G4VTrackingManager *> trackingManagersToFlush;` inserts each custom particle tracking manager pointer and flushes the set after the stack loop. |
| Why slow | The common default path pays only declaration/clear, but workloads with custom managers hash and probe a dynamic container per handed-over track. The number of distinct managers is usually tiny and stable for an event. |
| Proposed fix | Replace the per-event `unordered_set` with a small fixed-vector/bitset keyed by particle-definition tracking-manager index, using linear uniqueness for the expected small cardinality and falling back to a set only above the inline capacity. |
| Expected speedup | 1.05-1.25x in custom-tracking-manager handoff paths; neutral for ordinary `G4TrackingManager` events. |
| Validation | Custom manager fixtures must prove each distinct manager is flushed exactly once, in acceptable order, with identical deferred secondary stacking and abort behavior. |
| Implementation target | `g4-event-custom-tracking-smallset` |
| Citation | Stroustrup 2012; Intel 2024 Optimization Reference Manual; Drepper 2007. |
| Status | OPEN |

### BD-geant4-199  `G4TrackingManager` clears the secondary vector with repeated accessor calls at every track start

| Field | Value |
|-------|-------|
| File | `source/tracking/src/G4TrackingManager.cc`; `source/event/src/G4EventManager.cc` |
| Lines | `G4TrackingManager.cc`: 61-75; `G4EventManager.cc`: 246-263 |
| Hot-path % (profile-measured) | OPEN: pending perf aggregate; per-line self% `OPEN:` pending perf. |
| Category | 5 — Control flow |
| Current pattern | Snippet: `for (auto& itr : *GimmeSecondaries()) delete itr; GimmeSecondaries()->clear();` runs before every track, then the event manager later reads `GimmeSecondaries()` after tracking. |
| Why slow | The vector should usually be empty after the event manager stacks/deletes the prior track's secondaries, but the tracking manager still performs accessor calls and an empty-loop/clear path per track. Prior BD-geant4-017 covers ownership; this isolates redundant per-track cleanup checks. |
| Proposed fix | Add an explicit secondary-list ownership state or debug assertion so the normal post-stack path can skip clearing an already-empty vector, with a slow cleanup fallback only after abort/error paths. |
| Expected speedup | 1.02-1.08x in high-track-count events; also improves diagnostics for leaked secondary ownership. |
| Validation | Instrument empty/non-empty cleanup counts, run abort and `fKillTrackAndSecondaries` fixtures, and compare secondary ownership under ASan/LSan with fixed-seed event outputs. |
| Implementation target | `g4-tracking-secondary-cleanup-state` |
| Citation | Meyers 2005; Intel 2024 Optimization Reference Manual. |
| Status | OPEN |

### BD-geant4-200  Kill-track-and-secondaries cleanup deletes secondary tracks one by one in the event switch

| Field | Value |
|-------|-------|
| File | `source/event/src/G4EventManager.cc`; `source/event/src/G4TrackStack.cc` |
| Lines | `G4EventManager.cc`: 246-280; `G4TrackStack.cc`: 41-49 |
| Hot-path % (profile-measured) | OPEN: pending perf aggregate; per-line self% `OPEN:` pending perf. |
| Category | 6 — Memory allocation |
| Current pattern | Snippet: `for(auto & secondarie : *secondaries) { delete secondarie; } secondaries->clear(); delete track;` mirrors stack `clearAndDestroy()` element-wise deletion. |
| Why slow | Rare kill paths can still dominate pathological events with many rejected secondaries: each object is returned individually to its allocator and dynamic-particle payload cleanup is scattered, causing cache misses and allocator bookkeeping bursts. |
| Proposed fix | Batch-destroy killed secondary tracks through the same per-event arena proposed for secondary construction, preserving destructor side effects but amortizing allocator metadata and improving locality. |
| Expected speedup | 1.10-1.40x inside kill-heavy event cleanup; ordinary events see little change. |
| Validation | Compare killed-secondary counts, user track-information destructors, allocator free counts, ASan/LSan output, and event records for processes returning `fKillTrackAndSecondaries`. |
| Implementation target | `g4-event-killed-secondary-batch-destroy` |
| Citation | Berger et al. 2000; Lea 2000; Drepper 2007. |
| Status | OPEN |

## References for standard optimization techniques

- Berger, Emery D.; Zorn, Benjamin G.; McKinley, Kathryn S. 2000, "Composing High-Performance Memory Allocators", PLDI.
- Cormen, Thomas H.; Leiserson, Charles E.; Rivest, Ronald L.; Stein, Clifford. 2009, *Introduction to Algorithms*, 3rd ed.
- Drepper, Ulrich. 2007, "What Every Programmer Should Know About Memory".
- Herlihy, Maurice; Shavit, Nir. 2012, *The Art of Multiprocessor Programming*, revised first ed.
- Intel. 2024, *Intel 64 and IA-32 Architectures Optimization Reference Manual*.
- Knuth, Donald E. 1998, *The Art of Computer Programming*, Vol. 1, 3rd ed.
- Lea, Doug. 2000, "A Memory Allocator".
- Meyers, Scott. 2005, *Effective C++*, 3rd ed.
- Stroustrup, Bjarne. 2012, *A Tour of C++*.
- Sutter, Herb. 2005, *Exceptional C++ Style*.

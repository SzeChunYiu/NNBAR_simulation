# Geant4 bottleneck database — hit collection / sensitive detector shard

Status: compact-safe worker-4 iteration 5. This is the hot path 5
continuation for `docs/reports/bottleneck_database_geant4.md`; the shard is
separate only because the main database is already at the 500-line file cap.

## Source provenance and profile basis

- LUNARC socket guard returned `Connected` before remote inspection.
- Authoritative NNBAR Geant4 install check:
  `/projects/hep/fs10/shared/nnbar/billy/packages/hibeam_env/bin/geant4-config
  --version --prefix` reported Geant4 `11.2.2` at
  `/projects/hep/fs10/shared/nnbar/billy/packages/hibeam_env`.
- A bounded LUNARC search did not find an extracted `source/digits_hits` tree,
  so this iteration used the read-only upstream Geant4 `v11.2.2` source at
  `/tmp/geant4-v11.2.2`, matching the prior structured-review provenance.
- Hot-path weight follows the lane-spec basis: hit collection / sensitive
  detectors are about 10% aggregate Geant4 CPU. Per-line self-percentages are
  `OPEN:` until Phase 5 perf maps BasicExample/TestEm0/Hadr01/OpNovice2
  samples to exact source lines.
- Isolation check: documentation only. No `NNBAR_Detector/`,
  `nnbar_reconstruction/`, `scripts/`, `lunarc/`, `slurm/`, or `macro/` paths
  were modified.

## References used by entries

- Fredman, Komlos, and Szemeredi 1984, static perfect hashing.
- Botelho, Pagh, and Ziviani 2007, minimal perfect hashing.
- Futamura 1971/1983, partial evaluation / projection work.
- Hoelzle, Chambers, and Ungar 1991, polymorphic inline caches.
- Stroustrup 2012, *Why you should avoid linked lists*.
- Martin Thompson 2011, mechanical-sympathy data-oriented queues.
- Herlihy and Shavit 2012, *The Art of Multiprocessor Programming*.
- Intel 2024, *64 and IA-32 Architectures Optimization Reference Manual*.
- Cormen et al. 2009, *Introduction to Algorithms*.

---

## Hit collection / sensitive-detector hot path

This compact iteration covers hot path 5 from
`docs/parallel-sessions/g4-source-review.md`: `G4SDManager.cc`,
`G4VSensitiveDetector.cc`, and `G4HCofThisEvent.cc`, plus the adjacent inline
headers that define the actual per-step sensitive-detector and hits-collection
fast paths.

### BD-geant4-024  Event hit-container allocation is repeated at every event boundary

| Field | Value |
|-------|-------|
| File | `source/digits_hits/detector/src/G4SDManager.cc`; `source/digits_hits/hits/src/G4HCofThisEvent.cc` |
| Lines | `104-108`; `37-42` |
| Hot-path % (profile-measured) | Hit/SD family: about 10% aggregate Geant4 CPU; per-line self% `OPEN:` pending Phase 5 perf. |
| Category | 6 — Memory allocation |
| Current pattern | Short snippet: `new G4HCofThisEvent(...)`, then detector-tree initialization. |
| Why slow | Every event allocates a hits-container object and a separately allocated collection-vector sized from the stable HC table, even though detector geometry and collection count usually do not change between events. |
| Proposed fix | Add a per-thread reusable event-hit-container pool keyed by HC table generation, with a reset/clear path that preserves collection capacity and zeroes only active slots. |
| Expected speedup | 1.05-1.2x in event-boundary overhead; most useful for high-event-rate medical/space workloads with many short events. |
| Validation | Fixed-seed event runs must preserve collection IDs, null/non-null collection slots, hit counts, and event deletion ownership; allocator traces should show no general-heap allocation for `G4HCofThisEvent` after warm-up. |
| Implementation target | `geant4-fork:g4-hcevent-pool` and `g4gpu-phase6-hit-container-arena`. |
| Citation | Stroustrup 2012; Martin Thompson 2011. |
| Status | OPEN |

### BD-geant4-025  Active sensitive-detector initialization recursively walks the SD tree

| Field | Value |
|-------|-------|
| File | `source/digits_hits/detector/src/G4SDStructure.cc` |
| Lines | `178-199` |
| Hot-path % (profile-measured) | Event initialization/termination inside the hit/SD family; per-line self% `OPEN:` pending perf. |
| Category | 3 — Data structure |
| Current pattern | Short snippet: recurse over substructures, then call active detectors' begin/end hooks. |
| Why slow | The tree walk repeats every event even when the active detector set is unchanged, mixing hierarchy traversal, branch checks, and virtual callbacks. Large detector applications pay this before and after each event. |
| Proposed fix | Compile a flat active-detector schedule whenever registration or activation changes, then replay contiguous begin/end callback arrays at event boundaries. |
| Expected speedup | 1.1-1.5x for SD initialization/termination in geometries with many detector nodes; small but broad wall-clock improvement for event-heavy workloads. |
| Validation | Compare callback order, active/inactive behavior, and HCE contents against vanilla for nested SD paths, activation toggles, and dynamically registered detectors. |
| Implementation target | `geant4-fork:g4-flat-sd-event-schedule`. |
| Citation | Stroustrup 2012; Intel Optimization Manual 2024. |
| Status | OPEN |

### BD-geant4-026  Hits-collection ID lookup is a linear string scan with per-query concatenation

| Field | Value |
|-------|-------|
| File | `source/digits_hits/detector/src/G4HCtable.cc`; `source/digits_hits/detector/src/G4SDManager.cc`; `source/digits_hits/detector/src/G4VSensitiveDetector.cc` |
| Lines | `43-67`; `127-145`; `94-98` |
| Hot-path % (profile-measured) | Hit collection lookup / SD initialization family; per-line self% `OPEN:` pending perf. |
| Category | 3 — Data structure |
| Current pattern | Short snippet: loop over HC names; full-name queries build `SD/HC` strings before comparison. |
| Why slow | Collection IDs are static after detector setup, but lookup remains O(collections) string work and ambiguity checks. User SD code often calls `GetCollectionID` during initialization paths that repeat per run or worker thread. |
| Proposed fix | Build a registration-time map from canonical collection names to IDs, plus an optional minimal perfect hash for frozen detector configurations; preserve ambiguity diagnostics in a slow path. |
| Expected speedup | 5-50x for collection-ID lookup itself; wall-clock impact depends on user-code lookup frequency and thread count. |
| Validation | Exhaustively compare ID, missing, and ambiguous-name results for HC-only and `SD/HC` queries; verify persistent run metadata sees the same ID ordering. |
| Implementation target | `geant4-fork:g4-hctable-perfect-hash`. |
| Citation | Fredman, Komlos, and Szemeredi 1984; Botelho, Pagh, and Ziviani 2007. |
| Status | OPEN |

### BD-geant4-027  The per-step sensitive-detector gate mixes branches with virtual dispatch

| Field | Value |
|-------|-------|
| File | `source/digits_hits/detector/include/G4VSensitiveDetector.hh` |
| Lines | `82-92` |
| Hot-path % (profile-measured) | Per-step hit dispatch inside the hit/SD family; per-line self% `OPEN:` pending perf. |
| Category | 5 — Control flow |
| Current pattern | Short snippet: active flag, optional filter, optional readout geometry, then `ProcessHits(...)`. |
| Why slow | Common detectors have no filter and no readout geometry, but every hit-capable step still executes a generic branch ladder before a virtual call. Branch outcomes are detector-specific and stable over many steps. |
| Proposed fix | Generate a detector-specific hit dispatcher with guarded fast paths for `(active, no filter, no RO geometry)` and a polymorphic inline cache for the few common detector classes. |
| Expected speedup | 1.05-1.25x in SD dispatch overhead; 1-4% wall-clock for hit-rich calorimeter or medical detector runs. |
| Validation | Fixed-seed hit collections must match bit-for-bit for active toggles, filters, RO geometry, and derived `ProcessHits` side effects; fallback counters must trigger on all uncommon states. |
| Implementation target | `g4gpu-phase5d-jit-sd-dispatch` plus an upstream guarded fast-path MR. |
| Citation | Futamura 1971/1983; Hoelzle, Chambers, and Ungar 1991. |
| Status | OPEN |

### BD-geant4-028  Multi-sensitive detectors serially fan out through nested virtual Hit calls

| Field | Value |
|-------|-------|
| File | `source/digits_hits/detector/src/G4MultiSensitiveDetector.cc` |
| Lines | `66-71` |
| Hot-path % (profile-measured) | Per-step multi-SD dispatch; per-line self% `OPEN:` pending perf. |
| Category | 5 — Control flow |
| Current pattern | Short snippet: loop over contained detectors and accumulate `sd->Hit(aStep)` results. |
| Why slow | A composite SD stacks an outer virtual call with one virtual hit gate per contained SD. The boolean accumulation also creates a loop-carried dependency while the contained SD list is fixed after setup. |
| Proposed fix | Flatten composite SDs into the detector-specific dispatch schedule from BD-geant4-027, with optional all-success fast paths when return values are not observed by user code. |
| Expected speedup | 1.1-1.4x for composite-SD dispatch sections; most valuable in detectors that attach multiple logical scorers to the same sensitive volume. |
| Validation | Compare all contained SD callbacks, return aggregation, hit collections, and exception behavior for empty, single, and multi-SD composites. |
| Implementation target | `geant4-fork:g4-flat-multisd-dispatch`. |
| Citation | Hoelzle, Chambers, and Ungar 1991; Intel Optimization Manual 2024. |
| Status | OPEN |

### BD-geant4-029  Multi-functional detectors iterate every primitive scorer for each eligible step

| Field | Value |
|-------|-------|
| File | `source/digits_hits/detector/src/G4MultiFunctionalDetector.cc` |
| Lines | `50-57` |
| Hot-path % (profile-measured) | Per-step primitive-scorer dispatch; per-line self% `OPEN:` pending perf. |
| Category | 2 — Algorithm |
| Current pattern | Short snippet: if step length or energy deposit is nonzero, loop over all primitives. |
| Why slow | Primitive scorers are independent, but the current loop runs every primitive for every eligible step and gives each scorer a full `G4Step` view. Many scorers depend on disjoint observables or volume filters. |
| Proposed fix | Build a primitive-scorer dependency mask at registration time and dispatch only scorer groups whose required observables changed, using a compact function-pointer table for common primitive types. |
| Expected speedup | 1.2-2x inside multi-functional detector scoring for many-primitive applications; needs profile confirmation on scoring-heavy benchmarks. |
| Validation | Compare per-primitive maps, collection IDs, and end-of-event reductions for synthetic steps covering zero/nonzero length, zero/nonzero energy deposit, and volume-filter edge cases. |
| Implementation target | `g4gpu-phase6-scoring-dependency-mask`. |
| Citation | Cormen et al. 2009; Futamura 1971/1983. |
| Status | OPEN |

### BD-geant4-030  G4THitsCollection stores hit pointers in a growable vector without reserve hints

| Field | Value |
|-------|-------|
| File | `source/digits_hits/hits/include/G4THitsCollection.hh` |
| Lines | `94-99`; `129-151` |
| Hot-path % (profile-measured) | Hit insertion / collection ownership family; per-line self% `OPEN:` pending allocation trace. |
| Category | 6 — Memory allocation |
| Current pattern | Short snippet: `push_back` one hit pointer; constructors allocate a vector and destructors delete each hit. |
| Why slow | Hit-heavy events pay vector growth, pointer chasing, and per-hit heap deletion at event teardown. Detector-specific hit multiplicity is often predictable from occupancy or scoring-grid dimensions. |
| Proposed fix | Add optional reserve hints and event arenas for transient hits; for fixed-grid scorers, offer a contiguous SoA/POD hit buffer that preserves the `G4VHitsCollection` observer interface. |
| Expected speedup | 1.2-2x for hit insertion/teardown in calorimeter or optical-photon workloads; also lowers allocator variance between threads. |
| Validation | Compare hit order, pointer-stable access during the event, destructor side effects, and memory high-water marks; require identical serialized hit outputs. |
| Implementation target | `g4gpu-phase6-hit-arena` and `geant4-fork:g4-thitscollection-reserve`. |
| Citation | Stroustrup 2012; Herlihy and Shavit 2012. |
| Status | OPEN |

### BD-geant4-031  G4HCofThisEvent counts and deletes collections by scanning pointer slots

| Field | Value |
|-------|-------|
| File | `source/digits_hits/hits/src/G4HCofThisEvent.cc`; `source/digits_hits/hits/include/G4HCofThisEvent.hh` |
| Lines | `44-50`; `72-81` |
| Hot-path % (profile-measured) | Event-end hit collection bookkeeping; per-line self% `OPEN:` pending perf/allocation trace. |
| Category | 3 — Data structure |
| Current pattern | Short snippet: delete each stored collection; count non-null slots by scanning the vector. |
| Why slow | The HCE knows when collections are added, but event-end and observer paths still walk the full capacity and branch on null slots. Sparse detector configurations waste cycles and touch cache lines for absent collections. |
| Proposed fix | Maintain an active collection index list and active count when `AddHitsCollection` succeeds; event-end deletion and observers can walk only populated IDs while preserving capacity-index lookup. |
| Expected speedup | 1.05-1.3x in HCE bookkeeping for sparse HC tables; useful in large applications with many optional scorers. |
| Validation | Compare `GetHC(i)`, `GetNumberOfCollections()`, deletion ownership, and behavior for duplicate/invalid HC IDs against vanilla across sparse and dense tables. |
| Implementation target | `geant4-fork:g4-hcevent-active-index`. |
| Citation | Cormen et al. 2009; Intel Optimization Manual 2024. |
| Status | OPEN |

## Next implementations after hit / SD iteration

1. `g4gpu-phase6-hit-arena` (BD-geant4-030) — largest likely allocator win for
   hit-heavy detector workloads, and it composes with the track/secondary arena.
2. `g4gpu-phase5d-jit-sd-dispatch` (BD-geant4-027/028) — guarded dispatch
   specialization that should be bit-exact and upstreamable as a fast path.
3. `geant4-fork:g4-flat-sd-event-schedule` (BD-geant4-025) — low-risk event
   boundary improvement for large detector trees.
4. `geant4-fork:g4-hctable-perfect-hash` (BD-geant4-026) — setup/initialization
   speedup that removes repeated string scans without physics risk.
5. `g4gpu-phase6-scoring-dependency-mask` (BD-geant4-029) — higher-upside but
   needs a scoring-heavy benchmark to prove observable dependencies are safe.

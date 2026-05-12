# Geant4 bottleneck database — process-manager structured shard

Status: compact-safe worker-4 lane-swap iteration, 2026-05-12. This shard
claims the next free block `BD-geant4-131`--`BD-geant4-140` identified in
`docs/reports/g4gpu_bottleneck_gap_scan_20260512.md` and does not append to the
near-cap root database `docs/reports/bottleneck_database_geant4.md`.

## Source provenance and profile basis

- LUNARC socket guard returned `Connected` before remote inspection.
- LUNARC Geant4 install check reported version `11.2.2` at
  `/projects/hep/fs10/shared/nnbar/billy/packages/hibeam_env`.
- The LUNARC prefix exposes `include/Geant4/G4ProcessManager.hh`, but checked
  implementation paths under the prefix were absent:
  `source/processes/management/src/G4ProcessManager.cc` and
  `src/G4ProcessManager.cc`.
- The line-by-line review therefore used official upstream Geant4 `v11.2.2`
  raw source files fetched from `https://gitlab.cern.ch/geant4/geant4` into the
  local read-only cache `/tmp/geant4-v11.2.2`:
  - `G4ProcessManager.cc`: 1312 lines, SHA-256
    `979b4cfcf66cf3eb0dc5702e6eee024fbf7c790760ce5efa143bdb0348df30c8`
  - `G4ProcessManager.hh`: 351 lines, SHA-256
    `b1cbf36b16579e3d69458f0a68f9de2ce23ed101332c150ed28a2c8b9993677b`
  - `G4ProcessManager.icc`: 184 lines, SHA-256
    `eadab29d4eb9b9ac39ba7b23c9efef22f2598eb6ea392d0ec5b93d5c9ef411f2`
  - `G4ProcessVector.cc`: 150 lines, SHA-256
    `57060599eae37b3b90d8db5d9e9e5e857daff1959033a0f91c6dc09487d5b0ca`
  - `G4SteppingManager.cc`: 841 lines, SHA-256
    `1134641c714fe1665efb1b1ee36828372f02e53f5f375ee14354c9ae24444937`
- Hot-path weight remains `OPEN:` until Phase 5 perf maps BasicExample/TestEm0,
  Hadr01/Hadr04, and optical workloads to exact source lines. Process-manager
  configuration entries are mostly startup/reconfiguration enablers; DoIt and
  active-vector dispatch entries can affect every transported step.
- Isolation check: documentation only. No `NNBAR_Detector/`,
  `nnbar_reconstruction/`, `scripts/`, `lunarc/`, `slurm/`, or `macro/` paths
  were modified.

## References used by entries

- Futamura 1971/1983, partial evaluation and projection.
- Hoelzle, Chambers, and Ungar 1991, polymorphic inline caches.
- Intel 2024, *64 and IA-32 Architectures Optimization Reference Manual*.
- Stroustrup 2012, cache-friendly contiguous data-structure guidance.
- Fraser and Hanson 1995, `lcc` retargetable-code-generator design.
- Herlihy and Shavit 2012, concurrent/object-lifetime design.
- Vose 1991, table-driven categorical sampling; cited only where dispatch-table
  replacement is analogous, not for physics sampling.

---

### BD-geant4-131  AddProcess mutates three ordered vectors and rebuilds GPIL views per added process

| Field | Value |
|-------|-------|
| File | `source/processes/management/src/G4ProcessManager.cc` |
| Lines | 405-510 |
| Hot-path % (profile-measured) | Startup / physics-list construction: `OPEN:` pending initialization profiling. Runtime benefit is enabling immutable dispatch descriptors used by later entries. |
| Category | 3 — Data structure |
| Current pattern | Snippet: `theProcessList->insert(aProcess)`, `new G4ProcessAttribute(aProcess)`, per-DoIt `InsertAt(...)`, then `CreateGPILvectors()`. |
| Why slow | Adding one process updates the global process table, the all-process list, up to three ordered DoIt vectors, all affected attribute indices, and then rebuilds all GPIL vectors. Physics-list setup repeats this small graph mutation dozens of times per particle. |
| Proposed fix | Add a process-manager builder/finalize phase: collect process descriptors, ordering parameters, and applicability once, then sort and materialize all six vectors in one bulk pass. Keep the current mutating API as a compatibility wrapper that marks the builder dirty. |
| Expected speedup | 1.5-3x for process-manager construction on particles with many processes; negligible event-loop speedup by itself, but it unlocks immutable vector descriptors for BD-geant4-136--139. |
| Validation | Compare `DumpInfo()` process order, `idxProcVector`, `ordProcVector`, active flags, and all `Get*ProcessVector()` contents for every particle in a reference physics list; then run fixed-seed event replays to require identical selected processes and final states. |
| Implementation target | `g4gpu-phase5d-process-manager-builder`; upstream Geant4 MR `g4-process-manager-bulk-finalize`. |
| Citation | Stroustrup 2012; Fraser and Hanson 1995. |
| Status | OPEN |

### BD-geant4-132  Ordered insertion does an O(processes) position scan plus an O(processes) index repair

| Field | Value |
|-------|-------|
| File | `source/processes/management/src/G4ProcessManager.cc`; `source/processes/management/src/G4ProcessVector.cc` |
| Lines | `G4ProcessManager.cc` 307-338 and 383-400; `G4ProcessVector.cc` 125-149 |
| Hot-path % (profile-measured) | Startup / dynamic process activation: `OPEN:` pending physics-list setup profile. |
| Category | 2 — Algorithm |
| Current pattern | Snippet: `FindInsertPosition(...)` scans `theAttrVector`; `InsertAt(...)` inserts into the vector and increments later `idxProcVector` slots. |
| Why slow | Each ordered insertion performs two linear passes over the same small process set, plus `std::vector` insertion movement. The asymptotic cost is acceptable for tiny lists, but repeated across all particles and DoIt vectors it creates avoidable setup work and complicated index mutation. |
| Proposed fix | During the builder/finalize phase, stable-sort descriptors by `(DoIt kind, ordering, original sequence)` and assign final indices once. For compatibility mode, add a single helper that returns both insertion point and affected-index span to avoid duplicate scans. |
| Expected speedup | 1.2-2x for setup sections dominated by process ordering; lower risk than runtime changes because no physics random stream is touched. |
| Validation | Golden tests for equal-order, `ordLast`, first/second/last ordering, inactive processes, and removal/reinsert cases; assert exact vector order and index arrays before event replay. |
| Implementation target | `g4gpu-phase5d-process-order-bulk-sort`. |
| Citation | Intel 2024 data-movement guidance; Stroustrup 2012. |
| Status | OPEN |

### BD-geant4-133  SetProcessOrdering removes, reinserts, and fully regenerates GPIL vectors for one ordering change

| Field | Value |
|-------|-------|
| File | `source/processes/management/src/G4ProcessManager.cc` |
| Lines | 620-704 |
| Hot-path % (profile-measured) | Rare dynamic reconfiguration / setup: `OPEN:`. Event-loop impact appears when this invalidates runtime dispatch caches. |
| Category | 3 — Data structure |
| Current pattern | Snippet: `RemoveAt(ip, ...)`, update `ordProcVector`, `InsertAt(ip, ...)`, `CheckOrderingParameters(...)`, `CreateGPILvectors()`. |
| Why slow | A single ordering edit performs vector erasure, vector insertion, two index-repair passes, consistency checks, and a full six-vector GPIL rebuild. This makes any later runtime cache conservative because there is no compact mutation epoch or per-vector dirty bit. |
| Proposed fix | Introduce per-DoIt-vector epochs and dirty flags. Reorder one DoIt vector incrementally, rebuild only its matching GPIL reverse view, and bump an epoch consumed by stepping-manager dispatch descriptors. |
| Expected speedup | 1.3-2.5x for ordering-heavy initialization and much cheaper invalidation of optimized GPIL/DoIt tables. |
| Validation | Run ordering mutation tests before and after initialization; assert epochs change exactly once per edited vector and fallback dispatch is used when a mutation occurs during tracking. Fixed-seed replays must preserve selected process identity. |
| Implementation target | `g4gpu-phase5d-process-vector-epochs`. |
| Citation | Herlihy and Shavit 2012; Hoelzle, Chambers, and Ungar 1991. |
| Status | OPEN |

### BD-geant4-134  First/second/last ordering helpers duplicate mutation paths and special-case scans

| Field | Value |
|-------|-------|
| File | `source/processes/management/src/G4ProcessManager.cc` |
| Lines | 707-903 |
| Hot-path % (profile-measured) | Setup / physics-list construction: `OPEN:`. |
| Category | 5 — Control flow |
| Current pattern | Snippet: `SetProcessOrderingToFirst(...)` and `SetProcessOrderingToSecond(...)` hand-roll remove/insert logic; `SetProcessOrderingToSecond(...)` rescans attributes to find the first non-zero ordering. |
| Why slow | Three public ordering helpers encode overlapping policy branches separately, which makes the process-manager mutation surface larger than necessary and increases the chance that optimized cache invalidation misses a path. |
| Proposed fix | Replace helper internals with one `ReorderProcess(idDoIt, placement)` primitive that computes target ordering/position, mutates the selected DoIt vector once, and calls the same dirty-vector/epoch logic as BD-geant4-133. |
| Expected speedup | 1.1-1.5x in setup paths using first/second/last helpers; primarily a maintainability and cache-correctness win. |
| Validation | Exhaustively exercise repeated first/last warnings, two-process equal-order cases, second-position insertion, inactive processes, and invalid DoIt indices; compare warnings, vector order, and `DumpInfo()` output. |
| Implementation target | `g4gpu-phase5d-process-reorder-primitive`. |
| Citation | Fraser and Hanson 1995; Intel 2024 branch/control-flow guidance. |
| Status | OPEN |

### BD-geant4-135  CreateGPILvectors rebuilds all reverse GPIL vectors even when one DoIt vector changes

| Field | Value |
|-------|-------|
| File | `source/processes/management/src/G4ProcessManager.cc` |
| Lines | 1135-1159 |
| Hot-path % (profile-measured) | Setup / reconfiguration: `OPEN:`; can affect event-loop cache invalidation cost. |
| Category | 3 — Data structure |
| Current pattern | Snippet: reset GPIL indices for every process, clear each GPIL vector, then insert every DoIt process in reverse order. |
| Why slow | GPIL vectors are deterministic reverse views of DoIt vectors, but the code stores and rebuilds full pointer vectors. One DoIt edit rebuilds AtRest, AlongStep, and PostStep GPIL views and calls `GetAttribute(...)` repeatedly. |
| Proposed fix | Store GPIL as a reverse view descriptor `(doItVector, reverse=true)` or rebuild only the dirty GPIL vector. If materialized storage is kept for ABI compatibility, reserve capacity and update indices in one reverse pass over the changed vector. |
| Expected speedup | 1.5-3x for GPIL regeneration; reduces setup noise and simplifies direct dispatch-table generation. |
| Validation | Compare all `GetProcessVector(idx*, typeGPIL)` entries and `idxProcVector` values against vanilla after add/remove/reorder/activate/inactivate sequences; event replay must preserve GPIL winner order. |
| Implementation target | `g4gpu-phase5d-gpil-reverse-view`. |
| Citation | Stroustrup 2012; Intel 2024 cache-locality guidance. |
| Status | OPEN |

### BD-geant4-136  Six pointer vectors plus separate attributes force pointer chasing instead of compact dispatch descriptors

| Field | Value |
|-------|-------|
| File | `source/processes/management/include/G4ProcessManager.hh`; `source/processes/management/include/G4ProcessManager.icc` |
| Lines | `G4ProcessManager.hh` 291-336; `G4ProcessManager.icc` 83-121 |
| Hot-path % (profile-measured) | Dispatch metadata overhead: `OPEN:` pending Phase 5 process-vector cache-miss counters. |
| Category | 3 — Data structure |
| Current pattern | Snippet: `G4ProcessVector* theProcVector[SizeOfProcVectorArray]` and inline getters returning raw `G4ProcessVector*`. |
| Why slow | The stepping manager sees arrays of process pointers but not compact metadata such as process type, forced-condition capability, side-effect class, or direct GPIL/DoIt thunks. Hot loops therefore reload process objects and branch on policy scattered across classes. |
| Proposed fix | Build an immutable `ProcessDispatchDescriptor` array per particle/DoIt kind after physics initialization. Each descriptor stores the process pointer plus cached process type, activation epoch, optional direct thunk, and side-effect flags while preserving the old vector API as a view. |
| Expected speedup | 1.1-1.4x on process-dispatch overhead once used by GPIL/DoIt loops; larger when combined with BD-geant4-137--139. |
| Validation | Descriptor construction tests compare every field to vanilla process/vector state; dispatch uses descriptors only when the epoch matches, otherwise falls back to the original vectors. Event replay must preserve selected process order and secondary production. |
| Implementation target | `g4gpu-phase5d-process-dispatch-descriptors`. |
| Citation | Hoelzle, Chambers, and Ungar 1991; Intel 2024. |
| Status | OPEN |

### BD-geant4-137  Process inactivation leaves null entries that every GPIL and DoIt loop must test

| Field | Value |
|-------|-------|
| File | `source/processes/management/src/G4ProcessManager.cc`; `source/tracking/src/G4SteppingManager.cc` |
| Lines | `G4ProcessManager.cc` 906-979; `G4SteppingManager.cc` 465-470, 526-529, and 734-737 |
| Hot-path % (profile-measured) | Per-step dispatch branch overhead: `OPEN:` pending null-slot counters in production physics lists. |
| Category | 5 — Control flow |
| Current pattern | Snippet: inactivation writes `nullptr` into vectors; PostStep, AlongStep GPIL, and AlongStep DoIt loops check and continue on null entries. |
| Why slow | In ordinary production, process activation is stable for long stretches, but every step still pays null-branch checks. If a user inactivates a process, the sparse vector preserves indices at the cost of branches in all future dispatch loops. |
| Proposed fix | Maintain a compact active descriptor list for event-loop dispatch and a sparse compatibility view for public indices. Activation changes bump an epoch and rebuild the compact list outside the hot loop. |
| Expected speedup | 1-3% wall-clock if null checks and sparse vectors appear in perf; higher in custom applications that inactivate many processes. |
| Validation | Toggle process activation during controlled runs and compare public vector indices, active flags, GPIL winner order, DoIt calls, and final events. Add a stress test with alternating active/inactive processes to force fallback. |
| Implementation target | `g4gpu-phase5d-compact-active-process-list`. |
| Citation | Intel 2024 branch-prediction guidance; Herlihy and Shavit 2012. |
| Status | OPEN |

### BD-geant4-138  AlongStep DoIt dispatch treats all continuous processes as equally side-effectful

| Field | Value |
|-------|-------|
| File | `source/tracking/src/G4SteppingManager.cc` |
| Lines | 722-758 |
| Hot-path % (profile-measured) | AlongStep DoIt per-step overhead: `OPEN:` pending process-level call counts. |
| Category | 9 — JIT specialization |
| Current pattern | Snippet: for every AlongStep process, call `AlongStepDoIt(...)`, `UpdateStepForAlongStep(...)`, `ProcessSecondariesFromParticleChange()`, set track status, then `Clear()`. |
| Why slow | Many continuous processes have predictable side-effect classes for a given particle/physics list, but the generic loop performs secondary extraction, status propagation, and particle-change cleanup uniformly. This repeats policy work for every step even when a process never creates secondaries or cannot alter track status. |
| Proposed fix | Use descriptors from BD-geant4-136 to split AlongStep DoIt into specialized loops: no-secondary/no-status-change fast path, status-only path, and full generic path. Retain byte-for-byte fallback when a process advertises unknown side effects. |
| Expected speedup | 1.1-1.3x inside AlongStep DoIt dispatch; 1-4% event-level gain in transportation/MSC/ionization-heavy workloads if perf confirms dispatch overhead. |
| Validation | Instrument vanilla particle-change deltas per process, classify side effects, then replay fixed seeds and assert identical step updates, track statuses, secondary lists, and process-defined-step metadata. |
| Implementation target | `g4gpu-phase5d-alongstep-sideeffect-specialization`. |
| Citation | Futamura 1971/1983; Hoelzle, Chambers, and Ungar 1991. |
| Status | OPEN |

### BD-geant4-139  PostStep DoIt dispatch scans inverse order and condition flags after the winner is known

| Field | Value |
|-------|-------|
| File | `source/tracking/src/G4SteppingManager.cc` |
| Lines | 773-825 |
| Hot-path % (profile-measured) | PostStep DoIt per-step overhead: `OPEN:` pending selected-condition histograms. |
| Category | 5 — Control flow |
| Current pattern | Snippet: iterate `np`, read `SelectedPostStepDoItVector` in reverse order, evaluate four condition clauses, call `InvokePSDIP(...)`, then run a second scan for `StronglyForced` after a killed track. |
| Why slow | The GPIL phase already computed selected/forced conditions, but DoIt dispatch reinterprets the condition vector through branchy predicates and inverse indexing. The killed-track strongly-forced pass is rare but remains interleaved with the common path. |
| Proposed fix | During GPIL selection, materialize a compact PostStep invocation list for the current step: normal selected process, forced processes, and a separate strongly-forced-after-kill list. Invoke that list directly in DoIt. |
| Expected speedup | 1.1-1.4x inside PostStep DoIt dispatch; broad but small event-level gain on secondary-rich EM/hadronic workloads. |
| Validation | Step-level trace comparison of condition flags, invocation order, killed-track behavior, `fWorldBoundary` updates, particle changes, and secondaries for NotForced/Forced/ExclusivelyForced/StronglyForced cases. |
| Implementation target | `g4gpu-phase5d-poststep-invocation-list`. |
| Citation | Intel 2024 branch-control guidance; Hoelzle, Chambers, and Ungar 1991. |
| Status | OPEN |

### BD-geant4-140  G4ProcessVector owns a heap vector and exposes insertion/erasure instead of reserved immutable storage

| Field | Value |
|-------|-------|
| File | `source/processes/management/include/G4ProcessVector.hh`; `source/processes/management/src/G4ProcessVector.cc`; `source/processes/management/include/G4ProcessVector.icc` |
| Lines | `G4ProcessVector.hh` 44-101; `G4ProcessVector.cc` 37-57 and 125-149; `G4ProcessVector.icc` 51-66 |
| Hot-path % (profile-measured) | Setup and metadata locality: `OPEN:` pending physics-list construction profile. |
| Category | 6 — Memory allocation |
| Current pattern | Snippet: `G4ProcessVector` allocates `new G4ProcVector()`, `insert(...)` pushes back, `insertAt(...)` inserts by iterator walk, and `removeAt(...)` erases. |
| Why slow | Each `G4ProcessVector` is a separate heap object wrapping another heap vector. Insert/erase operations move pointer ranges and pair poorly with process-manager index arrays. The event loop later consumes these scattered allocations through pointer indirections. |
| Proposed fix | Add a small-buffer/reserved-storage implementation for the common process-count range and freeze vectors after initialization. A compatibility wrapper can still expose `G4ProcessVector` while descriptors use contiguous immutable storage. |
| Expected speedup | 1.2-2x for vector construction/mutation and modest dispatch cache-locality gains when descriptors alias contiguous storage. |
| Validation | ABI/API tests for `entries`, `index`, `contains`, `operator[]`, `insertAt`, `removeAt`, copy/assignment, and destructor behavior; full physics-list construction and fixed-seed event replay must match vanilla. |
| Implementation target | `g4gpu-phase5d-process-vector-small-buffer`. |
| Citation | Stroustrup 2012; Intel 2024 memory-hierarchy guidance. |
| Status | OPEN |

## Concrete next-step proposal

Queue a worker-3 implementation spike named
`g4gpu-phase5d-process-dispatch-descriptors` that implements only the safe
metadata half first: descriptor construction, epoch invalidation, and read-only
trace comparison against vanilla process vectors. Do **not** replace GPIL or
DoIt dispatch until the descriptor trace is bit-exact for at least FTFP_BERT,
QGSP_BERT_HP, and an EM-only physics list. If that passes, the first runtime
experiment should be BD-geant4-139 (PostStep invocation list), because it is a
local stepping-manager change with a clear step-level trace oracle and no
physics-table numerical changes.

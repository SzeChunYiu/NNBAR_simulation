# OpenMC bottleneck database — geometry and boundary hot path

Status: compact-safe worker-0 lane-swap from `codex-tasks/review/worker-0.txt`.
Scope is OpenMC v0.15.3 CSG geometry navigation after the existing
cross-section and transport shards. This shard deliberately continues at
`BD-openmc-023` and does not repeat `BD-openmc-001`--`022` from
`docs/reports/bottleneck_database_openmc.md` and
`docs/reports/bottleneck_database_openmc_transport.md`.

## Source provenance and profile basis

- Source tree read from LUNARC: `/projects/hep/fs10/shared/nnbar/billy/openmc`.
- LUNARC checkout is detached at OpenMC tag `v0.15.3`, commit `27e38e894`.
- A read-only local mirror at `/tmp/openmc-v0.15.3` was used for line-number
  verification only; no OpenMC build, run, fork patch, or production data was
  modified.
- SHA-256 parity between local and LUNARC source was verified for
  `src/geometry.cpp`, `src/universe.cpp`, `src/cell.cpp`, `src/surface.cpp`,
  `src/boundary_condition.cpp`, and `src/particle.cpp` before these line
  references were written.
- Hot-path percentages below inherit the lane-spec profile basis: OpenMC
  geometry tracking is expected to account for roughly 20--25% of transport
  CPU. Exact per-line self percentages remain `OPEN:` until a pinned LUNARC
  `perf record` run maps samples to these ranges.

## References used by entries

- Romano et al. 2015, *OpenMC: A state-of-the-art Monte Carlo code for research
  and development*, Annals of Nuclear Energy 82.
- Wald, Boulos, and Shirley 2007, *Ray Tracing Deformable Scenes using Dynamic
  Bounding Volume Hierarchies*.
- Khuong and Morin 2015, *Array layouts for comparison-based searching*.
- Aho, Sethi, and Ullman 1986, *Compilers: Principles, Techniques, and Tools*.
- Futamura 1971/1983, partial evaluation / projection work.
- Williams, Waterman, and Patterson 2009, *Roofline: an insightful visual
  performance model for multicore architectures*.
- Herlihy and Shavit 2008, *The Art of Multiprocessor Programming*.

---

### BD-openmc-023  Z-plane universe partition lookup still performs branchy surface tests

| Field | Value |
|-------|-------|
| File | `src/universe.cpp` |
| Lines | 180-215 |
| Hot-path % (profile-measured) | `OPEN:` geometry tracking family; expected 20--25% aggregate transport CPU before per-symbol LUNARC perf. |
| Category | 2 — Algorithm |
| Current pattern | `UniversePartitioner::get_cells` performs a manual binary search over z-plane surface indices and calls the virtual `surf.sense(r, u)` at each decision before returning a candidate-cell vector. |
| Why slow | The partition surfaces are restricted to z planes, but the hot lookup still pointer-chases through `model::surfaces` and executes a virtual sense calculation instead of comparing against a compact sorted z-coordinate array. |
| Proposed fix | Store partition breakpoints as contiguous `double z0` values with Eytzinger or branchless binary-search layout; return the same candidate vector while retaining the generic surface path only for non-z partitioners. |
| Expected speedup | 1.05--1.20× for partitioned universe lookup; wall-clock impact depends on cell-search self% in CE lattice benchmarks. |
| Validation | For every model in a geometry regression suite, compare candidate-cell sets from the old and new partitioners for sampled `(r,u)` points, then require identical located cell/material/lattice histories in fixed-seed transport. |
| Implementation target | `openmc-fork` geometry partitioner PR plus optional `libMCAccel/adapters/openmc` z-slab search primitive. |
| Cross-code pattern | Mirrors Geant4 `BD-geant4-042` navigator backend dispatch and `BD-geant4-047` smart-voxel partitioning opportunities. |
| Citation | Khuong and Morin 2015; Wald, Boulos, and Shirley 2007. |
| Status | OPEN |

### BD-openmc-024  Complex cells defeat partition pruning by being copied into every z slab

| Field | Value |
|-------|-------|
| File | `src/universe.cpp` |
| Lines | 80-177 |
| Hot-path % (profile-measured) | `OPEN:` geometry tracking family; exact impact pending perf plus candidate-list size instrumentation. |
| Category | 3 — Data structure |
| Current pattern | `UniversePartitioner` builds z-plane partitions once, but any non-simple cell is inserted into every partition because its bounds are considered difficult to determine. |
| Why slow | Complex cells remain in all candidate lists, so later `find_cell` calls still evaluate their region expressions even when a coarse bounding volume would exclude them. Large mixed simple/complex models lose much of the partitioner's intended pruning. |
| Proposed fix | Precompute conservative bounding boxes for complex regions and insert them only into intersecting slabs; for high-complexity universes, use a small BVH over cell bounding boxes before falling back to exact `contains`. |
| Expected speedup | 1.1--1.5× for universe cell search in models with many complex CSG cells; neutral for already-simple slab-only models. |
| Validation | Assert the new candidate list is a superset of the true containing cell for randomized points, then compare full transport cell histories and lost-particle counts against vanilla. |
| Implementation target | `openmc-fork` universe partitioner enhancement. |
| Cross-code pattern | Same structural issue as Geant4 `BD-geant4-047`, where static geometry partition quality controls every later navigation query. |
| Citation | Wald, Boulos, and Shirley 2007; Williams, Waterman, and Patterson 2009. |
| Status | OPEN |

### BD-openmc-025  Nested fill descent reinterprets static cell-fill policy on every search

| Field | Value |
|-------|-------|
| File | `src/geometry.cpp` |
| Lines | 102-248 |
| Hot-path % (profile-measured) | `OPEN:` `find_cell_inner` descent under geometry tracking; pending LUNARC perf. |
| Category | 5 — Control flow |
| Current pattern | After a candidate cell is found, `find_cell_inner` branches on `Fill::MATERIAL`, `Fill::UNIVERSE`, and `Fill::LATTICE`, reapplies translation/rotation, updates coordinate levels, and repeats the generic search. |
| Why slow | Fill type, translation, rotation, and lattice kind are static geometry metadata, but every particle lookup executes the same policy branch ladder and transform checks. The common material-cell exit cannot be inlined separately from nested-universe/lattice descent. |
| Proposed fix | Build immutable cell-fill traversal descriptors at geometry initialization: direct material exits, universe-transform descriptors, and lattice descriptors with prebound transform and index functions. Dispatch through compact descriptors rather than reinterpreting `Cell` fields. |
| Expected speedup | 1.05--1.25× inside nested cell lookup for deep lattice/universe models; higher if branch misses dominate `find_cell_inner`. |
| Validation | Trace `(coord level, universe, cell, lattice index, material, sqrtkT)` for vanilla and descriptor traversal on fixed histories; require bit-identical traces and final tallies. |
| Implementation target | `openmc-fork` geometry descriptor prototype; descriptor layout reusable by MCAccel geometry adapters. |
| Cross-code pattern | Mirrors Geant4 `BD-geant4-043` and `BD-geant4-044` repeated daughter-transform construction in navigation. |
| Citation | Futamura 1971/1983; Aho, Sethi, and Ullman 1986. |
| Status | OPEN |

### BD-openmc-026  Surface crossing uses one generic path for boundary conditions and cell relocation

| Field | Value |
|-------|-------|
| File | `src/particle.cpp` |
| Lines | 549-629 |
| Hot-path % (profile-measured) | `OPEN:` surface-crossing geometry path; pending CE geometry perf. |
| Category | 5 — Control flow |
| Current pattern | `Particle::cross_surface` checks verbosity, DAGMC mode, boundary-condition presence, run mode, neighbor-list lookup, exhaustive fallback, and tangent retry in a single generic routine. |
| Why slow | Most production crossings have fixed run-mode and geometry-backend policies, but the hot path still carries all optional branches. The fallback and retry code also sits adjacent to the common neighbor success path, reducing instruction-cache locality. |
| Proposed fix | Select a crossing policy at initialization for common CSG transport modes (`no DAGMC`, `no boundary condition`, `neighbor-list enabled`) and keep the current routine as the fully general/debug fallback. |
| Expected speedup | 1.02--1.10× on boundary-heavy models if cross-surface branch/control overhead appears in perf; no speedup claim until measured. |
| Validation | Fixed-seed surface-crossing trace comparing old/new `(surface, old cell, new cell, BC action, lost flag)` tuples, including tangent and void-registry tests. |
| Implementation target | `openmc-fork` guarded CSG crossing-policy prototype. |
| Cross-code pattern | Analogous to Geant4 `BD-geant4-042` navigator dispatch and `BD-geant4-110` repeated step-state shuttling. |
| Citation | Futamura 1971/1983; Williams, Waterman, and Patterson 2009. |
| Status | OPEN |

### BD-openmc-027  Lattice crossing falls back to exhaustive cell searches after every tile move

| Field | Value |
|-------|-------|
| File | `src/geometry.cpp` |
| Lines | 301-357 |
| Hot-path % (profile-measured) | `OPEN:` lattice boundary crossing; pending lattice benchmark perf. |
| Category | 2 — Algorithm |
| Current pattern | `cross_lattice` updates lattice indices and local position, then calls `exhaustive_find_cell`; corner cases reset to root coordinates and search again. |
| Why slow | Neighboring lattice tile identity is known from the lattice translation, but the code redoes a general cell search inside the new tile. Repeated pin-cell or assembly crossings pay the same lookup cost at every tile boundary. |
| Proposed fix | Add a lattice adjacency/entry cache keyed by `(lattice id, old index, translation, entering surface)` that maps directly to the new universe and first candidate cells, falling back to exhaustive search only for ambiguous corners. |
| Expected speedup | 1.1--1.6× for lattice-boundary handling in repeated assembly geometries; wall-clock impact depends on lattice crossing frequency. |
| Validation | Compare vanilla and cached crossing traces for rect and hex lattices, including invalid-index leakage and corner-crossing fallbacks; require identical lost-particle behavior and tallies. |
| Implementation target | `openmc-fork` lattice-adjacency cache prototype. |
| Cross-code pattern | OpenMC analogue of Geant4 `BD-geant4-045` voxel-boundary marching and `BD-geant4-046` neighboring-slice safety scans. |
| Citation | Wald, Boulos, and Shirley 2007; Aho, Sethi, and Ullman 1986. |
| Status | OPEN |

### BD-openmc-028  Boundary-distance arbitration recomputes lattice and surface candidates per coordinate level

| Field | Value |
|-------|-------|
| File | `src/geometry.cpp` |
| Lines | 361-452 |
| Hot-path % (profile-measured) | `OPEN:` distance-to-boundary geometry kernel; pending perf. |
| Category | 5 — Control flow |
| Current pattern | `distance_to_boundary` loops over coordinate levels, calls each cell's surface-distance routine, switches on lattice type, applies rotation adjustments, and then resolves surface-vs-lattice coincidence rules. |
| Why slow | Static properties such as lattice type, rotated-coordinate status, and simple-cell surface-sign handling are interpreted on every boundary query. The common one-level/no-lattice case still runs through the same generic loop and comparison logic. |
| Proposed fix | Generate compact per-coordinate-level boundary descriptors with separate fast paths for no-lattice, rect-lattice, and hex-lattice cells; hoist coincidence policy and simple-cell sign handling into descriptor fields. |
| Expected speedup | 1.05--1.25× for `distance_to_boundary`; larger in deeply nested lattice geometries if descriptor dispatch removes branch misses. |
| Validation | Dense randomized ray regression comparing `(distance, surface, lattice_translation, coord_level)` exactly or within existing floating tolerances, followed by fixed-seed transport boundary traces. |
| Implementation target | `openmc-fork` boundary-query descriptor patch; candidate for `libMCAccel/core/geometry`. |
| Cross-code pattern | Mirrors Geant4 `BD-geant4-045` and `BD-geant4-046` repeated navigation-boundary arithmetic. |
| Citation | Futamura 1971/1983; Williams, Waterman, and Patterson 2009. |
| Status | OPEN |

### BD-openmc-029  Event surface crossing checks optional source, window, and tally hooks every crossing

| Field | Value |
|-------|-------|
| File | `src/particle.cpp` |
| Lines | 288-329 |
| Hot-path % (profile-measured) | `OPEN:` event surface-crossing path; pending history/event-mode comparison. |
| Category | 5 — Control flow |
| Current pattern | `Particle::event_cross_surface` saves previous cells, distinguishes lattice and surface crossings, checks surface-source hooks before/after crossing, checks weight-window checkpointing, and checks active surface tallies. |
| Why slow | Surface sources, weight windows, and surface tallies are run-configuration features, yet their guards remain in every crossing even when disabled. Event-mode batches magnify this small branch cost across many particles. |
| Proposed fix | Build a crossing pipeline from static run settings: separate no-hook, tally-only, surface-source, and weight-window variants, with the current fully dynamic routine kept for uncommon mixed configurations. |
| Expected speedup | 1.02--1.08× for event-mode surface crossing if perf shows hook guards in the hot path; zero claim for tally-heavy runs where hooks are intentionally active. |
| Validation | Event trace comparing hook calls, surface-bank contents, weight-window effects, and surface-current scores under every enabled/disabled combination. |
| Implementation target | `openmc-fork` event crossing pipeline specialization. |
| Cross-code pattern | Similar to Geant4 `BD-geant4-041` track hooks and `BD-geant4-109` per-step endpoint copying. |
| Citation | Aho, Sethi, and Ullman 1986; Futamura 1971/1983. |
| Status | OPEN |

### BD-openmc-030  Vacuum boundary handling keeps random-ray and Monte Carlo leakage in one runtime branch

| Field | Value |
|-------|-------|
| File | `src/boundary_condition.cpp` |
| Lines | 18-31 |
| Hot-path % (profile-measured) | `OPEN:` boundary-condition handling under leakage-heavy problems; pending perf. |
| Category | 5 — Control flow |
| Current pattern | `VacuumBC::handle_particle` checks `settings::solver_type` at each vacuum crossing, then either delegates to reflective random-ray behavior plus angular-flux zeroing or kills the Monte Carlo particle. |
| Why slow | Solver type is fixed for a run, but leakage crossings carry both paths. The random-ray branch also reaches into `RandomRay` storage through a cast that ordinary Monte Carlo histories should never see. |
| Proposed fix | Instantiate solver-specific vacuum boundary handlers during surface initialization, or split Monte Carlo and random-ray vacuum BC classes behind the same input syntax. |
| Expected speedup | Small per-crossing control-flow reduction in leakage-heavy fixed-source models; primarily a cleanup that enables stronger inlining of ordinary Monte Carlo leakage. |
| Validation | Compare leakage tally, particle weight/liveness, random-ray angular flux zeroing, and boundary event traces for both solver types. |
| Implementation target | `openmc-fork` boundary-condition class split. |
| Cross-code pattern | Mirrors Geant4 `BD-geant4-033` force-condition branch ladders in per-step process handling. |
| Citation | Futamura 1971/1983; Aho, Sethi, and Ullman 1986. |
| Status | OPEN |

### BD-openmc-031  Reflective boundaries re-run cell search after returning to the previous cell

| Field | Value |
|-------|-------|
| File | `src/particle.cpp` |
| Lines | 657-710 |
| Hot-path % (profile-measured) | `OPEN:` reflective-boundary handling; pending reflective benchmark perf. |
| Category | 2 — Algorithm |
| Current pattern | `cross_reflective_bc` flips the direction and surface, restores the previous root cell, resets to root coordinates, and then calls `neighbor_list_find_cell` to redetermine lower-universe coordinates. |
| Why slow | For simple root-universe reflections the destination cell is already known, but the routine still prepares for lower-universe/lattice ambiguity and may search geometry again. Reflective boxes or repeated boundary bounces pay this cost many times. |
| Proposed fix | Add a guarded simple-reflection fast path when the prior coordinate stack proves no lower-universe ambiguity; otherwise use the current neighbor-list search. Cache reflected lower-coordinate stacks for repeated reflective surfaces. |
| Expected speedup | 1.05--1.30× for reflection-heavy models; negligible when reflective boundaries are rare. |
| Validation | Fixed-seed reflective-boundary traces comparing direction, surface sign, coordinate stack, surface tallies, mesh-surface tallies, and lost-particle diagnostics. |
| Implementation target | `openmc-fork` reflective-boundary fast path. |
| Cross-code pattern | Related to Geant4 `BD-geant4-050` touchable-history access and `BD-geant4-110` repeated track/step state synchronization. |
| Citation | Aho, Sethi, and Ullman 1986; Williams, Waterman, and Patterson 2009. |
| Status | OPEN |

### BD-openmc-032  Rotational periodic boundaries recompute trigonometric rotation per crossing

| Field | Value |
|-------|-------|
| File | `src/boundary_condition.cpp` |
| Lines | 254-290 |
| Hot-path % (profile-measured) | `OPEN:` periodic-boundary handling; pending periodic-geometry benchmark. |
| Category | 4 — Mathematical |
| Current pattern | `RotationalPeriodicBC::handle_particle` determines the struck partner surface, sets the signed target surface, recomputes `std::cos(theta)` and `std::sin(theta)`, rotates position and direction, then applies albedo and transfers the particle. |
| Why slow | The periodic angle is fixed after construction, so sine/cosine and signed surface mappings are invariant. Recomputing transcendental functions per crossing is unnecessary in repeated rotational-periodic geometries. |
| Proposed fix | Precompute forward/backward `(cos, sin, new_surface_sign)` descriptors in the constructor and use a small table indexed by the struck surface. Preserve the current runtime checks as debug assertions. |
| Expected speedup | 1.2--2.0× for the rotational-periodic handler itself; wall-clock impact limited to models with frequent periodic crossings. |
| Validation | Compare old/new periodic crossing traces for forward/backward hits, including albedo, new position/direction, target surface sign, and downstream cell lookup. |
| Implementation target | `openmc-fork` periodic-boundary micro-optimization. |
| Cross-code pattern | Same invariant-hoisting theme as Geant4 `BD-geant4-043` transform reuse and `BD-geant4-045` boundary arithmetic specialization. |
| Citation | Futamura 1971/1983; Williams, Waterman, and Patterson 2009. |
| Status | OPEN |

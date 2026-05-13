# OpenMC bottleneck database — transport-loop hot path

Status: compact-safe worker-4 lane-swap from `codex-tasks/review/worker-1.txt`.
Scope is OpenMC v0.15.3 Monte Carlo transport: source sampling,
geometry/cell search, surface-distance/crossing decisions, and collision
reaction sampling. This shard deliberately continues the existing database at
`BD-openmc-013` and does not repeat `BD-openmc-001`--`012` from
`docs/reports/bottleneck_database_openmc.md`.

## Source provenance and profile basis

- Source tree read from LUNARC: `/projects/hep/fs10/shared/nnbar/billy/openmc`.
- LUNARC source checkout is detached at OpenMC tag `v0.15.3`, commit
  `27e38e894`.
- A read-only local mirror was copied to `/tmp/openmc-v0.15.3` for line-number
  verification only; no OpenMC build, run, or production data mutation occurred.
- SHA-256 parity between the local mirror and LUNARC source was verified for
  `src/simulation.cpp`, `src/source.cpp`, `src/geometry.cpp`,
  `src/universe.cpp`, `src/cell.cpp`, `src/surface.cpp`, `src/particle.cpp`,
  and `src/physics.cpp` before writing these line references.
- Hot-path percentages below are transport-family review estimates pending a
  pinned LUNARC `perf record` on an OpenMC CE pin-cell / assembly benchmark.
  Any implementation must collect per-symbol self percentages before claiming a
  measured speedup.

## References used by entries

- Romano et al. 2015, *OpenMC: A state-of-the-art Monte Carlo code for research
  and development*, Annals of Nuclear Energy 82.
- Khuong and Morin 2015, *Array layouts for comparison-based searching*.
- Vose 1991, *A linear algorithm for generating random numbers with a given
  distribution*.
- Aho, Sethi, and Ullman 1986, *Compilers: Principles, Techniques, and Tools*.
- Futamura 1971/1983, partial evaluation / projection work.
- Herlihy and Shavit 2008, *The Art of Multiprocessor Programming*.
- Stroustrup 2012, *Why you should avoid Linked Lists*.
- Wald, Boulos, and Shirley 2007, *Ray Tracing Deformable Scenes using Dynamic
  Bounding Volume Hierarchies*.
- Williams, Waterman, and Patterson 2009, *Roofline: an insightful visual
  performance model for multicore architectures*.

---

### BD-openmc-013  History transport repeatedly branches through the scalar event pipeline

| Field | Value |
|-------|-------|
| File | `src/simulation.cpp` |
| Lines | 804-820 |
| Hot-path % (profile-measured) | `OPEN:` transport driver family; per-line self% pending LUNARC `perf`. |
| Category | 5 — Control flow |
| Current code snippet | `while (p.alive()) { p.event_calculate_xs(); ... p.event_advance(); ... p.event_cross_surface(); ... p.event_collide(); }` |
| Current pattern | Every history executes the same scalar method chain and tests `p.alive()` between stages before reviving secondaries. |
| Why slow | The common neutron-in-material path pays repeated unpredictable alive/event branches and cannot specialize away inactive features such as surface source, collision track, time cutoffs, or optional tallies. |
| Proposed fix | Add a setup-selected transport-step functor for common policy combinations (`CE neutron`, `no timed tallies`, `no collision track`, etc.) while keeping the existing function as the fully general fallback. Generate the functor from static run settings and call it from the OpenMP loop. |
| Expected speedup | 1.02--1.08× wall-clock on ordinary CE history-based transport if branch misses dominate the driver overhead; zero claim until perf confirms driver self%. |
| Validation | Record a vanilla per-history event trace `(event type, material, cell, surface, sampled nuclide/MT, RNG counter)` and require bit-identical traces under fixed seeds for every specialized policy combination; run keff/reaction-rate regressions afterward. |
| Implementation target | `openmc-fork` guarded transport-policy prototype; optional shared policy-specialization utility in `libMCAccel/adapters/openmc`. |
| Citation | Futamura 1971/1983; Aho, Sethi, and Ullman 1986. |
| Status | OPEN |

### BD-openmc-014  Event-based scheduler rescans all event queues every dispatch

| Field | Value |
|-------|-------|
| File | `src/simulation.cpp` |
| Lines | 851-873 |
| Hot-path % (profile-measured) | `OPEN:` event-based transport scheduler; pending event-mode benchmark. |
| Category | 5 — Control flow |
| Current code snippet | `int64_t max = std::max({calculate_fuel_xs_queue.size(), ..., collision_queue.size()}); if (max == queue.size()) process_*();` |
| Current pattern | Each event-kernel dispatch rebuilds a five-way maximum from queue sizes and then repeats equality checks to select the matching kernel. |
| Why slow | Queue sizes change only for queues touched by the last kernel, but the scheduler reloads every size and executes a priority if/else chain on every dispatch. Large event-based batches amplify this small control overhead. |
| Proposed fix | Maintain a tiny dirty priority structure or bitmask-indexed max queue whose entries are updated by event kernels when they push/pop work. Dispatch directly to the current queue id. |
| Expected speedup | 1.02--1.05× in event-based mode when scheduler churn appears in perf; negligible in history-based mode. |
| Validation | Fixed-seed event-mode replay comparing event-queue population after every kernel, final particle banks, tallies, and RNG streams. Include tie-order tests to preserve current deterministic queue ordering. |
| Implementation target | `openmc-fork` event-queue scheduler patch. |
| Citation | Aho, Sethi, and Ullman 1986; Williams, Waterman, and Patterson 2009. |
| Status | OPEN |

### BD-openmc-015  Constrained source sampling performs full geometry search per rejected site

| Field | Value |
|-------|-------|
| File | `src/source.cpp` |
| Lines | 177-213 and 226-270 |
| Hot-path % (profile-measured) | `OPEN:` source initialization in rejection-heavy fixed-source runs; pending source benchmark. |
| Category | 2 — Algorithm |
| Current code snippet | `site = this->sample(seed); ... accepted = satisfies_spatial_constraints(site.r) ...`; `satisfies_spatial_constraints` calls `exhaustive_find_cell(geom_state)`. |
| Current pattern | A rejected source site pays an exhaustive cell search and domain check before another random site is drawn. Rejection counters are function-static. |
| Why slow | Domain-constrained sources can reject many points, multiplying the cost of geometry search before transport even begins; shared static counters also create a mutable hot variable in parallel initialization. |
| Proposed fix | Compile constrained sources into domain-aware samplers where possible: sample directly from mesh/cell/material bounding volumes, prefilter with cheap bounding boxes, and keep per-thread rejection counters reduced at the end. Fall back to current exhaustive checks for arbitrary user distributions. |
| Expected speedup | 1.2--5× for highly constrained sources with large rejection fractions; neutral for unconstrained sources. |
| Validation | For direct-domain samplers, compare spatial distributions with KS/chi-square tests against the current rejection sampler; for fallback, require bit-identical accepted/rejected decisions and thread-safe counter totals under OpenMP. |
| Implementation target | `openmc-fork` source-sampler preprocessing plus `libMCAccel/core/sampling` helpers. |
| Citation | Vose 1991; Herlihy and Shavit 2008. |
| Status | OPEN |

### BD-openmc-016  IndependentSource duplicates rejection loops and per-sample policy checks

| Field | Value |
|-------|-------|
| File | `src/source.cpp` |
| Lines | 355-417 |
| Hot-path % (profile-measured) | `OPEN:` independent-source sampling; pending fixed-source source-profile run. |
| Category | 5 — Control flow |
| Current code snippet | `while (!accepted) { site.r = space_->sample(seed); accepted = satisfies_spatial_constraints(site.r); } ... dynamic_cast<Discrete*>(energy_.get()) ... while (true) { site.E = energy_->sample(seed); ... }` |
| Current pattern | Spatial and energy rejection are separate loops, and the monoenergetic energy-range check plus dynamic cast are performed for each sampled site. |
| Why slow | The source configuration is static, but the hot sampler repeats policy tests and cannot fuse spatial/energy/time acceptance into a single compiled predicate. |
| Proposed fix | Build a `SourceSamplingPlan` during input initialization: prevalidate monoenergetic bounds, prebind spatial/energy/time predicates, and expose a direct fast path for unconstrained or already-domain-aware sources. |
| Expected speedup | 1.05--1.3× for ordinary independent-source initialization; larger if constraints currently reject often. |
| Validation | Unit tests comparing accepted source-site distributions and RNG-consumption behavior for unconstrained, spatially constrained, energy-bounded, and kill-strategy sources. |
| Implementation target | `openmc-fork` source initialization refactor. |
| Citation | Futamura 1971/1983; Aho, Sethi, and Ullman 1986. |
| Status | OPEN |

### BD-openmc-017  Cell lookup walks neighbor/universe cell vectors with repeated region tests

| Field | Value |
|-------|-------|
| File | `src/geometry.cpp`; `src/universe.cpp` |
| Lines | `src/geometry.cpp:102-152`; `src/universe.cpp:40-59` |
| Hot-path % (profile-measured) | `OPEN:` geometry tracking / cell search; pending transport perf. |
| Category | 3 — Data structure |
| Current code snippet | `for (auto it = neighbor_list->cbegin(); ... ) { ... model::cells[i_cell]->contains(r, u, surf) }`; `for (auto i_cell : cells) { ... contains(r, u, surf) }` |
| Current pattern | Neighbor-list and fallback universe searches linearly test candidate cells and call `contains` until one matches. |
| Why slow | The candidates are stored as generic vectors of cell indices, so common surface-to-neighbor transitions still pay multiple pointer indirections and region-expression evaluations. Cell locality from the previous `(cell, surface)` crossing is not represented as a direct transition. |
| Proposed fix | Add a read-mostly transition cache keyed by `(previous cell, signed surface, coordinate level, lattice tile)` that maps directly to the next cell when unambiguous; fall back to the existing neighbor/universe search for ambiguous surfaces. |
| Expected speedup | 1.1--1.6× for cell finding in repeated lattice/CSG crossings; wall-clock impact depends on geometry-search self%. |
| Validation | Trace every surface crossing in a geometry regression suite and require identical next-cell/material/lattice state. Include ambiguous surfaces, nested universes, and DAGMC fallback cases. |
| Implementation target | `openmc-fork` geometry transition-cache prototype. |
| Citation | Stroustrup 2012; Wald, Boulos, and Shirley 2007. |
| Status | OPEN |

### BD-openmc-018  Neighbor-list misses mutate shared geometry during transport

| Field | Value |
|-------|-------|
| File | `src/geometry.cpp` |
| Lines | 256-281 |
| Hot-path % (profile-measured) | `OPEN:` neighbor-list cell search; pending threaded geometry benchmark. |
| Category | 7 — Concurrency |
| Current code snippet | `found = find_cell_inner(p, nullptr, verbose); if (found) c.neighbors_.push_back(p.coord(coord_lvl).cell());` |
| Current pattern | A miss in the cell neighbor list triggers exhaustive search, then appends the discovered neighbor to `c.neighbors_` during particle transport. |
| Why slow | Mutable neighbor growth in a threaded transport loop risks cache-line contention and forces conservative synchronization if made safe; even without contention, vector growth is a cold allocation path on a geometry hot miss. |
| Proposed fix | Freeze neighbor lists before transport using an offline surface-adjacency pass, or accumulate per-thread miss discoveries in fixed-capacity buffers and merge after a batch. The hot loop should read an immutable neighbor view. |
| Expected speedup | 1.05--1.3× in geometries with many first-time neighbor misses; also reduces thread-safety risk. |
| Validation | Run OpenMP transport with ThreadSanitizer on a geometry that forces neighbor misses; require no data races. Compare final neighbor graph, particle cell histories, and tallies against vanilla. |
| Implementation target | `openmc-fork` immutable-neighbor preprocessing patch. |
| Citation | Herlihy and Shavit 2008; Stroustrup 2012. |
| Status | OPEN |

### BD-openmc-019  Region distance reevaluates every surface token for each boundary query

| Field | Value |
|-------|-------|
| File | `src/cell.cpp` |
| Lines | 910-935 |
| Hot-path % (profile-measured) | `OPEN:` distance-to-boundary geometry kernel; pending perf. |
| Category | 3 — Data structure |
| Current code snippet | `for (int32_t token : expression_) { if (token >= OP_UNION) continue; ... model::surfaces[abs(token) - 1]->distance(r, u, coincident); }` |
| Current pattern | Boundary distance scans the full region-expression token vector, skips operator tokens, converts token signs, and calls each surface distance dynamically. |
| Why slow | Region topology is static after input parsing. Repeatedly walking operator tokens and recomputing `abs(token)-1` wastes instruction bandwidth and pointer-chases every candidate surface. |
| Proposed fix | Store a compact `distance_surfaces_` array per region with signed surface index, coincident-mask metadata, and prebound surface-type dispatch. Simple regions can use a straight contiguous loop; complex regions keep the old expression for containment semantics. |
| Expected speedup | 1.1--1.4× inside `Region::distance` for cells with many boolean tokens or repeated surfaces. |
| Validation | Exhaustive surface-distance unit tests over planes/cylinders/spheres/quadrics and randomized rays; require identical `(min_dist, signed_surface)` including coincident and tie cases. |
| Implementation target | `openmc-fork` CSG region precompute patch. |
| Citation | Aho, Sethi, and Ullman 1986; Stroustrup 2012. |
| Status | OPEN |

### BD-openmc-020  Complex region containment interprets boolean tokens at every cell test

| Field | Value |
|-------|-------|
| File | `src/cell.cpp` |
| Lines | 974-1028 |
| Hot-path % (profile-measured) | `OPEN:` cell containment during geometry search; pending perf. |
| Category | 5 — Control flow |
| Current code snippet | `for (auto it = expression_.begin(); it != expression_.end(); it++) { ... if (token < OP_UNION) ... else if (...) { do { it++; ... } while (depth > 0); } }` |
| Current pattern | Each complex containment test interprets the region-expression token stream and performs dynamic skip logic for short-circuiting. |
| Why slow | The boolean expression is static, but the hot path reinterprets it for every candidate cell and branch-predicts through user-dependent token structure. |
| Proposed fix | Compile complex regions at load time into a small bytecode or decision DAG with precomputed jump targets and surface indices; keep the token interpreter as debug/fallback. |
| Expected speedup | 1.1--1.5× for complex-cell containment; negligible for simple cells handled by `contains_simple`. |
| Validation | Property-test compiled and interpreted containment over randomized points/directions/on-surface signs for every region expression in benchmark models; assert identical truth values. |
| Implementation target | `openmc-fork` region-bytecode prototype. |
| Citation | Aho, Sethi, and Ullman 1986; Futamura 1971/1983. |
| Status | OPEN |

### BD-openmc-021  Surface distance kernels recompute common ray-shape algebra branch-by-branch

| Field | Value |
|-------|-------|
| File | `src/surface.cpp` |
| Lines | 208-217 and 400-442 |
| Hot-path % (profile-measured) | `OPEN:` surface-distance calls under `distance_to_boundary`; pending perf. |
| Category | 4 — Mathematical |
| Current code snippet | Plane: `const double d = f / u[i]`; cylinder: `const double quad = k * k - a * c; ... return (-k + sqrt(quad)) / a;` |
| Current pattern | Each surface type recomputes reciprocal/division and quadratic-root algebra with branch-heavy coincident/inside/outside cases. |
| Why slow | Axis-aligned planes and cylinders dominate many reactor geometries. Their ray coefficients can reuse per-particle reciprocal direction components and type-specialized coefficient packs rather than repeating generic scalar arithmetic. |
| Proposed fix | Precompute per-particle reciprocal direction components for plane distances, use a numerically stable prebound quadratic helper for cylinders/quadrics, and group surfaces by type in the region distance loop so common kernels can inline. |
| Expected speedup | 1.05--1.25× inside surface-distance evaluation for plane/cylinder-heavy geometries. |
| Validation | Dense randomized ray/surface regression comparing distances bit-for-bit where operation order is preserved; otherwise require sub-ulp/tolerance envelopes plus identical selected boundary in full transport. |
| Implementation target | `openmc-fork` surface-distance microkernel patch. |
| Citation | Aho, Sethi, and Ullman 1986; Williams, Waterman, and Patterson 2009. |
| Status | OPEN |

### BD-openmc-022  Collision reaction sampling linearly scans material and nuclide reaction lists

| Field | Value |
|-------|-------|
| File | `src/physics.cpp` |
| Lines | 494-518, 552-585, and 674-736 |
| Hot-path % (profile-measured) | `OPEN:` collision sampling / reaction selection; pending CE transport perf. |
| Category | 2 — Algorithm |
| Current code snippet | `for (int i = 0; i < n; ++i) { prob += atom_density * p.neutron_xs(i_nuclide).total; if (prob >= cutoff) return i_nuclide; }`; `for (auto& rx : nuc->fission_rx_) { prob += rx->xs(micro); ... }` |
| Current pattern | Collision sampling uses cumulative linear scans over material nuclides, partial fission reactions, and inelastic scattering reaction lists. |
| Why slow | The candidate lists are static for a material/nuclide, while per-collision probabilities change with cross section. Linear scans are cheap for small lists but become a repeated O(n) branchy sampler for isotope-rich materials and nuclides with many channels. |
| Proposed fix | Add adaptive samplers: keep linear scan for small lists; for large isotope/reaction lists, build per-material compact CDF work buffers with Eytzinger search or alias-table variants when probabilities are stable over many collisions in the same energy bin. |
| Expected speedup | 1.1--1.6× in material/nuclide reaction selection for isotope-rich CE problems; wall-clock impact depends on collision-sampling self%. |
| Validation | Fixed-RNG trace comparing sampled nuclide/reaction MT for the exact-CDF path; for alias variants that alter RNG consumption, require distribution-level chi-square/KS tests plus reaction-rate/keff agreement within stochastic uncertainty. |
| Implementation target | `openmc-fork` adaptive collision-sampler prototype; reusable `libMCAccel/core/sampling` primitive. |
| Citation | Vose 1991; Khuong and Morin 2015. |
| Status | OPEN |

## Concrete next-step proposal

Queue worker-3/OpenMC-adapter follow-up `openmc-geometry-transition-cache-prototype`
for BD-openmc-017 and BD-openmc-018 after a perf run confirms geometry-search
self time. It is deterministic, preserves current geometry semantics through a
fallback, and can be validated with exact cell/surface transition traces before
any stochastic tally comparison is needed.

# OpenMC bottleneck database — tally scoring hot path

Status: compact-safe worker-4 lane-swap from the review source-review queue.
Scope is OpenMC v0.15.3 tally scoring: filter-bin matching, event/score
loops, nuclide/reaction loops, atomics, and batch accumulation. This shard
continues at `BD-openmc-033` and deliberately does not repeat
`BD-openmc-001`--`032` from the cross-section, transport, and geometry shards.

## Source provenance and profile basis

- The local read-only mirror `/tmp/openmc-v0.15.3` was used for line-number
  inspection only. It byte-matches a fresh official OpenMC `v0.15.3` tag clone
  at commit `27e38e894` for every source file cited below.
- Prior shards verified `/tmp/openmc-v0.15.3` against the LUNARC OpenMC
  `v0.15.3` checkout. A fresh LUNARC socket guard was attempted in this
  iteration but did not complete before local fallback, so this report makes no
  new LUNARC-source freshness claim.
- The queue prompt named `Tally::score_events()`, but OpenMC v0.15.3 has no
  such function symbol. Event-count scoring is implemented by `SCORE_EVENTS`
  cases in `src/tallies/tally_scoring.cpp`.
- Hot-path percentages below are review estimates pending a pinned tally-heavy
  OpenMC `perf record` run that maps samples to the exact cited ranges.

## References used by entries

- Romano et al. 2015, *OpenMC: A state-of-the-art Monte Carlo code for research
  and development*, Annals of Nuclear Energy 82.
- Khuong and Morin 2015, *Array layouts for comparison-based searching*.
- Fredman, Komlos, and Szemeredi 1984, *Storing a sparse table with O(1)
  worst case access time*.
- Aho, Sethi, and Ullman 1986, *Compilers: Principles, Techniques, and Tools*.
- Futamura 1971/1983, partial evaluation / projection work.
- Herlihy and Shavit 2008, *The Art of Multiprocessor Programming*.
- Williams, Waterman, and Patterson 2009, *Roofline: an insightful visual
  performance model for multicore architectures*.
- Wald, Boulos, and Shirley 2007, *Ray Tracing Deformable Scenes using Dynamic
  Bounding Volume Hierarchies*.
- Stroustrup 2012, *Why you should avoid Linked Lists*.

---

### BD-openmc-033  Filter-bin discovery uses virtual per-filter calls on every scoring event

| Field | Value |
|-------|-------|
| File | `src/tallies/tally_scoring.cpp` |
| Lines | 31-57 |
| Hot-path % (profile-measured) | `OPEN:` tally filter matching; pending tally-heavy CE benchmark perf. |
| Category | 5 — Control flow |
| Current code snippet | `model::tally_filters[i_filt]->get_all_bins(p, tally_.estimator_, match);` |
| Current pattern | `FilterBinIter` loops over each filter in a tally and dispatches a virtual `get_all_bins` call whenever the particle-local match cache is not already populated. |
| Why slow | Tally-heavy models execute many short virtual calls from the inner scoring path; the call target, filter metadata, and particle state are scattered across memory and defeat inlining of common cases. |
| Proposed fix | Build setup-time filter-evaluator descriptors for common filter combinations and dispatch through compact function-pointer or policy-specialized evaluators, with the virtual path retained for rare/custom filters. |
| Expected speedup | 1.05--1.20x inside filter matching when many simple tallies are active; wall-clock impact depends on tally self time. |
| Validation | Replay fixed particle scoring events and require identical `FilterMatch` bins/weights for every tally/filter combination before comparing statepoint tallies bitwise or within current reduction order tolerance. |
| Implementation target | `openmc-fork` tally filter policy prototype; optional `libMCAccel/adapters/openmc` filter descriptor. |
| Cross-code pattern | Same policy-specialization opportunity as Geant4 process dispatch table work in `g4gpu-phase5d-jit-poststep-gpil`. |
| Citation | Futamura 1971/1983; Aho, Sethi, and Ullman 1986. |
| Status | OPEN |

### BD-openmc-034  Filter-combination iteration recomputes mixed-radix index/weight serially

| Field | Value |
|-------|-------|
| File | `src/tallies/tally_scoring.cpp` |
| Lines | 94-139 |
| Hot-path % (profile-measured) | `OPEN:` multi-filter tally scoring; pending filter-combination counter instrumentation. |
| Category | 2 — Algorithm |
| Current code snippet | `for (int i = tally_.filters().size() - 1; i >= 0; --i) { ... }`; `index_ += match.bins_[i_bin] * tally_.strides(i);` |
| Current pattern | Each next filter combination scans filters backward, mutates per-filter bin indices, and recomputes the flat tally index and product weight from all filters. |
| Why slow | Cartesian-product tallies repeatedly touch the same filter metadata and multiply/index state for every combination, even when only the last filter bin changes. |
| Proposed fix | Add an incremental mixed-radix iterator that updates `index_` and `weight_` by delta for the advanced filter, or pre-expand small static filter products into contiguous `(index, weight)` pairs. |
| Expected speedup | 1.05--1.3x for tallies with multiple filters and many bins; neutral for single-filter tallies. |
| Validation | Exhaustively compare generated `(filter_index, filter_weight)` sequences for synthetic filters and replay representative CE scoring events to require identical bin visits and accumulated results. |
| Implementation target | `openmc-fork` `FilterBinIter` fast iterator. |
| Cross-code pattern | Mirrors branchless/indexed traversal opportunities in geometry partition and process-vector reviews. |
| Citation | Aho, Sethi, and Ullman 1986; Williams, Waterman, and Patterson 2009. |
| Status | OPEN |

### BD-openmc-035  Energy filters use branchy binary search for every matching event

| Field | Value |
|-------|-------|
| File | `src/tallies/filter_energy.cpp` |
| Lines | 59-109 |
| Hot-path % (profile-measured) | `OPEN:` energy-filter matching; pending per-filter hit counters. |
| Category | 2 — Algorithm |
| Current code snippet | `auto bin = lower_bound_index(bins_.begin(), bins_.end(), E);`; `auto bin = lower_bound_index(bins_.begin(), bins_.end(), p.E());` |
| Current pattern | Continuous-energy incoming/outgoing energy filters check bounds and perform comparison-based lower-bound search for each scoring event. |
| Why slow | Energy bins are immutable after initialization, but the hot path repeats a branchy search through the same vectors. Histories often score nearby energies, so locality is not exploited. |
| Proposed fix | Store an Eytzinger-layout copy or cached last-bin/neighbor fast path for monotone or slowly varying scoring streams; fall back to current `lower_bound_index` for cold jumps. |
| Expected speedup | 1.1--1.6x for energy-filter binning in tally-heavy models; smaller wall-clock impact unless energy filters dominate. |
| Validation | Compare bin IDs for sampled energies at every bin boundary, underflow/overflow point, and replayed particle scoring trace before tally regression. |
| Implementation target | `openmc-fork` energy-filter binning helper shared by incoming/outgoing filters. |
| Cross-code pattern | Same search primitive as OpenMC `BD-openmc-001` and Geant4 physics-vector binary-search findings. |
| Citation | Khuong and Morin 2015; Aho, Sethi, and Ullman 1986. |
| Status | OPEN |

### BD-openmc-036  Mesh tracklength filters call geometry-style crossed-bin enumeration inside scoring

| Field | Value |
|-------|-------|
| File | `src/tallies/filter_mesh.cpp` |
| Lines | 35-59 |
| Hot-path % (profile-measured) | `OPEN:` mesh-filter tallies; pending mesh-tally benchmark. |
| Category | 4 — Geometry/data structure |
| Current code snippet | `model::meshes[mesh_]->bins_crossed(last_r, r, u, match.bins_, match.weights_);` |
| Current pattern | Non-tracklength mesh scoring performs one `get_bin`, while tracklength scoring asks the mesh to enumerate every crossed bin and weight during tally scoring. |
| Why slow | Fine mesh tallies turn a single transport step into a secondary geometry walk plus vector appends in the scoring path, amplifying memory traffic and branch divergence. |
| Proposed fix | Cache per-step mesh traversal fragments when the transport geometry step is already known, or add a specialized regular-mesh DDA accumulator that writes compact `(bin, weight)` pairs without generic vector growth. |
| Expected speedup | 1.1--1.5x for fine regular mesh tracklength tallies; no benefit for sparse non-mesh tallies. |
| Validation | Compare crossed-bin IDs and path-length weights for randomized rays through regular and unstructured meshes, then require identical mesh tally statepoint values for fixed seeds. |
| Implementation target | `openmc-fork` mesh tally traversal cache; possible `libMCAccel` regular-mesh accumulator. |
| Cross-code pattern | Related to Geant4 voxel/geometry traversal acceleration and OpenMC geometry partition findings. |
| Citation | Williams, Waterman, and Patterson 2009; Wald, Boulos, and Shirley 2007. |
| Status | OPEN |

### BD-openmc-037  CE nonanalog scoring is a large per-score switch with embedded nuclide loops

| Field | Value |
|-------|-------|
| File | `src/tallies/tally_scoring.cpp` |
| Lines | 578-615 and 676-760 |
| Hot-path % (profile-measured) | `OPEN:` CE tracklength/collision score loop; pending per-score perf counters. |
| Category | 5 — Control flow |
| Current code snippet | `for (auto i = 0; i < tally.scores_.size(); ++i) { ... switch (score_bin) { ... }`; `for (auto i = 0; i < material.nuclide_.size(); ++i) { ... }` |
| Current pattern | `score_general_ce_nonanalog` iterates each score, switches on score type, and for material-total fission-family scores loops over material nuclides inside selected switch arms. |
| Why slow | The hot scoring loop interleaves score dispatch, particle-type checks, material traversal, delayed-group branches, and atom-density loads; this blocks vectorization and repeats material metadata reads for related scores. |
| Proposed fix | Compile per-tally score plans at setup time: group simple macro scores, nuclide-reduction scores, and delayed-group expansion into small straight-line kernels that share material traversal and particle-type guards. |
| Expected speedup | 1.05--1.25x for CE nonanalog scoring with many score bins; higher for fission-family score sets in isotope-rich materials. |
| Validation | For each supported score plan, compare per-score contributions against the generic switch for replayed events, including delayed-group filters, void material, photons, and `multiply_density` cases. |
| Implementation target | `openmc-fork` tally score-plan prototype. |
| Cross-code pattern | Same setup-time specialization pattern as Geant4 GPIL/process-vector dispatch. |
| Citation | Futamura 1971/1983; Williams, Waterman, and Patterson 2009. |
| Status | OPEN |

### BD-openmc-038  SCORE_EVENTS increments a shared result bin with an atomic per event

| Field | Value |
|-------|-------|
| File | `src/tallies/tally_scoring.cpp` |
| Lines | 907-910 and 2297-2300 |
| Hot-path % (profile-measured) | `OPEN:` event-count score; pending `SCORE_EVENTS` contention benchmark. |
| Category | 6 — Parallel synchronization |
| Current code snippet | `#pragma omp atomic`; `tally.results_(filter_index, score_index, TallyResult::VALUE) += 1.0;` |
| Current pattern | Both CE and MG `SCORE_EVENTS` paths atomically increment the shared tally result for every matching scoring event. |
| Why slow | Popular event-count tallies create cache-line contention across OpenMP threads; the value is additive and does not require immediate global visibility. |
| Proposed fix | Accumulate event counts in thread-local or per-work-chunk scratch buffers and reduce into `results_` at batch boundaries, preserving existing atomic fallback for small tallies. |
| Expected speedup | 1.1--2.0x for `SCORE_EVENTS`-heavy tallies under high thread counts; negligible when atomics are sparse. |
| Validation | Run fixed-seed multi-thread tally tests across thread counts and require identical total counts plus unchanged non-event scores; add stress tests for repeated same-bin collisions. |
| Implementation target | `openmc-fork` tally thread-local accumulation buffer. |
| Cross-code pattern | Same reduction-vs-atomic tradeoff as Geant4 hit/tally collection synchronization reviews. |
| Citation | Herlihy and Shavit 2008; Williams, Waterman, and Patterson 2009. |
| Status | OPEN |

### BD-openmc-039  Analog CE tallies nest active-tally, filter, and nuclide loops per collision event

| Field | Value |
|-------|-------|
| File | `src/tallies/tally_scoring.cpp` |
| Lines | 2314-2363 |
| Hot-path % (profile-measured) | `OPEN:` analog CE tally scoring; pending tally mix benchmark. |
| Category | 3 — Data structure |
| Current code snippet | `for (auto i_tally : model::active_analog_tallies) { ... for (; filter_iter != end; ++filter_iter) { ... for (auto i = 0; i < tally.nuclides_.size(); ++i) { ... } } }` |
| Current pattern | Every analog event iterates active tallies, constructs filter iterators, loops filter combinations, then scans nuclide bins for event-nuclide or total-material matches. |
| Why slow | The loop layout is tally-major instead of event-match-major; it repeatedly touches tally metadata and branches over nuclide bins even when only one event nuclide can contribute. |
| Proposed fix | Build an event-nuclide-to-tally-bin index for analog CE tallies so common `(event_nuclide, total)` contributions jump directly to candidate bins after filters match. |
| Expected speedup | 1.05--1.25x for many analog tallies/nuclide bins; neutral for very small tally sets. |
| Validation | Compare scored bin sets for every event nuclide and total-material bin against the generic loop, then run analog tally statepoint regressions. |
| Implementation target | `openmc-fork` analog tally bin index. |
| Cross-code pattern | Mirrors sparse-table lookup opportunities in cross-section and process-manager reviews. |
| Citation | Fredman, Komlos, and Szemeredi 1984; Stroustrup 2012. |
| Status | OPEN |

### BD-openmc-040  Tracklength and collision estimators duplicate nuclide-density lookup and CE/MG dispatch

| Field | Value |
|-------|-------|
| File | `src/tallies/tally_scoring.cpp` |
| Lines | 2416-2475 and 2543-2605 |
| Hot-path % (profile-measured) | `OPEN:` tracklength/collision tally drivers; pending estimator-separated perf. |
| Category | 5 — Control flow |
| Current code snippet | `auto j = mat->mat_nuclide_index_[i_nuclide];`; `if (settings::run_CE) { score_general_ce_nonanalog(...); } else { score_general_mg(...); }` |
| Current pattern | Tracklength and collision drivers both perform material nuclide lookup, optional log-union update, density handling, then branch on CE/MG mode before entering the general score loop. |
| Why slow | Nearly identical estimator code is duplicated and keeps a runtime CE/MG branch in the inner tally path even though the run mode is fixed for the calculation. |
| Proposed fix | Factor a setup-selected estimator kernel for CE vs MG and shared nuclide-density descriptor lookup; keep the existing generic branch only for unusual runtime-switch contexts. |
| Expected speedup | 1.03--1.12x for tracklength/collision scoring with many active tallies; larger if descriptor lookup improves cache locality. |
| Validation | Compare per-event calls and resulting tally values for CE and MG test problems, including missing nuclide bins and `multiply_density=false`. |
| Implementation target | `openmc-fork` estimator-driver specialization. |
| Cross-code pattern | Same fixed-run-mode specialization used in Geant4 physics-list/process-manager acceleration candidates. |
| Citation | Futamura 1971/1983; Aho, Sethi, and Ullman 1986. |
| Status | OPEN |

### BD-openmc-041  Surface-current tally atomically updates every score bin in the inner loop

| Field | Value |
|-------|-------|
| File | `src/tallies/tally_scoring.cpp` |
| Lines | 2622-2662 |
| Hot-path % (profile-measured) | `OPEN:` surface-current tally scoring; pending boundary-heavy benchmark. |
| Category | 6 — Parallel synchronization |
| Current code snippet | `for (auto score_index = 0; score_index < tally.scores_.size(); ++score_index) { #pragma omp atomic ... }` |
| Current pattern | For each surface tally and filter combination, the code multiplies current by filter weight and atomically adds the same score to every score bin. |
| Why slow | Surface-heavy models can concentrate many threads on a small set of boundary bins; repeating atomics per score bin serializes on cache lines and prevents chunk-level coalescing. |
| Proposed fix | Use per-thread surface tally buffers keyed by `(filter_index, score_index)` and reduce at synchronization points; specialize single-score current tallies to one buffered increment. |
| Expected speedup | 1.1--1.8x for boundary/surface-source benchmarks with high thread count and few surface bins. |
| Validation | Fixed-seed surface-current tests across thread counts must match current statepoint sums; include reflective/periodic boundary cases from the geometry shard. |
| Implementation target | `openmc-fork` buffered surface tally accumulation. |
| Cross-code pattern | Same batched hit/reduction strategy as Geant4 sensitive-detector and OpenMC transport atomic opportunities. |
| Citation | Herlihy and Shavit 2008; Williams, Waterman, and Patterson 2009. |
| Status | OPEN |

### BD-openmc-042  Batch accumulation streams dense result arrays and zeros VALUE each batch

| Field | Value |
|-------|-------|
| File | `src/tallies/tally.cpp` |
| Lines | 821-874 |
| Hot-path % (profile-measured) | `OPEN:` batch-end tally reduction; pending large-tally statepoint benchmark. |
| Category | 1 — Microarchitecture |
| Current code snippet | `for (int i = 0; i < results_.shape()[0]; ++i) { for (int j = 0; j < results_.shape()[1]; ++j) { ... results_(i, j, TallyResult::VALUE) = 0.0; ... } }` |
| Current pattern | `Tally::accumulate` normalizes every filter/score bin, zeros the `VALUE` slot, and updates moment slots with an OpenMP parallel loop over dense `results_`. |
| Why slow | Large sparse tallies still stream every dense bin at batch end, including bins that received no contribution; moment slots interleave VALUE/SUM/SUM_SQ updates in one layout. |
| Proposed fix | Track a sparse dirty-bin list for tallies with low occupancy and use dense streaming only after occupancy crosses a threshold; optionally split hot `VALUE` scratch from long-lived moments. |
| Expected speedup | 1.2--3.0x for very sparse large filter/score spaces; small overhead for dense tallies if the threshold is conservative. |
| Validation | Compare accumulation moments for dense and sparse synthetic tallies, including higher moments, MPI reduction modes, fixed-source normalization, and random-ray solver normalization. |
| Implementation target | `openmc-fork` dirty-bin tally accumulation prototype. |
| Cross-code pattern | Same sparse-active-bin approach as hit collection and geometry candidate-list optimization. |
| Citation | Williams, Waterman, and Patterson 2009; Stroustrup 2012. |
| Status | OPEN |

## Next-step proposal

Queue a worker-3 / OpenMC-adapter implementation task for `BD-openmc-038` and
`BD-openmc-041`: prototype thread-local tally accumulation buffers for
`SCORE_EVENTS` and surface-current tallies, then validate fixed-seed tally
statepoints across OpenMP thread counts before attempting broader score-loop
specialization.

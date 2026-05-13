# OpenMC bottleneck database — tally scoring hot path

Status: compact-safe worker-4 lane-swap from `codex-tasks/review/worker-1.txt`.
Scope is OpenMC v0.15.3 tally scoring: filter matching, score/nuclide/reaction
loops, `SCORE_EVENTS` handling, and tally-bin accumulation. This shard continues
at `BD-openmc-033` and does not repeat `BD-openmc-001`--`032` from the prior
OpenMC bottleneck database shards.

## Source provenance and profile basis

- Source tree read from LUNARC: `/projects/hep/fs10/shared/nnbar/billy/openmc`.
- LUNARC checkout is detached at OpenMC tag `v0.15.3`, commit `27e38e894`.
- A read-only local mirror at `/tmp/openmc-v0.15.3` was used for line-number
  verification only; no OpenMC build, run, fork patch, NNBAR code, or production
  data was modified.
- SHA-256 parity between local and LUNARC source was verified for
  `src/tallies/tally.cpp`, `src/tallies/tally_scoring.cpp`,
  `include/openmc/tallies/tally.h`, and
  `include/openmc/tallies/tally_scoring.h` before these line references were
  written.
- The queue phrase `Tally::score_events()` was resolved by source grep as the
  `SCORE_EVENTS` switch arms in `src/tallies/tally_scoring.cpp`; OpenMC v0.15.3
  has no `Tally::score_events` function symbol.
- Hot-path percentages below inherit the lane-spec profile basis: OpenMC tallies
  / scoring account for roughly 10--15% of transport CPU in tally-heavy runs.
  Exact per-line self percentages remain `OPEN:` until a pinned LUNARC `perf
  record` run maps samples to these ranges.

## References used by entries

- Romano et al. 2015, *OpenMC: A state-of-the-art Monte Carlo code for research
  and development*, Annals of Nuclear Energy 82.
- Khuong and Morin 2015, *Array layouts for comparison-based searching*.
- Aho, Sethi, and Ullman 1986, *Compilers: Principles, Techniques, and Tools*.
- Futamura 1971/1983, partial evaluation / projection work.
- Williams, Waterman, and Patterson 2009, *Roofline: an insightful visual
  performance model for multicore architectures*.
- Herlihy and Shavit 2008, *The Art of Multiprocessor Programming*.
- Stroustrup 2012, *Why you should avoid Linked Lists*.
- Higham 2002, *Accuracy and Stability of Numerical Algorithms*.

---

### BD-openmc-033  Filter-bin construction repeats virtual filter dispatch for every active tally

| Field | Value |
|-------|-------|
| File | `src/tallies/tally_scoring.cpp`; `include/openmc/tallies/tally_scoring.h` |
| Lines | `src/tallies/tally_scoring.cpp:31-57`; `include/openmc/tallies/tally_scoring.h:21-52` |
| Hot-path % (profile-measured) | `OPEN:` tally/scoring family; expected 10--15% aggregate transport CPU before per-symbol LUNARC perf. |
| Category | 5 — Control flow |
| Current code snippet | `for (auto i_filt : tally_.filters()) { ... model::tally_filters[i_filt]->get_all_bins(p, tally_.estimator_, match); ... }` |
| Current pattern | Each `FilterBinIter` constructor walks the tally filter list, checks cached `bins_present_`, and invokes the filter virtual `get_all_bins` method when a particle/tally event has not already populated that filter. |
| Why slow | Filter policy is static for a tally, but scoring reinterprets the filter vector and pays a virtual call chain per relevant event/tally pair. Many tallies share cell, material, energy, or particle filters, so work can repeat before any score is accumulated. |
| Proposed fix | Build a per-tally `FilterScoringPlan` at tally setup: compact filter ids, prebound filter-kind dispatch, and a small event-local cache keyed by `(filter id, estimator, event generation)`. Keep the existing virtual path for uncommon/custom filters. |
| Expected speedup | 1.05--1.25× inside filter matching for tally-heavy CE fixed-source or depletion problems; wall-clock depends on number of active filters per event. |
| Validation | Record vanilla `(tally id, filter id, bins, weights)` tuples for fixed-seed histories and require identical tuples from the plan path across cell/energy/material/time filters before comparing final tally means and variances. |
| Implementation target | `openmc-fork` tally-filter scoring-plan PR; reusable `libMCAccel/adapters/openmc` filter-dispatch descriptor. |
| Cross-code pattern | Same static-policy hoisting as Geant4 `BD-geant4-033`/`BD-geant4-041` process and hook dispatch. |
| Citation | Futamura 1971/1983; Aho, Sethi, and Ullman 1986. |
| Status | OPEN |

### BD-openmc-034  Filter combination iteration recomputes strides and weights for every product bin

| Field | Value |
|-------|-------|
| File | `src/tallies/tally_scoring.cpp`; `src/tallies/tally.cpp` |
| Lines | `src/tallies/tally_scoring.cpp:94-139`; `src/tallies/tally.cpp:503-515` |
| Hot-path % (profile-measured) | `OPEN:` filter-combination iteration; pending tally-filter perf. |
| Category | 3 — Data structure |
| Current code snippet | `index_ += match.bins_[i_bin] * tally_.strides(i); weight_ *= match.weights_[i_bin];` |
| Current pattern | The iterator searches backward through filters, mutates `i_bin_`, and recomputes flattened index and product weight over all filters for each valid bin combination. |
| Why slow | The stride vector is precomputed, but the valid-bin Cartesian product is generated through mutable per-filter state and an O(n_filters) recomputation. Common single-bin filters still participate in every index/weight pass. |
| Proposed fix | Emit an event-local flat list of `(filter_index, filter_weight)` pairs once per tally event. Collapse one-bin filters into a base offset/weight and iterate only over multi-bin filters; use a contiguous small-vector representation for the resulting combinations. |
| Expected speedup | 1.1--1.4× for filter-index generation in tallies with multiple energy/mesh/time bins; neutral for one-filter tallies. |
| Validation | Exhaustively compare flattened indices and weights for synthetic filter-match products, including empty filters and mixed one-/many-bin filters; then replay fixed histories and compare raw `results_` updates. |
| Implementation target | `openmc-fork` filter-combination flattener. |
| Cross-code pattern | Mirrors Geant4 `BD-geant4-050` touchable/history flattening and `BD-geant4-047` static geometry index precompute. |
| Citation | Stroustrup 2012; Williams, Waterman, and Patterson 2009. |
| Status | OPEN |

### BD-openmc-035  Delayed-group fission scoring mutates filter-match state and recomputes bin products

| Field | Value |
|-------|-------|
| File | `src/tallies/tally_scoring.cpp` |
| Lines | 147-176 and 713-759 |
| Hot-path % (profile-measured) | `OPEN:` delayed-fission tally path; pending delayed-group benchmark. |
| Category | 5 — Control flow |
| Current code snippet | `dg_match.bins_[i_bin] = d_bin; ... for (auto i = 0; i < tally.filters().size(); ++i) { ... } ... dg_match.bins_[i_bin] = original_bin;` |
| Current pattern | `score_fission_delayed_dg` temporarily edits the particle filter-match bin, recomputes the full flattened filter index/weight, atomically updates the result, and restores the original bin for every delayed group contribution. |
| Why slow | Mutating shared event-local filter state around every delayed group creates extra stores, increases aliasing risk, and repeats the same stride/weight product that the surrounding `FilterBinIter` already computed. |
| Proposed fix | Pass a precomputed base filter index/weight plus a delayed-group stride into a pure helper that computes `filter_index = base + d_bin * dg_stride` without modifying `FilterMatch`. |
| Expected speedup | 1.1--1.6× in delayed-neutron tally scoring when delayed-group filters are active; zero effect for tallies without delayed groups. |
| Validation | Unit compare delayed-group filter indices for all delayed-group bins and filter-order permutations; fixed-seed fission histories must produce identical delayed-nu-fission, decay-rate, and IFP beta tallies. |
| Implementation target | `openmc-fork` delayed-group filter-index fast path. |
| Cross-code pattern | Same mutable-state removal theme as Geant4 `BD-geant4-109`/`BD-geant4-110` step-state copy cleanup. |
| Citation | Aho, Sethi, and Ullman 1986; Higham 2002 for preserving accumulation semantics. |
| Status | OPEN |

### BD-openmc-036  Continuous-energy nonanalog scoring carries a large score switch in the inner loop

| Field | Value |
|-------|-------|
| File | `src/tallies/tally_scoring.cpp` |
| Lines | 578-1115 |
| Hot-path % (profile-measured) | `OPEN:` CE nonanalog score/nuclide/reaction loop; pending CE tally perf. |
| Category | 9 — JIT specialization |
| Current code snippet | `for (auto i = 0; i < tally.scores_.size(); ++i) { auto score_bin = tally.scores_[i]; ... switch (score_bin) { ... } }` |
| Current pattern | For every filter/nuclide combination, the CE nonanalog scorer loops over runtime `scores_` and enters a broad switch covering flux, reaction rates, fission moments, heating, events, IFP, and arbitrary MT reactions. |
| Why slow | The score list is static after input parsing, but each scoring event redoes the switch, particle-type guards, material checks, and optional delayed-group logic. This prevents inlining the common score subset used by a given tally. |
| Proposed fix | Compile each tally score list into a vector of score functors or template-specialized kernels selected at setup. Group simple linear XS scores into a fused loop and keep rare scores (IFP, delayed group, heating) in cold helpers. |
| Expected speedup | 1.1--1.5× inside CE nonanalog scoring for tallies with a small fixed score set; wall-clock depends on tally frequency and score count. |
| Validation | For every score type enabled in a regression matrix, compare per-event raw score contributions and final means/variances under fixed seeds; require bit-identical results for algebraically unchanged paths. |
| Implementation target | `openmc-fork` tally-score functor prototype; optional LLVM/Cling specialization later only after deterministic functors pass. |
| Cross-code pattern | Same static score/process list specialization as Geant4 `BD-geant4-061` and `BD-geant4-101`. |
| Citation | Futamura 1971/1983; Aho, Sethi, and Ullman 1986. |
| Status | OPEN |

### BD-openmc-037  SCORE_EVENTS updates pay the full score loop and atomic path

| Field | Value |
|-------|-------|
| File | `src/tallies/tally_scoring.cpp`; `include/openmc/constants.h` |
| Lines | `src/tallies/tally_scoring.cpp:907-911`; `src/tallies/tally_scoring.cpp:1519-1523`; `src/tallies/tally_scoring.cpp:2297-2301`; `include/openmc/constants.h:319-319` |
| Hot-path % (profile-measured) | `OPEN:` events-score arm; pending event-count tally benchmark. |
| Category | 7 — Concurrency |
| Current code snippet | `case SCORE_EVENTS: ... #pragma omp atomic tally.results_(filter_index, score_index, TallyResult::VALUE) += 1.0; continue;` |
| Current pattern | Event-count scores are handled as switch arms inside CE nonanalog, CE analog, and MG general scorers, each performing an OpenMP atomic update to the shared `xtensor` result bin. |
| Why slow | Counting events does not need cross-section data, nuclide loops, or floating score calculation, but it still flows through the generic score dispatcher and contends on the same per-bin atomic path under OpenMP. |
| Proposed fix | Split event-count tallies into a per-thread dense counter buffer keyed by filter bin/score index; reduce into `results_` at batch or tally reduction time. Dispatch to this path before the general score switch when a tally contains only `SCORE_EVENTS` or other pure counts. |
| Expected speedup | 1.2--3× for event-count tally updates under high thread contention; smaller if atomics are uncontended. |
| Validation | Compare per-thread and reduced event counts to vanilla atomics on deterministic synthetic collisions/surface crossings; run ThreadSanitizer on the counter path and compare fixed-seed final tally means. |
| Implementation target | `openmc-fork` per-thread tally accumulator for count-only scores. |
| Cross-code pattern | Mirrors Geant4 `BD-geant4-024`/`BD-geant4-025` sensitive-detector hit accumulation contention. |
| Citation | Herlihy and Shavit 2008; Williams, Waterman, and Patterson 2009. |
| Status | OPEN |

### BD-openmc-038  Continuous-energy analog scoring duplicates fission and event logic with more runtime policy checks

| Field | Value |
|-------|-------|
| File | `src/tallies/tally_scoring.cpp` |
| Lines | 1116-1621 |
| Hot-path % (profile-measured) | `OPEN:` CE analog score loop; pending analog-tally perf. |
| Category | 5 — Control flow |
| Current code snippet | `void score_general_ce_analog(...) { ... for (...) { switch (score_bin) { ... settings::survival_biasing ... tally.energyout_filter_ ... } } }` |
| Current pattern | CE analog scoring implements another large score switch with survival-biasing, outgoing-energy, delayed-group, fission-bank, and event-type guards interleaved in the hot loop. |
| Why slow | Most analog tallies use a fixed estimator/score/filter policy, but the routine rechecks survival biasing, outgoing-energy filter presence, and fission state per score. The CE nonanalog and analog implementations also duplicate branches that could share precompiled score actions. |
| Proposed fix | Build analog-specific score actions at setup: simple event/reaction counters, fission outgoing-energy helpers, delayed-group helpers, and survival-biasing variants. The top-level loop then invokes only actions present in the tally. |
| Expected speedup | 1.05--1.35× in analog-tally scoring; largest for fission tallies with many disabled optional features. |
| Validation | Fixed-seed collision trace comparing each analog score contribution, including survival-biasing on/off, outgoing-energy filters, delayed groups, and event MT filters. |
| Implementation target | `openmc-fork` analog score-action refactor. |
| Cross-code pattern | Same hot/cold path split as Geant4 `BD-geant4-033` force-condition and `BD-geant4-099` decay/stopping optional-path specialization. |
| Citation | Futamura 1971/1983; Aho, Sethi, and Ullman 1986. |
| Status | OPEN |

### BD-openmc-039  Multigroup scoring repeatedly queries XS tables inside a duplicated giant switch

| Field | Value |
|-------|-------|
| File | `src/tallies/tally_scoring.cpp` |
| Lines | 1622-2313 |
| Hot-path % (profile-measured) | `OPEN:` MG tally score loop; pending multigroup benchmark. |
| Category | 3 — Data structure |
| Current code snippet | `const auto& macro_xs = data::mg.macro_xs_[p.material()]; ... switch (score_bin) { ... macro_xs.get_xs(...); nuc_xs.get_xs(...); }` |
| Current pattern | The MG scorer duplicates the general score loop and repeatedly calls macro/nuclide `get_xs` helpers for each score, estimator branch, delayed group, and nuclide bin. |
| Why slow | Cross-section table identity, reaction channel, delayed-group count, and estimator policy are fixed enough to pre-bind for each score. Repeated generic `get_xs` calls and duplicated CE/MG switch structure scatter memory access and inflate instruction cache footprint. |
| Proposed fix | Emit MG tally descriptors with contiguous score-channel handles and per-score function pointers/functors. Cache macro and nuclide table row handles once per particle group/material before looping over requested scores. |
| Expected speedup | 1.1--1.4× inside MG scoring for tally-heavy deterministic multigroup runs; no impact on CE-only jobs. |
| Validation | Compare MG score contributions over all MgxsType channels, delayed groups, estimator modes, and survival-biasing settings; verify final tallies against vanilla on fixed multigroup pin-cell models. |
| Implementation target | `openmc-fork` MG tally descriptor and row-cache prototype. |
| Cross-code pattern | Data-descriptor analogue of Geant4 `BD-geant4-071` neutron-HP table view and `BD-geant4-080` thermal-scattering descriptor opportunities. |
| Citation | Stroustrup 2012; Williams, Waterman, and Patterson 2009. |
| Status | OPEN |

### BD-openmc-040  Tally drivers duplicate nested tally/filter/nuclide loops and reset filter matches every event

| Field | Value |
|-------|-------|
| File | `src/tallies/tally_scoring.cpp` |
| Lines | 2314-2414 and 2416-2490 |
| Hot-path % (profile-measured) | `OPEN:` analog and tracklength tally drivers; pending driver self% perf. |
| Category | 5 — Control flow |
| Current code snippet | `for (auto i_tally : model::active_analog_tallies) { ... for (; filter_iter != end; ++filter_iter) { ... for (auto i = 0; i < tally.nuclides_.size(); ++i) { ... } } }` |
| Current pattern | Analog CE/MG and tracklength drivers independently implement active-tally loops, filter-bin loops, nuclide-bin loops, `assume_separate` checks, and final resets of every particle filter match. |
| Why slow | The estimator-specific drivers share the same loop skeleton, but it is expanded repeatedly with runtime CE/MG branches and full filter-match resets after each event. Resetting every `FilterMatch` touches filters not used by the just-scored tallies. |
| Proposed fix | Introduce a generic tally-driver skeleton over precomputed `ActiveTallyPlan` descriptors. Track the subset of filter ids touched during scoring and clear only those marks; specialize the score backend once for CE, MG, analog, and tracklength modes. |
| Expected speedup | 1.05--1.25× in tally driver overhead, with larger memory-traffic savings when many filters exist but only a few are active per event. |
| Validation | Instrument touched-filter sets and require identical filter reuse/clear behavior under fixed histories; compare final tallies for analog CE, analog MG, tracklength, and timed-tracklength estimators. |
| Implementation target | `openmc-fork` active-tally plan / touched-filter reset patch. |
| Cross-code pattern | Matches Geant4 `BD-geant4-041` optional hook dispatch and `BD-geant4-108` repeated tracking-state bookkeeping. |
| Citation | Aho, Sethi, and Ullman 1986; Futamura 1971/1983. |
| Status | OPEN |

### BD-openmc-041  Collision and tracklength drivers redo nuclide/material lookup and CE/MG dispatch per tally

| Field | Value |
|-------|-------|
| File | `src/tallies/tally_scoring.cpp` |
| Lines | 2416-2475 and 2543-2605 |
| Hot-path % (profile-measured) | `OPEN:` collision/tracklength estimator setup; pending material-rich CE perf. |
| Category | 2 — Algorithm |
| Current code snippet | `auto j = mat->mat_nuclide_index_[i_nuclide]; ... if (settings::run_CE) { score_general_ce_nonanalog(...); } else { score_general_mg(...); }` |
| Current pattern | For each active tally and nuclide bin, the drivers look up material-nuclide membership, sometimes compute the log-union grid index, update microscopic XS, and branch on global CE/MG mode before scoring. |
| Why slow | Material membership and tally nuclide bins are static relative to the material; CE/MG mode is global. The hot loop can use a precomputed material/tally nuclide map and setup-selected scorer instead of repeating hash/vector lookups and global branches. |
| Proposed fix | Precompute `TallyMaterialNuclidePlan` entries per `(tally, material)` with present nuclide slot, density multiplier policy, and missing-nuclide XS-update requirement. Split CE and MG driver entry points at setup. |
| Expected speedup | 1.1--1.5× for estimator setup in isotope-rich materials or tallies with many nuclide bins. |
| Validation | Compare selected nuclide slots, atom densities, missing-nuclide micro-XS updates, and scores for materials with/without requested nuclides; fixed-seed tallies must match vanilla exactly. |
| Implementation target | `openmc-fork` material/tally nuclide plan and CE/MG driver split. |
| Cross-code pattern | Similar to Geant4 `BD-geant4-121` hadronic target material selection and `BD-geant4-032` PIL process-table specialization. |
| Citation | Khuong and Morin 2015; Futamura 1971/1983. |
| Status | OPEN |

### BD-openmc-042  Shared `xtensor` bin accumulation uses atomics for every scoring contribution

| Field | Value |
|-------|-------|
| File | `src/tallies/tally_scoring.cpp`; `src/tallies/tally.cpp`; `include/openmc/tallies/tally.h` |
| Lines | `src/tallies/tally_scoring.cpp:170-172`; `src/tallies/tally_scoring.cpp:2307-2310`; `src/tallies/tally_scoring.cpp:2648-2649`; `src/tallies/tally.cpp:821-873`; `include/openmc/tallies/tally.h:159-163` |
| Hot-path % (profile-measured) | `OPEN:` tally-bin accumulation and batch reduction; pending threaded tally perf. |
| Category | 7 — Concurrency |
| Current code snippet | `#pragma omp atomic tally.results_(filter_index, score_index, TallyResult::VALUE) += score * filter_weight;` |
| Current pattern | Scoring functions atomically add each contribution into the shared `results_` tensor. Batch accumulation later walks `results_.shape()` to normalize, zero `VALUE`, and update sums/squares. |
| Why slow | Fine-grained atomics serialize hot bins under OpenMP and force random writes through an `xtensor` indexing path. The batch accumulator then revisits the full dense tensor even when only a sparse subset of bins was touched. |
| Proposed fix | Use per-thread or per-task scratch accumulators for active tally bins, with a sparse touched-bin list and deterministic reduction into `results_` at synchronization points. Preserve dense `xtensor` storage for public API/statepoint output. |
| Expected speedup | 1.2--4× for tally-heavy multithreaded runs with contended bins; lower but still positive for sparse tallies due to touched-bin batch accumulation. |
| Validation | Compare raw per-bin contributions before/after reduction under fixed seeds; verify deterministic reductions produce identical or documented roundoff-bounded sums, then compare statepoint tally means/standard deviations. |
| Implementation target | `openmc-fork` per-thread tally accumulator; later shared `libMCAccel/core/accumulation` primitive. |
| Cross-code pattern | Directly mirrors Geant4 `BD-geant4-024`--`BD-geant4-031` sensitive-detector/hit-map accumulation bottlenecks. |
| Citation | Herlihy and Shavit 2008; Higham 2002; Williams, Waterman, and Patterson 2009. |
| Status | OPEN |

## Concrete next-step proposal

Queue an `openmc-tally-accumulator-prototype` task for worker-3/OpenMC adapter
work after a LUNARC `perf record` confirms tally self time on a tally-heavy CE
pin-cell or assembly benchmark. Start with `BD-openmc-042` plus the count-only
subset of `BD-openmc-037`: per-thread accumulators are deterministic, can be
validated against raw per-bin contribution traces, and unblock later descriptor
work in `BD-openmc-033`--`BD-openmc-041`.

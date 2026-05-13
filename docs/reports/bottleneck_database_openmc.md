# OpenMC bottleneck database — cross-section lookup hot path

Status: compact-safe worker-4 iteration 1. Scope is OpenMC continuous-energy
cross-section lookup/interpolation plus the adjacent secondary samplers named in
`docs/parallel-sessions/openmc-source-review.md`.

## Source provenance and profile basis

- Source tree read on LUNARC only: `/projects/hep/fs10/shared/nnbar/billy/openmc`.
- `git fetch --tags` on 2026-05-11 reported latest stable tag `v0.15.3`; the
  working tree is detached at `v0.15.3` (`HEAD` `27e38e894`).
- Line-reference verifier refresh on 2026-05-12 confirmed
  `calculate_urr_xs` starts at line 871 in `src/nuclide.cpp`; BD-openmc-007
  now cites a range that encloses that signature.
- No local OpenMC build, local clone, NNBAR code, or production data was touched.
- The hot-path percentage is inherited from the lane spec's published OpenMC
  profiling basis: cross-section lookup and interpolation accounts for roughly
  35--50% of transport CPU. Per-line self percentages remain `OPEN:` until a
  LUNARC `perf record` run on a pinned OpenMC benchmark maps samples to these
  exact lines.
- Cross-code references point to the current Geant4 source-review report
  (`docs/reports/g4_source_review_hotpaths.md`) because a formal
  `bottleneck_database_geant4.md` has not yet been created.

## References used by entries

- Romano et al. 2015, *OpenMC: A state-of-the-art Monte Carlo code for research
  and development*, Annals of Nuclear Energy 82.
- Khuong and Morin 2015, *Array layouts for comparison-based searching*.
- Fredman, Komlós, and Szemerédi 1984, *Storing a sparse table with O(1)
  worst case access time*.
- Aho, Sethi, and Ullman 1986, *Compilers: Principles, Techniques, and Tools*.
- Futamura 1971/1983, partial evaluation / projection work.
- Vose 1991, *A linear algorithm for generating random numbers with a given
  distribution*.
- Williams, Waterman, and Patterson 2009, *Roofline: an insightful visual
  performance model for multicore architectures*.
- Hölzle, Chambers, and Ungar 1991, *Optimizing Dynamically-Typed
  Object-Oriented Languages With Polymorphic Inline Caches*.
- Stroustrup 2012, *Why you should avoid Linked Lists*.

---

### BD-openmc-001  Reduced-range binary search remains a branchy inner-loop search

| Field | Value |
|-------|-------|
| File | `src/nuclide.cpp` |
| Lines | 616-746 |
| Hot-path % (profile-measured) | Cross-section lookup/interpolation family: 35--50% aggregate OpenMC CE transport CPU per lane-spec published profiling; per-line self% `OPEN:` pending LUNARC perf. |
| Category | 2 — Algorithm |
| Current pattern | Log-union grid narrows the interval, then calls `lower_bound_index(&grid.energy[i_low], &grid.energy[i_high], p.E())` and divides by the selected bin width. |
| Why slow | The reduced range still performs comparison-based, branch-dependent search with dependent loads before every microscopic XS interpolation. Smooth energy histories often move to the same or neighboring bin, but the generic search cannot exploit that locality. |
| Proposed fix | Add a cached-bin/neighbor fast path keyed by `(nuclide, temperature, last_grid_bin)`; fall back to an Eytzinger-layout search for nonlocal jumps. Preserve the existing log-union table as the authoritative guard and return exactly the same `i_grid`. |
| Expected speedup | 1.2--1.8× for nuclide-grid bin selection; 3--8% wall-clock on cross-section-heavy CE benchmarks if lookup dominates. |
| Validation | Replay a recorded `(nuclide, temperature, E)` trace from vanilla OpenMC and require identical `i_grid`, interpolation factor, and microscopic totals for every lookup, including grid boundaries and duplicate-energy points. |
| Implementation target | `openmc-fork` upstream PR plus optional `libMCAccel/adapters/openmc` search primitive. |
| Cross-code pattern | Mirrors Geant4 `PIL-08`/`PIL-09` physics-vector bin search in `g4_source_review_hotpaths.md`. |
| Citation | Khuong and Morin 2015; Aho, Sethi, and Ullman 1986. |
| Status | OPEN |

### BD-openmc-002  Material macro-XS accumulation is scalar AoS over nuclides

| Field | Value |
|-------|-------|
| File | `src/material.cpp` |
| Lines | 829-899 |
| Hot-path % (profile-measured) | Cross-section lookup/interpolation family: 35--50% aggregate OpenMC CE transport CPU; per-line self% `OPEN:` pending perf. |
| Category | 3 — Data structure |
| Current pattern | `Material::calculate_neutron_xs` loops over `nuclide_`, calls `p.update_neutron_xs(...)`, then adds each microscopic channel into `p.macro_xs()` one scalar field at a time. |
| Why slow | The loop mixes S(a,b) checks, cache updates, atom-density loads, and five separate scalar reductions. That interleaves control flow with memory traffic and limits vectorization across nuclides in materials with many isotopes. |
| Proposed fix | Build a read-only material XS descriptor after material finalization: contiguous nuclide indices, atom densities, S(a,b) metadata, and channel offsets. Provide a hot no-S(a,b) reducer that vectorizes total/absorption/fission/nu-fission/photon-production accumulation, with the current loop as the rare-table fallback. |
| Expected speedup | 1.15--1.4× inside material macro-XS accumulation for isotope-rich reactor materials; 2--5% wall-clock on CE pin-cell and assembly cases. |
| Validation | Fixed-seed transport comparing macro totals and selected reaction probabilities; exhaustive material-unit test over mixtures with/without S(a,b), density multipliers, and NCrystal. |
| Implementation target | `openmc-fork` upstream PR; descriptor layout reusable by `libMCAccel` OpenMC adapter. |
| Cross-code pattern | Similar to Geant4 `PIL-07` flattened lambda-table view and `PIL-10` vectorized interpolation. |
| Citation | Williams, Waterman, and Patterson 2009; Stroustrup 2012 linked-list/data-locality guidance. |
| Status | OPEN |

### BD-openmc-003  Microscopic XS cache invalidates on exact floating-state equality

| Field | Value |
|-------|-------|
| File | `src/particle.cpp` |
| Lines | 859-877 |
| Hot-path % (profile-measured) | Cross-section lookup/interpolation family: 35--50% aggregate OpenMC CE transport CPU; per-line self% `OPEN:` pending perf. |
| Category | 1 — Microarchitecture |
| Current pattern | Cache reuse tests exact `E`, `sqrtkT`, S(a,b) index/fraction, and NCrystal XS before calling `Nuclide::calculate_xs`. |
| Why slow | Exact-energy equality is a weak locality key for transport after scattering, so the branch usually falls through to the full lookup. Even when the same energy bin and interpolation tuple are reused by tallies or repeated scoring, the cache key does not expose that cheaper equivalence. |
| Proposed fix | Extend `NuclideMicroXS` with the last `(i_log_union, i_temp, i_grid, interp_factor)` tuple and a fast path for repeated scoring at unchanged bin/interpolation state. Keep exact-energy validation in debug builds to ensure no approximate reuse changes physics. |
| Expected speedup | 1.05--1.2× in workloads with repeated tally/scoring access to the same microscopic XS; low risk because the fallback is unchanged. |
| Validation | Instrument cache hit/miss logs, then require identical microscopic channel values and event outcomes with fixed seeds. Add adversarial tests where two energies share a bin but have different interpolation factors to prove the guard does not over-reuse. |
| Implementation target | `openmc-fork` upstream PR. |
| Cross-code pattern | Aligns with Geant4 `PIL-05` guarded EM lambda state cache. |
| Citation | Aho, Sethi, and Ullman 1986. |
| Status | OPEN |

### BD-openmc-004  Temperature selection scans temperature grids in the lookup path

| Field | Value |
|-------|-------|
| File | `src/nuclide.cpp` |
| Lines | 616-714 |
| Hot-path % (profile-measured) | Cross-section lookup/interpolation family: 35--50% aggregate OpenMC CE transport CPU; per-line self% `OPEN:` pending perf. |
| Category | 2 — Algorithm |
| Current pattern | `TemperatureMethod::NEAREST` and interpolation modes loop over `kTs_` to find or sample a temperature index. |
| Why slow | Temperature grids are static after data load, but each nuclide lookup redoes a linear scan and carries runtime policy branches. The cost is small for few temperatures but multiplies by nuclides and histories. |
| Proposed fix | Precompute a per-material/per-cell temperature-index descriptor for the current `sqrtkT` and split nearest vs. stochastic interpolation into separate function objects selected at setup. For many-temperature data, replace linear scan with binary/Eytzinger search. |
| Expected speedup | 1.05--1.25× for temperature-rich Doppler cases; negligible for single-temperature libraries. |
| Validation | Compare selected `i_temp` sequences under fixed RNG streams for nearest and interpolation modes, including out-of-range clamps. Cross-section outputs must remain bit-identical. |
| Implementation target | `openmc-fork` upstream PR. |
| Cross-code pattern | Mirrors Geant4 `PIL-06` process/model shape specialization: static policy should not branch in every lookup. |
| Citation | Khuong and Morin 2015; Futamura 1971/1983. |
| Status | OPEN |

### BD-openmc-005  Linear interpolation repeats divisions and channel loads per nuclide

| Field | Value |
|-------|-------|
| File | `src/nuclide.cpp` |
| Lines | 616-775 |
| Hot-path % (profile-measured) | Cross-section lookup/interpolation family: 35--50% aggregate OpenMC CE transport CPU; per-line self% `OPEN:` pending perf. |
| Category | 4 — Mathematical |
| Current pattern | Compute one interpolation factor, then separately evaluate total, absorption, fission, nu-fission, and photon-production channels from `xs(i_grid, channel)` and `xs(i_grid + 1, channel)`. |
| Why slow | The same two grid rows are read repeatedly, and linear interpolation does not use precomputed slopes/intercepts. Channel-wise calls through the `xtensor` accessor may inhibit compact vector loads. |
| Proposed fix | During data finalization, emit per-temperature channel blocks with precomputed slopes or two-row SoA descriptors. In the hot path, load all active channels from contiguous memory and evaluate `y0 + f * slope` (or FMA) with a branchless fissionable mask. |
| Expected speedup | 1.15--1.6× for microscopic interpolation arithmetic; 4--10% of cross-section family time if bin search has already been optimized. |
| Validation | First require bit-identical scalar operation order; if FMA changes last-bit rounding, gate with a documented tolerance plus keff/reaction-rate regression on pinned benchmarks. |
| Implementation target | `openmc-fork` upstream PR; SoA view reusable by `libMCAccel`. |
| Cross-code pattern | Directly mirrors Geant4 `PIL-10` interpolation precompute. |
| Citation | Aho, Sethi, and Ullman 1986; Williams, Waterman, and Patterson 2009. |
| Status | OPEN |

### BD-openmc-006  Depletion-reaction interpolation remains in the generic XS routine

| Field | Value |
|-------|-------|
| File | `src/nuclide.cpp` |
| Lines | 616-813 |
| Hot-path % (profile-measured) | Cross-section lookup/interpolation family: 35--50% aggregate OpenMC CE transport CPU; depletion-specific self% `OPEN:` pending perf. |
| Category | 5 — Control flow |
| Current pattern | `Nuclide::calculate_xs` checks `simulation::need_depletion_rx` and, when enabled, loops over depletion MTs with threshold checks in the same routine used for ordinary transport. |
| Why slow | A burnup/depletion policy is global for a run, but the inner lookup carries the branch and optional reaction loop. When enabled, the loop walks reaction metadata and adds unpredictable threshold branches after the main XS interpolation. |
| Proposed fix | Split neutron XS evaluation into two setup-selected call paths: transport-only and depletion-enabled. For depletion mode, store present depletion reactions in a compact threshold-sorted descriptor and stop at the first impossible higher-multiplicity threshold. |
| Expected speedup | Transport-only: small branch-removal win. Depletion-enabled: 1.1--1.3× for the depletion reaction subloop. |
| Validation | Unit compare every depletion reaction channel for all `DEPLETION_RX` entries across threshold boundaries; full depletion benchmark must match reaction rates and final inventories within existing stochastic uncertainty. |
| Implementation target | `openmc-fork` upstream PR. |
| Cross-code pattern | Same hot/cold path separation as Geant4 `PIL-02` force-condition splitting. |
| Citation | Hölzle, Chambers, and Ungar 1991; Aho, Sethi, and Ullman 1986. |
| Status | OPEN |

### BD-openmc-007  URR probability-table lookup stacks searches and expensive log/exp interpolation

| Field | Value |
|-------|-------|
| File | `src/nuclide.cpp` |
| Lines | 871-950 |
| Hot-path % (profile-measured) | Cross-section lookup/interpolation family: 35--50% aggregate OpenMC CE transport CPU; URR self% `OPEN:` pending benchmark in resonance-heavy materials. |
| Category | 4 — Mathematical |
| Current pattern | `calculate_urr_xs` lower-bounds the energy, upper-bounds two CDF rows, then either linearly interpolates or performs log-log interpolation with repeated `std::log`/`std::exp` calls. |
| Why slow | URR transport combines several branchy searches with transcendental interpolation in a path that is repeatedly sampled for resonance-region histories. Table interpolation mode is static, but the runtime branches remain in every lookup. |
| Proposed fix | Pretransform URR energy and positive XS values into log space for log-log tables, split lin-lin and log-log kernels at data-load time, and store CDF rows in Eytzinger or alias-table form depending on row length. |
| Expected speedup | 1.3--2.0× inside URR lookup for log-log tables; wall-clock depends on resonance workload fraction. |
| Validation | Fixed-seed test comparing sampled probability-bin indices, interpolated elastic/fission/capture values, and downstream reaction selection. Include zero/negative XS cases that currently skip log-log interpolation. |
| Implementation target | `openmc-fork` upstream PR; CDF sampler could live in `libMCAccel/core/sampling`. |
| Cross-code pattern | Combines Geant4 `PIL-09` search-layout issue and `PIL-10` interpolation-transcendental issue. |
| Citation | Khuong and Morin 2015; Vose 1991; Aho, Sethi, and Ullman 1986. |
| Status | OPEN |

### BD-openmc-008  Reaction XS lookup repeats threshold branch and indirect value indexing

| Field | Value |
|-------|-------|
| File | `src/reaction.cpp` |
| Lines | 100-113 |
| Hot-path % (profile-measured) | Cross-section lookup/interpolation family: 35--50% aggregate OpenMC CE transport CPU; reaction-channel self% `OPEN:` pending perf. |
| Category | 1 — Microarchitecture |
| Current pattern | `Reaction::xs` checks `i_grid < threshold`, then indexes `x.value` at threshold-shifted positions and performs two-point interpolation. |
| Why slow | Threshold checks and shifted indices recur for every reaction channel. For known reaction sets, the threshold and value base pointer are static, yet the hot call still recomputes the offset and branches. |
| Proposed fix | Build per-temperature reaction descriptors with `base = value.data() - threshold`, `threshold`, and precomputed slope where legal. Use a branchless mask for below-threshold or split thresholded/non-thresholded reactions into separate loops. |
| Expected speedup | 1.05--1.2× for reaction-channel scoring and depletion-channel lookups; larger when many MT-specific tallies call `Reaction::xs`. |
| Validation | Exhaustive energy-grid boundary tests for each reaction threshold; compare tally scores and sampled reaction MTs in fixed-seed transport. |
| Implementation target | `openmc-fork` upstream PR. |
| Cross-code pattern | Similar to Geant4 `PIL-10` per-channel interpolation precompute. |
| Citation | Aho, Sethi, and Ullman 1986; Williams, Waterman, and Patterson 2009. |
| Status | OPEN |

### BD-openmc-009  Thermal S(a,b) XS selection repeats static temperature-policy work

| Field | Value |
|-------|-------|
| File | `src/thermal.cpp` |
| Lines | 173-210 and 285-296 |
| Hot-path % (profile-measured) | Cross-section lookup/interpolation family: 35--50% aggregate OpenMC CE transport CPU; thermal self% `OPEN:` pending cold/thermal benchmark. |
| Category | 5 — Control flow |
| Current pattern | `ThermalScattering::calculate_xs` scans `kTs_` and branches on temperature method, then `ThermalData::calculate_xs` invokes stored function objects for elastic/inelastic XS. |
| Why slow | Thermal-scattering policy and data availability are static for a material/table, but the lookup path repeats policy selection and nullable elastic checks. Thermal moderator workloads can hit this path for many collisions. |
| Proposed fix | Prebind a thermal-table evaluator at data-load time: nearest vs. interpolated temperature, elastic-present vs. inelastic-only, and search layout for multi-temperature data. Cache the selected thermal temperature index in the material descriptor when cell temperature is fixed. |
| Expected speedup | 1.1--1.3× inside S(a,b) XS lookup in moderator-heavy cases. |
| Validation | Compare selected thermal temperature index, elastic/inelastic XS, and scatter branch for fixed seeds over water/graphite/polyethylene tables and temperature-boundary cases. |
| Implementation target | `openmc-fork` upstream PR. |
| Cross-code pattern | Mirrors Geant4 `PIL-05`/`PIL-06` guarded material-model selection. |
| Citation | Futamura 1971/1983; Khuong and Morin 2015. |
| Status | OPEN |

### BD-openmc-010  Correlated and Kalbach secondary samplers duplicate linear CDF scans

| Field | Value |
|-------|-------|
| File | `src/secondary_correlated.cpp`; `src/secondary_kalbach.cpp` |
| Lines | `src/secondary_correlated.cpp:156-264`; `src/secondary_kalbach.cpp:117-239` |
| Hot-path % (profile-measured) | Adjacent physics-sampling hot path named by lane spec under cross-section lookup review; per-line self% `OPEN:` pending perf. |
| Category | 2 — Algorithm |
| Current pattern | Both samplers lower-bound incident energy, linearly scan discrete and continuous outgoing CDF portions, branch on interpolation mode, then run nearly identical inverse-CDF algebra. |
| Why slow | The same sampling skeleton is duplicated with scalar linear scans over CDF arrays. Large outgoing distributions pay O(n) search where O(log n) or O(1) alias sampling is available, and duplicated code blocks make optimizer specialization harder. |
| Proposed fix | Extract a shared tabular-angle-energy sampler with per-distribution precomputed search descriptors: small CDFs stay linear, large CDFs use Eytzinger binary search or Vose alias tables for discrete portions. Split histogram vs. lin-lin kernels at load time. |
| Expected speedup | 1.3--2.5× for outgoing-energy bin selection in reactions with long distributions; material wall-clock impact depends on secondary-production frequency. |
| Validation | For fixed RNG streams, compare selected outgoing bins, sampled `E_out`, `mu`, and reaction secondaries. For alias-table mode, require distribution-level KS p-value ≥ 0.05 and unbiased means if exact RNG-consumption order cannot be preserved. |
| Implementation target | `openmc-fork` upstream PR plus `libMCAccel/core/sampling` primitive. |
| Cross-code pattern | This is the OpenMC analogue of the Geant4 physics-sampling/DoIt review queued after PIL/geometry. |
| Citation | Vose 1991; Khuong and Morin 2015. |
| Status | OPEN |

### BD-openmc-011  Thermal secondary samplers combine helper binary searches with linear CDF walks

| Field | Value |
|-------|-------|
| File | `src/secondary_thermal.cpp` |
| Lines | 14-55 and 247-291 |
| Hot-path % (profile-measured) | Adjacent thermal-sampling hot path named by lane spec; per-line self% `OPEN:` pending moderator benchmark. |
| Category | 2 — Algorithm |
| Current pattern | `get_energy_index` and `CoherentElasticAE::sample` lower-bound energy grids; `IncoherentInelasticAE::sample` linearly walks `e_out_cdf` before inverse lin-lin sampling. |
| Why slow | Thermal scattering is frequent in moderated systems, yet energy-index and outgoing-energy selection use generic branchy searches with no per-table specialization. The CDF walk is O(n) in the outgoing grid length. |
| Proposed fix | Add per-thermal-table search descriptors: neighbor cache for incident energy, Eytzinger search for Bragg factors, and alias/Eytzinger CDF selection for outgoing energy depending on distribution size. Share the inverse lin-lin algebra with BD-openmc-010. |
| Expected speedup | 1.2--2.0× for thermal secondary energy/cosine sampling in moderator-heavy workloads. |
| Validation | Fixed-seed compare for coherent elastic Bragg-edge index and incoherent inelastic outgoing bin/energy; distribution-level KS for alias mode if RNG order intentionally changes. |
| Implementation target | `openmc-fork` upstream PR. |
| Cross-code pattern | Same CDF-search class as BD-openmc-010 and future Geant4 DoIt sampler entries. |
| Citation | Vose 1991; Khuong and Morin 2015. |
| Status | OPEN |

### BD-openmc-012  Windowed multipole evaluation pays per-pole complex/Faddeeva cost in scalar loops

| Field | Value |
|-------|-------|
| File | `src/wmp.cpp` |
| Lines | 82-166 |
| Hot-path % (profile-measured) | Cross-section lookup/interpolation family: 35--50% aggregate OpenMC CE transport CPU; WMP self% `OPEN:` pending WMP-enabled benchmark. |
| Category | 4 — Mathematical |
| Current pattern | `WindowedMultipole::evaluate` computes `sqrt(E)`, locates a window, evaluates curvefit terms, then loops over poles with scalar complex arithmetic and temperature-dependent Faddeeva calls. |
| Why slow | The pole loop mixes complex loads, branch-dependent fission terms, and expensive special-function calls. Window metadata is static and pole data can be laid out for vector batches, but the current code evaluates one particle/nuclide at a time. |
| Proposed fix | Split 0 K and finite-temperature evaluators, precompute `sqrt(E_min_)`, store pole residues in SoA form, and vectorize batches of pole evaluations for the same window. Investigate rational/Chebyshev approximants for Faddeeva under a strict error envelope. |
| Expected speedup | 1.2--2.0× inside WMP evaluation; potentially high impact for resonance-heavy WMP-enabled runs. |
| Validation | Compare `(sig_s, sig_a, sig_f)` over dense energy-temperature grids against the scalar evaluator with relative error bounds below nuclear-data uncertainty; fixed-seed transport must preserve reaction-rate and keff statistics. |
| Implementation target | `openmc-fork` upstream PR; special-function vector kernel could live in `libMCAccel/core/math`. |
| Cross-code pattern | Complements Geant4 `PIL-10` mathematical-interpolation precompute, but WMP has OpenMC-specific special-function validation needs. |
| Citation | Aho, Sethi, and Ullman 1986; Williams, Waterman, and Patterson 2009. |
| Status | OPEN |

## Concrete next-step proposal

Queue worker-3/OpenMC-adapter follow-up after the baseline OpenMC build task is
complete: `openmc-xs-bin-search-prototype`. It should implement BD-openmc-001
only, because it is deterministic, high-impact, and validation can be purely
bit-exact on recorded `(nuclide, temperature, E)` lookup traces before any full
transport benchmark is run.

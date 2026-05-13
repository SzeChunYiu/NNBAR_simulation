# G4GPU Phase 8 algorithm survey for Geant4 acceleration

Date: 2026-05-11. Status: compact-safe survey deliverable for
`g4gpu-phase8-survey`. Strategy root: `docs/specs/g4gpu-line-by-line-acceleration.md`.

Scope and evidence standard: this report ranks deterministic computer-science
and applied-math methods by `speedup_or_variance_gain × validatability / effort`.
All speedups below are hypotheses for the Phase 5 benchmark suite, not measured
G4GPU results. "Not deeply applied to Geant4" means this pass found no first-
class production Geant4 integration in the checked Geant4, GeantV, Celeritas,
AdePT, and Opticks sources [R1-R6]; a Geant4 developer audit should still
confirm novelty before publication. Existing GPU work attacks EM transport,
vectorization, or optical photons; Phase 8 should prefer bit-checkable or
statistically unbiased deterministic transformations before any surrogate ML.

## Section 1 -- Deterministic methods (PRIMARY)

Format per item: `Use / field / why not Geant4 / hot path / gain / sketch /
validation / effort`.

1. **Quasi-Monte Carlo: Sobol, Halton, Niederreiter.** Use: low-discrepancy
   quadrature with Koksma-Hlawka-style error bounds for smooth integrands
   [R7,R8]. Field: finance, rendering, UQ libraries; McMule documents adaptive
   VEGAS usage rather than a cited Sobol path [R43], so any Sherpa/McMule QMC
   claim remains unpromoted. Not Geant4: transport consumes random dimensions
   dynamically, so sequence dimensions must be assigned reproducibly across
   branching secondaries. Hot path: all sampling, especially PIL/DoIt. Gain:
   3-20x fewer events for smooth observables, not per-event speed. Sketch:
   implement a dimension ledger per track and randomized Sobol engine behind a
   Geant4-compatible RNG adapter. Validation: compare fixed-seed PRNG and QMC
   estimators on six benchmark observables; prove unbiasedness only for
   randomized QMC. Effort: 6 worker-weeks.
2. **Stratified sampling + Russian roulette + splitting.** Use: reactor and
   shielding Monte Carlo variance reduction; MCNP documents geometry/energy
   splitting and roulette with weight correction [R9]. Field: neutron/photon
   transport. Not Geant4: general-purpose detector workflows lack a problem-
   specific importance map. Hot path: rare neutron/cosmic backgrounds and deep
   shielding. Gain: 5-100x variance reduction for rare tallies. Sketch: add
   user-supplied importance regions and weight-preserving split/kill policies.
   Validation: weight-sum conservation, analog-vs-biased mean agreement, and
   lower variance on rare tallies. Effort: 5 weeks.
3. **Importance sampling with control and antithetic variates.** Use: standard
   Monte Carlo variance-reduction theory [R10]. Field: finance, queueing,
   stochastic simulation. Not Geant4: needs observable-specific control models
   and careful negative-weight bookkeeping. Hot path: DoIt sampling and final
   tally estimation. Gain: 2-10x variance reduction where analytic controls
   exist. Sketch: pair random variates for symmetric samplers and add optional
   control tallies from first-order range/energy-loss models. Validation:
   estimator unbiasedness tests and variance-ratio confidence intervals.
   Effort: 4 weeks.
4. **Korobov / rank-1 lattice rules.** Use: structured QMC lattice rules in
   numerical integration [R8]. Field: UQ and finance. Not Geant4: lattice
   dimensionality is brittle under random process branching. Hot path: batch
   integration over systematic-throw ensembles. Gain: 3-30x fewer samples for
   low-effective-dimension systematic scans. Sketch: use shifted rank-1
   lattices for outer parameter ensembles, not inner stochastic transport at
   first. Validation: randomized shifts provide error bars; compare to PRNG
   ensembles. Effort: 3 weeks.
5. **Polynomial chaos expansion (PCE).** Use: generalized polynomial chaos for
   uncertainty propagation with exponential convergence for low-dimensional
   stochastic inputs [R11]. Field: CFD/UQ. Not Geant4: transport randomness is
   high-dimensional and discontinuous, but detector systematics are low-
   dimensional. Hot path: systematic ensembles, not per-event stepping. Gain:
   10-100x fewer full simulations for smooth calibration/systematic parameters.
   Sketch: train non-intrusive PCE on benchmark outputs versus material and
   calibration parameters. Validation: holdout systematic points and Sobol
   indices. Effort: 4 weeks.
6. **SAH-BVH geometry.** Use: surface-area heuristic spatial hierarchies in ray
   tracing [R12]. Field: graphics, OptiX-style traversal. Not Geant4: Geant4
   geometry semantics include placements, replicas, touchables, and boundary
   tolerances, not just triangles. Hot path: geometry navigation. Gain: 1.5-5x
   navigation speed on complex static geometry. Sketch: build a read-only BVH
   of candidate solids per detector region and fall back to exact Geant4-style
   boundary checks. Validation: bitwise identical volume boundary sequence on
   random rays plus benchmark KS tests. Effort: 8 weeks.
7. **Cache-oblivious BVH/layouts.** Use: data structures with asymptotic cache
   efficiency independent of cache size [R13]. Field: databases/search trees.
   Not Geant4: existing object graphs optimize flexibility, not memory layout.
   Hot path: geometry and material lookup. Gain: 1.2-2x from fewer cache misses.
   Sketch: van-Emde-Boas/order BVH nodes and compact immutable navigation data.
   Validation: perf cache-miss counters and exact geometry traversal agreement.
   Effort: 4 weeks.
8. **Cuckoo / perfect hashing for material and particle lookup.** Use: cuckoo
   hashing gives worst-case constant lookup after construction [R14]. Field:
   databases, compilers, routing tables. Not Geant4: dynamic user physics lists
   and materials favor maps and registries. Hot path: material, isotope,
   particle, and process lookup. Gain: 1.1-1.8x in lookup-heavy stepping.
   Sketch: build immutable minimal/perfect tables at initialization; expose a
   mutation barrier. Validation: exhaustive key parity and perf lookup counters.
   Effort: 2 weeks.
9. **SVD/tensor compression of cross-section tables.** Use: SVD/Tucker/CP
   decompositions compress multiway arrays [R15]. Field: recommender systems,
   signal processing, scientific data compression. Not Geant4: interpolation
   accuracy must satisfy physics tolerances across sharp thresholds. Hot path:
   PIL cross-section interpolation. Gain: 1.2-3x memory-bandwidth reduction.
   Sketch: offline compress smooth table blocks and preserve exact tabulation
   near thresholds/resonances. Validation: max relative error, monotonicity, and
   benchmark distribution parity. Effort: 6 weeks.
10. **Persistent immutable data structures.** Use: HAMT/persistent vectors for
    cheap snapshots [R16]. Field: functional runtimes and databases.
    Not Geant4: C++ object model mutates run/event/track state. Hot path: touchable
    history and per-track state copies. Gain: 1.1-1.5x plus safer concurrency.
    Sketch: represent touchable histories as interned persistent paths.
    Validation: identical volume ancestry and allocation-count reduction.
    Effort: 5 weeks.
11. **JIT compilation via LLVM ORC or Cling.** Use: LLVM ORC JIT and Cling
    compile/link code at runtime [R17,R18]. Field: language runtimes, ROOT/CERN
    analysis. Not Geant4: plugin ABI, reproducibility, and sandboxing are hard.
    Hot path: process dispatch and detector-specific branch elimination. Gain:
    1.3-4x for single-particle/single-physics benchmark kernels. Sketch: emit a
    detector+particle specialized kernel after initialization. Validation:
    generated-source hash, fixed-seed parity, and fallback-to-generic tests.
    Effort: 8 weeks.
12. **Partial evaluation / Futamura projection.** Use: specialize a generic
    interpreter/program with static inputs [R19]. Field: compilers and DSLs.
    Not Geant4: static/dynamic boundaries are not explicit in the toolkit API.
    Hot path: particle-specialized stepping. Gain: 1.5-5x if process lists and
    cuts are static. Sketch: factor transport into a small DSL and generate
    muon/gamma/neutron kernels. Validation: generated code differential tests
    against generic transport. Effort: 10 weeks.
13. **Symbolic/computer-algebra preprocessing.** Use: FORM and CAS workflows in
    high-order particle-physics calculations [R20]. Field: QCD/NLO algebra.
    Not Geant4: hadronic models mix empirical tables and procedural code, not
    closed-form expressions. Hot path: differential cross-section kernels where
    formulas exist. Gain: 1.1-3x for formula-heavy kernels. Sketch: generate
    optimized C/CUDA from validated analytic submodels only. Validation: MPFR
    oracle comparison and interval error bounds. Effort: 6 weeks.
14. **PGO + LTO.** Use: GCC/LLVM support profile feedback and link-time whole-
    program optimization [R21,R22]. Field: production compilers. Not Geant4:
    many experiment builds prioritize portable defaults and plugin boundaries.
    Hot path: whole CPU fallback. Gain: 1.1-1.3x low-risk speedup. Sketch:
    collect Phase 5 profiles and build CPU fallback with PGO+ThinLTO. Validation:
    benchmark parity and ABI smoke tests. Effort: 1 week.
15. **Work-stealing schedulers.** Use: Cilk-style work stealing has provable
    bounds for dynamic multithreaded computations [R23]. Field: task runtimes.
    Not Geant4: current event-level MT avoids fine-grained scheduling
    complexity. Hot path: track stack and secondary bursts. Gain: 1.2-3x load
    balance on shower-heavy events. Sketch: per-species deques with deterministic
    replay mode. Validation: fixed-seed event parity and scheduler trace checks.
    Effort: 6 weeks.
16. **Actor model / structured concurrency.** Use: actors model asynchronous
    message-passing systems [R24]. Field: distributed systems. Not Geant4:
    actor messages add overhead and complicate deterministic replay. Hot path:
    event services, scoring, I/O, and heterogeneous CPU/GPU pipelines. Gain:
    1.1-2x mostly from latency hiding. Sketch: actors for geometry, physics,
    hit scoring, and output queues after track kernels mature. Validation:
    replayable message logs and backpressure tests. Effort: 8 weeks.
17. **C++20 coroutines for transport continuations.** Use: standardized
    coroutine language support [R25]. Field: async runtimes/generators.
    Not Geant4: heap-allocated coroutine frames and ABI maturity are risks.
    Hot path: deep stepping call stack and host/device suspension. Gain: 1.1-1.8x
    if frames are pooled and continuations replace virtual recursion. Sketch:
    prototype coroutine state machine for CPU fallback only. Validation: frame
    allocation caps and exact step sequence. Effort: 5 weeks.
18. **Mixed precision with interval guards.** Use: mixed precision can combine
    fast low precision with high-precision correction [R26], while interval
    arithmetic bounds rounding error [R27]. Field: numerical linear algebra and
    verified computing. Not Geant4: geometric boundary tolerances are fragile.
    Hot path: geometry predicates and smooth table interpolation. Gain: 1.2-3x
    on GPU/CPU SIMD. Sketch: FP32 fast path with interval or double fallback
    near boundaries/thresholds. Validation: interval containment plus boundary
    stress tests. Effort: 6 weeks.
19. **Posit numbers.** Use: posit arithmetic proposes tapered precision as a
    float alternative [R28]. Field: experimental numeric hardware. Not Geant4:
    little commodity hardware and difficult reproducibility. Hot path: none
    until hardware exists. Gain: speculative. Sketch: keep as research note,
    not Phase 8 implementation. Validation: MPFR oracle if prototyped. Effort:
    2 weeks for paper study only.
20. **Arbitrary precision / Arb / MPFR.** Use: MPFR gives correctly rounded
    multiprecision [R29]; Arb gives ball arithmetic with error radii [R30].
    Field: verified numerics. Not Geant4: too slow for inner loops. Hot path:
    oracle generation, not production. Gain: validation confidence, not speed.
    Sketch: build oracle tests for cross-section interpolation and geometry
    boundaries. Validation: exact containment proofs. Effort: 3 weeks.
21. **Branchless surface tests via SIMD masks.** Use: robust and branchless
    ray-box intersection improves ray/box throughput [R31]. Field: graphics and
    VecGeom-like geometry. Not Geant4: each solid has special tolerances and
    inside/outside states. Hot path: geometry navigation. Gain: 1.2-2.5x for
    box/tube-heavy detectors. Sketch: branchless AABB/tube kernels with exact
    fallback near tolerance boundaries. Validation: exhaustive boundary tests
    and KS parity. Effort: 4 weeks.
22. **Bit-parallel popcount geometry/material queries.** Use: broadword rank/
    select operations accelerate bit-vector queries [R32]. Field: succinct
    indexes, IR, databases. Not Geant4: material/region membership is object-
    graph based. Hot path: candidate solid/material masks. Gain: 1.1-2x when
    many candidates can be represented as bitsets. Sketch: encode region
    membership and active-process masks as word-aligned bitsets. Validation:
    exhaustive membership parity. Effort: 3 weeks.
23. **Tropical semiring / min-plus step computation.** Use: min-plus algebra
    models shortest-path/min-plus optimization [R33]. Field: optimization and
    scheduling. Not Geant4: step limitation is a min over heterogeneous physics,
    geometry, and user limits with side effects. Hot path: step-limit reduction.
    Gain: 1.1-1.5x via vectorized min-reduction, not a new physics model.
    Sketch: express candidate step lengths as arrays and reduce branchlessly.
    Validation: exact chosen-limiter parity. Effort: 2 weeks.
24. **NTT/FFT shower convolutions.** Use: Cooley-Tukey FFT accelerates
    convolution-like transforms [R34]. Field: signal processing. Not Geant4:
    showers are geometry- and material-dependent branching processes, not
    stationary convolutions. Hot path: response libraries or optical/EM
    repeated unit responses. Gain: 2-20x only for linear response subproblems.
    Sketch: precompute unit-response Green functions for validated homogeneous
    blocks. Validation: residual distribution against full Geant4. Effort: 6
    weeks.
25. **Compressed sensing for sparse hits.** Use: sparse signal recovery from
    incomplete measurements [R35,R36]. Field: imaging, sensing. Not Geant4:
    simulation must generate truth, not infer it from fewer observations.
    Hot path: hit I/O and compression after transport. Gain: 2-10x output-size
    reduction for sparse calorimeter/TPC hits. Sketch: compress hit buffers with
    sparse encodings, not replace transport. Validation: lossless or bounded-
    lossy reconstruction tests per observable. Effort: 4 weeks.
26. **Reservoir sampling for streaming hit collection.** Use: one-pass random
    samples of unknown-length streams [R37]. Field: streaming algorithms.
    Not Geant4: production scoring usually needs all hits, not samples. Hot path:
    diagnostics/profiling hit streams. Gain: O(1) memory diagnostics and less
    debug I/O. Sketch: add labelled diagnostic-only reservoirs, never physics
    output. Validation: uniform inclusion tests. Effort: 1 week.
27. **Bloom filters for material/process caching.** Use: space/time tradeoff for
    approximate membership with false positives but no false negatives [R38].
    Field: databases and caches. Not Geant4: false positives can waste work and
    false negatives would be illegal. Hot path: negative cache lookups. Gain:
    1.1-1.5x if misses dominate. Sketch: use Bloom filters only as prefilters
    before exact lookup. Validation: zero false negatives by construction plus
    exact-result parity. Effort: 2 weeks.
28. **Reversible computation / Bennett checkpointing.** Use: reversible
    simulation trades time/space and stores enough history to reverse [R39].
    Field: reversible/quantum computing and adjoint methods. Not Geant4:
    stochastic branching and secondary allocation make reversible state huge.
    Hot path: future differentiable transport/checkpointing, not Phase 8 speed.
    Gain: enables gradients or memory tradeoffs, not immediate throughput.
    Sketch: deterministic event replay with sparse checkpoints. Validation:
    reverse-to-initial-state tests. Effort: 8 weeks.

## Section 2 -- Ranking

Scores are ordinal: 5=high, 1=low; `rank score = gain × validatability / effort`.

| Rank | Method | Gain | Validatable | Effort | Score | Disposition |
|---:|---|---:|---:|---:|---:|---|
| 1 | PGO + LTO | 2 | 5 | 1 | 10.0 | Free win; do during Phase 5/8 baseline |
| 2 | Perfect/cuckoo hashing | 2 | 5 | 2 | 5.0 | Phase 8a engineering |
| 3 | Tropical/min-plus step reduction | 2 | 5 | 2 | 5.0 | Phase 8a engineering |
| 4 | Bloom-filter prefilters | 2 | 5 | 2 | 5.0 | Free-ish if exact fallback is mandatory |
| 5 | Reservoir diagnostics | 1 | 5 | 1 | 5.0 | Diagnostic win, not physics speed |
| 6 | SAH-BVH geometry | 5 | 5 | 8 | 3.1 | Phase 8b high-impact geometry |
| 7 | Branchless SIMD surfaces | 3 | 5 | 4 | 3.8 | Phase 8a/5d candidate |
| 8 | Stratified/splitting/RR | 5 | 4 | 5 | 4.0 | Phase 8c variance-reduction |
| 9 | QMC RNG ledger | 5 | 4 | 6 | 3.3 | Phase 8d; high payoff but subtle |
| 10 | Control/antithetic variates | 3 | 4 | 4 | 3.0 | Pair with variance-reduction phase |
| 11 | Mixed precision + intervals | 3 | 4 | 6 | 2.0 | Needs oracle-heavy validation |
| 12 | JIT specialization | 4 | 4 | 8 | 2.0 | Phase 9 if ABI risk accepted |
| 13 | Partial evaluation DSL | 5 | 4 | 10 | 2.0 | Long-term compiler moat |
| 14 | SVD/tensor tables | 3 | 3 | 6 | 1.5 | Only smooth table blocks |
| 15 | Cache-oblivious layouts | 2 | 5 | 4 | 2.5 | Bundle with BVH layout |
| 16 | Work stealing | 3 | 4 | 6 | 2.0 | After deterministic replay exists |
| 17 | PCE systematics | 5 | 3 | 4 | 3.8 | Use for UQ, not event transport |
| 18 | FFT response convolution | 4 | 3 | 6 | 2.0 | Only homogeneous response libraries |
| 19 | Compressed sensing hits | 3 | 3 | 4 | 2.2 | I/O compression, not physics |
| 20 | Coroutines | 2 | 4 | 5 | 1.6 | Prototype only |
| 21 | Actor model | 2 | 3 | 8 | 0.8 | System architecture, later |
| 22 | Symbolic preprocessing | 3 | 4 | 6 | 2.0 | Formula-only kernels |
| 23 | Immutable touchables | 2 | 5 | 5 | 2.0 | Safety+allocation win |
| 24 | Arb/MPFR oracle | 1 | 5 | 3 | 1.7 | Validation infrastructure |
| 25 | Rank-1 lattices | 3 | 4 | 3 | 4.0 | Outer systematic ensembles |
| 26 | Posits | 1 | 2 | 2 | 1.0 | Watchlist only |
| 27 | Reversible computation | 1 | 3 | 8 | 0.4 | Differentiable future |
| 28 | Persistent data structures | 2 | 5 | 5 | 2.0 | Combine with touchable intern pool |

Top-five implementation candidates after collapsing tiny diagnostics into larger
work packages: **PGO/LTO**, **perfect hashing + Bloom exact-prefilter**, **SAH-BVH
+ cache-aware layout**, **branchless/min-plus geometry-step kernels**, and
**formal variance reduction/QMC**. Free wins are PGO/LTO, immutable lookup-table
construction, Bloom prefilters with exact fallback, reservoir diagnostic sampling,
and branchless reductions that preserve the exact chosen limiter.

## Section 3 -- ML methods (SECONDARY)

> ML methods in HEP simulation face a permanent validation challenge: any
> distribution-level test only proves the model is correct on the tested
> distribution. Out-of-domain failure modes cannot be ruled out. For Geant4
> deployment the model must either: (a) be auditable to the same standard as
> a tabulated cross section, which no current architecture supports, or (b)
> only be used in regions where the deterministic method is impractical.

- **CaloChallenge.** Community benchmark for fast calorimeter simulation with
  quality, timing, and model-size comparisons [R40]. Useful as an evaluation
  pattern, but it validates finite datasets, not arbitrary detector states.
- **CaloFlow / CaloFlow II.** Normalizing-flow shower generation can emulate
  many-channel calorimeter deposits quickly [R41]. Candidate for response-library
  acceleration only after deterministic FFT/response-table options fail.
- **Transformer calorimeter samplers.** CaloDREAM uses autoregressive and vision
  transformers for calorimeter response emulation [R42]; newer hadronic/point-
  cloud transformer work should be treated as fallback research. Required guard:
  explicit domain classifier, deterministic fallback, and no silent deployment.

## Section 4 -- Validation framework

1. **Distribution agreement.** For every candidate, compare reference Geant4 and
   candidate outputs on Phase 5 benchmarks: total deposited energy, leading KE,
   multiplicity, vertex/entry position, per-detector hit counts, timing, and
   weights. Default gates: KS p-value not below the predeclared multiple-test
   threshold, KL/JS divergence <= 1% where binned densities are stable, and
   bootstrap confidence intervals overlapping the reference.
2. **Out-of-domain coverage.** Sweep particle type, energy, material, boundary
   distance, detector region, and secondary multiplicity. A candidate must report
   `NotInDomain` and fall back exactly when its proven envelope is exceeded.
3. **Bit-exact reproducibility.** Pure engineering changes (hashing, PGO/LTO,
   branchless exact kernels, BVH candidates before fallback) must produce fixed-
   seed identical event records except for documented floating-point reordering.
4. **QMC reproducibility.** QMC methods require a dimension ledger, randomized
   scrambling/shift seed, and independent-scramble error bars; fixed pseudo-
   random bit-exactness is replaced by deterministic replay of ledger+scramble.
5. **Error bounds.** Mixed precision, compressed tables, symbolic kernels, and
   FFT/response libraries must ship interval/MPFR/Arb oracle tests and maximum
   relative/absolute error budgets tied to physics observables, not just unit
   arithmetic.
6. **Performance proof.** No speed claim is promoted without Phase 5 wall-time,
   step-time, cache-miss, branch-miss, and GPU occupancy evidence on all six
   canonical events.

## Section 5 -- Recommended Phase 8/9/10 redefinition

1. **Phase 8a: deterministic CPU/GPU free-win package.** Proposed files:
   `benchmarks/profiles/pgo/README.md`, `cmake/G4GPUOptimization.cmake`,
   `src/core/StaticLookupTables.*`, `tests/test_static_lookup_tables.cc`.
   Gate: exact lookup parity and full Phase 5 benchmark parity. Acceptance:
   PGO+LTO build documented; material/particle/process lookup tables are
   immutable; no validation regression; >=10% CPU speedup target. Estimate: 3
   worker-weeks.
2. **Phase 8b: geometry acceleration with exact fallback.** Proposed files:
   `src/geometry/BVHNavigator.*`, `src/geometry/BranchlessSolids.*`,
   `tests/test_bvh_navigation.cc`, `benchmarks/geometry_ray_audit.cc`. Gate:
   random-ray and boundary-stress tests reproduce the exact volume sequence or
   fall back. Acceptance: >=1.5x navigation speed on at least four benchmarks
   with zero topology mismatches. Estimate: 8 worker-weeks.
3. **Phase 8c: formal variance-reduction layer.** Proposed files:
   `src/variance/ImportanceMap.*`, `src/variance/SplittingRoulette.*`,
   `tests/test_variance_unbiasedness.cc`, `docs/validation/variance_reduction.md`.
   Gate: weighted analog-vs-biased mean agreement within bootstrap tolerance.
   Acceptance: >=5x effective sample-size gain for at least one rare-background
   benchmark with conserved expected weights. Estimate: 6 worker-weeks.
4. **Phase 8d: QMC transport experiment.** Proposed files:
   `src/random/SobolLedger.*`, `src/random/RandomizedQMC.*`,
   `tests/test_qmc_replay.cc`, `docs/validation/qmc_dimension_ledger.md`.
   Gate: ledger replay is deterministic; independent scrambles produce valid
   uncertainty estimates. Acceptance: >=3x variance reduction on smooth flagship
   observables without biased means. Estimate: 6 worker-weeks.
5. **Phase 9a: JIT/partial-evaluation prototype.** Proposed files:
   `src/jit/TransportSpecializer.*`, `src/jit/GeneratedKernelManifest.*`,
   `tests/test_jit_specializer.cc`. Gate: generated kernel hash is recorded;
   generic fallback always available. Acceptance: one muon-only or gamma-only
   benchmark has fixed-seed parity and >=1.5x CPU speedup. Estimate: 10
   worker-weeks.
6. **Phase 10 support: verified-numerics oracle, not production transport.**
   Proposed files: `tests/oracle/mpfr_cross_sections.py`,
   `tests/oracle/arb_geometry_boundaries.py`, `docs/validation/error_bounds.md`.
   Gate: every approximate table/precision change includes an oracle fixture.
   Acceptance: no approximate kernel lands without a physics-observable error
   budget. Estimate: 3 worker-weeks.

## References

- [R1] Geant4 Collaboration, "Geant4 -- a simulation toolkit," NIM A 506
  (2003), DOI 10.1016/S0168-9002(03)01368-8: https://impact.ornl.gov/en/publications/geant4-a-simulation-toolkit
- [R2] Geant4 documentation portal (living reference): https://geant4.org/docs/
- [R3] GeantV prototype results (2020): https://arxiv.org/abs/2005.00949
- [R4] Celeritas GPU particle transport (2022): https://arxiv.org/abs/2203.09467
- [R5] AdePT Geant4 R&D page (living project page): https://geant4.web.cern.ch/collaboration/working_groups/task_force_rd/g4rd14
- [R6] Blyth, "Opticks: GPU Optical Photon Simulation for Particle Physics using NVIDIA OptiX" (CHEP 2016): https://simoncblyth.github.io/env/report/opticks-blyth-chep2016.pdf
- [R7] Caflisch, "Monte Carlo and quasi-Monte Carlo methods" (1998): https://www.cambridge.org/core/services/aop-cambridge-core/content/view/FE7C779B350CFEA45DB2A4CCB2DA9B5C/S0962492900002804a.pdf/monte_carlo_and_quasimontecarlo_methods.pdf
- [R8] Niederreiter/Xing low-discrepancy sequences (1998): https://link.springer.com/chapter/10.1007/978-1-4612-1702-2_6
- [R9] MCNP 6.3 theory/user manual (2022): https://mcnp-green.lanl.gov/pdf_files/TechReport_2022_LANL_LA-UR-22-30006Rev.1_KuleszaAdamsEtAl.pdf
- [R10] Glynn and Szechtman, control variates (2002): https://web.stanford.edu/~glynn/papers/2002/GSzechtman02.html
- [R11] Xiu and Karniadakis polynomial chaos (2002): https://maths-people.anu.edu.au/~jakeman/QuantifyingUncertainty/Publications/year/2002.html
- [R12] MacDonald and Booth, SAH ray-tracing space subdivision (1990): https://dblp.org/rec/journals/vc/MacDonaldB90
- [R13] Bender, Demaine, Farach-Colton cache-oblivious B-trees (2000): https://erikdemaine.org/papers/FOCS2000b/
- [R14] Pagh and Rodler, cuckoo hashing (2001): https://tidsskrift.dk/brics/article/view/21692
- [R15] Kolda and Bader tensor decompositions (2009): https://www.kolda.net/publication/koba09/
- [R16] Bagwell HAMT/persistent maps overview (2001): https://infoscience.epfl.ch/entities/publication/b892b2ce-7bf0-41d2-b68c-fb44a3c64a33
- [R17] LLVM ORCv2 JIT docs (living reference): https://llvm.org/docs/ORCv2.html
- [R18] Vasilev et al., Cling C++ interpreter / ROOT 6 context (2012): https://cling.readthedocs.io/
- [R19] Futamura projection overview (2016): https://arxiv.org/abs/1611.09906
- [R20] FORM 4.0 (2012): https://arxiv.org/abs/1203.6543
- [R21] GCC optimization options (living compiler manual): https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html
- [R22] LLVM LTO docs (living compiler manual): https://www.llvm.org/docs/LinkTimeOptimization.html
- [R23] Blumofe and Leiserson, work stealing (1999): https://sites.cs.ucsb.edu/~cappello/190B/papers/CilkJACMp720-blumofe.pdf
- [R24] Agha actor model book (1986): https://osl.cs.illinois.edu/publications/books/daglib/0066897.html
- [R25] ISO coroutine technical specification N4680 (2017): https://isocpp.org/files/papers/n4680.pdf
- [R26] Higham and Mary mixed precision (2022): https://www.cambridge.org/core/journals/acta-numerica/article/mixed-precision-algorithms-in-numerical-linear-algebra/43CA701BA29251B5790C653E66F46197
- [R27] Moore, interval analysis (1966): https://openlibrary.org/works/OL14903880W/Interval_analysis
- [R28] Gustafson and Yonemoto posit arithmetic (2017): https://posithub.org/docs/BeatingFloatingPoint.pdf
- [R29] Fousse et al., MPFR multiple-precision library (2007): https://www.mpfr.org/
- [R30] Johansson, Arb ball arithmetic (2017): https://arxiv.org/abs/1611.02831
- [R31] Williams et al., robust ray-box intersection (2005): https://people.csail.mit.edu/amy/papers/box-jgt.pdf
- [R32] Vigna broadword rank/select (2008): https://vigna.di.unimi.it/ftp/papers/Broadword.pdf
- [R33] Baccelli et al., "Synchronization and Linearity" / min-plus algebra
  (1992), plus a living tropical-semiring reference: https://docs.oscar-system.org/v1.3/TropicalGeometry/semiring/
- [R34] Cooley and Tukey FFT reference (1965): https://www.ams.org/journals/mcom/1965-19-090/S0025-5718-1965-0178586-1/
- [R35] Candes, Romberg, Tao compressed sensing (2006): https://authors.library.caltech.edu/records/4xtrg-6sy14
- [R36] Donoho compressed sensing (2006): https://jrom.ece.gatech.edu/wp-content/uploads/sites/436/2011/04/donoho06co.pdf
- [R37] Vitter reservoir sampling (1985): https://www.cs.usfca.edu/~mmalensek/cs677/schedule/papers/vitter1985random.pdf
- [R38] Bloom filters (1970): https://www.cs.princeton.edu/courses/archive/spr05/cos598E/bib/p422-bloom.pdf
- [R39] Bennett reversible computation (1973): https://www.cs.princeton.edu/courses/archive/fall04/cos576/papers/bennett73.html
- [R40] CaloChallenge 2022 benchmark paper (2024): https://arxiv.org/abs/2410.21611
- [R41] CaloFlow (2021): https://arxiv.org/abs/2106.05285
- [R42] CaloDREAM (2024): https://arxiv.org/abs/2405.09629
- [R43] McMule documentation, "General aspects of using McMule" / VEGAS
  integration settings (living reference): https://mule-tools.gitlab.io/manual/general/

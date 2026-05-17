# G4GPU Phase 8 algorithm survey -- ranking, validation, packages, matrix, references

Split from `docs/reports/algorithm_survey_for_geant4.md` on 2026-05-17 to satisfy the 500-line file cap.
Owns Sections 2--5, appendices, ML methods, validation gates, and references R1--R47.

## Section 2 -- Ranking

Scores are ordinal and intentionally conservative: gain is a 1--5 score for expected
speedup or effective-sample-size improvement; validatability is a 1--5 score for how
directly the method can be proven equivalent or bounded; effort is worker-weeks
collapsed to a 1--10 score. The ranking score is `gain × validatability / effort`. Raw
rank is not the same as implementation order because tiny diagnostic wins are bundled
into larger packages.

The raw ranking confirms the strategy: start with free engineering wins, then move to
exact geometry acceleration and formal variance-reduction/QMC. Posits, reversible
computation, actors, and broad response surrogates are later research topics rather than
Phase 8 blockers.

| Rank | Method | Gain | Validatable | Effort | Score | Flag | Rationale |
|---:|---|---:|---:|---:|---:|---|---|
| 1 | PGO + LTO | 2 | 5 | 1 | 10.00 | FREE WIN | Do in Phase 5/8 baseline; no physics theory risk. |
| 2 | Perfect/cuckoo hashing | 2 | 5 | 2 | 5.00 | FREE WIN | Immutable lookup tables after initialization. |
| 3 | Tropical/min-plus step reduction | 2 | 5 | 2 | 5.00 | FREE WIN | Branchless exact chosen-limiter reduction. |
| 4 | Bloom prefilters with exact fallback | 2 | 5 | 2 | 5.00 | FREE-ISH | Safe only as a prefilter; pair with perfect hashing. |
| 5 | Reservoir diagnostics | 1 | 5 | 1 | 5.00 | DIAGNOSTIC | Observability win, not a physics accelerator. |
| 6 | Rank-1 lattice systematic ensembles | 3 | 4 | 3 | 4.00 | UQ | Outer systematic scans; low implementation cost. |
| 7 | Stratified/RR/splitting | 5 | 4 | 5 | 4.00 | PHASE 8 | Largest rare-event variance-reduction candidate. |
| 8 | Branchless SIMD surface tests | 3 | 5 | 4 | 3.75 | PHASE 8 | Strong exact-geometry engineering target. |
| 9 | PCE systematics | 5 | 3 | 4 | 3.75 | UQ | Powerful but not transport hot path. |
| 10 | QMC RNG ledger | 5 | 4 | 6 | 3.33 | PHASE 8 | High payoff; subtle reproducibility ledger. |
| 11 | Bit-parallel masks | 2 | 5 | 3 | 3.33 | BUNDLE | Fold into static lookup/BVH packages. |
| 12 | SAH-BVH geometry | 5 | 5 | 8 | 3.12 | PHASE 8 | Strategic high-impact geometry accelerator. |
| 13 | Control/antithetic variates | 3 | 4 | 4 | 3.00 | PHASE 8 | Pair with formal variance-reduction work. |
| 14 | Cache-oblivious layouts | 2 | 5 | 4 | 2.50 | BUNDLE | Bundle with SAH-BVH packed snapshots. |
| 15 | Compressed sensing hits | 3 | 3 | 4 | 2.25 | I/O | Output compression only. |
| 16 | Mixed precision + intervals | 3 | 4 | 6 | 2.00 | VALIDATION | Useful but oracle-heavy. |
| 17 | JIT specialization | 4 | 4 | 8 | 2.00 | PHASE 9 | Compiler risk; good after free wins. |
| 18 | Partial evaluation DSL | 5 | 4 | 10 | 2.00 | PHASE 9/10 | Long-term compiler moat. |
| 19 | Work stealing | 3 | 4 | 6 | 2.00 | PHASE 9 | After queue/SoA infrastructure. |
| 20 | Symbolic preprocessing | 3 | 4 | 6 | 2.00 | SELECTIVE | Formula-only kernels. |
| 21 | Immutable touchable histories | 2 | 5 | 5 | 2.00 | BUNDLE | Allocation/concurrency win with SoA. |
| 22 | FFT/NTT shower convolution | 4 | 3 | 6 | 2.00 | RESPONSE | Validated homogeneous response libraries. |
| 23 | Anyprecision / Arb/MPFR oracle | 1 | 5 | 3 | 1.67 | REQUIRED | Validation infrastructure, not speed. |
| 24 | Coroutines | 2 | 4 | 5 | 1.60 | PROTOTYPE | Only if frame allocation is controlled. |
| 25 | SVD/tensor cross-section tables | 3 | 3 | 6 | 1.50 | SELECTIVE | Smooth table blocks only. |
| 26 | Posits | 1 | 2 | 2 | 1.00 | WATCHLIST | No hardware path now. |
| 27 | Actor model | 2 | 3 | 8 | 0.75 | PHASE 9 | Coarse orchestration only. |
| 28 | Reversible computation | 1 | 3 | 8 | 0.38 | PHASE 10 | Differentiable future. |

### Defended ranking decisions

  - PGO/LTO wins first because it requires no physics-model change and provides an
    immediate baseline discipline for every later claim.
  - Perfect hashing, Bloom prefilters, and bitset masks are grouped because all require
    the same immutable id/key snapshot and can share parity tests.
  - Tropical/min-plus reductions are ranked highly not because the speedup is huge, but
    because the selected limiter can be compared exactly against vanilla Geant4.
  - Reservoir sampling is high-scoring but diagnostic-only; it should help profiling and
    trace capture, not become a flagship physics accelerator.
  - SAH-BVH is ranked below several smaller wins by raw score because implementation
    effort is high, but it remains one of the top strategic Phase 8 packages due to
    geometry’s large CPU share.
  - Formal variance reduction and QMC are the main deterministic alternatives to ML for
    rare or smooth observables; they reduce required event count rather than per-event
    wall time.
  - PCE and rank-1 lattices are excellent for systematic ensembles but should not be
    sold as Geant4 transport acceleration.
  - JIT and partial evaluation are attractive long-term because they can erase virtual
    dispatch and unused physics branches, but they require a stronger reproducibility
    and generated-code manifest than Phase 8 currently has.
  - Mixed precision belongs behind verified-numerics gates. It is unacceptable to trade
    boundary correctness for speed without interval or oracle evidence.
  - ML methods are deliberately absent from the deterministic ranking. They are
    evaluated separately in Section 3 because their validation failure modes are
    qualitatively different.

## Section 3 -- ML methods (SECONDARY)

> ML methods in HEP simulation face a permanent validation challenge: any
> distribution-level test only proves the model is correct on the tested
> distribution. Out-of-domain failure modes cannot be ruled out. For Geant4
> deployment the model must either: (a) be auditable to the same standard as
> a tabulated cross section, which no current architecture supports, or (b)
> only be used in regions where the deterministic method is impractical.

### ML-CaloChallenge

- **Evidence:** [R41]
- **Value:** A community benchmark for fast calorimeter simulation that compares shower
  quality, generation time, and model size across submitted generative models. It is
  useful because it defines common datasets and metrics, but the benchmark still
  validates only the sampled detector/domain, not all possible Geant4 states.
- **Validation blocker:** Agreement on finite distributions cannot prove correctness for
  untested geometries, materials, particles, energies, rare tails, or user cuts.
- **Acceptable role:** Use only as an evaluation template for response-library
  fallbacks. A G4GPU ML component would need an explicit domain envelope, deterministic
  fallback, and refusal behavior outside the benchmarked region.
- **Required gates:**
  - Version-pinned training data and generation code.
  - Out-of-domain detector and a deterministic fallback.
  - Reference Geant4 comparison on every deployed geometry/material/energy envelope.
  - Runtime monitoring of inputs so the surrogate cannot silently extrapolate.

### ML-CaloFlow and CaloFlow II

- **Evidence:** [R42,R43]
- **Value:** Normalizing-flow calorimeter shower generators show that learned densities
  can reproduce many calorimeter observables quickly and with tractable likelihoods.
  They are attractive for homogeneous response blocks but are still learned surrogates.
- **Validation blocker:** Agreement on finite distributions cannot prove correctness for
  untested geometries, materials, particles, energies, rare tails, or user cuts.
- **Acceptable role:** Consider only after FFT/response-table deterministic libraries
  fail or are too costly. Require held-out geometry, material, energy, and incident-
  angle coverage tests.
- **Required gates:**
  - Version-pinned training data and generation code.
  - Out-of-domain detector and a deterministic fallback.
  - Reference Geant4 comparison on every deployed geometry/material/energy envelope.
  - Runtime monitoring of inputs so the surrogate cannot silently extrapolate.

### ML-Transformer and diffusion hadronic/calorimeter samplers

- **Evidence:** [R44]
- **Value:** Autoregressive, vision-transformer, and diffusion-like samplers can model
  complex showers and correlations. They are powerful black-box density models, which is
  exactly the validation problem for Geant4 deployment.
- **Validation blocker:** Agreement on finite distributions cannot prove correctness for
  untested geometries, materials, particles, energies, rare tails, or user cuts.
- **Acceptable role:** Treat as Phase 10 research. Require a deterministic fallback,
  domain classifier, training-data manifest, calibration monitoring, and a policy that
  no model silently extrapolates.
- **Required gates:**
  - Version-pinned training data and generation code.
  - Out-of-domain detector and a deterministic fallback.
  - Reference Geant4 comparison on every deployed geometry/material/energy envelope.
  - Runtime monitoring of inputs so the surrogate cannot silently extrapolate.

## Section 4 -- Validation framework

### V1 Distribution agreement

  - Predeclare histograms: total deposited energy, leading-particle kinetic energy,
    multiplicity, vertex/entry position, per-detector hit counts, time distributions,
    weights, and process ids.
  - Use KS tests for one-dimensional unbinned or finely binned observables and energy-
    distance or MMD-style checks for multivariate summaries when needed.
  - Predeclare the primary one-dimensional KS threshold as corrected p >= 0.01, or
    equivalently D <= the two-sample critical value after the chosen multiple-test
    correction. Treat 0.01 <= corrected p < 0.05 as a warning band requiring
    independent rerun or physics-owner review; corrected p < 0.01 fails promotion.
  - Exact engineering changes remain stricter than KS: if fixed-seed step parity is
    expected, any bit/step mismatch fails even when all distribution tests pass.
  - Control multiple comparisons with a fixed false-discovery policy or Bonferroni-style
    threshold before looking at results.
  - Require KL or Jensen-Shannon divergence <= 1% only where binned densities have
    enough statistics; otherwise report bootstrap intervals and do not overinterpret
    sparse bins.

### V2 Bit-exact and step-exact parity

  - Engineering-only changes must be bit-exact under fixed seed wherever the operation
    order is unchanged.
  - If floating-point reordering is unavoidable, record max ULP/absolute differences and
    prove the selected branch/volume/process sequence is unchanged.
  - Step-level traces should include volume id, material id, process id, step limiter,
    pre/post position, kinetic energy, weight, and RNG ledger state.
  - No throughput claim can bypass step trace parity for the microbenchmarks most
    relevant to the changed code.

### V3 Weighted-estimator correctness

  - Variance-reduction methods must conserve expected weight through splitting,
    roulette, and importance changes.
  - Analog and biased estimators must be compared on paired benchmark problems with
    enough statistics to see variance reduction.
  - Downstream scorers must be audited for weight awareness before biased events are
    used.
  - Reports must include sum of weights, sum of weight squared, effective sample size,
    and confidence intervals.

### V4 QMC reproducibility

  - A QMC run is reproducible only if the sequence type, scramble/shift seed, dimension
    ledger, event/track dimension assignments, and fallback PRNG draws are recorded.
  - Independent scrambles provide error bars; deterministic low-discrepancy points alone
    do not.
  - Sequence-dimensional exhaustion or unledgered user random draws must fail closed.
  - Validation compares means and uncertainties against PRNG reference, not bit-
    identical event histories.

### V5 Out-of-domain coverage

  - Every approximate or surrogate method must declare its particle, energy, material,
    geometry, angle, and boundary-distance domain.
  - The runtime must detect out-of-domain inputs and fall back exactly.
  - Coverage tests must include adversarial boundaries, thresholds, rare secondary
    multiplicities, and extreme weights.
  - A domain miss is a correct fallback event, not a failure, as long as it is counted
    and reported.

### V6 Error bounds and oracle tests

  - Mixed precision, compressed tables, generated formulas, and response libraries
    require MPFR/Arb or equivalent oracle fixtures.
  - Document error bounds with interval arithmetic where possible; when interval
    containment is impossible, record the physical approximation envelope explicitly.
  - Error budgets must be attached to physics observables, not just scalar arithmetic
    operations.
  - Boundary and threshold grids must be denser than smooth regions.
  - Approximate kernels fail validation when oracle evidence is absent or stale.

### V7 Performance evidence

  - Use the Phase 5 benchmark suite: canonical Geant4 examples plus representative
    NNBAR-equivalent gamma, muon, nbar, cosmic, optical, and beam-neutron events.
  - Collect wall time, step time, perf cache-miss and branch-miss counters, allocation
    counts, and GPU occupancy when relevant.
  - Separate training profiles from validation profiles for PGO/LTO and specialization.
  - Report both per-event speedup and effective-sample-size gain; do not multiply them
    unless independent validation justifies it.

### V8 Reproducible manifests

  - Every promoted run stores code commit, compiler, flags, Geant4 version, physics
    list, random/QMC seed, geometry hash, table hash, and generated-code hash if
    applicable.
  - Benchmark artifacts must include scripts sufficient to rerun the reference and
    candidate.
  - A failed or missing manifest blocks the claim even if local tests pass.
  - Validation reports should be machine-readable enough for CI gates.

## Section 5 -- Recommended Phase 8/9/10 redefinition

### Top-five ranking-to-spec mapping

The top five raw ranking rows are implementation-scoped explicitly: PGO+LTO,
perfect/cuckoo hashing, tropical/min-plus step reduction, Bloom prefilters, and
reservoir diagnostics all land in Phase 8a. The reservoir item is diagnostic-only: it
must improve validation/profiling trace quality without changing physics transport.

### Phase 8a -- Deterministic free-win package

- **Files to produce:**
  - `cmake/G4GPUOptimization.cmake`
  - `benchmarks/profiles/pgo/README.md`
  - `src/core/StaticLookupTables.*`
  - `src/core/ExactPrefilter.*`
  - `src/core/ReservoirTraceSampler.*`
  - `tests/test_static_lookup_tables.cc`
  - `tests/test_step_limiter_reduction.cc`
  - `tests/test_reservoir_trace_sampling.cc`
- **Validation gate:** Exact lookup parity; fixed-seed event parity; ABI smoke tests;
  separate PGO training and validation profiles; reservoir trace sampling has fixed-size,
  seed-replayable diagnostic output and never feeds back into transport decisions.
- **Acceptance criteria:** PGO+LTO build documented; immutable lookup/prefilter tables
  built after initialization; selected limiter parity; reservoir diagnostics implemented as
  a no-physics-effect observability tool; >=10% CPU speedup target on at least four Phase
  5 CPU benchmarks.
- **Worker-week estimate:** 3 worker-weeks

### Phase 8b -- Geometry acceleration with exact fallback

- **Files to produce:**
  - `src/geometry/BVHNavigator.*`
  - `src/geometry/PackedNavigationSnapshot.*`
  - `src/geometry/BranchlessSolids.*`
  - `tests/test_bvh_navigation.cc`
  - `benchmarks/geometry_ray_audit.cc`
  - `docs/validation/geometry_acceleration.md`
- **Validation gate:** Random-ray and boundary-stress tests reproduce exact volume
  sequences or fall back; unsupported solids/replicas are fail-closed.
- **Acceptance criteria:** >=1.5x navigation speed on at least four benchmarks; zero
  topology mismatches; distribution gates pass on the full Phase 5 suite.
- **Worker-week estimate:** 8 worker-weeks

### Phase 8c -- Formal variance-reduction layer

- **Files to produce:**
  - `src/variance/ImportanceMap.*`
  - `src/variance/SplittingRoulette.*`
  - `src/variance/ControlVariates.*`
  - `tests/test_variance_unbiasedness.cc`
  - `docs/validation/variance_reduction.md`
- **Validation gate:** Weight-conservation tests; analog-vs-biased estimator agreement;
  scorer weight-awareness audit.
- **Acceptance criteria:** >=5x effective sample-size gain for at least one rare-
  background benchmark with conserved expected weights and documented confidence
  intervals.
- **Worker-week estimate:** 6 worker-weeks

### Phase 8d -- QMC transport experiment

- **Files to produce:**
  - `src/random/SobolLedger.*`
  - `src/random/RandomizedQMC.*`
  - `tests/test_qmc_replay.cc`
  - `tests/test_qmc_dimension_exhaustion.cc`
  - `docs/validation/qmc_dimension_ledger.md`
- **Validation gate:** Deterministic ledger replay; independent-scramble error bars;
  fail-closed user RNG and dimension-exhaustion handling.
- **Acceptance criteria:** >=3x variance reduction on smooth flagship observables
  without biased means; no claim for discontinuous/rare observables unless separately
  validated.
- **Worker-week estimate:** 6 worker-weeks

### Phase 9a -- JIT and partial-evaluation prototype

- **Files to produce:**
  - `src/jit/TransportSpecializer.*`
  - `src/jit/GeneratedKernelManifest.*`
  - `src/jit/TransportDSL.*`
  - `tests/test_jit_specializer.cc`
  - `docs/validation/generated_kernel_manifest.md`
- **Validation gate:** Generated-source hash recorded; compiler and flags pinned;
  generic fallback always available; fixed-seed step parity for supported subset.
- **Acceptance criteria:** One muon-only or gamma-only benchmark has fixed-seed parity
  and >=1.5x CPU speedup; unsupported effects fall back to generic transport.
- **Worker-week estimate:** 10 worker-weeks

### Phase 10a -- Verified-numerics oracle infrastructure

- **Files to produce:**
  - `tests/oracle/mpfr_cross_sections.py`
  - `tests/oracle/arb_geometry_boundaries.py`
  - `docs/validation/error_bounds.md`
  - `scripts/validate_oracle_fixtures.py`
- **Validation gate:** Oracle fixtures pinned and rerunnable; approximate kernels cannot
  merge without an oracle manifest.
- **Acceptance criteria:** Every compressed-table, mixed-precision, symbolic, or
  response-library proposal carries a physics-observable error budget and adversarial
  threshold/boundary tests.
- **Worker-week estimate:** 3 worker-weeks

### Phase 10b -- ML response-library fallback policy

- **Files to produce:**
  - `docs/validation/ml_surrogate_policy.md`
  - `src/surrogate/DomainEnvelope.*`
  - `tests/test_surrogate_fallback.cc`
  - `benchmarks/ml_response_holdout/README.md`
- **Validation gate:** Domain envelope detection; deterministic fallback; pinned
  training and validation data; no silent extrapolation.
- **Acceptance criteria:** ML only runs in declared domains where deterministic response
  libraries are impractical; every out-of-domain event falls back and is counted.
- **Worker-week estimate:** 6 worker-weeks for policy/prototype, excluding model
  training

## Appendix A -- Method-to-hot-path matrix

| Method | PIL | Geometry | DoIt | Stack/scheduler | Hit/I/O | Systematics/UQ | Validation role |
|---|---:|---:|---:|---:|---:|---:|---:|
| D01 Quasi-Monte Carlo: Sobol, Halton, Niederreiter sequences | Y |  | Y |  |  |  | Y |
| D02 Stratified sampling plus Russian roulette and splitting |  |  | Y | Y |  |  | Y |
| D03 Importance sampling with control variates and antithetic variates |  |  | Y |  |  |  | Y |
| D04 Korobov and rank-1 lattice rules |  |  |  |  |  | Y | Y |
| D05 Polynomial chaos expansion for uncertainty propagation |  |  |  |  |  | Y | Y |
| D06 SAH-BVH geometry |  | Y |  |  |  |  | Y |
| D07 Cache-oblivious BVH and navigation layouts |  | Y |  |  |  |  | Y |
| D08 Cuckoo and perfect hashing for material and particle lookup | Y |  |  |  |  |  | Y |
| D09 SVD and tensor decomposition compression of cross-section tables | Y |  |  |  |  |  | Y |
| D10 Persistent and immutable data structures for touchable history |  | Y |  | Y |  |  | Y |
| D11 JIT compilation via LLVM ORC or Cling | Y | Y | Y |  |  |  | Y |
| D12 Partial evaluation and Futamura-style specialization | Y |  | Y |  |  |  | Y |
| D13 Symbolic and computer-algebra preprocessing | Y |  | Y |  |  |  | Y |
| D14 Profile-guided optimization and link-time optimization | Y | Y | Y | Y | Y |  | Y |
| D15 Work-stealing schedulers |  |  |  | Y |  |  | Y |
| D16 Actor model and structured concurrency |  |  |  | Y | Y |  | Y |
| D17 C++20 coroutines for the transport state machine |  |  | Y | Y |  |  | Y |
| D18 Mixed precision with interval guards | Y | Y |  |  |  |  | Y |
| D19 Posit numbers |  |  |  |  |  |  | Watch |
| D20 Anyprecision / arbitrary precision and Arb/MPFR oracle paths |  |  |  |  |  |  | Oracle |
| D21 Branchless surface tests via SIMD comparison masks |  | Y |  |  |  |  | Y |
| D22 Bit-parallel popcount geometry and material queries | Y | Y |  |  |  |  | Y |
| D23 Tropical semiring and min-plus step-length computation | Y | Y |  |  |  |  | Y |
| D24 Number-theoretic transforms and FFT shower convolutions |  |  | Y |  |  |  | Y |
| D25 Compressed sensing for sparse hits |  |  |  |  | Y |  | Y |
| D26 Reservoir sampling for streaming hit collection |  |  |  |  | Diag |  | Diag |
| D27 Bloom filters for material and process caching | Y |  |  |  |  |  | Y |
| D28 Reversible computation and Bennett checkpointing |  |  |  | Y |  |  | Replay |

## Appendix B -- Acceptance checklist for this report

- **All 28 deterministic methods covered:** D01--D28 subsections in Section 1 each
  contain hot path, gain, validation, and effort.
- **Citations present:** References [R1]--[R47] cover Geant4, accelerators,
  deterministic methods, and ML benchmarks.
- **Section 2 explicit ranking:** The ranking table sorts by the declared score and
  includes a defended-ranking subsection.
- **ML disclaimer prominent:** Section 3 starts with the mandated disclaimer before any
  ML method details.
- **Validation framework mandatory:** Section 4 defines distribution, bit-exact,
  weighted, QMC, OOD, oracle, performance, and manifest gates.
- **At least five Phase 8+ specs:** Section 5 proposes seven concrete packages with
  files, gates, acceptance criteria, and worker-week estimates.
- **Validation-first recommendations:** Every proposal states how physics equivalence,
  unbiasedness, or error bounds will be demonstrated.

## References

- [R1] Geant4 Collaboration, "Geant4 -- a simulation toolkit," NIM A 506 (2003), DOI
  10.1016/S0168-9002(03)01368-8:
  https://impact.ornl.gov/en/publications/geant4-a-simulation-toolkit
- [R2] Geant4 documentation portal and application guides: https://geant4.org/docs/
- [R3] Geant4/CLHEP HepJamesRandom class specification:
  https://geant4-internal.web.cern.ch/ooaandd/design/class_spec/global/randomclassspec
- [R4] GeantV prototype paper: https://arxiv.org/abs/2005.00949
- [R5] Celeritas GPU particle transport roadmap: https://arxiv.org/abs/2203.09467
- [R6] AdePT Geant4 R&D page:
  https://geant4.web.cern.ch/collaboration/working_groups/task_force_rd/g4rd14
- [R7] AdePT electromagnetic shower offload paper: https://arxiv.org/abs/2209.15445
- [R8] Opticks GPU optical-photon report:
  https://simoncblyth.github.io/env/report/opticks-blyth-chep2016.pdf
- [R9] Caflisch, Monte Carlo and quasi-Monte Carlo methods:
  https://www.cambridge.org/core/services/aop-cambridge-core/content/view/FE7C779B350CFEA45DB2A4CCB2DA9B5C/S0962492900002804a.pdf/monte_carlo_and_quasimonte_carlo_methods.pdf
- [R10] MCNP 6.3 theory/user manual: https://mcnp-green.lanl.gov/pdf_files/TechReport_2022_LANL_LA-UR-22-30006Rev.1_KuleszaAdamsEtAl.pdf
- [R11] Glasserman and Szechtman, control variates and variance reduction:
  https://web.stanford.edu/~glynn/papers/2002/GSzechtman02.html
- [R12] LatticeBuilder rank-1 lattice rules paper: https://arxiv.org/abs/1608.06377
- [R13] Xiu and Karniadakis generalized polynomial chaos: https://maths-people.anu.edu.au/~jakeman/QuantifyingUncertainty/Publications/year/2002.html
- [R14] MacDonald and Booth surface-area heuristic BVH record:
  https://dblp.org/rec/journals/vc/MacDonaldB90
- [R15] Bender, Demaine, and Farach-Colton cache-oblivious B-trees:
  https://erikdemaine.org/papers/FOCS2000b/
- [R16] Pagh and Rodler cuckoo hashing: https://tidsskrift.dk/brics/article/view/21692
- [R17] Kolda and Bader tensor decompositions and applications:
  https://www.kolda.net/publication/koba09/
- [R18] Bagwell HAMT / ideal hash trees:
  https://infoscience.epfl.ch/entities/publication/b892b2ce-7bf0-41d2-b68c-fb44a3c64a33
- [R19] LLVM ORCv2 JIT documentation: https://llvm.org/docs/ORCv2.html
- [R20] ROOT Cling C++ interpreter manual: https://root.cern/manual/cling/
- [R21] Futamura projection and partial evaluation overview:
  https://arxiv.org/abs/1611.09906
- [R22] FORM 4.0 symbolic manipulation system: https://arxiv.org/abs/1203.6543
- [R23] GCC optimization options including profile feedback:
  https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html
- [R24] LLVM link-time optimization documentation:
  https://www.llvm.org/docs/LinkTimeOptimization.html
- [R25] Blumofe and Leiserson work-stealing scheduler:
  https://supertech.mit.edu/biblio/scheduling-multithreaded-computations-work-stealing/
- [R26] Agha actor model book record:
  https://osl.cs.illinois.edu/publications/books/daglib/0066897.html
- [R27] ISO C++ coroutine technical specification N4680:
  https://isocpp.org/files/papers/n4680.pdf
- [R28] Higham and Mary mixed-precision algorithms:
  https://www.cambridge.org/core/journals/acta-numerica/article/mixed-precision-algorithms-in-numerical-linear-algebra/43CA701BA29251B5790C653E66F46197
- [R29] Gustafson and Yonemoto posit arithmetic:
  https://posithub.org/docs/BeatingFloatingPoint.pdf
- [R30] GNU MPFR library: https://www.mpfr.org/
- [R31] Arb ball arithmetic paper: https://arxiv.org/abs/1611.02831
- [R32] Williams et al., robust ray-box intersection:
  https://people.csail.mit.edu/amy/papers/box-jgt.pdf
- [R33] Vigna, broadword rank/select queries:
  https://vigna.di.unimi.it/ftp/papers/Broadword.pdf
- [R34] OSCAR documentation for tropical semirings: https://docs.oscar-system.org/v1.3/TropicalGeometry/semiring/
- [R35] Cooley and Tukey FFT paper:
  https://www.ams.org/journals/mcom/1965-19-090/S0025-5718-1965-0178586-1/
- [R36] Candes, Romberg, and Tao compressed sensing: https://arxiv.org/abs/math/0409186
- [R37] Donoho compressed sensing: https://jrom.ece.gatech.edu/wp-content/uploads/sites/436/2011/04/donoho06co.pdf
- [R38] Vitter reservoir sampling:
  https://dsf.berkeley.edu/cs286/papers/reservoirsampling-toms1985.pdf
- [R39] Bloom filters original CACM paper:
  https://www.cs.princeton.edu/courses/archive/spr05/cos598E/bib/p422-bloom.pdf
- [R40] Bennett logical reversibility of computation:
  https://www.cs.princeton.edu/courses/archive/fall04/cos576/papers/bennett73.html
- [R41] CaloChallenge 2022 community benchmark: https://arxiv.org/abs/2410.21611
- [R42] CaloFlow normalizing-flow shower generation: https://arxiv.org/abs/2106.05285
- [R43] CaloFlow II: https://arxiv.org/abs/2110.11377
- [R44] CaloDREAM transformer calorimeter generation: https://arxiv.org/abs/2405.09629
- [R45] Sherpa event-generator documentation: https://sherpa-team.gitlab.io/
- [R46] Vegas revisited: adaptive Monte Carlo beyond factorization:
  https://arxiv.org/abs/hep-ph/9806432
- [R47] McMule general manual, statistics section:
  https://mule-tools.gitlab.io/manual/general/

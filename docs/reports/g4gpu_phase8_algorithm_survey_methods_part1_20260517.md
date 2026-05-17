# G4GPU Phase 8 algorithm survey -- deterministic methods part 1

Split from `docs/reports/algorithm_survey_for_geant4.md` on 2026-05-17 to satisfy the 500-line file cap.
Owns methods D01--D14. See the index for executive summary, split manifest, and top ranking table.

## Section 1 -- Deterministic methods (PRIMARY)

Each entry includes: method definition, existing field of use, why Geant4 has not adopted it deeply, target hot path, expected gain, implementation sketch, validation plan, risks, and worker-week estimate.

### D01 -- Quasi-Monte Carlo: Sobol, Halton, Niederreiter sequences

- **Evidence:** [R3,R9,R45,R46,R47]
- **What it is:** Replace independent pseudo-random points with low-discrepancy
  deterministic or randomized-low-discrepancy point sets. The mathematical promise is
  lower integration error for low-effective-dimension smooth observables; it is not a
  faster step kernel by itself.
- **Where it is used:** Numerical integration, rendering, finance, uncertainty
  quantification, and collider-event phase-space integration experiments. Sherpa is
  the collider-generator reference to audit for production adaptive/QMC integration.
  The checked McMule manual documents adaptive VEGAS over pseudo-random points rather
  than a first-class QMC mode, so any external claim that "McMule uses QMC" must be
  source-audited before publication; for this survey it is treated as an adjacent
  high-energy phase-space integration comparator.
- **Why it is not already a Geant4 default:** Geant4 random dimensions are consumed
  through deep, data-dependent process calls; secondaries branch; user actions may draw
  random numbers; and default reproducibility assumptions are tied to CLHEP pseudo-
  random engines. A QMC engine therefore needs a dimension ledger rather than a simple
  drop-in RNG swap.
- **Geant4 hot path attacked:** Sampling in PIL and DoIt, rare-background tallies, outer
  analysis estimators; not geometry or I/O.
- **Back-of-envelope gain:** 3--20x fewer events for smooth flagship observables; 1.0x
  per-event speed.
- **Implementation sketch:**
  - Add a Geant4-compatible `RandomizedQMC` adapter with Sobol and Niederreiter
    backends.
  - Assign each track a deterministic dimension ledger keyed by process, material, and
    secondary rank.
  - Start with independent randomized scrambles per event batch so error bars remain
    meaningful.
  - Keep CLHEP PRNG as the default fallback for user actions or unledgered process
    calls.
- **Validation strategy:**
  - Ledger replay must be deterministic for a fixed scramble seed.
  - Analog PRNG and QMC means must agree within bootstrap intervals on the Phase 5
    benchmark suite.
  - Independent scrambles must yield honest uncertainty estimates; plain deterministic
    QMC error bars are not enough.
  - Audit random-dimension exhaustion and branching with synthetic showers before
    claiming physics validity.
- **Failure modes / review risks:**
  - High-dimensional branching can erase the theoretical advantage.
  - Changing sample order can break bit-exact legacy comparisons even when estimates are
    unbiased.
  - A reviewer will reject any QMC result without a clear reproducibility ledger.
- **Effort estimate:** 6 worker-weeks

### D02 -- Stratified sampling plus Russian roulette and splitting

- **Evidence:** [R10]
- **What it is:** Bias the sampling effort toward important phase-space regions, split
  tracks entering high-importance regions, and roulette tracks entering low-importance
  regions while preserving expected weight.
- **Where it is used:** Reactor, shielding, medical-dose, and rare-event Monte Carlo
  transport.
- **Why it is not already a Geant4 default:** Geant4 is intentionally general-purpose
  and usually lacks a problem-specific importance map. Detector simulations also prefer
  unweighted event records, so weight propagation must be explicit and auditable.
- **Geant4 hot path attacked:** Sampling and stack management for rare neutron,
  skyshine, cosmic, and deep-shielding backgrounds.
- **Back-of-envelope gain:** 5--100x variance reduction on rare tallies when an
  importance map is known; no gain on inclusive observables.
- **Implementation sketch:**
  - Introduce immutable importance regions with material, volume, energy, and direction
    bins.
  - Implement weight-conserving split and roulette policies at boundaries and process
    exits.
  - Store track weights in the accelerated event record and output schema.
  - Provide an analog transport mode for paired validation runs.
- **Validation strategy:**
  - Expected weight must be conserved over boundary crossings and process decisions.
  - Analog and biased estimators must agree within predeclared confidence intervals.
  - Effective sample size must improve on at least one rare-background benchmark.
  - All scoring code must consume weights; unweighted histograms become invalid.
- **Failure modes / review risks:**
  - Bad importance maps can increase variance.
  - Weighted secondaries complicate downstream user analysis.
  - The method is validatable but experiment-specific, so it should be opt-in.
- **Effort estimate:** 5 worker-weeks

### D03 -- Importance sampling with control variates and antithetic variates

- **Evidence:** [R11]
- **What it is:** Use correlated estimators to cancel fluctuations or draw from a more
  useful distribution while correcting the estimator exactly.
- **Where it is used:** Stochastic simulation, finance, queueing theory, and first-order
  transport approximations.
- **Why it is not already a Geant4 default:** Geant4 physics kernels are heterogeneous;
  many lack a simple analytic control variate. Negative or correlated weights also
  require careful output semantics.
- **Geant4 hot path attacked:** DoIt final-state sampling and final analysis tallies
  where analytic approximations exist.
- **Back-of-envelope gain:** 2--10x variance reduction for observables with a strong
  first-order model.
- **Implementation sketch:**
  - Prototype antithetic pairing for symmetric angular and energy samplers.
  - Add optional control tallies from CSDA range, Bethe-Bloch mean loss, or analytic
    attenuation.
  - Keep primary event generation unchanged; attach variance-reduction metadata to
    tallies.
  - Promote only controls with a documented covariance gain on Phase 5 outputs.
- **Validation strategy:**
  - Unbiasedness tests over controlled toy samplers.
  - Variance-ratio confidence intervals against analog transport.
  - No promotion if the control changes event records rather than only estimators.
  - Pairing must not reorder random draws in a way that breaks replay.
- **Failure modes / review risks:**
  - Observable-specific engineering limits generality.
  - Poor controls add overhead and no gain.
  - Negative covariance assumptions can fail in discontinuous detector selections.
- **Effort estimate:** 4 worker-weeks

### D04 -- Korobov and rank-1 lattice rules

- **Evidence:** [R9,R12]
- **What it is:** Evaluate integrals on structured lattice points, often with random
  shifts for uncertainty estimates. This is most attractive for outer systematic scans
  rather than inner stochastic transport.
- **Where it is used:** Quasi-Monte Carlo integration, especially low-dimensional smooth
  parameter integrals.
- **Why it is not already a Geant4 default:** Track-level branching makes fixed lattice
  dimensions brittle. Detector systematic parameters are lower-dimensional and have more
  stable dimensions.
- **Geant4 hot path attacked:** Systematic-throw ensembles, calibration response scans,
  and material-uncertainty propagation.
- **Back-of-envelope gain:** 3--30x fewer systematic samples for smooth low-effective-
  dimension scans.
- **Implementation sketch:**
  - Implement shifted rank-1 lattice designs in the benchmark driver, not inside Geant4
    first.
  - Map material scale, calibration, and alignment parameters onto lattice dimensions.
  - Use multiple independent shifts for error bars.
  - Feed resulting parameter points to unchanged Geant4 runs.
- **Validation strategy:**
  - Holdout pseudo-random ensembles must agree within confidence intervals.
  - Random shifts must produce stable error estimates.
  - Discontinuous cut-based observables require stratification or fallback.
  - The lattice generator and seed must be stored in the run manifest.
- **Failure modes / review risks:**
  - Not an event-throughput improvement.
  - Can fail badly for high-effective-dimension or discontinuous responses.
  - Needs a clean benchmark manifest before publication.
- **Effort estimate:** 3 worker-weeks

### D05 -- Polynomial chaos expansion for uncertainty propagation

- **Evidence:** [R13]
- **What it is:** Approximate output observables as polynomial expansions in uncertain
  inputs, replacing many Monte Carlo systematic throws with a fitted or projected
  surrogate.
- **Where it is used:** CFD, uncertainty quantification, sensitivity analysis, and
  surrogate response models for smooth parameter spaces.
- **Why it is not already a Geant4 default:** Particle transport randomness is high-
  dimensional and discontinuous, but detector calibration/material systematics are often
  low-dimensional and smooth enough to model.
- **Geant4 hot path attacked:** Outer uncertainty propagation, not per-step transport.
- **Back-of-envelope gain:** 10--100x fewer full Geant4 runs for smooth systematic
  envelopes.
- **Implementation sketch:**
  - Define a small vector of validated systematic knobs for Phase 5 benchmarks.
  - Run a sparse quadrature or regression design over those knobs.
  - Fit non-intrusive PCE models for final observables and acceptance ratios.
  - Publish Sobol sensitivity indices to show which parameters dominate.
- **Validation strategy:**
  - Holdout points must be within predeclared residual tolerances.
  - PCE uncertainty must include regression and transport statistical errors.
  - Discontinuous observables need adaptive basis or fail closed.
  - No event-level physics claim may be made from PCE alone.
- **Failure modes / review risks:**
  - Excellent for UQ but not a Geant4 hot-path accelerator.
  - Surrogate validity is local to the scanned parameter domain.
  - Reviewers may treat it as a response model, not transport improvement.
- **Effort estimate:** 4 worker-weeks

### D06 -- SAH-BVH geometry

- **Evidence:** [R1,R2,R5,R8,R14]
- **What it is:** Build a bounding-volume hierarchy whose splits minimize an estimated
  surface-area traversal cost. Use it to narrow candidate solids before exact
  Geant4-compatible boundary checks.
- **Where it is used:** Production ray tracing, collision detection, GPU ray traversal,
  and OptiX-style geometry acceleration.
- **Why it is not already a Geant4 default:** Geant4 geometry includes placements,
  parameterisations, replicas, touchables, tolerances, and user extension points. A
  graphics BVH over triangles is not enough.
- **Geant4 hot path attacked:** Geometry navigation and boundary distance calculation.
- **Back-of-envelope gain:** 1.5--5x navigation speed on complex static geometry;
  possibly more on GPU RT-like traversal.
- **Implementation sketch:**
  - Export immutable candidate solid bounding volumes after geometry close.
  - Build per-region SAH BVHs with compact node arrays.
  - Use BVH only as a candidate filter; exact solid distance and navigator semantics
    remain authoritative.
  - Fallback to vanilla navigation near tolerance boundaries, replicas, or unsupported
    solids.
- **Validation strategy:**
  - Random-ray volume sequence must match vanilla Geant4 exactly or report fallback.
  - Boundary stress tests must cover points within tolerance of every supported solid.
  - Perf counters must show fewer candidate solid tests and lower navigation time.
  - Canonical benchmarks must pass distribution gates after the navigation swap.
- **Failure modes / review risks:**
  - Topology mismatches are catastrophic; exact fallback is non-negotiable.
  - Dynamic geometry or parameterisations can invalidate the hierarchy.
  - Upstream acceptance requires a minimal, isolated navigator interface.
- **Effort estimate:** 8 worker-weeks

### D07 -- Cache-oblivious BVH and navigation layouts

- **Evidence:** [R15]
- **What it is:** Lay out tree and navigation data so traversal has good cache behavior
  without tuning for one cache size. For BVHs this means compact node arrays and vEB-
  like ordering.
- **Where it is used:** Databases, external-memory search trees, mesh layouts, and
  cache-efficient indexing.
- **Why it is not already a Geant4 default:** Geant4 object graphs prioritize
  flexibility and polymorphism; cache-oblivious layouts require immutable packed views
  built after initialization.
- **Geant4 hot path attacked:** Geometry navigation, material lookup, touchable-history
  reads.
- **Back-of-envelope gain:** 1.2--2x from lower cache misses; stacks with SAH-BVH.
- **Implementation sketch:**
  - Create a packed `NavigationSnapshot` after geometry closure.
  - Store BVH nodes, material ids, and transform ids in contiguous arrays.
  - Use cache-oblivious ordering for deep trees and SoA arrays for vectorized traversal.
  - Keep original Geant4 objects as provenance and fallback.
- **Validation strategy:**
  - Cache-miss and branch-miss counters must improve on Phase 5 geometry probes.
  - All packed ids must round-trip to original Geant4 volumes and materials.
  - Snapshot hashes must change when geometry changes.
  - Distribution tests must not see differences beyond documented FP ordering.
- **Failure modes / review risks:**
  - Memory duplication can hurt small geometries.
  - The layout is only safe after geometry becomes immutable.
  - The gain is engineering-heavy and workload-dependent.
- **Effort estimate:** 4 worker-weeks

### D08 -- Cuckoo and perfect hashing for material and particle lookup

- **Evidence:** [R16]
- **What it is:** Replace repeated map lookups with prebuilt constant-time tables once
  the set of materials, particles, regions, and processes is frozen.
- **Where it is used:** Databases, compilers, packet routing, and immutable runtime
  dictionaries.
- **Why it is not already a Geant4 default:** Geant4 allows user code to register
  materials and processes during initialization. The safe point for perfect tables is
  after run-manager initialization, with a mutation barrier.
- **Geant4 hot path attacked:** Material, isotope, particle, process, cut, and scorer
  lookup.
- **Back-of-envelope gain:** 1.1--1.8x in lookup-heavy stepping and scoring paths;
  strong "free win" potential.
- **Implementation sketch:**
  - Inventory lookup keys touched in Phase 5 profiles.
  - Generate immutable minimal/perfect tables at initialization close.
  - Keep exact map fallback for debug mode and unsupported mutation.
  - Expose a table manifest with key count, hash seed, and collision-free proof.
- **Validation strategy:**
  - Exhaustive key parity against original maps.
  - Mutation attempts after table seal must fail loudly or rebuild tables.
  - Profile counters must show fewer comparisons and allocations.
  - Fixed-seed event records must be bit-identical.
- **Failure modes / review risks:**
  - Low gain if maps are not hot in real profiles.
  - Thread-local or user-defined registries need special handling.
  - Perfect-hash construction time must not dominate short jobs.
- **Effort estimate:** 2 worker-weeks

### D09 -- SVD and tensor decomposition compression of cross-section tables

- **Evidence:** [R17]
- **What it is:** Compress smooth multidimensional cross-section and response tables
  into low-rank factors while preserving interpolation accuracy.
- **Where it is used:** Scientific data compression, recommender systems, signal
  processing, and reduced-order models.
- **Why it is not already a Geant4 default:** Physics tables contain thresholds,
  resonances, discontinuities, and monotonicity constraints. A low-rank approximation is
  only acceptable where error bounds are tight.
- **Geant4 hot path attacked:** PIL cross-section interpolation and GPU memory
  bandwidth.
- **Back-of-envelope gain:** 1.2--3x for bandwidth-limited smooth table blocks; no gain
  near exact preserved thresholds.
- **Implementation sketch:**
  - Classify tables into smooth, threshold, resonance, and discontinuous blocks.
  - Compress only smooth blocks offline with max-error and monotonicity constraints.
  - Generate exact-preserved guard bands around thresholds.
  - Add a runtime switch to compare compressed and original table values.
- **Validation strategy:**
  - Max absolute and relative error budgets per table.
  - Monotonicity and positivity tests after decompression.
  - MPFR or double-precision oracle comparisons on dense grids.
  - Benchmark distributions must match reference within KS/KL gates.
- **Failure modes / review risks:**
  - A small cross-section error can amplify in thin rare processes.
  - Compression is hard to justify for hadronic resonance tables.
  - Implementation belongs behind a fail-closed validation manifest.
- **Effort estimate:** 6 worker-weeks

### D10 -- Persistent and immutable data structures for touchable history

- **Evidence:** [R18]
- **What it is:** Represent histories and configuration views as shared immutable paths
  so child tracks can reuse state instead of copying mutable object chains.
- **Where it is used:** Functional runtimes, databases, immutable snapshots, and
  concurrent data sharing.
- **Why it is not already a Geant4 default:** Geant4 touchables and tracks are mutable
  C++ objects with longstanding APIs. A persistent representation must be introduced as
  an internal snapshot, not a user-visible break.
- **Geant4 hot path attacked:** Touchable-history copies, secondary creation, stack
  transfer, and multi-threaded sharing.
- **Back-of-envelope gain:** 1.1--1.5x plus lower allocation pressure and easier
  concurrency.
- **Implementation sketch:**
  - Intern immutable volume-parent paths and transforms after geometry close.
  - Store tracks with references to interned histories instead of deep copies.
  - Use reference-counted or arena-owned nodes with deterministic lifetimes.
  - Expose conversion helpers back to Geant4 touchable APIs.
- **Validation strategy:**
  - Volume ancestry must match original touchables exactly.
  - Allocation counts per step and per secondary must drop.
  - Fixed-seed event parity is mandatory.
  - Thread sanitizer and lifetime tests must run on stress showers.
- **Failure modes / review risks:**
  - API compatibility is delicate.
  - Reference counting can erase performance gains if too granular.
  - Best bundled with SoA track work rather than standalone.
- **Effort estimate:** 5 worker-weeks

### D11 -- JIT compilation via LLVM ORC or Cling

- **Evidence:** [R19,R20]
- **What it is:** Generate or specialize code at runtime for the actual detector,
  particle set, cuts, and physics list, then compile it to native code before the event
  loop.
- **Where it is used:** Language runtimes, ROOT/CERN analysis workflows, shader
  compilers, and scientific DSLs.
- **Why it is not already a Geant4 default:** Geant4 plugin ABI, reproducibility,
  security, build portability, and experiment validation all resist runtime code
  generation.
- **Geant4 hot path attacked:** Process dispatch, geometry branch elimination, and
  particle-specific stepping kernels.
- **Back-of-envelope gain:** 1.3--4x for single-particle or restricted-physics kernels;
  unknown for full hadronic events.
- **Implementation sketch:**
  - Start with a manifest-driven offline/JIT hybrid that emits C++ for one muon-only
    kernel.
  - Compile through LLVM ORC or Cling in a sandboxed build directory.
  - Record generated source, compiler flags, module versions, and object hash.
  - Always keep the generic Geant4 fallback path available.
- **Validation strategy:**
  - Generated and generic kernels must match fixed-seed step records.
  - The generated-source hash must be stable and archived.
  - Fallback must activate on unsupported processes or user hooks.
  - Compiler/version changes require validation cache invalidation.
- **Failure modes / review risks:**
  - ABI and reproducibility risks are larger than algorithmic risks.
  - Runtime compilation overhead may dominate small jobs.
  - Upstream Geant4 may accept static specialization more readily than JIT.
- **Effort estimate:** 8 worker-weeks

### D12 -- Partial evaluation and Futamura-style specialization

- **Evidence:** [R21]
- **What it is:** Separate static detector/physics-list data from dynamic track data,
  then specialize the generic transport program with respect to the static part.
- **Where it is used:** Compiler theory, interpreters, DSLs, and staged computation.
- **Why it is not already a Geant4 default:** Geant4 does not expose a small pure
  interpreter over transport semantics; static and dynamic effects are interleaved
  through object-oriented calls.
- **Geant4 hot path attacked:** Particle-specialized stepping, process-selection
  dispatch, and GPU kernel generation.
- **Back-of-envelope gain:** 1.5--5x if static boundaries can be extracted cleanly.
- **Implementation sketch:**
  - Define a minimal transport DSL for one particle family and a small set of processes.
  - Mark geometry, cuts, and process tables as static inputs.
  - Generate specialized C++/CUDA kernels from the DSL.
  - Differential-test generated kernels against the generic interpreter.
- **Validation strategy:**
  - Semantics tests for every DSL primitive against Geant4.
  - Generated kernel differential tests over random tracks and materials.
  - Proof-style documentation of static/dynamic boundaries.
  - Fallback for every effect not represented in the DSL.
- **Failure modes / review risks:**
  - High design cost before first speedup.
  - Only a subset of Geant4 may be representable at first.
  - The payoff is large but belongs after Phase 8 free wins.
- **Effort estimate:** 10 worker-weeks

### D13 -- Symbolic and computer-algebra preprocessing

- **Evidence:** [R22,R30,R31]
- **What it is:** Use FORM, Mathematica, Maple, or similar systems to simplify analytic
  cross-section expressions and generate optimized C/CUDA code with error guards.
- **Where it is used:** NLO/NNLO QCD, symbolic manipulation, code generation, and
  verified formula evaluation.
- **Why it is not already a Geant4 default:** Many Geant4 hadronic models are empirical,
  tabular, or procedural rather than closed-form analytic expressions.
- **Geant4 hot path attacked:** Formula-heavy EM and low-level differential cross-
  section samplers.
- **Back-of-envelope gain:** 1.1--3x where closed forms exist; none for empirical
  cascades.
- **Implementation sketch:**
  - Inventory formula-heavy kernels in EM/gamma and muon phases.
  - Generate branch-minimized code from symbolic expressions.
  - Compare generated code to MPFR/Arb oracle evaluations.
  - Use generated code only behind the original physics-model interface.
- **Validation strategy:**
  - Pointwise oracle comparisons over the full domain.
  - Interval bounds on approximation and rounding error.
  - Distribution parity on benchmark outputs that use the formula.
  - Generated source and CAS scripts must be archived.
- **Failure modes / review risks:**
  - CAS output can be fast but opaque unless scripts are reviewed.
  - Hadronic models may have too little analytic structure.
  - Code generation must preserve units and Geant4 conventions.
- **Effort estimate:** 6 worker-weeks

### D14 -- Profile-guided optimization and link-time optimization

- **Evidence:** [R23,R24]
- **What it is:** Build Geant4 or the G4GPU CPU fallback with representative profiles
  and LTO so the compiler can inline, devirtualize, and layout code more effectively.
- **Where it is used:** Production compiler engineering and whole-program optimization.
- **Why it is not already a Geant4 default:** Experiment software stacks often favor
  reproducible portable builds over profile-specific optimization. Geant4 plugins and
  dynamic libraries reduce whole-program visibility.
- **Geant4 hot path attacked:** Whole CPU fallback: PIL, geometry, process dispatch,
  stack, and I/O.
- **Back-of-envelope gain:** 10--30% CPU speedup is a realistic free-win target;
  profile-dependent.
- **Implementation sketch:**
  - Use Phase 5 benchmark suite to collect training profiles.
  - Add documented `Release+PGO+LTO` CMake presets for G4GPU and upstreamable Geant4
    patches.
  - Keep baseline release builds for comparison.
  - Record compiler, flags, profile input, and binary hash.
- **Validation strategy:**
  - Fixed-seed event output should be identical except for documented FP reordering.
  - ABI smoke tests must load common examples and plugins.
  - Training and validation benchmarks must be separated.
  - No speedup claim without wall-time and perf-counter evidence.
- **Failure modes / review risks:**
  - Profile mismatch can hurt workloads outside the training suite.
  - Compiler-specific behavior affects reproducibility.
  - Despite low theory risk, this still needs formal benchmark discipline.
- **Effort estimate:** 1 worker-week


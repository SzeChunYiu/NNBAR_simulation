# G4GPU Phase 8 algorithm survey -- deterministic methods part 2

Split from `docs/reports/algorithm_survey_for_geant4.md` on 2026-05-17 to satisfy the 500-line file cap.
Owns methods D15--D28. See the index for executive summary, split manifest, and top ranking table.

### D15 -- Work-stealing schedulers

- **Evidence:** [R25]
- **What it is:** Use per-worker deques and stealing to balance dynamic secondary
  showers instead of assigning whole events or coarse chunks to fixed workers.
- **Where it is used:** Cilk/TBB-style task runtimes, dynamic parallelism, graph
  algorithms, and irregular computation.
- **Why it is not already a Geant4 default:** Geant4 event-level multithreading is
  simpler and reproducible. Fine-grained stealing can reorder tracks and expose latent
  thread-safety assumptions.
- **Geant4 hot path attacked:** Track stack, secondary bursts, shower tails, and
  heterogeneous CPU/GPU queues.
- **Back-of-envelope gain:** 1.2--3x load-balance improvement on shower-heavy workloads.
- **Implementation sketch:**
  - Implement deterministic-replay work stealing for G4GPU track queues first.
  - Use per-species queues to improve cache and warp coherence.
  - Capture scheduler traces for debugging.
  - Keep event-level MT as a compatibility mode.
- **Validation strategy:**
  - Fixed-seed replay mode must reproduce the same event record.
  - Scheduler traces must be stable under controlled worker counts.
  - Load-balance metrics must improve without raising synchronization overhead.
  - Race detectors and stress tests are mandatory.
- **Failure modes / review risks:**
  - Parallel order can change floating-point accumulation.
  - Fine-grained tasks can increase overhead on simple events.
  - Requires prior SoA/queue infrastructure.
- **Effort estimate:** 6 worker-weeks

### D16 -- Actor model and structured concurrency

- **Evidence:** [R26]
- **What it is:** Represent transport services as actors or structured tasks with
  explicit message flow, backpressure, and lifecycle management.
- **Where it is used:** Distributed systems, message-passing runtimes, fault isolation,
  and pipeline orchestration.
- **Why it is not already a Geant4 default:** Actor messages add overhead to tight
  stepping loops, and Geant4 APIs assume synchronous call stacks in many places.
- **Geant4 hot path attacked:** System-level orchestration: scoring, hit streaming,
  CPU/GPU handoff, and I/O latency hiding.
- **Back-of-envelope gain:** 1.1--2x mostly from pipeline overlap, not inner-loop speed.
- **Implementation sketch:**
  - Limit actors to coarse services: GPU transport partition, hit writer, scorer, and
    monitor.
  - Use bounded queues and backpressure so memory use remains predictable.
  - Attach trace ids to messages for deterministic replay.
  - Do not actorize individual steps.
- **Validation strategy:**
  - Replayable message logs for fixed seeds.
  - Backpressure tests under pathological hit rates.
  - End-to-end event record parity against synchronous mode.
  - Latency and queue-depth profiles must show overlap benefits.
- **Failure modes / review risks:**
  - At the wrong granularity actors make performance worse.
  - Debugging distributed state is harder than a call stack.
  - This is Phase 9 system plumbing, not a Phase 8 first target.
- **Effort estimate:** 8 worker-weeks

### D17 -- C++20 coroutines for the transport state machine

- **Evidence:** [R27]
- **What it is:** Represent a track stepping sequence as an explicit resumable
  continuation rather than a deep nested call stack.
- **Where it is used:** Async runtimes, generators, game loops, and state-machine
  simplification.
- **Why it is not already a Geant4 default:** Coroutine frame allocation, compiler
  maturity, and ABI support vary. Geant4 virtual APIs were not designed around resumable
  functions.
- **Geant4 hot path attacked:** CPU fallback stepping, host/device suspension, and
  persistent-kernel emulation.
- **Back-of-envelope gain:** 1.1--1.8x if frame pooling and inlining work; otherwise
  neutral or negative.
- **Implementation sketch:**
  - Prototype a coroutine-based CPU stepping microbenchmark outside Geant4 APIs.
  - Pool coroutine frames or use custom allocators.
  - Measure call-stack depth, allocations, and branch behavior.
  - Promote only if code becomes faster and not just prettier.
- **Validation strategy:**
  - Allocation caps for coroutine frames.
  - Exact step-sequence parity with non-coroutine stepping.
  - Compiler matrix across GCC/Clang versions used on LUNARC.
  - Performance counters compared to direct loops.
- **Failure modes / review risks:**
  - Language support alone does not imply speed.
  - Heap frames can destroy cache locality.
  - Could be useful for Phase 9 persistence but not a top Phase 8 target.
- **Effort estimate:** 5 worker-weeks

### D18 -- Mixed precision with interval guards

- **Evidence:** [R28,R30,R31]
- **What it is:** Use lower precision on smooth arithmetic paths and prove or check that
  the low-precision result is inside a safe error envelope; fall back to double near
  boundaries.
- **Where it is used:** Numerical linear algebra, weather models, GPU computing, and
  verified numerics.
- **Why it is not already a Geant4 default:** Geant4 geometry tolerances, thin
  materials, and threshold physics can be sensitive to small numerical changes.
- **Geant4 hot path attacked:** Geometry predicates, smooth table interpolation, and
  GPU-friendly arithmetic.
- **Back-of-envelope gain:** 1.2--3x on SIMD/GPU arithmetic where FP32 is safe.
- **Implementation sketch:**
  - Classify arithmetic sites by sensitivity: safe, guarded, and forbidden.
  - Use FP32/BF16 only on safe or interval-guarded paths.
  - Fallback to double when intervals overlap a boundary or threshold.
  - Generate MPFR/Arb oracle fixtures for each approximate kernel.
- **Validation strategy:**
  - Interval containment must prove the exact double result is safely away from branch
    boundaries.
  - Boundary stress tests must cover tolerance-scale perturbations.
  - Distribution tests must pass after mixed-precision enablement.
  - Approximate kernels need a documented physics-observable error budget.
- **Failure modes / review risks:**
  - Rounding changes near boundaries can change topology.
  - GPU speedups may not transfer to CPU.
  - The validation burden is high but tractable for selected kernels.
- **Effort estimate:** 6 worker-weeks

### D19 -- Posit numbers

- **Evidence:** [R29]
- **What it is:** Evaluate tapered-precision posit arithmetic as an alternative to IEEE
  floating point for selected arithmetic kernels.
- **Where it is used:** Experimental numerical formats and hardware research.
- **Why it is not already a Geant4 default:** Commodity CPUs/GPUs do not provide
  mainstream posit hardware, and software emulation is too slow for Geant4 hot loops.
- **Geant4 hot path attacked:** No immediate production hot path; possible paper-study
  comparison for future hardware.
- **Back-of-envelope gain:** Speculative; no Phase 8 throughput claim.
- **Implementation sketch:**
  - Keep a literature and microbenchmark note only.
  - If emulated, compare posit, FP32, FP64, and MPFR on one formula-heavy kernel.
  - Do not integrate into transport without hardware support.
  - Track possible future tensor-core or custom-accelerator relevance.
- **Validation strategy:**
  - MPFR oracle comparisons for any posit experiment.
  - Reproducibility across posit libraries must be checked.
  - No physics output should depend on posit arithmetic in Phase 8.
  - The result should be a watchlist disposition, not a product feature.
- **Failure modes / review risks:**
  - Hardware availability is the blocker.
  - Reviewer acceptance would be difficult without standardization.
  - Opportunity cost is high relative to PGO/BVH/QMC.
- **Effort estimate:** 2 worker-weeks for study only

### D20 -- Anyprecision / arbitrary precision and Arb/MPFR oracle paths

- **Evidence:** [R30,R31]
- **What it is:** Use high-precision and interval arithmetic as an oracle for kernels
  whose production implementation uses double, float, compression, or generated code.
- **Where it is used:** Verified numerics, special functions, exact rounding,
  interval/ball arithmetic, and validation tooling.
- **Why it is not already a Geant4 default:** Arbitrary precision is too slow for
  production transport but ideal for fail-closed validation of approximations.
- **Geant4 hot path attacked:** Validation infrastructure for cross sections, geometry
  boundaries, and symbolic kernels; not event throughput.
- **Back-of-envelope gain:** Validation confidence, not speed.
- **Implementation sketch:**
  - Create oracle scripts for selected cross-section interpolation and geometry
    predicates.
  - Use MPFR for correctly rounded scalar checks and Arb for interval containment.
  - Store oracle grids and tolerance manifests with each approximate kernel.
  - Require oracle fixtures before approximate changes land.
- **Validation strategy:**
  - Oracle itself must be deterministic and version-pinned.
  - Production result must be inside the oracle interval or within a documented budget.
  - Tests must include threshold and boundary adversarial points.
  - Promotion gates must fail closed when oracle data are missing.
- **Failure modes / review risks:**
  - Large oracle grids can be slow; keep them targeted.
  - Users may misunderstand oracle support as production arbitrary precision.
  - This is a prerequisite for approximate speedups rather than a speedup.
- **Effort estimate:** 3 worker-weeks

### D21 -- Branchless surface tests via SIMD comparison masks

- **Evidence:** [R32]
- **What it is:** Replace branch-heavy solid intersection predicates with SIMD-friendly
  min/max comparisons and masks, while preserving exact fallback near tolerances.
- **Where it is used:** Ray tracing, collision detection, vectorized geometry libraries,
  and GPU kernels.
- **Why it is not already a Geant4 default:** Geant4 solids encode detailed
  inside/outside/tolerance semantics, so a generic ray-box formula is not enough for all
  shapes.
- **Geant4 hot path attacked:** Geometry navigation for boxes, tubes, and other high-
  frequency solids.
- **Back-of-envelope gain:** 1.2--2.5x on supported solid predicates.
- **Implementation sketch:**
  - Profile which solids dominate Phase 5 navigation.
  - Implement branchless AABB and tube microkernels in G4GPU geometry code.
  - Use masks to compute candidate distances and limiter flags.
  - Fallback to vanilla solid methods near tolerance boundaries or unsupported shapes.
- **Validation strategy:**
  - Exhaustive randomized boundary tests for each supported solid.
  - Chosen distance and inside/outside state must match reference or fallback.
  - Perf counters must show branch-miss reduction.
  - Full benchmark outputs must satisfy distribution gates.
- **Failure modes / review risks:**
  - Tolerance bugs are easy and severe.
  - SIMD speedups depend on data layout.
  - Should be developed with the BVH random-ray audit.
- **Effort estimate:** 4 worker-weeks

### D22 -- Bit-parallel popcount geometry and material queries

- **Evidence:** [R33]
- **What it is:** Represent candidate memberships, active process sets, or material
  masks as bit vectors and use popcount/rank/select style operations for fast queries.
- **Where it is used:** Succinct indexes, information retrieval, databases, bitset
  analytics, and compiler dataflow.
- **Why it is not already a Geant4 default:** Geant4 membership currently lives in
  object graphs and process lists; bitsets require stable ids and immutable snapshots.
- **Geant4 hot path attacked:** Candidate solid filtering, material-region membership,
  active-process selection, and scoring masks.
- **Back-of-envelope gain:** 1.1--2x where many candidates can be masked in machine
  words.
- **Implementation sketch:**
  - Assign stable dense ids to materials, regions, processes, and candidate solids.
  - Generate word-aligned bitsets after initialization.
  - Use SIMD/popcount for broad filtering before exact lookup.
  - Expose debug dumps to map bits back to original Geant4 names.
- **Validation strategy:**
  - Exhaustive parity between bitsets and object-graph membership.
  - No false negatives are allowed; false positives must be exact-fallback filtered.
  - Perf counters must justify bitset memory overhead.
  - Fixed-seed event output must match.
- **Failure modes / review risks:**
  - Sparse or tiny sets do not benefit.
  - Id stability is required for reproducibility.
  - Best combined with perfect hashing and packed navigation snapshots.
- **Effort estimate:** 3 worker-weeks

### D23 -- Tropical semiring and min-plus step-length computation

- **Evidence:** [R34]
- **What it is:** View the step limiter as a min-reduction over candidate distances from
  geometry, physics processes, user cuts, and safety constraints; implement the
  reduction as explicit min-plus dataflow.
- **Where it is used:** Optimization, shortest paths, scheduling, and algebraic dynamic
  programming.
- **Why it is not already a Geant4 default:** Geant4 step limitation includes side
  effects and process bookkeeping, so only the pure candidate-distance reduction can be
  algebraically refactored.
- **Geant4 hot path attacked:** PIL/geometry/user-limit step selection and branch-heavy
  limiter choice.
- **Back-of-envelope gain:** 1.1--1.5x from vectorized branchless reductions.
- **Implementation sketch:**
  - Separate pure candidate-distance calculation from side-effectful process state
    updates.
  - Store candidate lengths and limiter ids in SoA arrays.
  - Use SIMD min-reduction and stable tie-breaking.
  - Invoke the original side-effect path for the selected limiter.
- **Validation strategy:**
  - Chosen limiter id and step length must match vanilla Geant4 for fixed seeds.
  - Tie-breaking tests for equal candidate lengths.
  - No process state may be updated before the selected limiter is known.
  - Distribution parity on all Phase 5 benchmarks.
- **Failure modes / review risks:**
  - Refactoring side effects is the hard part.
  - Speed gain is modest but low-theory-risk.
  - This should be packaged as an engineering free win.
- **Effort estimate:** 2 worker-weeks

### D24 -- Number-theoretic transforms and FFT shower convolutions

- **Evidence:** [R35]
- **What it is:** Replace repeated transport through validated homogeneous response
  blocks with convolution of a precomputed unit response when the system is linear
  enough.
- **Where it is used:** Signal processing, convolutional solvers, response libraries,
  and fast transforms.
- **Why it is not already a Geant4 default:** Full showers are branching, material-
  dependent, and geometry-dependent; arbitrary detector transport is not a stationary
  convolution.
- **Geant4 hot path attacked:** Optical response libraries, homogeneous calorimeter
  blocks, and repeated linear detector response components.
- **Back-of-envelope gain:** 2--20x only for validated response-library subproblems.
- **Implementation sketch:**
  - Identify linear or approximately linear detector response regions.
  - Build unit-response libraries from high-statistics reference Geant4 runs.
  - Use FFT/NTT convolution only inside those declared regions.
  - Fallback to full transport when geometry/material/state leaves the domain.
- **Validation strategy:**
  - Residual distributions against full Geant4 for held-out particles and energies.
  - Energy conservation and non-negativity checks.
  - Domain classifier must be explicit and fail closed.
  - No hadronic cascade replacement without a dedicated validation campaign.
- **Failure modes / review risks:**
  - Looks like a surrogate if overused.
  - Boundary and nonlinearity effects can dominate.
  - Useful for Phase 10 response libraries, not a core Phase 8 hot path.
- **Effort estimate:** 6 worker-weeks

### D25 -- Compressed sensing for sparse hits

- **Evidence:** [R36,R37]
- **What it is:** Exploit sparse detector occupancy to reduce stored hit information or
  diagnostic readout, possibly with bounded-loss recovery.
- **Where it is used:** Imaging, signal recovery, sparse reconstruction, and data
  compression.
- **Why it is not already a Geant4 default:** Simulation creates truth; it cannot infer
  ungenerated hits from fewer measurements without changing the problem. The safe role
  is output compression or diagnostics.
- **Geant4 hot path attacked:** Hit collection and I/O, especially sparse TPC or
  calorimeter output.
- **Back-of-envelope gain:** 2--10x output-size reduction when lossless or observable-
  bounded compression is possible.
- **Implementation sketch:**
  - Start with lossless sparse encodings for hit buffers.
  - Evaluate bounded-loss compressed sensing only for derived diagnostics.
  - Keep raw-hit fallback and per-observable error budgets.
  - Record compression metadata in output manifests.
- **Validation strategy:**
  - Lossless mode must round-trip exactly.
  - Lossy mode must preserve declared observables within confidence/error budgets.
  - Compression must never hide physics validation failures.
  - I/O wall-time and file-size reductions must be measured.
- **Failure modes / review risks:**
  - Can be mistaken for fast simulation if not scoped tightly.
  - Sparse recovery assumptions may fail in showers or high pile-up.
  - Downstream analysis compatibility is the main engineering cost.
- **Effort estimate:** 4 worker-weeks

### D26 -- Reservoir sampling for streaming hit collection

- **Evidence:** [R38]
- **What it is:** Maintain a uniform fixed-size sample from a hit or step stream of
  unknown length using constant memory.
- **Where it is used:** Streaming algorithms, telemetry, online diagnostics, and
  profiling.
- **Why it is not already a Geant4 default:** Physics scoring usually needs the full hit
  set. Reservoirs are safe for diagnostics and profiling, not production physics output.
- **Geant4 hot path attacked:** Debug/profiling I/O, online monitoring, and trace
  summaries.
- **Back-of-envelope gain:** O(1) memory diagnostics and lower debug I/O; not a physics
  speedup.
- **Implementation sketch:**
  - Add diagnostic-only reservoirs keyed by detector, particle, and process.
  - Store inclusion probabilities and random seeds with the sample.
  - Disable reservoirs for production scoring unless explicitly requested.
  - Use samples to guide Phase 5/8 profiling, not validation.
- **Validation strategy:**
  - Uniform inclusion tests on synthetic streams.
  - Deterministic replay under fixed seed.
  - Clear labels that reservoir outputs are diagnostics-only.
  - No production histograms may silently consume reservoirs.
- **Failure modes / review risks:**
  - Easy to misuse as a lossy physics output.
  - No impact on normal transport throughput.
  - Still valuable as a one-week observability free win.
- **Effort estimate:** 1 worker-week

### D27 -- Bloom filters for material and process caching

- **Evidence:** [R39]
- **What it is:** Use compact probabilistic filters to avoid expensive exact negative
  lookups, with exact lookup still required on positive responses.
- **Where it is used:** Databases, caches, networking, and approximate membership
  queries.
- **Why it is not already a Geant4 default:** False positives waste work but are safe
  with exact fallback; false negatives would be invalid and must be impossible by
  construction.
- **Geant4 hot path attacked:** Negative cache lookups for material/process/scorer
  membership.
- **Back-of-envelope gain:** 1.1--1.5x if negative lookups dominate.
- **Implementation sketch:**
  - Measure negative lookup rates in Phase 5 profiles.
  - Build immutable Bloom filters for stable key sets after initialization.
  - Use filters only as prefilters before exact lookup.
  - Tune false-positive rate and hash count in benchmark manifests.
- **Validation strategy:**
  - Construction tests prove every true key is accepted by the filter.
  - Exact fallback ensures output parity despite false positives.
  - Profile evidence must show enough avoided exact lookups.
  - Filter seeds and parameters must be reproducible.
- **Failure modes / review risks:**
  - No benefit if exact lookup is cheap or positives dominate.
  - Hash overhead can outweigh savings for small sets.
  - Should be paired with perfect hashing, not a standalone phase.
- **Effort estimate:** 2 worker-weeks

### D28 -- Reversible computation and Bennett checkpointing

- **Evidence:** [R40]
- **What it is:** Store enough information or checkpoints to replay or reverse
  computation, trading time for memory and enabling derivative-like workflows without
  black-box ML.
- **Where it is used:** Reversible/quantum computation, adjoint methods, checkpointing,
  and differentiable simulation research.
- **Why it is not already a Geant4 default:** Geant4 stochastic branching, secondary
  allocation, and user actions make full reversibility extremely expensive. Random draws
  and discrete choices must be logged.
- **Geant4 hot path attacked:** Future differentiable transport and memory-bounded
  replay; not Phase 8 throughput.
- **Back-of-envelope gain:** No immediate speedup; enables gradients or memory tradeoffs
  in Phase 10.
- **Implementation sketch:**
  - Prototype deterministic event replay with sparse checkpoints.
  - Log RNG ledger, process choices, and secondary creation records.
  - Use reversible replay for debugging and adjoint experiments only.
  - Combine with persistent data structures if Phase 10 differentiability proceeds.
- **Validation strategy:**
  - Replay-to-identical event state from checkpoints.
  - Reverse-to-initial-state tests on small deterministic kernels.
  - Memory/time overhead curves for checkpoint intervals.
  - No production deployment without a clear differentiable-transport use case.
- **Failure modes / review risks:**
  - Huge state logs can exceed original memory use.
  - Discrete stochastic choices limit differentiability.
  - Long-term research, not a near-term Geant4 speed path.
- **Effort estimate:** 8 worker-weeks


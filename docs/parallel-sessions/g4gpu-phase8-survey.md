# Lane: g4gpu-phase8-survey (Algorithm survey: deterministic CS methods + ML, validation-first)

## Goal

Survey computer-science and applied-math methods that have NOT been deeply
applied to Geant4 — with **physics validation** as the top filter. Output: a
single decision document ranking methods by (expected speedup × validatability
× implementation cost).

Hard preference: **deterministic, provably correct methods first.** ML methods
go in the report but in a separate section and only as fallback for problems
the deterministic methods cannot solve. HEP reviewers (FTFP/BERT authors,
Geant4 collaboration board) will reject black-box ML; they will accept
deterministic numerical methods with rigorous error bounds.

Read the strategy root first: `docs/specs/g4gpu-line-by-line-acceleration.md`

This is research / synthesis. No code produced. Deliverable is one markdown
report.

## Output

`docs/reports/algorithm_survey_for_geant4.md` (target 800–1500 lines).

### Section 1 — Deterministic methods (PRIMARY)

For each method below: what it is, where it is currently used (which field),
why it has not been applied to Geant4, expected speedup or variance reduction
on which Geant4 hot path, and a one-paragraph implementation sketch.

**Sampling / integration:**
1. Quasi-Monte Carlo (Sobol, Halton, Niederreiter sequences) — variance
   reduction O(log^d(N)/N) vs. PRNG's O(1/√N). Sherpa and McMule use this.
   Geant4 still uses CLHEP HepJamesRandom (pseudo-random).
2. Stratified sampling + Russian roulette + splitting (formal MCNP-style
   variance reduction with provable unbiasedness).
3. Importance sampling with rigorous bounds (control variates, antithetic
   variates).
4. Korobov / rank-1 lattice rules.
5. Polynomial chaos expansion for uncertainty propagation (replaces MC
   ensembles for systematic uncertainties).

**Geometry / data structures:**
6. SAH-BVH (Surface Area Heuristic BVH) — production ray tracer geometry,
   not used in Geant4 (which uses voxels).
7. Cache-oblivious BVH layouts (Bender, Demaine, Farach-Colton).
8. Cuckoo / perfect hashing for material and particle lookup (replace
   `std::map` with O(1) worst-case).
9. SVD / tensor decomposition compression of cross-section tables.
10. Persistent / immutable data structures (HAMT, persistent vectors) for
    cheap-copy touchable history.

**Computation / specialization:**
11. JIT compilation via LLVM ORC or Cling — specialize transport to the
    actual detector at runtime.
12. Partial evaluation / Futamura projection — generate a particle-
    specialized kernel (e.g. muon-only) from a generic one.
13. Symbolic / computer-algebra preprocessing — Mathematica/FORM/Maple
    generate optimized C code for differential cross sections. Standard in
    NLO/NNLO QCD, not used for Geant4 hadronic.
14. Profile-Guided Optimization (PGO) + Link-Time Optimization (LTO) —
    free 10–30%, most Geant4 installs don't use either.

**Concurrency / scheduling:**
15. Work-stealing schedulers (Cilk / TBB task graphs) replacing
    thread-per-event MT.
16. Actor model / structured concurrency (Erlang/Akka style) — split each
    event into actor messages, better balance.
17. C++20 coroutines for transport state machine — explicit continuations
    replace Geant4's deep call stacks.

**Numerical / precision:**
18. Mixed precision (FP32 / BF16 / FP16) where bounded error is acceptable;
    interval arithmetic to prove the bound.
19. Posit numbers (next-gen FP format) for inner loops.
20. Anyprecision / arb / MPFR for the rare cases where extra precision
    matters more than speed.

**Bit-level / SIMD:**
21. Branchless surface tests via SIMD comparison masks.
22. Bit-parallel popcount-based geometry queries.
23. Tropical semiring (min-plus algebra) for step-length computation —
    vectorizes naturally because `min` is associative.

**Algorithmic novelty:**
24. Number-theoretic transforms / FFTs for shower convolutions — replace
    repeated transport with analytical convolution of unit response.
25. Compressed sensing for sparse hits (calorimeter occupancy << 1).
26. Reservoir sampling for streaming hit collection.
27. Bloom filters for material caching.
28. Reversible computation (Bennett's algorithm) — non-ML autograd for
    transport derivatives.

For each method, the report must include:
- The Geant4 hot path it would attack (PIL / geometry / DoIt / stack / I/O)
- A back-of-envelope speedup estimate
- Validation strategy (how do we prove the result still matches Geant4?)
- Effort estimate (worker-weeks)

### Section 2 — Ranking

Produce a ranked table sorted by `speedup × validatability / effort`. The top
five entries become the Phase 8–10 implementation specs. Specifically flag
which entries are "free wins" (no theoretical risk, just engineering).

### Section 3 — ML methods (SECONDARY)

Cover ML methods only after section 1 is complete, in a clearly demarcated
section with this disclaimer at the top:

> ML methods in HEP simulation face a permanent validation challenge: any
> distribution-level test only proves the model is correct on the tested
> distribution. Out-of-domain failure modes cannot be ruled out. For Geant4
> deployment the model must either: (a) be auditable to the same standard as
> a tabulated cross section, which no current architecture supports, or (b)
> only be used in regions where the deterministic method is impractical.

Then cover: CaloChallenge, Caloflow, transformer hadronic samplers — but
with the validation problem flagged for each.

### Section 4 — Validation framework

This section is mandatory and applies to ALL methods (deterministic and ML).
- KS test thresholds for distribution agreement
- Coverage tests for out-of-domain failure
- Bit-exact reproducibility under fixed-seed PRNG (where applicable)
- Reproducibility under QMC seeds
- Documented error bounds (interval arithmetic where possible)

### Section 5 — Recommended Phase 8/9/10 redefinition

Concrete spec proposals for the top five deterministic methods, with:
- Files to produce
- Validation gate
- Acceptance criteria
- Worker-week estimate

## Iteration cycle

1. Read this spec and the strategy root
2. Mark `g4gpu-phase8-survey` RUNNING in MASTER_PLAN.md
3. Web search and document Section 1 first, then Section 2, then 3-5
4. Save report at `docs/reports/algorithm_survey_for_geant4.md`
5. Commit on a feature branch
6. Mark DONE

## Acceptance

- Section 1 covers all 28 methods with citations
- Section 2 ranking is explicit and defended
- Section 3 ML disclaimer is in place and prominent
- Section 5 yields ≥ 5 concrete Phase 8+ spec proposals
- Recommendations are validatable (every proposal answers "how do we prove
  the physics is still right?")

## Stop condition

After committing the report, stop. The planner uses Section 5 to scope the
real Phase 8a/8b/... implementation specs.

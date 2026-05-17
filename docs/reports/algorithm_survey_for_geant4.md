# G4GPU Phase 8 algorithm survey for Geant4 acceleration

Date: 2026-05-11
Lane: `g4gpu-phase8-survey`
Status: decision report deliverable for Phase 8 scoping
Strategy root: `docs/specs/g4gpu-line-by-line-acceleration.md`

## Executive summary

This report surveys deterministic computer-science and applied-math methods that could
accelerate Geant4-style Monte Carlo transport while keeping physics validation as the
dominant filter. The scoring objective is `expected speedup_or_variance_gain ×
validatability / implementation effort`. All numerical gains are hypotheses for future
Phase 5/8 benchmark measurements, not measured G4GPU results.

The highest-confidence recommendations are engineering transformations that preserve
exactly the same physics state: profile-guided and link-time optimization, immutable
perfect/cuckoo lookup tables, exact Bloom prefilters, bitset masks, branchless min-
reductions, and branchless surface tests with exact fallback. These are the “free wins”
because they should be bit-checkable against unmodified Geant4.

The highest-impact but larger deterministic bets are SAH-BVH geometry with exact
navigator fallback, formal variance reduction, and a QMC dimension-ledger experiment.
These do not replace Geant4 physics models; they change traversal, scheduling, or
estimator efficiency while keeping validation explicit.

ML appears only after deterministic methods. The validation issue is structural:
distribution-level tests cannot prove correctness outside the tested domain. ML can be a
response-library fallback for domains where deterministic methods fail, but it should
not define the primary Geant4 acceleration roadmap.

### Top-five deterministic implementation packages

  - Phase 8a: deterministic free-win package: PGO/LTO, immutable lookup tables, exact
    prefilters, bitset masks, and branchless step-min reductions.
  - Phase 8b: geometry acceleration: SAH-BVH plus cache-aware packed navigation and
    branchless supported-solid predicates, always with exact fallback.
  - Phase 8c: formal variance reduction: stratification, importance maps, splitting,
    roulette, and control variates with weight-conservation tests.
  - Phase 8d: QMC transport experiment: randomized Sobol/Niederreiter adapter with a
    per-track dimension ledger and independent-scramble error bars.
  - Phase 9a: compiler specialization: JIT or partial-evaluation prototype for a
    restricted muon-only or gamma-only kernel after Phase 8 validation discipline
    exists.

## Evidence and novelty caveat

The web/source scan used primary documentation, papers, and official project pages for
Geant4 and CLHEP random engines [R1,R2,R3], existing accelerator comparators including
Celeritas, AdePT, and Opticks [R5,R6,R7,R8], QMC, MCNP variance reduction, BVHs,
compiler/JIT infrastructure, verified numerics, compressed sensing, streaming
sampling, Bloom filters, reversible computation, and calorimeter ML benchmarks.
References are listed at the end.

“Not deeply applied to Geant4” means no first-class production Geant4 integration was
identified in the checked sources and local strategy documents. This is a survey-level
claim, not a final novelty proof. Before a publication or upstream merge request, each
selected method needs a Geant4-developer source audit and benchmark evidence.

The hard preference is deterministic and provably bounded methods first. Any method that
changes physics distributions must provide either exact equivalence, unbiased weighted
estimators, or an explicit error envelope tied to physics observables.


## Split manifest

This file is the <=500-line index for the Phase 8 algorithm survey. The full
survey content is preserved in the linked part files below:

- `docs/reports/g4gpu_phase8_algorithm_survey_methods_part1_20260517.md` -- Section 1 methods D01--D14 (sampling, geometry/data structures, and specialization through PGO/LTO).
- `docs/reports/g4gpu_phase8_algorithm_survey_methods_part2_20260517.md` -- Section 1 methods D15--D28 (concurrency, numerical/precision, bit-level/SIMD, and algorithmic novelty).
- `docs/reports/g4gpu_phase8_algorithm_survey_validation_refs_20260517.md` -- Sections 2--5, ML methods, validation framework V1--V8, Phase 8/9/10 packages, hot-path matrix, acceptance checklist, and references R1--R47.

Line-cap verification target: this index and each part file must remain <=500
lines. Substantive method details live in the split parts; this index keeps the
executive summary, novelty caveat, top ranking table, and acceptance checklist.

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


## Worker handoff metadata

- Factory item: A2 / Phase 8 survey line-cap evidence repair.
- Role type: `specialist-contractor`.
- Manager / escalation: `VALIDATOR`.
- Branch/worktree: active simulation checkout at `/Volumes/MyDrive/nnbar/nnbar/simulation`.
- Writable lease: this index, the three split part files, and `docs/parallel-sessions/MASTER_PLAN.md` evidence rows only.
- Blocker queue checked: `codex-tasks/g4gpu/blockers.txt` contained no `/goal`
  lines before this split-manifest repair was verified.

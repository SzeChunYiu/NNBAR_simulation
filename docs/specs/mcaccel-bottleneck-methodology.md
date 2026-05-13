# MCAccel — Line-by-Line Bottleneck Hunting Methodology

## Premise

Most MC transport code is slower than it has to be at *every layer*, not just
the GPU layer. Many bottlenecks have nothing to do with hardware: the wrong
algorithm, the wrong data layout, the wrong control flow, the wrong
allocation pattern. Some of the biggest wins available to us are pure
software engineering — they cost zero hardware and ship as upstream patches
that benefit every user immediately.

This document defines how worker-3 (implementation) and worker-4
(source review) hunt for bottlenecks systematically, so that across the
target codes (Geant4, OpenMC, MCPL, eventually MCNP/PHITS/FLUKA via
adapters) we find and fix every line that's slower than it needs to be.

## The loop

```
┌─────────────────────────────────────────────────────────────┐
│  1. PROFILE     run benchmark suite, capture perf+ncu       │
│  2. RANK        sort hot spots by exclusive cycles consumed │
│  3. READ        open the source file, read line by line     │
│  4. CATEGORIZE  identify why it is slow (10 categories)     │
│  5. PROPOSE     write a fix with measured-speedup estimate  │
│  6. VALIDATE    plan how to prove the fix preserves physics │
│  7. IMPLEMENT   worker-3 picks from database, ships fix     │
│  8. MEASURE     rerun benchmarks, confirm speedup           │
│  9. UPSTREAM    submit MR (if non-GPU) or land in libMCAccel│
└─────────────────────────────────────────────────────────────┘
```

This loop runs continuously. Every iteration moves the profile flatter.

## The 10 bottleneck categories

Every annotation in the bottleneck database must pick exactly one primary
category. Many fixes touch multiple, but the *root* cause should be one.

| # | Category | What it looks like | Standard fix | Example references |
|---|----------|-------------------|--------------|--------------------|
| **1** | **Microarchitecture** | Branchy inner loop, cache-line crossing, unaligned access, no prefetch | SIMD intrinsics (AVX-512/NEON), branchless code via masks, cache-line alignment, software prefetch | Intel Optimization Manual; Daniel Lemire's blog; *Computer Architecture: A Quantitative Approach* |
| **2** | **Algorithm** | O(n) where O(log n) exists; O(log n) where O(1) exists | Replace with better algorithm of same physics | Cormen et al.; specific HEP refs e.g. Apostolakis CHEP 2021 |
| **3** | **Data structure** | AoS where SoA helps; `std::map` where perfect hash works; linked list where vector works | Replace with cache-friendly structure | Bjarne Stroustrup's "Why You Should Avoid Linked Lists"; *Data-Oriented Design* |
| **4** | **Mathematical** | Iterative solve where closed form exists; table lookup where polynomial fits; redundant transcendentals | Symbolic preprocessing (FORM/Maple), polynomial fits, identity exploitation | Knuth Vol. 2; NIST DLMF |
| **5** | **Control flow** | Deep virtual call chains, unpredictable branches, useless work on hot path | Devirtualize via JIT/templating, branch hint, hoist condition, partial evaluation | Futamura 1971; LLVM Project Optimization Notes |
| **6** | **Memory allocation** | `new`/`delete` in hot loop, `std::vector` growth, std::string concat | Pool allocators, arena allocators, fixed-capacity buffers | Bloomberg BDE; EASTL `fixed_vector` |
| **7** | **Concurrency** | Coarse locking, false sharing, sequential append-only data structures | Lock-free queues, per-thread buffers, work stealing | *The Art of Multiprocessor Programming*; TBB |
| **8** | **GPU offload** | Embarrassingly parallel inner loop running on one CPU thread | CUDA / SYCL / HIP / OptiX kernel | NVIDIA CUDA Programming Guide |
| **9** | **JIT specialization** | Generic dispatch where the runtime configuration is known | LLVM ORC, Cling, partial evaluation, template metaprogramming | LLVM ORC tutorials; *Futamura projection* |
| **10** | **Symbolic / closed-form** | Numerical integration / sampling where the integral is solvable analytically | Mathematica/FORM/SymPy pre-compute, code generation | *Symbolic Computation in HEP* (NNLOJet, MadGraph) |

A small number of bottlenecks belong in two categories. When ambiguous, pick
the category whose fix you would actually implement first.

## Output: the bottleneck database

Every source-review iteration appends to a single, structured database:

`docs/reports/bottleneck_database_<code>.md` where `<code>` is `geant4`,
`openmc`, `mcpl`, etc.

Each entry uses this format:

```markdown
### BD-<code>-<NNN>  <one-line title>

| Field | Value |
|-------|-------|
| File | `source/processes/electromagnetic/utils/src/G4VEnergyLossProcess.cc` |
| Lines | 421-447 |
| Hot-path % (profile-measured) | 6.3% of total CPU on TestEm0 benchmark |
| Category | 1 — Microarchitecture |
| Current pattern | Loop over secondary particles with virtual call per step;
each call reads `fAlongStepEnergyLoss` then writes back via virtual dispatch |
| Why slow | Branch mispredict (virtual call cannot be inlined), cache miss
on `G4ParticleChange` write, no SIMD use of the four accumulators |
| Proposed fix | Replace virtual call site with a compile-time dispatch table
specialized for the four most common processes; pack accumulators
in a 64-byte aligned struct |
| Expected speedup | 1.4× on this function, 0.09× wall-clock on TestEm0 |
| Validation | Bit-exact under fixed seed on TestEm0; KS p-value ≥ 0.05 on
energy spectra |
| Implementation target | `geant4-fork` upstream MR + libMCAccel patch |
| Citation | Lemire 2019, "How fast can you read a CSV file in C++?" |
| Status | OPEN → CLAIMED → IMPLEMENTED → MERGED |
```

Numbering: zero-padded sequence (`BD-geant4-001`, `BD-geant4-002`, ...).
Worker-3 picks open entries by `(impact × validatability) / effort` and
implements them, updating the Status field as it ships.

## Anti-patterns (do not waste cycles on these)

The methodology fails if we annotate code that isn't actually hot. To
prevent that:

- **No entry without profile evidence.** If `perf` / Nsight reports the
  function as <0.5% of CPU, it doesn't go in the database unless it shows
  up on a different hot-path workload. We are not optimizing cold code.
- **No "could be vectorized" without instruction-level analysis.** If the
  inner loop is already memory-bound (cache misses dominate), SIMD won't
  help. Annotate the actual bottleneck.
- **No GPU offload as default.** Category 8 is the last resort, not the
  first. Try categories 1–7 first; GPU offload often loses to a clever
  CPU implementation when host↔device transfer dominates.
- **No ML.** Per the deterministic-first decision in
  `docs/parallel-sessions/g4gpu-phase8-survey.md`, ML methods only enter
  the database after every deterministic option has been considered.

## Coverage strategy

Geant4 source has ~2M lines. We do not read every line. We read every line
in the **profiled hot 20%**.

The hot 20% is reproducibly identified by:
1. Running each canonical benchmark (BasicExample, TestEm0, Hadr01,
   Hadr02, OpNovice2, Par01) under `perf record -F 199`.
2. Aggregating with `perf report --no-children --sort=symbol`.
3. Selecting symbols with cumulative `Self %` until cumulative coverage
   hits 80% of total cycles.
4. Mapping symbols back to source files via debug info.

Worker-4 reads these files top to bottom and annotates every opportunity
found, not just one per file. Target density: ~50 bottlenecks per million
lines in the hot 20% (so ~20 annotations per 400-line hot file).

## How worker-3 and worker-4 cooperate

| Worker | Owns | Output |
|--------|------|--------|
| worker-4 | Reading, profiling, annotating | Bottleneck database entries (`OPEN` status) |
| worker-3 | Implementation, validation, upstream | Status transitions: `OPEN` → `CLAIMED` → `IMPLEMENTED` → `MERGED` |

worker-4 never modifies code in the target MC repos. worker-3 never
annotates without checking the database first.

The planner monitors the database for stale `OPEN` entries (no one claimed
them after a week of high `priority × validatability / effort` ranking) and
re-prioritizes worker-3's queue.

## Cross-code pattern recognition

Once the bottleneck database has ≥100 entries across Geant4, OpenMC, and
MCPL, the planner runs a recurring `cross-code-pattern-analysis` task that
identifies bottlenecks shared across codes. Those become *universal*
optimizations contributed to `core/` and used by every adapter.

This is how we turn "Geant4 is faster" into "all MC transport is faster":
by spotting the patterns that recur across codes and fixing them once in
the shared core.

## Acceptance for the methodology

This methodology is considered established when:
- ≥ 50 bottleneck database entries exist for Geant4 with profile evidence
- ≥ 5 entries have transitioned to `IMPLEMENTED` with measured speedup
- ≥ 1 entry has transitioned to `MERGED` upstream
- ≥ 10 OpenMC entries exist alongside Geant4 entries
- ≥ 3 cross-code patterns identified for the universal core

At that point, the loop is self-sustaining and the methodology is the
project's permanent operating procedure.

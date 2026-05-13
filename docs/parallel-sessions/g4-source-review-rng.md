# Lane: g4-source-review-rng

## Role

You are an isolated Geant4 source-review worker. Your job is to read the
CLHEP random-number generator sources embedded in Geant4 11.2.2, identify
concrete optimization opportunities, and write a structured bottleneck database
shard. You do **not** implement any fixes in this lane — you only document
findings.

## Goal

Produce shard file `docs/reports/g4_bottleneck_database_rng_clhep.md`
containing exactly **10 structured BD entries** numbered `BD-geant4-161`
through `BD-geant4-170`.

These entries will feed directly into the CPC/JINST paper on vanilla Geant4
CPU speedup. Every entry must cite real source lines, a plausible performance
mechanism, a concrete algorithmic fix, and a testable validation plan.

## Repos and paths

| Purpose | Path |
|---------|------|
| Geant4 11.2.2 source (read-only) | `/Volumes/MyDrive/nnbar/nnbar/simulation/GEANT4_Packages/src/geant4-v11.2.2/source/` |
| Simulation repo (write specs here) | `/Volumes/MyDrive/nnbar/nnbar/simulation/` |

**Do NOT** modify any file outside `docs/reports/` and `docs/parallel-sessions/`
in the simulation repo. Never touch `NNBAR_Detector/`, `nnbar_reconstruction/`,
`scripts/`, `slurm/`, `macros/`, or production data paths.

## Required reading (before writing any entry)

1. `docs/parallel-sessions/MASTER_PLAN.md` — current status and BD range accounting.
2. `docs/reports/bottleneck_database_geant4.md` — existing entries: do not duplicate.
3. `docs/reports/g4gpu_bottleneck_gap_scan_20260512.md` — confirmed next free
   block after allocator_mt shard is 161.
4. `docs/reports/g4_source_review_hotpaths.md` — prior RNG analysis notes.

## Source files to inspect

Open and read **all** of the following files before writing entries:

```
source/externals/clhep/src/Ranlux64Engine.cc
source/externals/clhep/src/RandFlat.cc
source/externals/clhep/src/RandGauss.cc
source/externals/clhep/src/RandExponential.cc
source/externals/clhep/include/CLHEP/Random/Ranlux64Engine.h
```

Also inspect related files if present:
```
source/externals/clhep/src/MixMaxRng.cc
source/externals/clhep/include/CLHEP/Random/MixMaxRng.h
source/externals/clhep/src/RandBit.cc
source/externals/clhep/src/RandPoisson.cc
source/externals/clhep/include/CLHEP/Random/defs.h
```

## Focus themes

The 10 entries MUST collectively cover the following themes:

1. **RANLUX64 luxury-level overhead**: The `Ranlux64Engine` generates floats
   using a luxury-level skip that discards a configurable number of values per
   block. Find the inner generation loop and the skip logic. Document the
   wasted compute per usable random number at the default luxury level (3 or 4).

2. **Box-Muller Gaussian sampling**: `RandGauss` uses Box-Muller transform
   which calls `std::log`, `std::sqrt`, and `std::cos`/`std::sin` per pair.
   Find the exact call site, document the transcendental function cost, and
   describe the ziggurat or Kinderman-Ramage alternatives with references.

3. **Exponential distribution rejection loop**: `RandExponential` uses a
   rejection or logarithm-based sampling. Find whether it calls `std::log`
   per sample or uses a Marsaglia-style alias approach. If it uses `std::log`,
   document the SIMD-vectorizable alternative.

4. **RandFlat hot path and modulo arithmetic**: `RandFlat::shoot()` maps the
   raw integer output to `[0,1)`. Document any integer/float conversion
   overhead, modulo operations, or unnecessary double-precision upcasting that
   SIMD vectorization would eliminate.

5. **Lack of AVX2/SSE4 vectorization in CLHEP**: The CLHEP RNG sources use
   scalar loops. Document where `__m256d` or `_mm256_*` intrinsics would
   permit generating 4 doubles in a single instruction, and identify the
   blocking data dependencies.

6. **Thread-local engine state access**: Geant4 MT uses one engine per thread.
   Find where `HepRandomEngine::flat()` or `getEngine()` is called on the hot
   path and whether the thread-local lookup adds overhead (TLS fetch latency,
   function call overhead).

7. **Gaussian cache miss on odd-call parity**: `RandGauss` caches one value of
   a pair for the next call (`set_cached_gaussian`). Find the flag check and
   cached-value branch on the hot path. Document cache-miss probability and
   branch-prediction impact.

8. **Poisson sampling threshold**: `RandPoisson` switches algorithms at a mean
   threshold (often lambda=12 or 88). Find the threshold, document that
   physics workloads frequently straddle it, and describe a unified algorithm
   (e.g., Hormann's transformed rejection) that avoids the branch.

9. **MixMaxRng state size and cache impact**: If `MixMaxRng` is present, its
   state vector (N=17 or N=240) may not fit in a cache line. Document the
   state size and the number of cache misses per generation block.

10. **Missing batch/SIMD generation API**: CLHEP has no `flatArray(n, buf)`
    vectorizable API. Every consumer calls `flat()` in a scalar loop. Document
    the interface gap and the Intel MKL VSL / CUDA cuRAND equivalent that
    shows the achievable speedup.

## BD shard format

Every entry MUST use this exact table structure:

```
### BD-geant4-NNN  One-line title

| Field | Value |
|-------|-------|
| File | `source/path/to/File.cc` |
| Lines | NNN-NNN |
| Hot-path % (profile-measured) | X% aggregate; per-line self% `OPEN:` pending perf. |
| Category | N — Category name |
| Current pattern | Snippet: `code` description of what Geant4 currently does. |
| Why slow | Explanation of the bottleneck. |
| Proposed fix | Concrete fix with algorithm/data structure reference. |
| Expected speedup | N.N-N.Nx inside <subsystem>; broader estimate. |
| Validation | How to validate correctness after fix. |
| Implementation target | `branch-or-target-name`. |
| Citation | Author Year; standard CS citation. |
| Status | OPEN |
```

**Categories:**
- 1 — Vectorization
- 2 — Algorithm
- 3 — Data structure
- 4 — Mathematical
- 5 — Control flow
- 6 — Memory allocation
- 8 — Synchronization

## Source-provenance protocol

Before writing any entry:
1. Open the actual source file in the Geant4 11.2.2 tree.
2. Verify function name and line range by reading the file.
3. Record the exact relative path from the source root.
4. If a file is absent at the listed path, search nearby directories and
   document the actual path found.

## Shard header requirements

```markdown
# Geant4 bottleneck database — RNG / CLHEP shard

Scope: structured source-review entries for Geant4 `v11.2.2` CLHEP random
number generator paths (Ranlux64, RandFlat, RandGauss, RandExponential).
BD range: 161–170.

Source provenance: [describe which local path used, git describe or SHA-256,
confirm files were opened before line numbers were cited]

Isolation check: documentation only. No `NNBAR_Detector/`,
`nnbar_reconstruction/`, `scripts/`, `lunarc/`, `slurm/`, or `macro/` paths
were modified.
```

## Citation standards

- Marsaglia and Tsang 2000, *A simple method for generating gamma variables*
- Kinderman and Ramage 1976, *Computer generation of normal random variables*
- Lüscher 1994, RANLUX algorithm
- Devroye 1986 *Non-Uniform Random Variate Generation* (Springer)
- Vose 1991 alias method; Walker 1977 alias tables
- Hormann 1993 transformed rejection for Poisson
- Intel 2024 *64 and IA-32 Architectures Optimization Reference Manual*
- Intel MKL Vector Statistics Library documentation

## Paper context

These BD entries directly feed the **CPC/JINST paper on vanilla Geant4 CPU
speedup**. The RNG subsystem is called O(10) times per step across physics
processes, making even modest per-call overhead multiplicative.

## Non-goals / isolation

- Do NOT write any code patches or modified source files.
- Do NOT touch `NNBAR_Detector/`, `nnbar_reconstruction/`, `slurm/`, macros.
- Do NOT claim measured speedup numbers.
- Do NOT modify `docs/reports/bottleneck_database_geant4.md`.
- Do NOT overlap with BD-geant4-001 through BD-geant4-160.

## Output

Write the completed shard to:
```
docs/reports/g4_bottleneck_database_rng_clhep.md
```

Then update `docs/parallel-sessions/MASTER_PLAN.md`:
- Mark lane `g4-source-review-rng` DONE.
- Record: "Shard rng_clhep: BD-geant4-161–170, written YYYY-MM-DD."

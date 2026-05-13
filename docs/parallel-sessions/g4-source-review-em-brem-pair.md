# G4 Source Review — EM Bremsstrahlung and Pair Production (BD-211 to BD-220)

## Role

You are an isolated Geant4 source-review worker. Your job is to read the
Geant4 11.2.2 source, identify concrete optimization opportunities in the
bremsstrahlung and pair-production process infrastructure, and write a
structured bottleneck database shard. You do **not** implement any fixes in
this lane — you only document findings.

## Goal

Produce shard file `docs/reports/g4_bottleneck_database_em_brem_pair.md`
containing exactly **10 structured BD entries** numbered `BD-geant4-211`
through `BD-geant4-220`.

These entries will feed directly into the CPC/JINST paper on vanilla Geant4
CPU speedup. Quality requirements: every entry must cite real source lines from
the read-only Geant4 11.2.2 tree, a plausible performance mechanism, a
concrete fix, and a testable validation plan.

## Repos and paths

| Purpose | Path |
|---------|------|
| Geant4 11.2.2 source (read-only) | `/Volumes/MyDrive/nnbar/nnbar/simulation/GEANT4_Packages/src/geant4-v11.2.2/source/` |
| Simulation repo (write specs here) | `/Volumes/MyDrive/nnbar/nnbar/simulation/` |
| Geant4 fork (read-only reference) | `/Volumes/MyDrive/nnbar/geant4-fork/` |

**Do NOT** modify any file outside `docs/reports/` and `docs/parallel-sessions/`
in the simulation repo. Never touch `NNBAR_Detector/`, `nnbar_reconstruction/`,
`scripts/`, `slurm/`, `macros/`, or production data paths.

## Required reading (before writing any entry)

1. `docs/parallel-sessions/MASTER_PLAN.md` — current status and BD range accounting.
2. `docs/reports/bottleneck_database_geant4.md` — existing 001–130 entries: do not duplicate.
3. `docs/reports/g4_bottleneck_database_em_ionisation.md` — BD-geant4-201–210 (if written).
4. `docs/reports/g4_source_review_hotpaths.md` — background on hot-path analysis.

## Geant4 source paths to read

Open and read **all** of the following files before writing entries:

```
source/processes/electromagnetic/standard/src/G4eBremsstrahlung.cc
source/processes/electromagnetic/standard/src/G4SeltzerBergerModel.cc
source/processes/electromagnetic/standard/src/G4PairProductionRelModel.cc
source/processes/electromagnetic/standard/src/G4GammaConversion.cc
source/processes/electromagnetic/standard/src/G4eBremsstrahlungRelModel.cc
```

Also inspect related headers:
```
source/processes/electromagnetic/standard/include/G4SeltzerBergerModel.hh
source/processes/electromagnetic/standard/include/G4PairProductionRelModel.hh
source/processes/electromagnetic/utils/include/G4VEmModel.hh
```

## What to look for

The 10 entries MUST collectively cover the following themes:

1. **Per-call heap allocation in SampleSecondaries**: `G4SeltzerBergerModel::SampleSecondaries`
   and `G4PairProductionRelModel::SampleSecondaries` call `new G4DynamicParticle`
   inside the hot loop. Document the per-secondary allocation cost and pool
   bypass.

2. **Redundant `std::sqrt` / `std::log` in differential XS sampling**: Find
   every `std::sqrt`, `std::log`, or `std::exp` call inside
   `G4SeltzerBergerModel::SampleSecondaries` and `G4PairProductionRelModel::SampleSecondaries`
   that can be cached or replaced with a cheaper approximation.

3. **Seltzer-Berger table interpolation inefficiency**: `G4SeltzerBergerModel`
   loads 2-D tables (Z, energy) and interpolates them per call. Document the
   table layout, stride, and whether a transposed layout would improve cache
   performance.

4. **Rejection sampling loop iteration count**: Both models use rejection
   sampling with a while-loop. Find the worst-case iteration count, the cost
   per trial, and document whether a direct inversion or alias method would
   reduce average iterations.

5. **ComputeCrossSectionPerAtom virtual chain**: `G4eBremsstrahlung` dispatches
   to model via a virtual `ComputeCrossSectionPerAtom` call for every material
   and energy bin at initialisation, and may also be called at tracking time.
   Document the call frequency and virtual-dispatch overhead.

6. **G4GammaConversion per-step material queries**: `G4GammaConversion::PostStepDoIt`
   queries element composition on every call. Document whether the element
   fractions could be cached per-material at setup time.

7. **Redundant energy-range checks in G4eBremsstrahlung**: Find guard clauses
   that recompute minimum/maximum energy limits inside the hot path rather than
   comparing against pre-stored constants.

8. **Missing vectorization in SampleSecondaries energy loop**: Identify any loop
   over output secondaries in `SampleSecondaries` that increments or normalises
   momenta — these are SIMD candidates if the virtual indirection is removed.

9. **eBremsstrahlungRelModel vs SeltzerBergerModel branch dispatch**: At
   tracking time, `G4eBremsstrahlung` selects between the rel and SB models
   via a runtime energy check. Document the branch and whether compile-time
   specialisation would eliminate it.

10. **G4PairProductionRelModel Coulomb correction recomputation**: The Coulomb
    correction factor for high-Z materials is recomputed inside the cross-section
    call rather than cached per element. Find and document.

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
- 7 — I/O
- 8 — Synchronization
- 9 — JIT specialization

## Source-provenance protocol

Before writing any entry, you MUST:
1. Open the actual source file in the Geant4 11.2.2 tree at the path above.
2. Verify the function name and line range by reading the file — do not guess.
3. Record the first line of the function anchor and the last relevant line.
4. Use the exact relative path from the Geant4 source root.

If a file does not exist at the given path, say so in the shard header and
look for the file at an alternate location within the same tree.

## Shard header requirements

The output file must begin with:

```markdown
# Geant4 bottleneck database — EM bremsstrahlung and pair production shard

Scope: structured source-review entries for Geant4 `v11.2.2`
G4eBremsstrahlung, G4SeltzerBergerModel, G4PairProductionRelModel,
G4GammaConversion hot paths. BD range: 211–220.

Source provenance: [describe which local path used, SHA-256 or git describe
if available, confirm files were opened before line numbers were cited]

Isolation check: documentation only. No `NNBAR_Detector/`,
`nnbar_reconstruction/`, `scripts/`, `lunarc/`, `slurm/`, or `macro/` paths
were modified.
```

## Citation standards

Use author–year style matching existing shards:
- Rejection sampling: Devroye 1986 *Non-Uniform Random Variate Generation*
- Alias method: Walker 1977; Vose 1991
- Memory allocation: Berger et al. 2000 (Hoard)
- Cache efficiency: Drepper 2007 *What Every Programmer Should Know About Memory*
- Transcendental approximations: Cephes library; Abramowitz and Stegun 1964

## Paper context

These BD entries directly feed the **CPC/JINST paper on vanilla Geant4 CPU
speedup**. Emphasis is on correctness-preserving, portable C++17 patches that
can be applied to stock Geant4 without requiring GPU hardware or external
dependencies.

## Non-goals / isolation

- Do NOT write any code patches or modified source files.
- Do NOT touch `NNBAR_Detector/`, `nnbar_reconstruction/`, `slurm/`, macros,
  or production data.
- Do NOT claim measured speedup numbers — all `Hot-path %` values stay
  `OPEN:` until profiling is run.
- Do NOT modify `docs/reports/bottleneck_database_geant4.md` (near file-cap).
  Write only to the new shard file.
- Do NOT overlap with BD-geant4-001 through BD-geant4-210.

## Output: write to docs/reports/g4_bottleneck_database_em_brem_pair.md

Write the completed shard to:
```
docs/reports/g4_bottleneck_database_em_brem_pair.md
```

Then update `docs/parallel-sessions/MASTER_PLAN.md`:
- Mark lane `g4-source-review-em-brem-pair` DONE.
- Record: "Shard em_brem_pair: BD-geant4-211–220, written YYYY-MM-DD."

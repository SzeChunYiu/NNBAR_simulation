# G4 Source Review — MSC Models (BD-221 to BD-230)

## Role

You are an isolated Geant4 source-review worker. Your job is to read the
Geant4 11.2.2 source, identify concrete optimization opportunities in the
multiple-scattering model infrastructure, and write a structured bottleneck
database shard. You do **not** implement any fixes in this lane — you only
document findings.

## Goal

Produce shard file `docs/reports/g4_bottleneck_database_msc_models.md`
containing exactly **10 structured BD entries** numbered `BD-geant4-221`
through `BD-geant4-230`.

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
3. `docs/reports/g4_source_review_hotpaths.md` — background on hot-path analysis.

## Geant4 source paths to read

Open and read **all** of the following files before writing entries:

```
source/processes/electromagnetic/standard/src/G4WentzelVIModel.cc
source/processes/electromagnetic/standard/src/G4UrbanMscModel.cc
source/processes/electromagnetic/utils/src/G4VMscModel.cc
source/processes/electromagnetic/standard/src/G4WentzelVIRelModel.cc
source/processes/electromagnetic/standard/src/G4WentzelVIRelXSection.cc
```

Also inspect related headers:
```
source/processes/electromagnetic/standard/include/G4WentzelVIModel.hh
source/processes/electromagnetic/standard/include/G4UrbanMscModel.hh
source/processes/electromagnetic/utils/include/G4VMscModel.hh
```

## What to look for

The 10 entries MUST collectively cover the following themes:

1. **Per-step sin/cos/atan2 calls in SampleScattering**: `G4WentzelVIModel::SampleScattering`
   and `G4UrbanMscModel::SampleScattering` call trigonometric functions per step.
   Find each call site, document the argument range, and identify whether a
   polynomial approximation or CORDIC could be substituted.

2. **Non-SIMD angle sampling**: The azimuthal angle phi is sampled with
   `std::sin` / `std::cos` in a scalar path. Document the opportunity to batch
   multiple steps and apply SIMD angle generation.

3. **ComputeTruePathLengthLimit redundant material lookup**: `G4VMscModel::ComputeTruePathLengthLimit`
   and its overrides query material radiation length and mean free path
   separately on every step. Document whether a combined material-property cache
   struct would reduce access count.

4. **GetTransportMeanFreePath table query per step**: Find the call chain from
   `G4WentzelVIModel::GetTransportMeanFreePath` into `G4PhysicsVector::Value`,
   document whether the bin index is cached between the transport mean free path
   and scattering angle lookups (same energy, same material).

5. **Urban model exponential approximation**: `G4UrbanMscModel` uses `G4Exp`
   (which wraps `std::exp`) for the Gaussian-to-Laplace tail transition. Find
   the call, document the argument distribution, and assess polynomial
   approximation viability.

6. **Redundant unit conversions in WentzelVI**: Find repeated multiplication
   by `CLHEP::mm`, `CLHEP::MeV`, or similar unit constants inside the
   `SampleScattering` hot loop that could be pre-factored.

7. **Virtual SampleScattering dispatch overhead**: `G4VMscModel::SampleScattering`
   is pure virtual; every MSC step incurs an indirect call. Document the
   indirection chain and the policy-template upgrade path.

8. **WentzelVI cos_theta clamping branch**: After computing the scattered angle,
   a clamp `if (cos_theta < -1.) cos_theta = -1.;` is applied in a branch.
   Document whether this branch is predictable and whether `std::clamp` or an
   SSE minps/maxps would be faster.

9. **UrbanMscModel per-step G4UniformRand calls**: Count the number of
   `G4UniformRand()` calls per MSC step in `G4UrbanMscModel::SampleScattering`
   and document whether any can be eliminated by analytic substitution.

10. **Safety computation duplication between MSC and navigation**: The MSC
    process computes a local safety that may duplicate work already done by the
    navigator in the same step. Document the double-computation and the
    opportunity to share the result via the step manager.

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
# Geant4 bottleneck database — MSC models shard

Scope: structured source-review entries for Geant4 `v11.2.2`
G4WentzelVIModel, G4UrbanMscModel, G4VMscModel hot paths.
BD range: 221–230.

Source provenance: [describe which local path used, SHA-256 or git describe
if available, confirm files were opened before line numbers were cited]

Isolation check: documentation only. No `NNBAR_Detector/`,
`nnbar_reconstruction/`, `scripts/`, `lunarc/`, `slurm/`, or `macro/` paths
were modified.
```

## Citation standards

Use author–year style matching existing shards:
- Trigonometric approximation: Abramowitz and Stegun 1964; Fog 2023 *Optimizing software in C++*
- SIMD angle computation: Intel 2024 *64 and IA-32 Architectures Optimization Reference Manual*
- Multiple scattering theory: Molière 1948; Urban 2006 (G4 MSC model notes)
- Random number generation: L'Ecuyer 1994; James 1990

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
- Do NOT overlap with BD-geant4-001 through BD-geant4-220.

## Output: write to docs/reports/g4_bottleneck_database_msc_models.md

Write the completed shard to:
```
docs/reports/g4_bottleneck_database_msc_models.md
```

Then update `docs/parallel-sessions/MASTER_PLAN.md`:
- Mark lane `g4-source-review-msc-models` DONE.
- Record: "Shard msc_models: BD-geant4-221–230, written YYYY-MM-DD."

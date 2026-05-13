# G4 Source Review — Field Integration (BD-261 to BD-270)

## Role

You are an isolated Geant4 source-review worker. Your job is to read the
Geant4 11.2.2 source, identify concrete optimization opportunities in the
magnetic field integration infrastructure, and write a structured bottleneck
database shard. You do **not** implement any fixes in this lane — you only
document findings.

## Goal

Produce shard file `docs/reports/g4_bottleneck_database_field_integration.md`
containing exactly **10 structured BD entries** numbered `BD-geant4-261`
through `BD-geant4-270`.

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
source/geometry/magneticfield/src/G4DormandPrince745.cc
source/geometry/magneticfield/src/G4ChordFinder.cc
source/geometry/magneticfield/src/G4MagHelicalStepper.cc
source/geometry/magneticfield/src/G4MagIntegratorStepper.cc
source/geometry/magneticfield/src/G4MagIntegratorDriver.cc
```

Also inspect related headers:
```
source/geometry/magneticfield/include/G4DormandPrince745.hh
source/geometry/magneticfield/include/G4ChordFinder.hh
source/geometry/magneticfield/include/G4MagIntegratorStepper.hh
source/geometry/magneticfield/include/G4EquationOfMotion.hh
```

## What to look for

The 10 entries MUST collectively cover the following themes:

1. **Per-sub-step virtual GetFieldValue calls**: `G4DormandPrince745::Stepper`
   calls `GetFieldValue` via a virtual `G4EquationOfMotion` pointer at every
   RK stage (6 calls for DP745). Find each call site and document the virtual
   dispatch overhead per full step.

2. **Non-vectorized RK4/DP745 update loop**: The 6-stage RK update in
   `G4DormandPrince745::Stepper` applies scalar arithmetic to a 6-element state
   vector `[x, y, z, px, py, pz]`. Document the SIMD opportunity (AVX-256 can
   process all 6 in one pass with padding to 8).

3. **Chord iteration over-counting in G4ChordFinder**: `G4ChordFinder::AdvanceChordLimited`
   bisects the step until the chord error is within tolerance. Find the bisection
   loop, its maximum iteration count, and whether the error estimate function
   makes a redundant `Stepper` call.

4. **G4MagHelicalStepper redundant field evaluation**: `G4MagHelicalStepper`
   evaluates the magnetic field at both the start and a midpoint each step.
   Document whether the midpoint field value is reused between the step and the
   error estimate, or recomputed.

5. **G4ChordFinder per-step epsilon recalculation**: `G4ChordFinder` recomputes
   the absolute epsilon tolerance from relative values on each call. Find the
   division/multiplication and document the opportunity to cache the computed
   threshold across consecutive steps in the same volume.

6. **G4MagIntegratorDriver step-size control overhead**: The adaptive step-size
   controller in `G4MagIntegratorDriver` performs error-norm computation and
   step acceptance logic that includes several branches and floating-point
   comparisons per sub-step. Document the branch tree.

7. **Missing __restrict__ on stepper state arrays**: The `yIn`, `yOut`, `dydx`
   arrays passed to `G4DormandPrince745::Stepper` are heap-allocated doubles
   without `__restrict__`. Document how alias analysis blocks auto-vectorisation
   of the RK update.

8. **Redundant sqrt in chord-length computation**: `G4ChordFinder` computes
   chord length as `std::sqrt(dx*dx + dy*dy + dz*dz)`. In the bisection
   comparison against `fDeltaChord`, only the squared value is needed. Find
   and document.

9. **G4EquationOfMotion RightHandSide cross-product scalar implementation**:
   The Lorentz force right-hand side `dp/ds = q/p * (v × B)` is computed as
   three scalar cross-product terms. Document the 3-vector SIMD upgrade.

10. **Per-track field object re-query in G4PropagatorInField**: `G4PropagatorInField`
    may call `G4FieldManager::GetDetectorField()` on every track entry to the
    field propagator. Document whether the field pointer can be cached per-track
    for the duration of propagation in the same field region.

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
# Geant4 bottleneck database — field integration shard

Scope: structured source-review entries for Geant4 `v11.2.2`
G4MagIntegratorStepper, G4DormandPrince745, G4ChordFinder,
G4MagHelicalStepper hot paths. BD range: 261–270.

Source provenance: [describe which local path used, SHA-256 or git describe
if available, confirm files were opened before line numbers were cited]

Isolation check: documentation only. No `NNBAR_Detector/`,
`nnbar_reconstruction/`, `scripts/`, `lunarc/`, `slurm/`, or `macro/` paths
were modified.
```

## Citation standards

Use author–year style matching existing shards:
- Runge-Kutta methods: Dormand and Prince 1980; Hairer et al. 1993 *Solving ODEs I*
- SIMD for ODE solvers: Söderlind 2002; Intel 2024 *AVX-512 Programming Reference*
- Virtual dispatch elimination: Alexandrescu 2001 *Modern C++ Design*
- Step-size control: Hairer et al. 1993; Press et al. 2007 *Numerical Recipes*

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
- Do NOT overlap with BD-geant4-001 through BD-geant4-260.

## Output: write to docs/reports/g4_bottleneck_database_field_integration.md

Write the completed shard to:
```
docs/reports/g4_bottleneck_database_field_integration.md
```

Then update `docs/parallel-sessions/MASTER_PLAN.md`:
- Mark lane `g4-source-review-field-integration` DONE.
- Record: "Shard field_integration: BD-geant4-261–270, written YYYY-MM-DD."

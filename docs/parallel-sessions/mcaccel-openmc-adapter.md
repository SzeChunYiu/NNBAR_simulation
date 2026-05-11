# Lane: mcaccel-openmc-adapter

## Goal

Prove the "MC-code-agnostic" claim by building a working OpenMC adapter
alongside the Geant4 work. OpenMC is the second target because:

- Modern C++ (easy to read, easy to PR against)
- MIT license (zero legal friction)
- Active maintainers receptive to upstream
- Different physics domain (reactor / shielding) — proves the core is
  truly generic, not Geant4-specific
- Headline benchmark suite (ICSBEP, k-inf, k-eff) is well-defined

If our core optimizations work for both Geant4 (high-E hadronic, complex
geometry) and OpenMC (low-E neutron, simpler geometry but huge cross-section
tables), they will work for everything in between.

Read first: `docs/specs/g4gpu-line-by-line-acceleration.md`, the
"Architecture" section that defines `core/` vs `adapters/`.

## What this lane produces

### Iteration 1 — Bootstrap

1. Clone OpenMC: `https://github.com/openmc-dev/openmc` at the latest tag
2. Build on LUNARC, run the headline benchmarks:
   - ICSBEP HEU-MET-FAST-001
   - PWR pin cell
   - k-inf for MOX assembly
3. Capture timings as `benchmarks/openmc-baseline/results.parquet`
4. Document the build at `docs/reports/openmc_baseline.md`

### Iteration 2 — Adapter scaffold

In the geant4-gpu repo (which is becoming the mctransport-accel repo):

1. Create `adapters/openmc/` directory tree mirroring `adapters/geant4/`
2. Identify OpenMC's hot paths (analogous to Geant4's PIL / geometry /
   sampling / track / hits) by reading `src/`:
   - `simulation.cpp` (transport loop)
   - `cross_sections.cpp` (interpolation — the analog of `G4PhysicsVector`)
   - `geometry.cpp` (CSG navigation — analogous but simpler than G4Navigator)
   - `random_lcg.cpp` (RNG — replaceable with QMC like Geant4)
3. Document mapping: which `core/` primitive maps to which OpenMC hot path
4. Commit the scaffold

### Iteration 3 — First non-trivial adapter

Pick the simplest universally-applicable optimization (likely QMC RNG) and
ship it in both adapters simultaneously. Validate on:
- Geant4: BasicExample, TestEm0 (bit-exact under fixed seed, variance
  reduction with new point sets)
- OpenMC: ICSBEP HEU-MET-FAST-001 (k-eff within published uncertainty)

This is the first piece of evidence that the core+adapter architecture
delivers cross-code wins.

## Iteration cycle

1. Read this spec
2. Mark `mcaccel-openmc-adapter` RUNNING in MASTER_PLAN.md
3. Execute one iteration above
4. Commit
5. If all three iterations done, mark DONE; else stop for next iteration

## Important

- All builds and runs on LUNARC
- OpenMC needs HDF5 + Python; load appropriate modules
- License compatibility: OpenMC is MIT, geant4-gpu currently has no LICENSE
  — add MIT license to geant4-gpu repo before publishing OpenMC adapter

## Acceptance

- OpenMC builds and runs the headline benchmarks on LUNARC
- `adapters/openmc/` scaffold exists with documented hot-path mapping
- First adapter optimization (QMC RNG) ships in both Geant4 and OpenMC
  adapter and validates on both

## Stop condition

After committing one iteration's deliverable, stop.

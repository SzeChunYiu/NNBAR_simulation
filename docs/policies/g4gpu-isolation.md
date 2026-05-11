# G4GPU ↔ NNBAR Simulation Isolation Policy

**Status:** Mandatory. Applies to all active lanes (`worker-0`, `worker-1`,
`worker-2`, `worker-3`, `worker-4`, and `planner`) and all SLURM/build
automation.

## The rule

**The NNBAR simulation (thesis-critical) must never link against, call, or
depend on the G4GPU R&D project (exploratory).** They are entirely separate
projects that happen to share a repository neighborhood.

Until a formal physics-parity gate (defined below) passes, every NNBAR signal
event, cosmic event, beam-background event, and pipeline result must come
from **vanilla Geant4 only**.

## Why

1. **G4GPU is exploratory R&D**: kernels under active development, validation
   incomplete, performance and correctness both unproven.
2. **The thesis must reproduce**: any number the thesis quotes (sensitivity,
   acceptance, cutflow survival, etc.) must be derivable from a deterministic,
   well-understood Geant4 chain. Mixing in unproven kernels invalidates every
   downstream observable.
3. **Reviewer defense**: external review (committee, paper referees, Geant4
   collaboration) will reject results that depend on unproven custom code.
   Keeping G4GPU strictly out of the NNBAR pipeline means the thesis chain is
   defensible regardless of how G4GPU evolves.

## What this means in practice

### Code

- **NNBAR_Detector/** must not include any G4GPU header.
- **NNBAR_Detector/CMakeLists.txt** must not `find_package(G4GPU)` and must
  not link `libG4GPU.so`.
- **nnbar_reconstruction/** must not import G4GPU Python bindings (none exist
  today; this is a forward-looking rule).
- **scripts/, lunarc/, slurm/** must not invoke any G4GPU binary, kernel, or
  test executable in any production-data path.

### Builds

- The NNBAR Geant4 binary on LUNARC at
  `/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/build/` is the
  thesis production binary. It links **only** vanilla Geant4.
- The G4GPU repo at `/Volumes/MyDrive/nnbar/geant4-gpu/` and on LUNARC at
  `/projects/hep/fs10/shared/nnbar/billy/geant4-gpu/` is a parallel, separate
  build tree. Nothing in the NNBAR build tree may reference it.

### Data

- Every Parquet file in `results/` that the thesis quotes must come from a
  vanilla-Geant4 run. Track provenance via a `simulator` column with the
  exact Geant4 version + build hash.
- G4GPU's own benchmark outputs live in
  `/Volumes/MyDrive/nnbar/geant4-gpu/benchmarks/results/` and are
  **research-only**. They never get rsync'd into the NNBAR results tree.

### Git / branches

- G4GPU work lives on G4GPU-prefixed branches (`lane/g4gpu-phase5`, etc.) in
  the geant4-gpu repo, never in `nnbar/simulation`.
- The NNBAR simulation repo may carry documentation about G4GPU (this file,
  strategy docs, survey reports). It may not carry G4GPU source or build
  configuration.

## The physics-parity gate

Before *any* migration of NNBAR production to a G4GPU backend, the following
gate must pass and be documented in `docs/reports/g4gpu_physics_parity.md`:

### Inputs

- A fixed set of seeds: 1000 events of each canonical type (n̄+C signal,
  cosmic, beam neutron) at thesis-relevant configurations.
- Fixed Geant4 version (currently 11.2.2 on LUNARC).
- Fixed physics list (G4HadronPhysicsFTFP_BERT non-HP / HP variants per
  the existing reproducibility audit).

### Comparison

Run each event set twice: once with vanilla Geant4, once with G4GPU. Compare:

1. **Per-event bit-exact track lists** where the algorithm is mathematically
   identical (e.g. JIT-specialized kernel, QMC with the same realization
   replayed, perfect-hash lookup). Tolerance: zero bits of difference.
2. **Distribution-level KS tests** where the algorithm is statistically
   equivalent but not bit-identical (e.g. QMC variance reduction with new
   point sets). Tolerance: KS p-value ≥ 0.05 on every flagship histogram
   (deposited energy, multiplicity, vertex position, leading-particle KE),
   AND KL divergence ≤ 0.1%.
3. **Downstream observables**: full reconstruction chain run on both sets
   of events. The final cutflow survival, sensitivity, and limit numbers
   must agree within their own statistical uncertainty.

### Gate output

The parity report must:
- Document every event set, every observable, every test statistic.
- List every place where bit-exact agreement was achieved vs. where only
  distributional agreement holds.
- Receive explicit sign-off from the project owner before any production
  switchover is approved.

Until the gate passes and is signed off, G4GPU stays out of the NNBAR
pipeline. Full stop.

## Audit responsibility

Every active lane is responsible for not breaking this rule. Worker-3 and
worker-4 may work on G4GPU/Geant4 acceleration only inside their isolated
implementation/review scopes; worker-0 through worker-2 and the planner must
keep NNBAR production code and data on the vanilla-Geant4 path. The planner
runs a recurring `g4gpu-isolation-audit` task that:
- greps NNBAR_Detector for any G4GPU reference;
- inspects every SLURM script in `lunarc/` for binaries outside the vanilla
  build tree;
- checks every `simulator` column in newly-committed result Parquets is
  `geant4-11.2.2-ftfp-bert` or equivalent;
- flags any violation as `BLOCKED` in MASTER_PLAN.md.

## When this rule changes

The rule relaxes — does not disappear — once the parity gate passes for a
specific physics process. Migration is **incremental and per-process**,
never wholesale.

### Migration roadmap (when each phase becomes thesis-eligible)

| What migrates | Gate that must pass | Earliest milestone |
|---------------|---------------------|--------------------|
| Muon transport (Phase 1 + voxel geom) | Bit-exact muon range / MCS / energy-loss vs. vanilla G4 over the cosmic energy spectrum | After Phase 5 benchmark suite + isolation-audit lock-in |
| Geometry navigation (Phase 2/3) | Bit-exact distance-to-boundary on the actual NNBAR detector geometry, all 6 benchmark events | After Phase 3 + per-event regression |
| Optical photons (Phase 4 via Opticks) | Opticks's own published validation + NNBAR-specific scintillator/lead-glass match | After Opticks integration |
| EM showers | Bit-exact / KS-equivalent on the gamma_100mev benchmark | After Phase 6 (SoA) + Phase 8a (QMC) |
| Hadronic (signal channel) | Distribution-level KS on n̄+C final states; downstream observables (sensitivity) within statistical uncertainty | Only after every other phase has migrated cleanly |

### How a migration actually happens

1. The G4GPU process passes its own benchmark gate (Phase 5 + per-phase test).
2. A `<process>-parity` task runs both backends on the same fixed-seed event
   sets and writes a parity report to `docs/reports/`.
3. The parity report is reviewed and explicitly signed off (by the project
   owner, then by the thesis advisor for thesis-critical channels).
4. The NNBAR build gets a single, well-documented opt-in flag (e.g.
   `-DNNBAR_USE_G4GPU_MUON=ON`) defaulting to OFF.
5. A controlled side-by-side run on a real SLURM batch confirms downstream
   observables (sensitivity, acceptance, cutflow survival) move within their
   statistical uncertainty.
6. Default flips to ON for that process only. Other processes stay on
   vanilla Geant4.

Until step 6 succeeds for a process, that process keeps using vanilla
Geant4 in production. There is no "experimental NNBAR run with G4GPU
backend" branch in MASTER_PLAN — every NNBAR production result the thesis
cites uses the fully audited, signed-off configuration.

### What this guarantees

- Thesis numbers are always defensible: every observable can be traced to a
  Geant4 configuration that has either always been vanilla or been
  individually validated.
- Reviewers cannot reject a result on grounds of "you used unproven code,"
  because every G4GPU process used in production was signed off.
- G4GPU development can move fast in isolation because it is not coupled
  to thesis deadlines.

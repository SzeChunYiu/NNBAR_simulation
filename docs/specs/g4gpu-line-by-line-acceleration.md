# G4GPU — Line-by-Line Acceleration Strategy

## Top-level rule: ISOLATION FROM NNBAR

G4GPU is a **separate exploratory project**. The NNBAR thesis pipeline does
not — and will not — depend on G4GPU until the physics-parity gate (defined
in `docs/policies/g4gpu-isolation.md`) passes for the specific physics being
migrated. Every kernel, every benchmark, every result described below lives
strictly inside the G4GPU repo (`/Volumes/MyDrive/nnbar/geant4-gpu/` locally,
mirror on LUNARC). No code or build configuration crosses the boundary into
`NNBAR_Detector/` or `nnbar_reconstruction/`.

**Goal**: a Geant4-compatible Monte Carlo backend that nobody else can beat on
throughput, latency, accuracy, *or* developer ergonomics. We attack every layer
of the transport pipeline, not just GPU offload.

This document is the strategic root for G4GPU phases 5+. Phases 0–4 (muon,
voxel geometry, RTX, optical) are infrastructure. The differentiated work
starts here.

---

## The six layers

Every Geant4 step crosses six layers. Existing GPU projects (AdePT, Celeritas,
Opticks) optimize one or two. We hit all six.

| Layer | What | Hot lines in Geant4 | Existing work | Our attack |
|-------|------|---------------------|---------------|------------|
| **L0 — Microarchitecture** | SIMD lanes, cache, branch prediction, prefetch | Voxel descent branches, cross-section interpolation loops, RNG | VecGeom (CPU SIMD geometry) | Branchless inner loops, cache-line aligned SoA, hand-tuned AVX-512/NEON intrinsics on the CPU fallback path |
| **L1 — Algorithm / data structure** | Struct-of-arrays, linear BVH, contiguous track stacks, pool allocators | G4Track/G4Step allocation, G4Stack push/pop, G4Navigator touchable history | AdePT, Celeritas (partial) | Full SoA particle representation, lock-free per-species queues, zero-alloc step path |
| **L2 — Compute substrate** | CUDA cores, RT cores, Tensor cores | Step kernels, geometry queries, sampling | Opticks (RT, optical only), AdePT (CUDA, EM only) | **First to use all three concurrently**: RT for geometry, CUDA for EM/neutron, Tensor for hadronic + cross-section inference |
| **L3 — Mathematical / surrogate** | Replace tabulated physics with neural samplers; replace samplers with closed forms | Bremsstrahlung, ionization, hadronic cascades (FTFP/BERT internals) | None integrated into transport | Neural cross-section nets at warp level; transformer-sampled hadronic finals; differentiable shower libraries |
| **L4 — System** | Persistent kernels, GPU-resident state, zero-copy hits, async I/O | Per-event CPU↔GPU marshalling, hit collection via `G4SDManager` | None | One persistent kernel per partition; hits streamed to host via GPUDirect or pinned ring buffer |
| **L5 — Cross-stack** | Differentiable transport, end-to-end ML coupling | N/A (not in Geant4) | None in HEP | PyTorch-backed autograd through every step; detector geometry as a learnable parameter |

A speedup from any one layer alone is a paper. Stacking all six is a thesis
chapter that the rest of the field hasn't even attempted.

---

## Where the cycles actually go (CPU baseline)

Measurements from published Geant4 profiling, confirmed by our own profile
runs (TBD — Phase 5 task 0 below):

| Hot path | % of CPU | Why it's slow |
|----------|----------|---------------|
| Physics Interaction Length (PIL) | ~30% | Cross-section table interpolation, MFP arithmetic, virtual dispatch per process |
| Geometry navigation | ~25% | Voxel descent, touchable copies, transformation cascades |
| Physics sampling (DoIt) | ~20% | Differential cross-section sampling, secondary creation/allocation |
| Track stack + step management | ~15% | `new`/`delete` on G4Track/G4Step, particle-by-particle scheduling |
| Hit collection + I/O | ~10% | Virtual SD dispatch, `std::map` lookups |

We attack each in the order of $\text{cycles\_saved} \times \text{coverage}$.

---

## Phase plan (after Phases 0–4)

### Phase 5 — Profile-driven baseline + L0 microarchitecture wins
**Scope.** Establish the measurement framework before anything else.

- Build a benchmark suite: 6 canonical events (low-E gamma, high-E muon,
  n̄-C annihilation, cosmic shower, optical, beam neutron).
- Wire `perf record` / `perf annotate` and NVIDIA Nsight Compute into CI.
- Apply L0 wins to the CPU fallback: AVX-512/NEON intrinsics for the cross-
  section interpolator, branchless surface intersection in `G4Box`/`G4Tubs`,
  cache-line alignment of `G4Track` and friends, prefetch ahead of touchable
  walks.
- Validate against vanilla Geant4 with KS test on energy/momentum/position
  distributions. Tolerance: ≤ 1% KL divergence on flagship histograms.

**Acceptance.** CPU fallback shows ≥1.8× speedup on the benchmark suite with
no regression on validation. Profile output is committed to the repo so the
next phase has a baseline.

### Phase 6 — L1 algorithmic redesign (SoA tracks, lock-free queues)
- Replace AoS `G4Track` with `TrackSoA` (position, momentum, energy, weight
  in separate aligned arrays).
- Per-species lock-free stacks; warp-coherent dequeue.
- Pool allocator for secondaries (zero `new`/`delete` in hot loop).

**Acceptance.** Allocator profile shows zero allocations during transport;
3–5× speedup on the benchmark suite over Phase 5 baseline.

### Phase 7 — L2 tri-compute integration
- Geometry kernel uses RT cores (Phase 3 work).
- EM/neutron kernels use CUDA cores (existing Phase 1 muon kernel extended
  to EM bremsstrahlung + neutron elastic).
- **Tensor cores idle until Phase 8** — Phase 7 finishes the
  classical-substrate work first.

**Acceptance.** All three GPU compute types light up under Nsight on a
mixed-physics event. 15–30× speedup over Geant4 baseline.

### Phase 8 — L3 deterministic algorithm wins (validation-first)
**Reframe.** ML methods are a validation liability in HEP — distribution-level
agreement doesn't rule out out-of-domain failure, and the Geant4 collaboration
will not accept a black-box hadronic sampler. The differentiated work is
**deterministic CS/math methods that have not been applied to Geant4**, every
one of which can be validated to the bit against the reference.

Phase 8 is scoped from the survey in `docs/parallel-sessions/g4gpu-phase8-survey.md`.
The top candidates (subject to survey results):

- **Phase 8a — Quasi-Monte Carlo throughout transport**: replace HepJamesRandom
  with Sobol/Niederreiter sequences in the inner sampling loops. Variance
  drops from O(1/√N) to O(log^d(N)/N) — meaning we need 10–100× fewer events
  for the same statistical power. **Provably correct** because QMC is just a
  different (better-distributed) sample set, not a different physics model.
- **Phase 8b — SAH-BVH geometry** (production ray-tracer data structure):
  replace voxel descent with a surface-area-heuristic BVH built once per
  detector. Bit-exact same physics, faster traversal.
- **Phase 8c — JIT-specialized transport kernels** (LLVM ORC or Cling):
  compile a particle-specialized kernel (muon-only, gamma-only, ...) at
  startup, eliding branches for unused processes. Bit-exact same physics.
- **Phase 8d — Formal variance reduction** (stratified sampling + Russian
  roulette + splitting + control variates) with rigorous unbiasedness proofs.
  Used in reactor codes (MCNP) for decades; underused in Geant4.
- **Phase 8e — Cuckoo / perfect hashing for material lookup**: O(1)
  worst-case replacement of `std::map`. Bit-exact same physics.

**Why this is the moat (revised).** None of these methods have been
deeply applied to Geant4, every one is publishable, every one is
**validatable to the bit** by comparing fixed-seed runs. HEP reviewers
will accept these on the same grounds they accept any algorithm
optimization in a published Monte Carlo code.

**ML appears later, as Phase 10b (subordinate to autograd).** ML is only
considered for problems where no deterministic method works, and even then
only with explicit out-of-domain refusal so a deterministic fallback can
take over.

**Acceptance.** End-to-end speedup ≥ 50× on the benchmark suite from Phase 5,
with bit-exact agreement (within FP rounding) against vanilla Geant4 on the
six benchmark events.

### Phase 9 — L4 persistent GPU pipeline
- One persistent kernel per partition; never returns to CPU during an event.
- Hits stream to host via a pinned ring buffer (GPUDirect when available).
- Async I/O writes Parquet on a separate thread.

**Acceptance.** Zero CPU↔GPU synchronization points inside an event. End-to-
end latency for a single NNBAR signal event drops below 1 ms (vs. Geant4
baseline of ~50–200 ms).

### Phase 10 — L5 differentiable transport
- Autograd through the GPU step loop (PyTorch backend on top of the CUDA
  kernels).
- Detector geometry, material thicknesses, calibration constants become
  learnable parameters.
- Enables: gradient-based detector optimization, sim-in-the-loop ML training,
  uncertainty propagation via Jacobian eval.

**Acceptance.** Demonstrate gradient descent on TPC drift-velocity to match
a target waveform. The autograd path delivers gradients within 5% of
finite-difference baseline at 100× the speed.

---

## Cross-cutting invariants

These are not phases; they apply throughout.

0. **Isolation invariant**: G4GPU never touches the NNBAR production pipeline
   until the physics-parity gate passes for the specific physics being
   migrated. The recurring `g4gpu-isolation-audit` task verifies this.
1. **Validation parity**: every kernel ships with a Geant4 reference test.
   The CI matrix runs the benchmark suite on every commit and fails on
   distribution drift beyond tolerance.
2. **No silent fallbacks**: if a kernel can't service a request (e.g.
   Phase 8 hadronic net out-of-range energy), it returns an explicit
   `NotInDomain` and the dispatcher falls back to a labelled CPU path
   that gets logged. We track fallback coverage as a first-class metric.
3. **Public benchmarks**: AdePT/Celeritas/Opticks publish numbers. We
   publish numbers on the *same* events, side-by-side. The point is the
   moat, and the moat is visible only when measured against rivals.
4. **Differentiable from day one (Phase 8+)**: every new kernel is written
   in a way that PyTorch can trace through. No CUDA-graph dead ends.

---

## What "nobody beats us" actually means

- Phases 5–7: we match AdePT/Celeritas on EM, beat them on geometry latency,
  and ship optical via Opticks integration.
- Phase 8: we are the only project with integrated hadronic on GPU.
- Phase 9: we are the only project with truly persistent-kernel transport.
- Phase 10: we are the only HEP simulator with autograd.

Any one of these is a paper. The stack is a thesis chapter the rest of the
field will be playing catch-up on for years.

---

## Next concrete actions (this week)

1. Write `docs/parallel-sessions/g4gpu-phase5.md` — benchmark suite + profiling
   harness spec.
2. Queue Phase 5 task 0 (benchmark suite) for worker-0.
3. Download NVIDIA OptiX 9 SDK to
   `/projects/hep/fs10/shared/nnbar/billy/packages/optix-9.0/` so Phase 3
   isn't actually blocked.
4. Open a literature-survey task for Phase 8 (neural physics surrogates in
   HEP — Calochallenge, FastCaloGAN, etc. — so we don't reinvent).

This document supersedes the "Phase 3/4 PLANNED" stub in MASTER_PLAN.md.
The new phases (5–10) should be promoted to the main G4GPU table as NEXT
once their spec files exist.

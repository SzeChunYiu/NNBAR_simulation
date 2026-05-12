# Geant4 bottleneck database — physics sampling / DoIt hot path

Status: compact-safe worker-4 iteration 3. This starts the structured Geant4
bottleneck database required by `docs/parallel-sessions/g4-source-review.md`.
Legacy free-form iterations already covered PIL and geometry in
`docs/reports/g4_source_review_hotpaths.md`; this file therefore starts with
hot path 3, physics sampling / DoIt.

## Source provenance and profile basis

- LUNARC socket guard returned `Connected` before remote inspection.
- Authoritative NNBAR Geant4 install check:
  `/projects/hep/fs10/shared/nnbar/billy/packages/hibeam_env/bin/geant4-config
  --version --prefix` reported Geant4 `11.2.2` at
  `/projects/hep/fs10/shared/nnbar/billy/packages/hibeam_env`.
- A bounded LUNARC search under `/projects/hep/fs10/shared/nnbar/billy` found
  conda package artifacts but no extracted `source/` implementation tree. This
  iteration therefore used the same read-only upstream Geant4 `v11.2.2` source
  archive at `/tmp/geant4-v11.2.2` as the legacy hot-path report.
- Hot-path weight is inherited from the strategy/spec basis: physics sampling /
  DoIt is about 20% of Geant4 CPU. Per-entry self-percentages are `OPEN:` until
  Phase 5 perf runs map samples to exact lines on BasicExample/TestEm0/Hadr01.
- Isolation check: documentation only. No `NNBAR_Detector/`,
  `nnbar_reconstruction/`, `scripts/`, `lunarc/`, `slurm/`, or `macro/` paths
  were modified.

## References used by entries

- Devroye 1986, *Non-Uniform Random Variate Generation*.
- Vose 1991, *A linear algorithm for generating random numbers with a given
  distribution*.
- Futamura 1971/1983, partial evaluation / projection work.
- Hoelzle, Chambers, and Ungar 1991, polymorphic inline caches.
- Bentley 1975, multidimensional binary search trees.
- Stroustrup 2012, *Why you should avoid linked lists*.
- O'Neill 2014, PCG random-number generators.
- Blackman and Vigna 2018, scrambled linear pseudorandom generators.
- Trefethen 2013, *Approximation Theory and Approximation Practice*.

---

### BD-geant4-001  Moller/Bhabha delta-ray rejection sampler repeats branchy trial loops

| Field | Value |
|-------|-------|
| File | `source/processes/electromagnetic/standard/src/G4MollerBhabhaModel.cc` |
| Lines | 266-388 |
| Hot-path % (profile-measured) | DoIt family: about 20% aggregate Geant4 CPU per lane-spec basis; per-line self% `OPEN:` pending Phase 5 perf. |
| Category | 4 — Mathematical |
| Current pattern | Snippet: `rndmEngine->flatArray(2, rndm)` inside separate Moller and Bhabha rejection loops, followed by rational majorant tests and repeated `while(grej * rndm[1] > z)`. |
| Why slow | Every secondary sample pays a particle-charge branch, a variable-count rejection loop, two RNG draws per trial, divisions, and a hard-to-predict loop exit. Electron and positron cases are stable for a track but are interleaved in one generic routine. |
| Proposed fix | Build per-primary-type, per-energy-bin inverse-CDF or alias samplers for the accepted delta-ray energy fraction, with the existing rejection sampler retained as an exact fallback outside the tabulated validity envelope. Keep the same angular/energy conservation path after sampling. |
| Expected speedup | 1.2-1.6x inside this sampler on electron-rich EM workloads; 1-3% wall-clock if Moller/Bhabha DoIt dominates TestEm0-style runs. |
| Validation | Compare sampled `x`, delta kinetic energy, final primary energy, and angular spectra against vanilla on fixed material/energy grids; require KS p-value >= 0.05 and energy-momentum closure to roundoff, plus fallback activation logs at all table boundaries. |
| Implementation target | `geant4-fork` upstream MR `g4-beit-delta-alias-sampler`; optional `libMCAccel/core/sampling` alias primitive. |
| Citation | Devroye 1986; Vose 1991. |
| Status | OPEN |

### BD-geant4-002  Moller/Bhabha secondary emission allocates one dynamic particle per delta ray

| Field | Value |
|-------|-------|
| File | `source/processes/electromagnetic/standard/src/G4MollerBhabhaModel.cc` |
| Lines | 266-388 |
| Hot-path % (profile-measured) | DoIt secondary-creation family: per-line self% `OPEN:` pending Phase 5 allocation/perf trace. |
| Category | 6 — Memory allocation |
| Current pattern | Snippet: `auto delta = new G4DynamicParticle(...)` followed by `vdp->push_back(delta)`. |
| Why slow | A heap allocation sits on the successful path for every produced delta ray. In shower workloads this feeds allocator contention, cache misses, and later `G4Track` allocation in `G4ParticleChange`. |
| Proposed fix | Add a per-event secondary arena or fixed-capacity small-vector path for `G4DynamicParticle` objects emitted by EM models. Preserve ownership semantics by draining the arena through the existing `G4ParticleChange` interface at end of step. |
| Expected speedup | 1.1-1.4x for high-secondary EM DoIt sections; larger reduction in allocator samples when stacked with BD-geant4-011/013. |
| Validation | Run fixed-seed EM shower benchmarks with allocation tracing enabled; require identical secondary definitions, four-vectors, creator process, track IDs, and final histograms. |
| Implementation target | `g4gpu-phase6-secondary-arena` plus upstream Geant4 allocator MR. |
| Citation | Stroustrup 2012. |
| Status | OPEN |

### BD-geant4-003  Seltzer-Berger bremsstrahlung uses generic per-call dispatch for stable material state

| Field | Value |
|-------|-------|
| File | `source/processes/electromagnetic/standard/src/G4SeltzerBergerModel.cc` |
| Lines | 466-534 |
| Hot-path % (profile-measured) | DoIt family: about 20% aggregate Geant4 CPU; per-line self% `OPEN:` pending Phase 5 perf. |
| Category | 5 — Control flow |
| Current pattern | Snippet: `SelectTargetAtom(...)`, ternary dispatch between `SampleEnergyTransfer(...)` and `gSBSamplingTable->SampleEnergyTransfer(...)`, then `GetAngularDistribution()->SampleDirection(...)`. |
| Why slow | Material, current Z, sampling-table mode, and angular-distribution type are stable across many steps, but the routine redispatches through generic selectors and an angular virtual interface for each photon. |
| Proposed fix | JIT- or template-specialize a bremsstrahlung DoIt fast path keyed by `(particle, material-cuts-couple, sampling-table mode, angular distribution type)`, with guards for model/table changes. |
| Expected speedup | 1.1-1.3x inside Seltzer-Berger `SampleSecondaries`; 1-2% wall-clock on electron/photon shower benchmarks. |
| Validation | Record vanilla `(Z, gammaEnergy, gamma direction, final primary direction, finalE)` tuples and require specialized output to match when using the same sampler, or distribution-level agreement when paired with BD-geant4-004. |
| Implementation target | `g4gpu-phase5d-jit-brem-doit` for upstreamable fast-path experiment. |
| Citation | Futamura 1971/1983; Hoelzle, Chambers, and Ungar 1991. |
| Status | OPEN |

### BD-geant4-004  Seltzer-Berger energy-transfer rejection loop mixes table lookup and transcendentals per trial

| Field | Value |
|-------|-------|
| File | `source/processes/electromagnetic/standard/src/G4SeltzerBergerModel.cc` |
| Lines | 537-615 |
| Hot-path % (profile-measured) | DoIt bremsstrahlung sampling family: per-line self% `OPEN:` pending Phase 5 perf. |
| Category | 4 — Mathematical |
| Current pattern | Snippet: `gammaEnergy = std::sqrt(std::max(G4Exp(...)-fDensityCorr,0.))`, `gSBDCSData[fCurrentIZ]->Value(...)`, and a rejection test against `vmax`. |
| Why slow | The trial loop performs RNG, exponential, square root, 2D table interpolation, optional positron correction, and branchy majorant checks until acceptance. Trial count is data-dependent and diverges between tracks. |
| Proposed fix | Precompute per-Z/per-log-energy CDF tiles in the transformed variable and sample by alias or monotone inverse interpolation. Keep the current rejection kernel as the audited fallback for sparse or extreme tiles. |
| Expected speedup | 1.5-3x inside bremsstrahlung energy sampling; 2-5% wall-clock on high-stat EM shower workloads if this routine is a top DoIt symbol. |
| Validation | For each material/Z and kinetic-energy grid point, compare photon-energy spectra, mean energy loss, and tail probabilities to vanilla; require KS p-value >= 0.05 and no degradation in total energy conservation. |
| Implementation target | `g4gpu-phase8a-brem-inverse-cdf` plus `core/sampling/alias_table`. |
| Citation | Devroye 1986; Vose 1991; Trefethen 2013. |
| Status | OPEN |

### BD-geant4-005  Seltzer-Berger cross-section quadrature recomputes DCS table values for stable grids

| Field | Value |
|-------|-------|
| File | `source/processes/electromagnetic/standard/src/G4SeltzerBergerModel.cc` |
| Lines | 395-458 |
| Hot-path % (profile-measured) | EM cross-section / DoIt setup family: per-line self% `OPEN:` pending perf. |
| Category | 4 — Mathematical |
| Current pattern | Snippet: nested 8-point quadrature loops call `G4Exp(...)`, `ComputeDXSectionPerAtom(k)`, and `gSBDCSData[fCurrentIZ]->Value(...)` repeatedly for the same Z and energy grid. |
| Why slow | The integral shape is smooth over log-energy for fixed Z/material-density correction, but the current path recomputes exponentials and interpolated DCS values rather than reusing an error-bounded approximation. |
| Proposed fix | Build an error-bounded Chebyshev/spline cache for the restricted cross-section integral keyed by `(Z, particle, density correction, cut/max bins)`, with runtime spot checks against the current quadrature. |
| Expected speedup | 1.3-2x for repeated Seltzer-Berger cross-section/integral evaluation; wall-clock impact depends on how often tables are refreshed during benchmark setup and stepping. |
| Validation | Exhaustive grid comparison against vanilla quadrature with a relative-error tolerance tighter than existing physics-table interpolation error; rerun EM examples and require unchanged sampled spectra within statistical uncertainty. |
| Implementation target | `geant4-fork` upstream MR `g4-sb-brem-quadrature-cache`. |
| Citation | Trefethen 2013. |
| Status | OPEN |

### BD-geant4-006  FTF reggeon cascade scans all nucleons for each wounded nucleon

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/models/parton_string/diffraction/src/G4FTFModel.cc` |
| Lines | 456-555 |
| Hot-path % (profile-measured) | Hadronic DoIt / cascade family: per-line self% `OPEN:` pending Hadr01/Hadr02 perf. |
| Category | 2 — Algorithm |
| Current pattern | Snippet: for each involved nucleon, `StartLoop()` then `while ((Neighbour = ...GetNextNucleon()))`, compute impact distance, `G4Exp(...)`, RNG, and possibly allocate `G4DiffractiveSplitableHadron`. |
| Why slow | This is an O(wounded * nucleons) scan with an exponential and random branch for every unhit neighbor. Nucleon positions are spatial data, but the code does not use a spatial index or cutoff. |
| Proposed fix | Build a per-nucleus transverse spatial bin/k-d-tree view and only visit neighbors inside a conservative radius where the destruction probability is non-negligible; pretabulate the exponential probability curve and keep the full scan as debug validation. |
| Expected speedup | 1.5-4x for heavy-nucleus reggeon cascade sections; 2-6% wall-clock on hadronic workloads with large nuclei if FTF is active. |
| Validation | Replay fixed seeds and compare involved-nucleon sets with the exact full scan when the cutoff is disabled; with cutoff enabled, require a provable upper bound on omitted probability plus distribution agreement for multiplicity and excitation observables. |
| Implementation target | `g4gpu-phase8b-ftf-spatial-neighbor-index`. |
| Citation | Bentley 1975; Devroye 1986. |
| Status | OPEN |

### BD-geant4-007  FTF participant excitation mixes multi-way random branching with participant-list rewinds

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/models/parton_string/diffraction/src/G4FTFModel.cc` |
| Lines | 847-1028 |
| Hot-path % (profile-measured) | Hadronic DoIt / FTF participant family: per-line self% `OPEN:` pending perf. |
| Category | 5 — Control flow |
| Current pattern | Snippet: sequential `G4UniformRand()` decisions choose elastic/inelastic/annihilation branches, and the annihilation branch rewinds `theParticipants` to mark later interactions inactive. |
| Why slow | The hot loop contains unpredictable branches, repeated virtual/model calls, and an O(n) participant rewind after annihilation. The categorical choice and invalidation policy are conceptually separate but interleaved. |
| Proposed fix | Pre-sample an interaction category using a small categorical/alias sampler, store participant validity in a compact bitset, and apply annihilation invalidation without rewinding the iterator. |
| Expected speedup | 1.1-1.4x inside `ExciteParticipants`; larger gains for nucleus-nucleus events with many participant interactions. |
| Validation | Fixed-seed audit of category choices, participant validity masks, collision counts, and final string counts; distribution checks for elastic/inelastic/annihilation fractions when the categorical sampler changes RNG ordering. |
| Implementation target | `g4gpu-phase8b-ftf-participant-bitset`. |
| Citation | Vose 1991; Hoelzle, Chambers, and Ungar 1991. |
| Status | OPEN |

### BD-geant4-008  FTF nucleon-adjustment sampling uses nested retry loops with repeated Gaussian and rapidity calculations

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/models/parton_string/diffraction/src/G4FTFModel.cc` |
| Lines | 1523-1854 |
| Hot-path % (profile-measured) | Hadronic DoIt / FTF sampling family: per-line self% `OPEN:` pending perf. |
| Category | 4 — Mathematical |
| Current pattern | Snippet: nested loops capped at 1000/10000 retries repeatedly call `GaussianPt(...)`, `sqrt`, `G4Log`, mass checks, and rapidity-window rejection. |
| Why slow | Infeasible phase-space proposals are discovered only after expensive kinematic reconstruction. Retry counts vary by event and create long-tail latency in hadronic showers. |
| Proposed fix | Derive and cache a feasible-domain envelope for `(Pt, Xplus, Xminus)` before sampling; batch-generate candidate transverse momenta/fractions, then accept the first candidate passing the rapidity constraints. |
| Expected speedup | 1.3-3x in this sampling routine, with biggest gains in difficult near-threshold events where vanilla retries many times. |
| Validation | Capture vanilla proposal/acceptance traces for representative projectiles and nuclei; compare accepted kinematic variables and residual mass distributions, and require identical conservation-law pass/fail decisions. |
| Implementation target | `g4gpu-phase8b-ftf-feasible-envelope-sampler`. |
| Citation | Devroye 1986; Trefethen 2013. |
| Status | OPEN |

### BD-geant4-009  FTF string building combines linear duplicate search with per-string heap allocation

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/models/parton_string/diffraction/src/G4FTFModel.cc` |
| Lines | 2000-2190 |
| Hot-path % (profile-measured) | Hadronic DoIt / string-building family: per-line self% `OPEN:` pending perf. |
| Category | 3 — Data structure |
| Current pattern | Snippet: `std::find(primaries.begin(), primaries.end(), ...)`, `primaries.push_back(...)`, and repeated `new G4KineticTrack` / `new G4ExcitedString`. |
| Why slow | Duplicate detection is O(n^2) over participant pointers, while string and kinetic-track construction uses scattered allocations. Nucleus events are small enough for fixed-capacity data structures but too frequent for generic heap churn. |
| Proposed fix | Replace pointer duplicate search with a small fixed-capacity pointer set or participant-index bitset; allocate `G4KineticTrack` and `G4ExcitedString` objects from a per-interaction arena. |
| Expected speedup | 1.2-2x in string construction for high-multiplicity FTF events; reduces allocator samples and improves cache locality. |
| Validation | Compare string vector size/order, parton PDG codes, four-vectors, spectator counts, and final hadronic final state against vanilla fixed-seed events. |
| Implementation target | `g4gpu-phase6-ftf-string-arena`. |
| Citation | Stroustrup 2012. |
| Status | OPEN |

### BD-geant4-010  Bertini cascade retries full collision generations until late failure tests pass

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/models/cascade/cascade/src/G4CascadeInterface.cc` |
| Lines | 260-379 |
| Hot-path % (profile-measured) | Hadronic DoIt / Bertini cascade family: per-line self% `OPEN:` pending Hadr01/Hadr02 perf. |
| Category | 2 — Algorithm |
| Current pattern | Snippet: `output->reset(); collider->collide(...); balance->collide(...);` repeats inside a retry loop until proton/nucleus-specific checks stop requesting retries. |
| Why slow | The full cascade and balance computation are rerun before cheap infeasibility and conservation diagnostics are known. Failed retries are pure wasted DoIt CPU and create event-time outliers. |
| Proposed fix | Instrument retry reasons, then add early feasibility predicates and a bounded candidate batch that rejects impossible states before running the full collider path. Cache bullet/target conversion across attempts. |
| Expected speedup | 1.2-2x for retry-heavy Bertini events; wall-clock impact depends on retry frequency in Hadr01/Hadr02 and NNBAR hadronic samples. |
| Validation | Log retry reasons/counts and final secondaries for vanilla and optimized runs; require identical accepted final states when early predicates are logically equivalent, or distribution agreement when candidate ordering changes. |
| Implementation target | `g4gpu-phase8b-bertini-retry-pruner`. |
| Citation | Devroye 1986. |
| Status | OPEN |

### BD-geant4-011  Bertini output conversion allocates dynamic particles and reaction products in tight loops

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/models/cascade/cascade/src/G4CascadeInterface.cc` |
| Lines | 550-614 |
| Hot-path % (profile-measured) | Hadronic secondary-output family: per-line self% `OPEN:` pending allocation trace. |
| Category | 6 — Memory allocation |
| Current pattern | Snippet: `return new G4DynamicParticle(...)` in `makeDynamicParticle`, then `theParticleChange.AddSecondary(...)` for every outgoing particle and fragment. |
| Why slow | Cascade output is already held in contiguous vectors, but conversion to public Geant4 secondaries pays per-secondary heap allocation and virtual/interface overhead. |
| Proposed fix | Reserve secondary capacity from the outgoing vector sizes and add an arena-backed `AddSecondaryFromCascade` fast path that constructs `G4DynamicParticle`/track storage once per event. |
| Expected speedup | 1.1-1.5x in high-multiplicity cascade output conversion; strong allocator-sample reduction when combined with BD-geant4-013. |
| Validation | Compare outgoing particle definitions, kinetic energies, directions, creator model IDs, and secondary order against vanilla fixed-seed cascade events. |
| Implementation target | `g4gpu-phase6-cascade-secondary-arena`. |
| Citation | Stroustrup 2012. |
| Status | OPEN |

### BD-geant4-012  HepJamesRandom flatArray is scalar and branch-heavy despite being called in sampling loops

| Field | Value |
|-------|-------|
| File | `source/externals/clhep/src/JamesRandom.cc` |
| Lines | 239-270 |
| Hot-path % (profile-measured) | RNG service across DoIt/PIL/cascade: per-line self% `OPEN:` pending perf. |
| Category | 1 — Microarchitecture |
| Current pattern | Snippet: `flatArray` simply loops over `flat()`, whose subtract-with-borrow update has multiple branches and a rejection loop for endpoint values. |
| Why slow | Sampling routines request random pairs/batches, but the engine emits one scalar double at a time with branchy state updates. This prevents vectorization and wastes instruction cache in every sampler that calls `flatArray`. |
| Proposed fix | Add a batch-generation path that unrolls and vectorizes the existing James recurrence for bitwise legacy mode, plus an opt-in PCG/xoshiro engine adapter for non-bit-exact high-throughput validation modes. |
| Expected speedup | 1.2-2x for RNG throughput; event-level gain depends on the fraction of samples spent in `flatArray` across EM and hadronic DoIt. |
| Validation | Legacy mode must reproduce the exact JamesRandom sequence for scalar and array calls. New engines require TestU01/PractRand screening plus Geant4 fixed-physics distribution tests and explicit non-bit-exact provenance. |
| Implementation target | `g4gpu-phase5d-rng-batch-flatarray`. |
| Citation | O'Neill 2014; Blackman and Vigna 2018. |
| Status | OPEN |

### BD-geant4-013  G4ParticleChange creates heap tracks for every secondary crossing the model boundary

| Field | Value |
|-------|-------|
| File | `source/track/src/G4ParticleChange.cc` |
| Lines | 44-95 |
| Hot-path % (profile-measured) | Cross-DoIt secondary creation / tracking boundary: per-line self% `OPEN:` pending allocation trace. |
| Category | 6 — Memory allocation |
| Current pattern | Snippet: each overload constructs `G4Track* aTrack = new G4Track(...)`, sets flags/touchables, then calls `G4VParticleChange::AddSecondary(aTrack)`. |
| Why slow | This turns every secondary produced by EM and hadronic DoIt into at least one heap allocation before stack scheduling. Allocation cost and scattered track memory are paid even when the next stage could consume a compact batch. |
| Proposed fix | Introduce a per-event `G4Track` pool with stable handles and reserve capacity from model-reported secondary counts; later phases can expose a TrackSoA handoff for GPU/CPU batch scheduling. |
| Expected speedup | 1.2-2x in secondary-heavy showers and reduced memory fragmentation across all physics models. |
| Validation | Fixed-seed comparison of secondary count/order, parent-child IDs, touchable handles, global time, and stack behavior; allocator trace should show zero general-heap `G4Track` allocations in the optimized path. |
| Implementation target | `g4gpu-phase6-track-pool-secondary-handoff`. |
| Citation | Stroustrup 2012. |
| Status | OPEN |

## Next implementations from this DoIt iteration

1. `g4gpu-phase6-track-pool-secondary-handoff` (BD-geant4-013) — broad,
   physics-preserving, allocation-heavy bottleneck with bit-exact validation.
2. `g4gpu-phase6-secondary-arena` (BD-geant4-002) — pairs naturally with the
   track pool and should reduce allocator samples in EM showers.
3. `g4gpu-phase6-cascade-secondary-arena` (BD-geant4-011) — same allocation
   pattern in Bertini output conversion.
4. `g4gpu-phase8a-brem-inverse-cdf` (BD-geant4-004) — high local speedup, but
   requires distribution-level rather than bit-exact validation.
5. `g4gpu-phase8b-ftf-spatial-neighbor-index` (BD-geant4-006) — large
   heavy-nucleus upside, needs cutoff/probability proof.
6. `g4gpu-phase8b-ftf-feasible-envelope-sampler` (BD-geant4-008) — attacks
   long-tail hadronic retries.
7. `g4gpu-phase5d-rng-batch-flatarray` (BD-geant4-012) — cross-cutting, with
   bit-exact legacy mode available.
8. `g4gpu-phase5d-jit-brem-doit` (BD-geant4-003) — moderate risk and useful
   JIT proving ground.
9. `g4gpu-phase8b-bertini-retry-pruner` (BD-geant4-010) — profile first to
   confirm retry frequency.
10. `g4-sb-brem-quadrature-cache` (BD-geant4-005) — likely setup/table speed,
    lower priority until perf shows runtime impact.

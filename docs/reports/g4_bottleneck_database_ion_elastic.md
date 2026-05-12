# Geant4 ion-elastic and nuclear-fragmentation bottleneck database shard

Scope: structured source-review entries for Geant4 `v11.2.2` ion elastic
scattering and adjacent low-energy nuclear-fragmentation paths. This shard fills
`BD-geant4-111`--`120` and intentionally avoids the completed or reserved
`BD-geant4-001`--`110` and `BD-geant4-121`--`130` findings.

Source provenance: LUNARC `/projects/hep/fs10/shared/nnbar/billy/geant4-fork`
reported `git describe --tags --always --dirty` = `v11.2.2` and short commit
`f840b5da3a`. The local mirror `/tmp/geant4-v11.2.2` was SHA-256 matched
against LUNARC for every file cited here before extracting line numbers. The
queued name `G4UHadronElasticProcess` is obsolete in this source tree: no
`G4UHadronElasticProcess*` file exists in the v11.2.2 checkout, and Geant4
history records it as removed; the reviewed successor process is
`G4HadronElasticProcess`. No measured speedup or priority promotion is claimed
here; every `Hot-path %` remains `OPEN:` until Phase 5 perf maps ion-elastic,
heavy-ion, and fragmentation workloads to exact source lines.

## Entries

### BD-geant4-111  Ion-elastic physics construction builds runtime objects instead of immutable descriptors

| Field | Value |
|-------|-------|
| File | `source/physics_lists/constructors/hadron_elastic/src/G4IonElasticPhysics.cc` |
| Lines | 76-93 |
| Hot-path % (profile-measured) | Physics-list setup and worker-thread initialization: per-line self% `OPEN:` pending ion/heavy-ion startup profiles. |
| Category | 6 — Memory allocation |
| Current pattern | Snippet: `new G4HadronElasticProcess("ionElastic")`, `new G4NuclNuclDiffuseElastic`, `new G4CrossSectionElastic(ionElasticXS)`, then `AddDiscreteProcess`. |
| Why slow | Each thread/run constructs the same process/model/cross-section graph through general heap allocation and virtual registration, even though the topology is fixed for generic ions. |
| Proposed fix | Add an immutable ion-elastic process descriptor that owns prebuilt model/data-set factories and publishes thread-local process instances from a compact arena; keep the current path as the descriptor builder and fallback. |
| Expected speedup | 1.05-1.2x for ion-physics startup and worker initialization; no event-loop speedup claimed unless allocator contention appears in profiles. |
| Validation | Compare process names, subtype, model energy limits, registered cross-section data sets, and first `PostStepDoIt` result against vanilla Geant4 for `G4GenericIon` over representative materials. |
| Implementation target | `g4gpu-phase6-ion-elastic-process-descriptor`. |
| Citation | Berger et al. 2000 Hoard allocator; Lam, Rothberg, and Wolf 1991 locality optimization. |
| Status | OPEN |

### BD-geant4-112  Elastic PostStepDoIt recomputes cross-section gate, target sampling, and model choice per interaction

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/processes/src/G4HadronElasticProcess.cc` |
| Lines | 61-177 |
| Hot-path % (profile-measured) | Hadron/ion elastic post-step dispatch: per-line self% `OPEN:` pending Hadr01/Hadr02 and ion-therapy-like elastic profiles. |
| Category | 5 — Control flow |
| Current pattern | Snippet: `ComputeCrossSection(dynParticle, material)`, `SampleZandA(...)`, optional diffraction `ComputeRatio(...)`, `ChooseHadronicInteraction(...)`, then `hadi->ApplyYourself(...)`. |
| Why slow | The particle, material-cuts couple, process state, and usually the active elastic model are stable across many steps, but every interaction re-enters generic data-store dispatch, target sampling, diffraction checks, and virtual model selection. |
| Proposed fix | Add a guarded elastic-interaction snapshot keyed by `(process, particle, material-cuts-couple, isotope-table epoch, diffraction-policy)` that directly calls the active model and target sampler; fall back on any data-store or process-manager mutation. |
| Expected speedup | 1.05-1.3x inside ion/hadron elastic `PostStepDoIt`; larger if profiles show branch misses or virtual dispatch dominating short-step workloads. |
| Validation | Fixed-seed replay compares accepted/rejected interactions, sampled `(Z,A)`, selected model name, recoil threshold, outgoing primary direction/energy, and secondary list. Distributional validation compares elastic angular spectra and reaction rates with KS p >= 0.05. |
| Implementation target | `g4gpu-phase5d-elastic-poststep-snapshot`. |
| Citation | Futamura 1971 partial evaluation; Hoelzle, Chambers, and Ungar 1991 polymorphic inline caches. |
| Status | OPEN |

### BD-geant4-113  Elastic recoil finalization allocates a track and repeats model-ID lookup for one secondary

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/processes/src/G4HadronElasticProcess.cc` |
| Lines | 217-245 |
| Hot-path % (profile-measured) | Elastic recoil creation/finalization: per-line self% `OPEN:` pending recoil-rich ion/proton profiles. |
| Category | 6 — Memory allocation |
| Current pattern | Snippet: `new G4Track(p, track.GetGlobalTime(), track.GetPosition())`, `G4PhysicsModelCatalog::GetModelID("model_" + hadi->GetModelName())`, `AddSecondary(t)`, else `delete p`. |
| Why slow | A one-secondary elastic recoil still pays general heap allocation, string concatenation/model-catalog lookup, touchable handle assignment, and late kinetic-energy cut handling. |
| Proposed fix | Cache the creator model ID in the selected elastic-model snapshot and route recoil candidates through a per-thread small secondary arena that commits to `G4Track` only after the recoil cut passes. |
| Expected speedup | 1.05-1.25x in recoil-producing elastic interactions; allocator samples should drop for heavy-ion and shielding workloads with frequent nuclear recoils. |
| Validation | Compare recoil presence, kinetic energy, direction after `rotateUz`, weight, touchable handle, creator model ID, local/non-ionizing energy deposit, and parent track status against vanilla Geant4. |
| Implementation target | `g4gpu-phase6-elastic-recoil-arena`. |
| Citation | Berger et al. 2000 Hoard allocator; EASTL fixed-vector design notes. |
| Status | OPEN |

### BD-geant4-114  Nucl-nucl diffuse elastic builds a 300-by-199 angle table with scalar quadrature per element

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/models/coherent_elastic/src/G4NuclNuclDiffuseElastic.cc` |
| Lines | 1008-1078 |
| Hot-path % (profile-measured) | Ion-elastic model initialization/table build: per-line self% `OPEN:` pending heavy-ion startup and first-event profiles. |
| Category | 4 — Mathematical |
| Current pattern | Snippet: `fAngleTable = new G4PhysicsTable(fEnergyBin)`, loop over `fEnergyBin`, allocate `new G4PhysicsFreeVector(fAngleBin-1)`, and call `integral.Legendre10(...)` for each angle bin. |
| Why slow | The angle CDF is deterministic for `(projectile, element, energy-grid policy)`, but construction performs roughly `300 * 199` scalar quadratures per element and heap-allocates one vector per energy bin. |
| Proposed fix | Precompute compact table descriptors per `(projectile, Z, A, energy-grid version)` using vectorized quadrature or offline generation, memory-map them at startup, and retain the current builder as a validation oracle/fallback for unseen nuclei. |
| Expected speedup | 2-10x for ion-elastic table construction; wall-clock impact depends on element count and first-event latency. |
| Validation | Compare every cumulative angle-bin value against the current builder within double precision tolerance; event-level validation compares sampled invariant-t and lab-angle distributions. |
| Implementation target | `g4gpu-phase6-nuclnucl-angle-table-cache`. |
| Citation | Press et al. 2007 numerical quadrature; Lam, Rothberg, and Wolf 1991 locality optimization. |
| Status | OPEN |

### BD-geant4-115  SampleTableThetaCMS linearly scans element, energy, and cumulative angle bins

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/models/coherent_elastic/src/G4NuclNuclDiffuseElastic.cc` |
| Lines | 855-972 |
| Hot-path % (profile-measured) | Ion-elastic angle sampling: per-line self% `OPEN:` pending per-interaction profiles after table construction. |
| Category | 2 — Algorithm |
| Current pattern | Snippet: loop over `fElementNumberVector`, loop over `fEnergyBin` with `GetLowEdgeEnergy`, then loops over `fAngleBin-1` cumulative values before interpolation. |
| Why slow | Element and energy grids are immutable after table build, yet every sample performs O(number-of-elements + energy bins + angle bins) data-dependent scans and may call `InitialiseOnFly` for a missed element. |
| Proposed fix | Replace scans with an element-Z direct index, logarithmic energy-bin index from the known `G4PhysicsLogVector` parameters, and binary-search or alias descriptors for the monotone angle CDF. |
| Expected speedup | 1.3-3x inside table-based ion-elastic angle sampling for large element/material sets and many ion-elastic interactions. |
| Validation | Fixed-seed descriptor mode compares selected element-table index, energy bin, angle bin, interpolated angle, and invariant-t; distributional mode compares angle CDFs with KS/Kuiper tests. |
| Implementation target | `g4gpu-phase8b-ion-elastic-cdf-index`. |
| Citation | Cormen et al. 2009 binary search; Walker 1977 alias tables; Vose 1991 alias method. |
| Status | OPEN |

### BD-geant4-116  Diffuse-elastic probability recomputes Bessel/exponential/Coulomb terms for every integrand call

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/models/coherent_elastic/src/G4NuclNuclDiffuseElastic.cc` |
| Lines | 476-562 |
| Hot-path % (profile-measured) | Diffuse-elastic integrand evaluation during table build and direct sampling: per-line self% `OPEN:` pending ion-elastic profiles. |
| Category | 4 — Mathematical |
| Current pattern | Snippet: `BesselJzero(krt)`, `BesselJone(krt)`, `BesselOneByArg(krt)`, `G4Exp(...)`, Coulomb correction, and polynomial combination are recomputed per `theta`. |
| Why slow | Quadrature repeatedly evaluates a smooth one-dimensional function whose coefficients are fixed for a `(projectile, target, momentum)` state; transcendentals and Bessel approximations dominate scalar arithmetic. |
| Proposed fix | Hoist state-invariant coefficients into a sampler descriptor and use Chebyshev/minimax or tabulated segment polynomials for the angular integrand, with the current formula as the exact oracle. |
| Expected speedup | 1.5-4x inside diffuse-elastic integrand evaluation; table-build speedup compounds with BD-geant4-114. |
| Validation | Compare integrand values over dense theta grids, integrated CDF bins, and sampled scattering-angle distributions; require relative error below the existing table interpolation tolerance. |
| Implementation target | `g4gpu-phase8b-diffuse-elastic-polynomial-integrand`. |
| Citation | Hart 1968 computer approximations; Mason and Handscomb 2002 Chebyshev polynomials. |
| Status | OPEN |

### BD-geant4-117  Local Bessel J0/J1 approximations branch on scalar arguments and repeat polynomial work

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/models/coherent_elastic/src/G4NuclNuclDiffuseElastic.cc` |
| Lines | 2034-2132 |
| Hot-path % (profile-measured) | Bessel approximation helper used by diffuse-elastic probabilities: per-line self% `OPEN:` pending table-build/integrand profiles. |
| Category | 1 — Microarchitecture |
| Current pattern | Snippet: `if (modvalue < 8.0)` chooses one rational approximation, else computes `sqrt`, `cos`, and `sin`; `BesselJone` repeats the same branch family. |
| Why slow | Scalar branchy approximations are called from tight quadrature loops with adjacent theta values; the path cannot use vector lanes and repeats range reductions for correlated inputs. |
| Proposed fix | Provide a vectorized Bessel microkernel for angle-table construction and a cached small-argument polynomial pack for per-sample fallback; preserve the current scalar code as a reference mode. |
| Expected speedup | 1.2-2x in the Bessel-heavy portion of table construction on AVX2/AVX-512 CPUs; no physics change because the approximation target is unchanged. |
| Validation | Exhaustively compare J0/J1 values across the active `krt` domain, then rerun BD-geant4-114 table comparisons and elastic-angle spectra. |
| Implementation target | `g4gpu-phase5d-vector-bessel-diffuse-elastic`. |
| Citation | Hart 1968 computer approximations; Intel Optimization Reference Manual 2024 SIMD/vectorization guidance. |
| Status | OPEN |

### BD-geant4-118  Direct SampleThetaCMS fallback integrates many sub-intervals per sampled angle

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/models/coherent_elastic/src/G4NuclNuclDiffuseElastic.cc` |
| Lines | 722-768 |
| Hot-path % (profile-measured) | Direct diffuse-elastic angle sampling fallback: per-line self% `OPEN:` pending profiles that distinguish table and non-table paths. |
| Category | 2 — Algorithm |
| Current pattern | Snippet: compute `norm = integral.Legendre96(...)`, then loop `i = 1..100` and call `integral.Legendre10(...)` until cumulative probability crosses the random target, followed by Gaussian smearing. |
| Why slow | Inverse-CDF sampling is approximated by repeated quadrature per event, producing data-dependent loop length and many calls into the expensive integrand instead of using a prepared CDF. |
| Proposed fix | Route all production sampling through validated CDF descriptors; keep direct quadrature only for table generation and oracle tests, or replace it with a monotone inverse-CDF spline built once per state. |
| Expected speedup | 5-20x for any workload still hitting direct sampling; should also reduce long-tail latency from variable quadrature counts. |
| Validation | Compare direct sampler and descriptor sampler on angle, invariant-t, and lab-frame theta distributions for every projectile/target/energy bin, with fixed-seed oracle checks in fallback mode. |
| Implementation target | `g4gpu-phase8b-diffuse-elastic-inverse-cdf`. |
| Citation | Devroye 1986 non-uniform random variate generation; Walker 1977 alias tables. |
| Status | OPEN |

### BD-geant4-119  Low-energy ion fragmentation resamples impact parameter and walks nucleons until projectile participants appear

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/models/pre_equilibrium/exciton_model/src/G4LowEIonFragmentation.cc` |
| Lines | 63-186 |
| Hot-path % (profile-measured) | Low-energy ion fragmentation participant selection and precompound handoff: per-line self% `OPEN:` pending low-energy ion fragmentation profiles. |
| Category | 2 — Algorithm |
| Current pattern | Snippet: `while(0==particlesFromProjectile)` draws `(x,y)`, rejects outside the disk, checks `projectileHorizon`, loops `aPrim.GetNextNucleon()`, then loops target nucleons and calls `theModel->DeExcite(anInitialState)`. |
| Why slow | Participant counting repeatedly samples geometry and walks nucleon containers until a non-empty projectile participant set appears; the same `(A,Z)` nuclei have reusable radial occupancy statistics. |
| Proposed fix | Precompute per-nucleus participant occupancy descriptors or alias tables over impact-parameter bins, then sample participant counts and charge counts directly with an exact-nucleon-loop fallback for validation and rare nuclei. |
| Expected speedup | 1.3-3x inside participant selection for ion-fragmentation workloads; wall-clock depends on low-energy ion reaction frequency. |
| Validation | Compare participant multiplicities, charged counts, target/projectile residual `(A,Z)`, excitation inputs, and final de-excitation products; require event-level conservation of charge, baryon number, energy, and momentum. |
| Implementation target | `g4gpu-phase8b-lowe-ion-participant-sampler`. |
| Citation | Walker 1977 alias tables; Devroye 1986 non-uniform random variate generation; Cormen et al. 2009 preprocessing/query tradeoffs. |
| Status | OPEN |

### BD-geant4-120  Precompound fragment emission integrates the PDF and then rejection-samples with a fixed retry cap

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/models/pre_equilibrium/exciton_model/src/G4PreCompoundFragment.cc` |
| Lines | 81-171 |
| Hot-path % (profile-measured) | Precompound fragment emission probability and kinetic-energy sampling: per-line self% `OPEN:` pending fragmentation/de-excitation profiles. |
| Category | 4 — Mathematical |
| Current pattern | Snippet: `nbins = std::max(nbins, 4)`, loop over `ProbabilityDistributionFunction(e, fr)` with early break, then `for(i=0; i<100; ++i)` rejection-samples `T`. |
| Why slow | Emission probability and sampling rebuild a one-dimensional distribution from scalar PDF calls for each fragment state, while related residual nuclei revisit similar energy windows and Coulomb-barrier parameters. |
| Proposed fix | Cache normalized kinetic-energy CDF descriptors keyed by `(fragment type, residual A/Z, excitation-energy bin, Coulomb-barrier option)` and sample with binary-search/alias or monotone-spline inversion; retain current integration as oracle. |
| Expected speedup | 1.5-5x inside fragment-emission sampling where precompound de-excitation dominates; should also reduce retry-tail variance from rejection sampling. |
| Validation | Compare integrated emission probabilities, sampled kinetic-energy spectra, emitted fragment type frequencies, and full de-excitation conservation checks against vanilla Geant4. |
| Implementation target | `g4gpu-phase8b-precompound-fragment-cdf`. |
| Citation | Devroye 1986 non-uniform random variate generation; Vose 1991 alias method; Press et al. 2007 numerical methods. |
| Status | OPEN |

## Next implementation candidates

1. `g4gpu-phase8b-diffuse-elastic-inverse-cdf` (BD-geant4-115/118): high
   validatability because it can be compared directly against existing CDFs and
   direct quadrature.
2. `g4gpu-phase6-nuclnucl-angle-table-cache` (BD-geant4-114/116/117): best
   startup/first-event win; validate by byte-level or tolerance-level table
   comparison before any physics run.
3. `g4gpu-phase5d-elastic-poststep-snapshot` (BD-geant4-112/113): likely small
   but broad event-loop win if elastic dispatch appears in Hadr/ion profiles.
4. `g4gpu-phase8b-precompound-fragment-cdf` (BD-geant4-119/120): targeted at
   low-energy ion fragmentation and can be validated with conservation and
   distribution tests before integration.

# Geant4 charged-transport bottleneck database shard

Scope: structured source-review entries for Geant4 `v11.2.2` charged-particle
transport and fluctuation paths: Urban/Wentzel multiple scattering,
Wentzel-style Coulomb scattering, Bethe-Bloch ionisation, and universal energy
loss fluctuations. This shard extends the existing Geant4 database beyond
`BD-geant4-001`--`080` and intentionally avoids the prior PIL, geometry,
generic DoIt, track/stack, hit/SD, optical-photon, EM/gamma, and neutron-HP
entries.

Source provenance: LUNARC `/projects/hep/fs10/shared/nnbar/billy/geant4-fork`
reported `git describe --tags --always --dirty` = `v11.2.2` and short commit
`f840b5da3a`. The local mirror `/tmp/geant4-v11.2.2` was SHA-256 matched
against LUNARC for every file cited here before extracting line numbers.
No measured speedup or priority promotion is claimed here; every `Hot-path %`
remains `OPEN:` until Phase 5 perf maps TestEm/medical-physics/HEP charged
particle workloads to exact source lines.

## Entries

### BD-geant4-081  Urban MSC cross-section correction table is searched and interpolated per query

| Field | Value |
|-------|-------|
| File | `source/processes/electromagnetic/standard/src/G4UrbanMscModel.cc` |
| Lines | 173-414 |
| Hot-path % (profile-measured) | Multiple-scattering cross-section query: per-line self% `OPEN:` pending charged-particle perf. |
| Category | 3 — Data structure |
| Current pattern | Snippet: `while ((iZ>=0)&&(Zdat[iZ]>=atomicNumber))`, `while ((iT>=0)&&(Tdat[iT]>=eKineticEnergy))`, then table interpolation through `celectron`/`cpositron`. |
| Why slow | The material element and energy grids are small and immutable, but every call redoes reverse linear searches, repeated relativistic transforms, and branch-specific coefficient interpolation. |
| Proposed fix | Build per-particle/material correction descriptors with cached Z bracket, low-energy T brackets, inverse widths, and charge-sign coefficient spans; keep the scalar formula as table-build/fallback oracle. |
| Expected speedup | 1.05-1.25x inside Urban MSC cross-section lookup for charged-particle workloads with repeated material/energy bins. |
| Validation | Exhaustively compare cross sections over active materials, particle charge signs, and log-energy grids against the current function within double precision tolerance; event-level validation compares step-length and angular spectra. |
| Implementation target | `g4gpu-phase6-urban-msc-correction-cache`. |
| Citation | Cormen et al. 2009 binary search/interpolation; Lam, Rothberg, and Wolf 1991 locality optimization. |
| Status | OPEN |

### BD-geant4-082  Urban MSC true-path limiter carries all stepping algorithms in one hot branch ladder

| Field | Value |
|-------|-------|
| File | `source/processes/electromagnetic/standard/src/G4UrbanMscModel.cc` |
| Lines | 434-670 |
| Hot-path % (profile-measured) | Urban MSC step limitation: per-line self% `OPEN:` pending electron/muon step profiles. |
| Category | 5 — Control flow |
| Current pattern | Snippet: `if (steppingAlgorithm == fUseDistanceToBoundary) ... else if(fUseSafety) ... else if(fUseSafetyPlus) ... else`, with boundary, safety, range, and randomization branches. |
| Why slow | A run normally uses one MSC stepping algorithm and stable boundary policy, yet each charged step carries rare branches, repeated safety conversions, and duplicated `Randomizetlimit()` decisions. |
| Proposed fix | Split the limiter into policy-specialized thunks selected at model setup, hoisting invariant algorithm/skin/range policy and retaining a guarded generic fallback for runtime parameter changes. |
| Expected speedup | 1.05-1.2x in Urban MSC step-limit code; broader if branch-predictor pressure is visible in fine-grained electron transport. |
| Validation | Fixed-seed replay compares true path length, geometric path length, boundary status, lateral-displacement flag, and final step limitation for every supported stepping algorithm. |
| Implementation target | `g4gpu-phase5d-urban-msc-policy-specialization`. |
| Citation | Futamura 1971 partial evaluation; Hoelzle, Chambers, and Ungar 1991 polymorphic inline caches. |
| Status | OPEN |

### BD-geant4-083  Urban MSC angle sampler recomputes distribution parameters and transcendental tails per step

| Field | Value |
|-------|-------|
| File | `source/processes/electromagnetic/standard/src/G4UrbanMscModel.cc` |
| Lines | 828-972 |
| Hot-path % (profile-measured) | Urban MSC angular sampling: per-line self% `OPEN:` pending TestEm/charged-track perf. |
| Category | 4 — Mathematical |
| Current pattern | Snippet: `G4Exp(-tau)`, `G4Log(lambdaeff/currentRadLength)`, `G4Exp(G4Log(b1)*c1)`, then `flatArray(2, rndmarray)` plus extra scalar draws for tails. |
| Why slow | The accepted angular distribution is parameterized by slowly varying `(tau, material radiation length, coefficient set)`, but every step recomputes exponent/log transforms and samples scalar branchy tail paths. |
| Proposed fix | Precompute compact angular-sampler coefficient packs on `(material, particle, tau/log-energy bin)` and use a direct or piecewise inversion sampler with the current routine as validation fallback. |
| Expected speedup | 1.15-2x inside Urban MSC angle sampling when angle generation dominates charged-electron workloads. |
| Validation | Compare `cos(theta)`, azimuth, lateral displacement, and final momentum-direction distributions per material and energy bin; require fixed-seed equivalence in fallback mode and KS p >= 0.05 for accelerated samplers. |
| Implementation target | `g4gpu-phase8b-urban-msc-angle-sampler`. |
| Citation | Devroye 1986 non-uniform random variate generation; Walker 1977 alias tables; Vose 1991 alias method. |
| Status | OPEN |

### BD-geant4-084  Wentzel VI transport cross section recomputes per-element target state every step

| Field | Value |
|-------|-------|
| File | `source/processes/electromagnetic/standard/src/G4WentzelVIModel.cc` |
| Lines | 704-754 |
| Hot-path % (profile-measured) | Wentzel VI transport cross section: per-line self% `OPEN:` pending charged-hadron/electron perf. |
| Category | 3 — Data structure |
| Current pattern | Snippet: loop over material elements calls `wokvi->SetupTarget(...)`, `ComputeTransportCrossSectionPerAtom`, `ComputeNuclearCrossSection`, and `ComputeElectronCrossSection`, then fills `xsecn`/`prob`. |
| Why slow | Material composition, cuts, and element Z values are stable across many steps; the current path rebuilds target state and cumulative element probabilities on every cross-section query. |
| Proposed fix | Cache a per-material Wentzel element descriptor containing density, cut, target setup values, and cumulative nuclear/electron weights for log-energy and `cosTheta` bins. |
| Expected speedup | 1.1-1.4x inside Wentzel VI cross-section setup for multi-element materials; also reduces downstream element-selection work. |
| Validation | Compare total transport cross section, `xtsec`, cumulative `xsecn`, and electron-ratio `prob` arrays over material/cut/energy grids; event-level checks compare scattering rates. |
| Implementation target | `g4gpu-phase6-wentzel-element-xs-cache`. |
| Citation | Stroustrup 2012 data-oriented containers; Lam, Rothberg, and Wolf 1991 locality optimization. |
| Status | OPEN |

### BD-geant4-085  Wentzel VI mixed single/multiple scattering loop linearly selects elements and samples scalar substeps

| Field | Value |
|-------|-------|
| File | `source/processes/electromagnetic/standard/src/G4WentzelVIModel.cc` |
| Lines | 494-675 |
| Hot-path % (profile-measured) | Wentzel VI scattering sampler: per-line self% `OPEN:` pending charged-particle perf. |
| Category | 5 — Control flow |
| Current pattern | Snippet: a `do` loop switches `singleScat`, linearly scans `xsecn` for the selected element, calls `SampleSingleScattering`, or samples multiple-scattering `z` with a rejection loop. |
| Why slow | The loop interleaves two physically distinct paths, emits unpredictable branches, reuses scalar random draws, and pays O(number-of-elements) selection whenever single scattering occurs. |
| Proposed fix | Split single- and multiple-scattering kernels, select elements through the cached cumulative descriptor from BD-geant4-084, and batch scalar random draws for the chosen path. |
| Expected speedup | 1.1-1.6x inside Wentzel sampling, depending on single-scattering frequency and material element count. |
| Validation | Fixed-seed fallback compares substep count, selected element, direction update, displacement, and proposed momentum; accelerated mode validates angular and displacement distributions. |
| Implementation target | `g4gpu-phase6-wentzel-sampler-split`. |
| Citation | Futamura 1971 partial evaluation; Herlihy and Shavit 2012 per-thread data structures. |
| Status | OPEN |

### BD-geant4-086  Wentzel single-scattering sampler evaluates form-factor/Mott rejection per trial

| Field | Value |
|-------|-------|
| File | `source/processes/electromagnetic/standard/src/G4WentzelOKandVIxSection.cc` |
| Lines | 331-382 |
| Hot-path % (profile-measured) | Wentzel single-scattering angle sampling: per-line self% `OPEN:` pending Coulomb/MSC perf. |
| Category | 2 — Algorithm |
| Current pattern | Snippet: sample `z1`, branch on nuclear form-factor mode, optionally call `fMottXSection->SetupKinematic(...)` and `RatioMottRutherfordCosT(...)`, then reject with `fMottFactor*flat() <= grej`. |
| Why slow | Form-factor and Mott-ratio evaluation occur in the variable-count rejection path even though target Z, energy, and angular cut bins are stable for many scatters. |
| Proposed fix | Build per-`(particle, Z, energy-bin, cosT range, form-factor mode)` CDF/alias samplers for the accepted angle distribution; retain current rejection as oracle and out-of-domain fallback. |
| Expected speedup | 1.2-2.5x inside single-scattering angle generation when Mott/form-factor corrections are active. |
| Validation | Compare accepted `cos(theta)`, azimuth, electron/nuclear branch, and recoil observables across Z and energy bins; require tail quantiles to match legacy rejection within statistical tolerance. |
| Implementation target | `g4gpu-phase8b-wentzel-single-scatter-alias`. |
| Citation | Walker 1977 alias tables; Vose 1991 alias method; Devroye 1986 non-uniform random variate generation. |
| Status | OPEN |

### BD-geant4-087  Bethe-Bloch dE/dx recalculates material correction stack per query

| Field | Value |
|-------|-------|
| File | `source/processes/electromagnetic/standard/src/G4BetheBlochModel.cc` |
| Lines | 245-329 |
| Hot-path % (profile-measured) | Bethe-Bloch restricted stopping power: per-line self% `OPEN:` pending charged-hadron/muon perf. |
| Category | 3 — Data structure |
| Current pattern | Snippet: material ionisation fields, ICRU90 lookup, density correction, shell correction, Barkas/high-order correction, and several `G4Log` evaluations are recomputed in one query path. |
| Why slow | The material correction state and cut-dependent terms are stable or slowly varying over log-energy bins, but the function repeatedly traverses material/ionisation objects and correction helpers. |
| Proposed fix | Cache per-material restricted-stopping descriptors with ICRU90 index, ionisation constants, correction handles, and log-energy interpolation blocks for the active particle/cut configuration. |
| Expected speedup | 1.05-1.3x inside dE/dx evaluation for charged-hadron and muon workloads. |
| Validation | Compare dE/dx over dense energy/cut grids for every active material and particle type; event-level validation checks range, deposited-energy spectra, and production-cut behavior. |
| Implementation target | `g4gpu-phase6-bethe-bloch-dedx-cache`. |
| Citation | Lam, Rothberg, and Wolf 1991 locality optimization; Press et al. 2007 interpolation. |
| Status | OPEN |

### BD-geant4-088  Bethe-Bloch delta-ray sampler repeats scalar rejection and immediate secondary allocation

| Field | Value |
|-------|-------|
| File | `source/processes/electromagnetic/standard/src/G4BetheBlochModel.cc` |
| Lines | 375-474 |
| Hot-path % (profile-measured) | Ionisation delta-ray production: per-line self% `OPEN:` pending charged-hadron perf. |
| Category | 6 — Memory allocation |
| Current pattern | Snippet: rejection samples `deltaKinEnergy` with `flatArray(2, rndm)`, may reject via projectile form factor, computes direction, then `new G4DynamicParticle(theElectron, ...)` and `vdp->push_back(delta)`. |
| Why slow | The sampler combines scalar rejection, optional angular-distribution dispatch, and heap allocation before the generic EM finalizer can apply cuts or batch secondary handling. |
| Proposed fix | Add a Bethe-Bloch delta-ray direct/alias sampler per energy-bin where valid, and route accepted delta rays into the shared EM secondary arena rather than allocating immediately. |
| Expected speedup | 1.1-1.8x inside delta-ray production for secondary-rich charged-particle tracks; allocator reduction composes with existing EM arena tasks. |
| Validation | Compare delta-ray energy, direction, rejection rate, secondary count/order, and primary energy balance; distributional validation uses KS tests on delta-ray spectra. |
| Implementation target | `g4gpu-phase8b-bethe-bloch-delta-sampler`. |
| Citation | Walker 1977 alias tables; Berger et al. 2000 Hoard allocator. |
| Status | OPEN |

### BD-geant4-089  Coulomb scattering recomputes target isotope, cross sections, and recoil object per secondary

| Field | Value |
|-------|-------|
| File | `source/processes/electromagnetic/standard/src/G4eCoulombScatteringModel.cc` |
| Lines | 212-301 |
| Hot-path % (profile-measured) | Coulomb scattering secondary sampling: per-line self% `OPEN:` pending charged-particle perf. |
| Category | 3 — Data structure |
| Current pattern | Snippet: `SelectTargetAtom(...)`, `SetupTarget(...)`, nuclear/electron cross-section calls, `SelectIsotopeNumber(...)`, `GetIon(...)`, and optional `new G4DynamicParticle(ion, dir, trec)`. |
| Why slow | Target element/isotope properties and recoil thresholds are stable for material and energy bins, but the sampler rediscoveres them and allocates an ion recoil object on each qualifying scatter. |
| Proposed fix | Cache Coulomb target descriptors with isotope masses, target setup values, and recoil-threshold policy; emit recoils through a secondary arena/pool after the cut decision is known. |
| Expected speedup | 1.05-1.3x in Coulomb scattering paths; larger allocator reduction in workloads with explicit nuclear recoils above threshold. |
| Validation | Fixed-seed replay compares selected element/isotope, recoil kinetic energy, recoil direction, non-ionizing deposit, and primary final energy; distributional tests compare scattering-angle and recoil spectra. |
| Implementation target | `g4gpu-phase6-coulomb-target-recoil-cache`. |
| Citation | Stroustrup 2012 data-oriented containers; Berger et al. 2000 Hoard allocator. |
| Status | OPEN |

### BD-geant4-090  Universal fluctuation model resizes heap random buffers in the ionisation tail sampler

| Field | Value |
|-------|-------|
| File | `source/processes/electromagnetic/standard/src/G4UniversalFluctuation.cc` |
| Lines | 89-238 |
| Hot-path % (profile-measured) | Energy-loss fluctuation sampling: per-line self% `OPEN:` pending charged-track perf. |
| Category | 6 — Memory allocation |
| Current pattern | Snippet: `G4Poisson(p3)` chooses `nnb`; if `nnb > sizearray`, the code `delete [] rndmarray; rndmarray = new G4double[nnb];`, then loops over `flatArray(nnb, rndmarray)`. |
| Why slow | Rare ionisation-tail draws can resize the heap buffer on the sampling path, and the per-draw loop consumes scalar randoms even though the tail size is known after the Poisson draw. |
| Proposed fix | Replace `rndmarray` with a thread-local small-buffer/vector-capacity policy and batch-generate randoms into fixed-capacity spans; optionally prebucket high-`p3` tail sampling into direct compound-Poisson kernels. |
| Expected speedup | 1.05-1.4x inside fluctuation sampling with reduced allocator outliers; strongest for thin-step charged-particle transport. |
| Validation | Compare sampled energy-loss distributions, Gaussian/Gamma/Glandz branch frequencies, Poisson tail counts, and total deposited energy over thin and thick absorbers. |
| Implementation target | `g4gpu-phase6-universal-fluctuation-buffer`. |
| Citation | Berger et al. 2000 Hoard allocator; Devroye 1986 non-uniform random variate generation. |
| Status | OPEN |

## Next implementations after charged-transport shard

1. `g4gpu-phase8b-urban-msc-angle-sampler` from BD-geant4-083: likely highest
   local sampler speedup, but requires careful angular-tail validation.
2. `g4gpu-phase6-wentzel-element-xs-cache` from BD-geant4-084: low-risk cache
   that feeds the Wentzel sampler split and Coulomb target descriptor work.
3. `g4gpu-phase8b-wentzel-single-scatter-alias` from BD-geant4-086: direct
   sampler for the Mott/form-factor rejection loop.
4. `g4gpu-phase6-bethe-bloch-dedx-cache` from BD-geant4-087: broadly useful
   for muon, proton, ion, and medical-physics workloads.
5. `g4gpu-phase8b-bethe-bloch-delta-sampler` from BD-geant4-088: pairs with
   the existing EM secondary-arena roadmap.
6. `g4gpu-phase6-universal-fluctuation-buffer` from BD-geant4-090: compact
   allocator-outlier fix with straightforward distribution tests.
7. `g4gpu-phase5d-urban-msc-policy-specialization` from BD-geant4-082: a
   controlled partial-evaluation task for the current MSC stepping policy.

# Geant4 optical-photon bottleneck database shard

Scope: additional structured source-review entries for Geant4 `v11.2.2`
optical-photon boundary, production, wavelength-shifting, and Rayleigh paths.
This shard extends the existing database beyond `BD-geant4-001`--`050` and
intentionally does not repeat the prior PIL, geometry, track/stack, hit/SD, or
generic DoIt entries.

Source provenance: LUNARC `/projects/hep/fs10/shared/nnbar/billy/geant4-fork`
reports `git describe --tags --always --dirty` = `v11.2.2` and short commit
`f840b5da3a`. The local mirror `/tmp/geant4-v11.2.2` was hash-matched against
LUNARC for all files cited in this shard before extracting line numbers.
No speedup or priority promotion is claimed here; every `Hot-path %` remains `OPEN:` until OpNovice2 or optical-calorimeter perf assigns measured self-time.

## Entries

### BD-geant4-051  Boundary PostStepDoIt repeats group-velocity lookups on small boundary steps

| Field | Value |
|-------|-------|
| File | `source/processes/optical/src/G4OpBoundaryProcess.cc` |
| Lines | 146-205 |
| Hot-path % (profile-measured) | Optical boundary PostStepDoIt: per-line self% `OPEN:` pending OpNovice2 / optical-calorimeter perf. |
| Category | 3 — Data structure |
| Current pattern | Snippet: `fMaterial2->GetMaterialPropertiesTable()`, then `aMPT->GetProperty(kGROUPVEL)`, then `groupvel->Value(fPhotonMomentum, idx_groupvel)` on the step-too-small boundary exit. |
| Why slow | Optical photons can bounce through many tolerance-scale boundary steps; each one pointer-chases material-property metadata and re-enters a generic physics-vector lookup even when the material pair and momentum bin are unchanged. |
| Proposed fix | Add a boundary-pair optical-property cache keyed by `(preMaterial, postMaterial, property, momentum-bin)` with invalidation tied to material-property-table mutation, falling back to the generic lookup for mutable tables. |
| Expected speedup | 1.05-1.25x in boundary-heavy optical sections; higher for scintillator/lead-glass geometries with many tolerance-limited surface bounces. |
| Validation | Fixed-seed optical replay must match velocity and time-of-flight bit-for-bit when the cached value is produced by the same `G4PhysicsVector::Value` bin; histogram KS p >= 0.05 for boundary timestamps when fallback paths are exercised. |
| Implementation target | `g4gpu-phase5d-optical-boundary-property-cache`. |
| Citation | Stroustrup 2012 data-oriented containers; Intel 2024 cache-optimization guidance. |
| Status | OPEN |

### BD-geant4-052  Facet-normal sampling uses nested rejection loops and scalar transcendentals

| Field | Value |
|-------|-------|
| File | `source/processes/optical/src/G4OpBoundaryProcess.cc` |
| Lines | 659-720 |
| Hot-path % (profile-measured) | Optical rough-surface boundary sampling: per-line self% `OPEN:` pending surface-model perf. |
| Category | 4 — Mathematical |
| Current pattern | Snippet: `alpha    = G4RandGauss::shoot(0.0, sigma_alpha)`, `sinAlpha = std::sin(alpha)`, then `} while(G4UniformRand() * f_max > sinAlpha || alpha >= halfpi);`; random `phi` feeds `std::cos`, `std::sin`, `facetNormal.rotateUz(normal)`, and the polish branch retries while `smear.mag2() > 1.0`. |
| Why slow | Rough-surface paths pay unpredictable rejection counts, multiple scalar transcendentals, and normalization/rotation work per bounce; this is branch- and RNG-heavy for optical simulations with diffuse or ground finishes. |
| Proposed fix | Precompute per-`sigma_alpha` alias/CDF tables for the truncated `g(alpha) sin(alpha)` distribution and provide a direct sphere-cap sampler for the polish branch; keep rejection code as the validation oracle. |
| Expected speedup | 1.2-2.0x in rough-boundary normal sampling; wall-clock impact depends on fraction of optical photons hitting ground/LUT/DAVIS surfaces. |
| Validation | Compare sampled facet-normal distributions with Kuiper/KS tests over `alpha`, `phi`, and reflected-angle histograms; replay fixed rough-boundary seeds with a compatibility mode that consumes the old RNG sequence. |
| Implementation target | `g4gpu-phase8b-optical-facet-normal-sampler`. |
| Citation | Walker 1977 alias tables; Vose 1991 alias method. |
| Status | OPEN |

### BD-geant4-053  LUT boundary reflection rejection-samples angular bins one photon at a time

| Field | Value |
|-------|-------|
| File | `source/processes/optical/src/G4OpBoundaryProcess.cc` |
| Lines | 820-891 |
| Hot-path % (profile-measured) | Optical LUT/DAVIS boundary model: per-line self% `OPEN:` pending LUT-surface perf. |
| Category | 2 — Algorithm |
| Current pattern | Snippet: `thetaIndex = (G4int)G4RandFlat::shootInt(thetaIndexMax - 1);`, `phiIndex   = (G4int)G4RandFlat::shootInt(phiIndexMax - 1);`, then `angularDistVal = fOpticalSurface->GetAngularDistributionValue(` inside a loop ending `} while(!G4BooleanRand(angularDistVal));` before rotating momentum/polarization. |
| Why slow | Acceptance-rejection over 2D angular bins has data-dependent loop counts and random table accesses; a low-probability bin distribution can burn many RNG calls and cache misses per reflected photon. |
| Proposed fix | Build per-incident-angle alias tables for `(theta, phi)` bins at optical-surface initialization and sample one bin in O(1), with the legacy rejection sampler retained behind a bit-compatible flag. |
| Expected speedup | 1.5-4x for LUT reflection sampling on surfaces with sparse angular distributions; negligible on non-LUT finishes. |
| Validation | For every incident-angle bin, chi-square the sampled `(theta, phi)` distribution against the original LUT probabilities; event-level validation compares reflected direction and polarization histograms. |
| Implementation target | `g4gpu-phase8b-optical-lut-alias-sampler`. |
| Citation | Walker 1977 alias tables; Vose 1991 alias method. |
| Status | OPEN |

### BD-geant4-054  DielectricDielectric combines many surface cases in a single branch ladder

| Field | Value |
|-------|-------|
| File | `source/processes/optical/src/G4OpBoundaryProcess.cc` |
| Lines | 1076-1348 |
| Hot-path % (profile-measured) | Optical dielectric boundary core: per-line self% `OPEN:` pending boundary-model perf. |
| Category | 5 — Control flow |
| Current pattern | Snippet: `if(fFinish == polished)`, `if(fSurfaceRoughness != 0. && fRindex1 > fRindex2)`, `if(sint2 >= 1.0)`, `else if(sint2 < 1.0)`, and backpainted `goto leap` all live in one routine. |
| Why slow | Common polished dielectric transitions share an instruction path with rough, unified, backpainted, total-internal-reflection, and transmission cases, producing unpredictable branches and blocking inlining of small specialized kernels. |
| Proposed fix | At optical-surface setup, generate or dispatch to specialized boundary kernels for polished dielectric, rough dielectric, backpainted dielectric, and unified-model cases; retain the current routine as the exact fallback. |
| Expected speedup | 1.2-1.8x in dielectric boundary handling, with broader gains for CMS/ATLAS calorimeter optics, GATE scintillator optics, and NNBAR lead-glass/scintillator surfaces. |
| Validation | Surface-case golden tests compare status, momentum, polarization, and material swaps for TIR, Fresnel reflection/refraction, roughness failures, and backpainted loops; fixed-seed optical examples must preserve physics histograms. |
| Implementation target | `g4gpu-phase5d-optical-boundary-specialization`. |
| Citation | Futamura 1971 partial evaluation; Consel and Noël 1996 partial evaluation. |
| Status | OPEN |

### BD-geant4-055  Complex-index reflectivity recomputes material-vector values and Fresnel setup per bounce

| Field | Value |
|-------|-------|
| File | `source/processes/optical/src/G4OpBoundaryProcess.cc` |
| Lines | 1443-1495 |
| Hot-path % (profile-measured) | Optical metal/coated reflectivity: per-line self% `OPEN:` pending metal-surface perf. |
| Category | 4 — Mathematical |
| Current pattern | Snippet: `fRealRIndexMPV->Value(...)`, `fImagRIndexMPV->Value(...)`, `GetFacetNormal(...)`, cross products, and `GetReflectivity(...)` are recomputed every time complex refractive indices are needed. |
| Why slow | Reflectivity at a fixed surface is a smooth function of photon momentum and incident angle; recomputing vector interpolation plus Fresnel algebra per bounce duplicates work across many photons in the same material/surface bins. |
| Proposed fix | Precompute a momentum-angle reflectivity grid per optical surface for complex-index materials, store interpolation coefficients, and bypass full Fresnel setup for table-covered bins. |
| Expected speedup | 1.1-1.6x for metal/coated-surface optical workloads; likely most visible in detector components with high-reflectivity wrappers. |
| Validation | Compare reflectivity values over dense momentum/angle grids against the current routine within a configurable absolute tolerance, then replay optical boundary examples and require unchanged absorption/reflection fractions within statistics. |
| Implementation target | `g4gpu-phase8b-optical-reflectivity-table`. |
| Citation | Press et al. 2007 interpolation; Intel 2024 table/cache optimization guidance. |
| Status | OPEN |

### BD-geant4-056  Cerenkov photon generation mixes rejection sampling with per-photon heap allocation

| Field | Value |
|-------|-------|
| File | `source/processes/electromagnetic/xrays/src/G4Cerenkov.cc` |
| Lines | 215-388 |
| Hot-path % (profile-measured) | Optical-photon production: per-line self% `OPEN:` pending Cerenkov-rich benchmark perf. |
| Category | 6 — Memory allocation |
| Current pattern | Snippet: per photon, the code rejection-samples energy through `Rindex->Value(sampledEnergy)`, computes trig/rotations, then executes `new G4DynamicParticle(...)` and `new G4Track(...)`. |
| Why slow | High-yield Cerenkov steps allocate two heap objects per photon and interleave allocation with rejection sampling and transcendentals, creating allocator contention and poor instruction/cache locality. |
| Proposed fix | Use a per-thread optical-secondary arena with batched photon generation; optionally pretabulate the accepted Cerenkov energy distribution per material/beta bin for alias sampling. |
| Expected speedup | 1.3-3x in Cerenkov-heavy examples depending on photon yield and allocator profile; also reduces tail latency in multi-threaded optical simulations. |
| Validation | Arena mode must preserve `G4Track`/`G4DynamicParticle` ownership semantics and produce identical secondary counts, energies, positions, times, and polarization distributions under fixed seeds or distributional RNG mode. |
| Implementation target | `g4gpu-phase6-optical-secondary-arena`. |
| Citation | Berger et al. 2000 Hoard allocator; Walker 1977 alias tables. |
| Status | OPEN |

### BD-geant4-057  Scintillation emission loops through component branches and allocates each optical secondary

| Field | Value |
|-------|-------|
| File | `source/processes/electromagnetic/xrays/src/G4Scintillation.cc` |
| Lines | 347-619 |
| Hot-path % (profile-measured) | Scintillation photon production: per-line self% `OPEN:` pending scintillator benchmark perf. |
| Category | 3 — Data structure |
| Current pattern | Snippet: a loop over `N_timeconstants` branches through component-specific `GetConstProperty` and integral-table pointers, then each photon samples `scintIntegral->GetEnergy(...)`, trig functions, `new G4DynamicParticle(...)`, `new G4Track(...)`, and optional `new G4ScintillationTrackInformation(...)`. |
| Why slow | The per-step component selection is branch-heavy even though material scintillation layout is static, and the per-photon heap path dominates for high-light-yield scintillators used in calorimetry and medical imaging. |
| Proposed fix | Compile a material-local scintillation emission descriptor containing component weights, time constants, integral pointers, and optional track-info policy; feed it to a batched secondary arena shared with Cerenkov/WLS. |
| Expected speedup | 1.3-3x in scintillation-heavy workloads, with largest gains when many photons are produced per charged-particle step. |
| Validation | Compare per-component photon counts, wavelength spectra, emission positions, emission times, polarization isotropy, and optional scintillation-track-info labels against vanilla for fixed material tables. |
| Implementation target | `g4gpu-phase6-scintillation-emission-descriptor`. |
| Citation | Stroustrup 2012 data-oriented containers; Berger et al. 2000 Hoard allocator. |
| Status | OPEN |

### BD-geant4-058  Finite-rise scintillation time sampling uses rejection from an exponential envelope

| Field | Value |
|-------|-------|
| File | `source/processes/electromagnetic/xrays/src/G4Scintillation.cc` |
| Lines | 638-651 |
| Hot-path % (profile-measured) | Scintillation finite-rise timing: per-line self% `OPEN:` pending finite-rise material perf. |
| Category | 4 — Mathematical |
| Current pattern | Snippet: `t  = -1.0 * tau2 * G4Log(1.0 - G4UniformRand());` inside a loop ending `while (G4UniformRand() > (1.0 - G4Exp(-t/tau1)));`. |
| Why slow | Rejection counts are data-dependent and each failed sample pays logarithm/exponential work; finite-rise scintillators can call this once per generated optical photon. |
| Proposed fix | Add a direct inverse-CDF or pretabulated-CDF sampler for common `(tau1, tau2)` pairs, selected from the material emission descriptor, with the rejection sampler retained for uncommon values. |
| Expected speedup | 1.5-3x for finite-rise time sampling; wall-clock impact scales with scintillation photon count and finite-rise material usage. |
| Validation | KS test sampled emission-time distributions against the current sampler for every material `(tau1, tau2)` pair; event-level validation checks photon time spectra and downstream hit-time distributions. |
| Implementation target | `g4gpu-phase8b-scintillation-time-sampler`. |
| Citation | Devroye 1986 non-uniform random variate generation; Walker 1977 alias tables. |
| Status | OPEN |

### BD-geant4-059  WLS photon re-emission uses bounded retry sampling plus temporary secondary vector

| Field | Value |
|-------|-------|
| File | `source/processes/optical/src/G4OpWLS.cc` |
| Lines | 89-226 |
| Hot-path % (profile-measured) | Wavelength-shifting photon production: per-line self% `OPEN:` pending WLS-material perf. |
| Category | 6 — Memory allocation |
| Current pattern | Snippet: `std::vector<G4Track*> proposedSecondaries`, up to 100 retries of `WLSIntegral->GetEnergy(CIIvalue)` per photon, then `new G4DynamicParticle(...)`, `new G4Track(...)`, `proposedSecondaries.push_back(...)`, and a second loop to `AddSecondary`. |
| Why slow | WLS combines data-dependent retry sampling with heap allocation and a temporary growable vector even though the eventual secondary count is bounded by `NumPhotons`. |
| Proposed fix | Precompute a truncated WLS emission sampler conditioned on primary-energy bin and write secondaries directly into a reserved particle-change/arena buffer, eliminating the temporary vector in the common path. |
| Expected speedup | 1.2-2.5x for WLS-heavy optical materials; also removes allocator variance in multi-threaded optical simulations. |
| Validation | Compare sampled WLS energy spectra under primary-energy truncation, secondary counts after retry limits, emission times, positions, touchables, and parent IDs to vanilla. |
| Implementation target | `g4gpu-phase6-wls-secondary-arena`. |
| Citation | Walker 1977 alias tables; Berger et al. 2000 Hoard allocator. |
| Status | OPEN |

### BD-geant4-060  Rayleigh scattering rejection-samples polarization with repeated vector normalization

| Field | Value |
|-------|-------|
| File | `source/processes/optical/src/G4OpRayleigh.cc` |
| Lines | 105-185 |
| Hot-path % (profile-measured) | Rayleigh optical scattering: per-line self% `OPEN:` pending scattering-dominated optical perf. |
| Category | 4 — Mathematical |
| Current pattern | Snippet: the routine samples `cost`, `phi`, rotates the direction, projects polarization with `.unit()`, handles a corner case, and rejects while `std::pow(cosTheta, 2) < G4UniformRand()`. |
| Why slow | The polarization-weighted angular distribution is implemented as rejection sampling with variable loop counts, repeated `sin/cos`, vector rotation, normalization, and `pow` per attempt. |
| Proposed fix | Derive a direct sampler for the Rayleigh polarization distribution or pretabulate a conditional CDF over `cosTheta`; replace `pow(cosTheta, 2)` with a multiply in the fallback path. |
| Expected speedup | 1.2-2x within Rayleigh scattering for optical media where Rayleigh length is short; modest otherwise. |
| Validation | KS/Kuiper tests on scattering angle, azimuth, and polarization projections; fixed-seed event replay with fallback mode and distributional comparison for direct-sampler mode. |
| Implementation target | `g4gpu-phase8b-rayleigh-direct-sampler`. |
| Citation | Devroye 1986 non-uniform random variate generation; Intel 2024 math microarchitecture guidance. |
| Status | OPEN |

## Next implementations after optical-photon shard

1. `g4gpu-phase6-optical-secondary-arena` from BD-geant4-056/057/059: shared
   Cerenkov/scintillation/WLS allocation win with validation by exact secondary
   metadata comparison.
2. `g4gpu-phase8b-optical-lut-alias-sampler` from BD-geant4-053: high upside
   on sparse LUT surfaces and clean distribution-level validation.
3. `g4gpu-phase5d-optical-boundary-specialization` from BD-geant4-054: broad
   boundary-dispatch win for polished/rough/backpainted dielectric surfaces.
4. `g4gpu-phase8b-optical-facet-normal-sampler` from BD-geant4-052: replaces
   nested rejection loops in rough-surface reflection.
5. `g4gpu-phase8b-scintillation-time-sampler` from BD-geant4-058: compact
   mathematical sampler with straightforward KS validation.
6. `g4gpu-phase5d-optical-boundary-property-cache` from BD-geant4-051/055:
   low-risk cache for repeated material/surface property lookups.
7. `g4gpu-phase8b-rayleigh-direct-sampler` from BD-geant4-060: narrower but
   useful for scattering-dominated optical media.

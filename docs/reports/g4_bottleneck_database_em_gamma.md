# Geant4 EM/gamma bottleneck database shard

Scope: additional structured source-review entries for Geant4 `v11.2.2`
standard and Livermore gamma electromagnetic paths. This shard extends the
existing database beyond `BD-geant4-001`--`060` and intentionally does not
repeat the prior PIL, geometry, track/stack, hit/SD, generic DoIt, or optical
photon entries.

Source provenance: LUNARC
`/projects/hep/fs10/shared/nnbar/billy/geant4-fork` reports
`git describe --tags --always --dirty` = `v11.2.2` and short commit
`f840b5da3a`. The local mirror `/tmp/geant4-v11.2.2` was SHA-256 matched
against LUNARC for every file cited here before extracting line numbers.
No speedup or priority promotion is claimed here; every `Hot-path %` remains
`OPEN:` until TestEm, gamma-calorimeter, or NNBAR-like EM perf assigns measured
self-time.

## Entries

### BD-geant4-061  Generic EM GPIL reselects model and mean-free-path state every step

| Field | Value |
|-------|-------|
| File | `source/processes/electromagnetic/utils/src/G4VEmProcess.cc` |
| Lines | 354-418 |
| Hot-path % (profile-measured) | EM post-step GPIL: per-line self% `OPEN:` pending TestEm and gamma-calorimeter perf. |
| Category | 5 — Control flow |
| Current pattern | Snippet: `DefineMaterial(...)`, `SelectModel(...)`, `ComputeIntegralLambda(...)`, then interaction-length bookkeeping on every post-step GPIL call. |
| Why slow | The hot path re-enters generic material/model selection and integral-lambda policy branches even when particle, couple, model interval, and cross-section monotonicity are stable across many steps. |
| Proposed fix | Add a guarded EM process-state snapshot keyed by `(process, particle, material-cuts-couple, model-index, xs-policy)` so stable tracks use a direct GPIL thunk; fall back whenever couple, cut, biasing, model activity, or lambda policy mutates. |
| Expected speedup | 1.05-1.25x in EM-heavy stepping loops; larger in fine-grained calorimeter or medical-physics geometries with many short gamma/electron steps. |
| Validation | Fixed-seed TestEm replays compare selected model index, mean free path, sampled interaction length, and final secondaries; distributional validation requires KS p >= 0.05 for step length and deposited-energy spectra. |
| Implementation target | `g4gpu-phase5d-em-gpil-snapshot`. |
| Citation | Futamura 1971 partial evaluation; Consel and Noël 1996 partial evaluation. |
| Status | OPEN |

### BD-geant4-062  Generic EM PostStepDoIt creates a transient dynamic-particle list before tracks

| Field | Value |
|-------|-------|
| File | `source/processes/electromagnetic/utils/src/G4VEmProcess.cc` |
| Lines | 460-637 |
| Hot-path % (profile-measured) | EM secondary finalization: per-line self% `OPEN:` pending TestEm and gamma-calorimeter perf. |
| Category | 6 — Memory allocation |
| Current pattern | Snippet: `secParticles.clear()`, `currentModel->SampleSecondaries(&secParticles, ...)`, then a loop allocates `new G4Track(dp, ...)`, applies cuts, creator IDs, and deletes failed secondaries. |
| Why slow | Model samplers allocate `G4DynamicParticle` objects, then the generic finalizer allocates `G4Track` objects and rechecks particle-type cuts through branch ladders; rejected particles still paid allocation and vector traffic. |
| Proposed fix | Introduce a per-thread EM secondary arena with a small fixed-capacity buffer carrying particle type, kinetic energy, direction, creator role, and cut decision before committing to `G4Track`; preserve the existing vector ABI as fallback. |
| Expected speedup | 1.1-1.6x in secondary-rich EM workloads; also reduces allocator contention in multi-threaded calorimeter and therapy simulations. |
| Validation | Compare secondary count, particle type, kinetic energy, direction, creator-model ID, weight, touchable, and local energy deposit for fixed seeds; stress with cuts on/off and biasing on/off. |
| Implementation target | `g4gpu-phase6-em-secondary-arena`. |
| Citation | Berger et al. 2000 Hoard allocator; Stroustrup 2012 data-oriented containers. |
| Status | OPEN |

### BD-geant4-063  Klein-Nishina Compton sampling uses scalar rejection and immediate heap allocation

| Field | Value |
|-------|-------|
| File | `source/processes/electromagnetic/standard/src/G4KleinNishinaCompton.cc` |
| Lines | 146-253 |
| Hot-path % (profile-measured) | Standard Compton scattering: per-line self% `OPEN:` pending TestEm gamma benchmark perf. |
| Category | 4 — Mathematical |
| Current pattern | Snippet: a Butcher-Messel rejection loop calls `flatArray(3, rndm)`, `G4Exp`, `sqrt`, then uses `cos/sin`, `rotateUz`, and `new G4DynamicParticle(...)` for the recoil electron. |
| Why slow | Rejection counts are data-dependent, each accepted sample pays scalar transcendentals, and the recoil electron is heap-allocated before the generic EM finalizer can apply cuts. |
| Proposed fix | Add per-energy-bin direct or alias samplers for the Klein-Nishina epsilon distribution and route recoil creation through the EM secondary arena; keep the legacy rejection sampler as a bit-compatible oracle mode. |
| Expected speedup | 1.2-2x inside standard Compton sampling; wall-clock impact depends on Compton interaction fraction in the benchmark. |
| Validation | KS/Kuiper tests over scattered-photon energy, polar angle, azimuth, and recoil-electron energy; exact-mode replay compares legacy sampler against the fallback, and arena mode compares all committed secondary metadata. |
| Implementation target | `g4gpu-phase8b-kn-compton-direct-sampler`. |
| Citation | Butcher and Messel 1960; Walker 1977 alias tables; Vose 1991 alias method. |
| Status | OPEN |

### BD-geant4-064  Standard Compton atomic cross section recomputes Z polynomials and logs per query

| Field | Value |
|-------|-------|
| File | `source/processes/electromagnetic/standard/src/G4KleinNishinaCompton.cc` |
| Lines | 99-142 |
| Hot-path % (profile-measured) | Standard Compton cross-section lookup: per-line self% `OPEN:` pending TestEm profile with table-build and run-time separated. |
| Category | 3 — Data structure |
| Current pattern | Snippet: `p1Z`--`p4Z` are recomputed from `Z`, then `G4Log(1.+2.*X)` and rational-polynomial terms are evaluated for each atom/energy query. |
| Why slow | The Z-dependent coefficients are invariant for an element, and many run-time queries revisit the same `(Z, energy-bin)` region through material-cuts-couple tables. |
| Proposed fix | Precompute per-Z coefficient packs and optionally a small log-energy interpolation table for the active material set; dispatch to the closed-form only outside cached bins or during physics-table construction. |
| Expected speedup | 1.05-1.2x in cross-section-heavy Compton workloads; low risk because the cached value is produced from the same formula. |
| Validation | Compare cross-section values over all active elements and log-energy grid points against the current formula within double precision tolerance; event-level validation checks interaction-type rates. |
| Implementation target | `g4gpu-phase6-em-cross-section-cache`. |
| Citation | Cormen et al. 2009 table lookup and interpolation; Lam, Rothberg, and Wolf 1991 locality optimization. |
| Status | OPEN |

### BD-geant4-065  Livermore Compton scattering samples scattering functions inside rejection trials

| Field | Value |
|-------|-------|
| File | `source/processes/electromagnetic/lowenergy/src/G4LivermoreComptonModel.cc` |
| Lines | 284-357 |
| Hot-path % (profile-measured) | Livermore low-energy Compton sampling: per-line self% `OPEN:` pending low-energy gamma perf. |
| Category | 2 — Algorithm |
| Current pattern | Snippet: each rejection trial samples epsilon, computes `x = sqrt(oneCosT / 2.) * cm / wlPhoton`, calls `ComputeScatteringFunction(x, Z)`, and rejects against `G4UniformRand() * Z`. |
| Why slow | The scattering-function table lookup is inside a variable-count rejection loop, so low-acceptance regions multiply random draws, square roots, and interpolation calls per accepted photon. |
| Proposed fix | Build per-`(Z, incident-energy-bin)` CDF or alias tables for the scattering-function-weighted epsilon distribution, with interpolation between incident-energy bins and the current loop as validation fallback. |
| Expected speedup | 1.3-3x in low-energy Compton sampling for materials where scattering-function rejection dominates; negligible for standard KN-only configurations. |
| Validation | For each tested Z and incident-energy bin, compare epsilon and angle distributions against the current sampler; event-level validation checks scattered photon spectra and electron energy deposits. |
| Implementation target | `g4gpu-phase8b-livermore-compton-alias`. |
| Citation | Cullen 1995 photon transport model; Walker 1977 alias tables; Vose 1991 alias method. |
| Status | OPEN |

### BD-geant4-066  Livermore Compton Doppler broadening loops over shell/profile sampling

| Field | Value |
|-------|-------|
| File | `source/processes/electromagnetic/lowenergy/src/G4LivermoreComptonModel.cc` |
| Lines | 284-424 |
| Hot-path % (profile-measured) | Doppler-broadened Compton: per-line self% `OPEN:` pending low-energy gamma perf with Doppler enabled. |
| Category | 2 — Algorithm |
| Current pattern | Snippet: a loop repeatedly calls `shellData->SelectRandomShell(Z)`, `BindingEnergy`, `profileData->RandomSelectMomentum(...)`, then solves a quadratic-like expression until `photonE <= eMax` or 1000 iterations. |
| Why slow | Shell and momentum-profile sampling are pointer-heavy and sit in a retry loop with data-dependent iteration counts; rare tails can create long-latency outliers in multi-threaded low-energy EM. |
| Proposed fix | Precompose per-Z shell occupancy with profile-momentum samplers into compact tables and add an energy-aware rejection envelope or direct conditional sampler for accepted Doppler momenta. |
| Expected speedup | 1.2-2.5x in Doppler-broadened Livermore Compton sections; also reduces long-tail latency. |
| Validation | Compare selected shell, binding-energy, Doppler momentum, scattered-photon energy, and local energy deposit distributions for every active Z; require tail quantiles and failed-iteration rates to match within statistical tolerance. |
| Implementation target | `g4gpu-phase8b-doppler-profile-sampler`. |
| Citation | Namito, Ban, and Hirayama 1994 Doppler broadening; Devroye 1986 non-uniform random variate generation. |
| Status | OPEN |

### BD-geant4-067  Livermore photoelectric cross-section code repeatedly dereferences coefficient vectors

| Field | Value |
|-------|-------|
| File | `source/processes/electromagnetic/lowenergy/src/G4LivermorePhotoElectricModel.cc` |
| Lines | 212-275 |
| Hot-path % (profile-measured) | Livermore photoelectric cross-section query: per-line self% `OPEN:` pending low-energy gamma perf. |
| Category | 3 — Data structure |
| Current pattern | Snippet: `(*(fParamHigh[Z]))[...]` and `(*(fParamLow[Z]))[...]` are dereferenced repeatedly through high/low/tabulated branches after on-the-fly element initialization checks. |
| Why slow | Coefficients for an element are stored as heap vectors and accessed by repeated pointer dereferences and index arithmetic; the branch structure mixes high-energy polynomial, low-energy polynomial, and table lookup cases. |
| Proposed fix | Materialize an immutable per-Z photoelectric coefficient struct with separate high/low polynomial blocks, threshold values, and table pointers; make the cross-section query a short branch over contiguous data. |
| Expected speedup | 1.05-1.3x in Livermore photoelectric cross-section calls; broader benefit in low-energy detector, shielding, and medical-imaging workloads. |
| Validation | Exhaustively compare cross-section values for every loaded Z over a log-energy grid spanning all branch thresholds; replay interaction-rate histograms in low-energy gamma examples. |
| Implementation target | `g4gpu-phase6-livermore-photoelectric-coeff-pack`. |
| Citation | Stroustrup 2012 data-oriented containers; Lam, Rothberg, and Wolf 1991 locality optimization. |
| Status | OPEN |

### BD-geant4-068  Livermore photoelectric shell selection scans shells with repeated coefficient/table lookups

| Field | Value |
|-------|-------|
| File | `source/processes/electromagnetic/lowenergy/src/G4LivermorePhotoElectricModel.cc` |
| Lines | 280-407 |
| Hot-path % (profile-measured) | Photoelectric shell sampling: per-line self% `OPEN:` pending low-energy gamma perf with fluorescence enabled/disabled. |
| Category | 2 — Algorithm |
| Current pattern | Snippet: high/low branches compute `cs0`, then loop over shells; the tabulated branch subtracts `GetValueForComponent(Z, j, gammaEnergy)` until the random cumulative value crosses zero. |
| Why slow | Shell selection is an O(number-of-shells) cumulative scan with branch-specific coefficient arithmetic or interpolation; the same Z and energy bins are revisited across many photons. |
| Proposed fix | Build per-Z, per-energy-bin shell CDF/alias tables for polynomial and tabulated regimes, with exact fallback at bin edges and for on-the-fly initialized elements. |
| Expected speedup | 1.2-2x in shell-rich photoelectric workloads, especially high-Z shielding/calorimeter materials with fluorescence enabled. |
| Validation | Compare selected shell distributions versus the current cumulative scan for each active Z and energy bin; event-level validation checks photoelectron, fluorescence, Auger, and local-deposit spectra. |
| Implementation target | `g4gpu-phase8b-photoelectric-shell-alias`. |
| Citation | Walker 1977 alias tables; Vose 1991 alias method. |
| Status | OPEN |

### BD-geant4-069  Relativistic pair-production cross sections integrate DCS on every high-energy query

| Field | Value |
|-------|-------|
| File | `source/processes/electromagnetic/standard/src/G4PairProductionRelModel.cc` |
| Lines | 182-219 |
| Hot-path % (profile-measured) | Pair-production high-energy cross-section query: per-line self% `OPEN:` pending high-energy gamma perf. |
| Category | 4 — Mathematical |
| Current pattern | Snippet: `numSub = 2` and an 8-point Gauss-Legendre loop call either `ComputeRelDXSectionPerAtom(...)` or `ComputeDXSectionPerAtom(...)` for each atom/energy query above the parameterized threshold. |
| Why slow | Numerical integration repeats for smooth functions of `(Z, gammaEnergy, LPM flag, screening mode)` even though active material sets and energy grids are known during a run. |
| Proposed fix | Precompute validated log-energy interpolation tables for the integrated cross section per active Z and LPM/screening mode; retain direct quadrature as table-builder and out-of-domain fallback. |
| Expected speedup | 1.2-2x for high-energy pair-production cross-section queries; wall-clock impact depends on gamma energy spectrum above the parameterized threshold. |
| Validation | Compare table interpolation against direct quadrature over dense log-energy grids with conservative relative tolerance; run high-energy gamma examples and compare pair-production rates and secondary spectra. |
| Implementation target | `g4gpu-phase6-pair-production-xs-table`. |
| Citation | Press et al. 2007 interpolation; Davis and Rabinowitz 1984 numerical integration. |
| Status | OPEN |

### BD-geant4-070  Pair-production epsilon sampling repeats screening/LPM functions in rejection loop

| Field | Value |
|-------|-------|
| File | `source/processes/electromagnetic/standard/src/G4PairProductionRelModel.cc` |
| Lines | 357-500 |
| Hot-path % (profile-measured) | Pair-production secondary sampling: per-line self% `OPEN:` pending high-energy gamma perf. |
| Category | 2 — Algorithm |
| Current pattern | Snippet: a rejection loop fills `rndmv[3]`, samples `eps`, recomputes screening and optional LPM functions for `greject`, then allocates electron and positron `G4DynamicParticle` objects. |
| Why slow | The accepted epsilon distribution is stable for `(Z, material, gamma-energy-bin, LPM mode)`, but the current path recomputes screening/LPM math inside a variable-count loop and allocates both secondaries immediately. |
| Proposed fix | Build per-bin epsilon alias/CDF tables that include screening and LPM mode, and route e+/e- creation through the EM secondary arena; use the current rejection loop as the reference sampler. |
| Expected speedup | 1.3-3x in pair-production secondary sampling; larger when LPM correction is active and rejection counts rise. |
| Validation | Compare epsilon, charge assignment, angular distributions, e+/e- kinetic energies, and committed secondary metadata; high-energy examples must preserve pair rates and energy-deposit spectra within statistics. |
| Implementation target | `g4gpu-phase8b-pair-production-epsilon-alias`. |
| Citation | Hubbell, Gimm, and Øverbø 1980 pair-production data; Walker 1977 alias tables; Vose 1991 alias method. |
| Status | OPEN |

## Next implementations after EM/gamma shard

1. `g4gpu-phase6-em-secondary-arena` from BD-geant4-062/063/070: one shared
   allocation/cut-finalization path for standard Compton, Livermore
   photoelectric, pair production, and later electron/ionisation samplers.
2. `g4gpu-phase8b-livermore-compton-alias` from BD-geant4-065/066: replaces
   two low-energy Compton rejection loops while keeping the current sampler as
   the validation oracle.
3. `g4gpu-phase8b-photoelectric-shell-alias` from BD-geant4-068: compact
   distribution-table task with straightforward shell-spectrum validation.
4. `g4gpu-phase8b-pair-production-epsilon-alias` from BD-geant4-070: high
   upside for high-energy gamma runs, especially with LPM enabled.
5. `g4gpu-phase5d-em-gpil-snapshot` from BD-geant4-061: connects this EM shard
   to the existing guarded GPIL dispatch-table scaffold.
6. `g4gpu-phase6-em-cross-section-cache` from BD-geant4-064/067/069: low-risk
   coefficient/table packing work that should be validated before sampler
   rewrites rely on cached cross sections.

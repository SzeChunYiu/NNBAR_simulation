# Geant4 neutron-HP bottleneck database shard

Scope: structured source-review entries for Geant4 `v11.2.2` high-precision
neutron and thermal-scattering paths. This shard extends the existing database
beyond `BD-geant4-001`--`070` and intentionally avoids prior PIL, geometry,
track/stack, hit/SD, generic DoIt, optical-photon, and EM/gamma entries.

Source provenance: LUNARC
`/projects/hep/fs10/shared/nnbar/billy/geant4-fork` reports
`git describe --tags --always --dirty` = `v11.2.2` and short commit
`f840b5da3a`. The local mirror `/tmp/geant4-v11.2.2` was SHA-256 matched
against LUNARC for every file cited here before extracting line numbers.
No speedup or priority promotion is claimed here; every `Hot-path %` remains
`OPEN:` until Hadr01/Hadr02, shielding, or thermal-neutron perf assigns
measured self-time.

## Entries

### BD-geant4-071  HP cross-section lookup scans forward from a hash hint and branches through interpolation policy

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/models/particle_hp/src/G4ParticleHPVector.cc` |
| Lines | 143-192 |
| Hot-path % (profile-measured) | Neutron-HP cross-section lookup: per-line self% `OPEN:` pending Hadr/thermal-neutron perf with HP data enabled. |
| Category | 3 — Data structure |
| Current pattern | Snippet: `theHash.GetMinIndex(e)` is followed by `for (i = min; i < nEntries; i++)`, duplicate-x guards, and `theInt.Interpolate(theManager.GetScheme(high), ...)` on every query. |
| Why slow | The hash narrows the search but still leaves a data-dependent scan and policy lookup in the query path; HP workloads revisit the same isotope/material energy grids many times. |
| Proposed fix | Build immutable segment descriptors with cached interpolation scheme, inverse width, and duplicate-x handling per interval; use binary-search or direct-bucket lookup to return a descriptor and evaluate a branch-light interpolation formula. |
| Expected speedup | 1.1-1.5x inside HP vector cross-section calls; wall-clock depends on HP fraction in shielding, reactor, and moderated-neutron simulations. |
| Validation | Exhaustively compare cross-section values for every loaded HP vector over original grid points plus dense midpoints; event-level validation compares reaction-channel rates and neutron spectra. |
| Implementation target | `g4gpu-phase5d-hp-vector-segment-cache`. |
| Citation | Cormen et al. 2009 binary search/table lookup; Lam, Rothberg, and Wolf 1991 locality optimization. |
| Status | OPEN |

### BD-geant4-072  HP vector sampling linearly searches cumulative bins and rejection-samples the local segment

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/models/particle_hp/src/G4ParticleHPVector.cc` |
| Lines | 363-457 |
| Hot-path % (profile-measured) | HP distribution sampling: per-line self% `OPEN:` pending HP final-state perf. |
| Category | 2 — Algorithm |
| Current pattern | Snippet: each call first clamps negative `Y`, then `for (G4int i = 0; i < GetVectorLength(); i++)` searches `theIntegral`, samples a segment, and repeats while `G4UniformRand() > test` or `IsBlocked(result)`. |
| Why slow | A linear CDF scan and rejection loop are repeated for tabulated distributions that are immutable after data load; the negative-Y cleanup also re-walks data during sampling. |
| Proposed fix | Normalize once at load time, precompute alias or binary-search CDF tables per HP vector, and split blocked intervals into explicit allowed segments so sampling is one lookup plus one interpolation. |
| Expected speedup | 1.3-3x inside HP distribution sampling for long tabulations; also reduces long-tail latency from repeated rejection. |
| Validation | Compare sampled `X` distributions against the current sampler for each tabulation with KS/Kuiper tests, and verify blocked intervals are never emitted. |
| Implementation target | `g4gpu-phase8b-hp-vector-alias-sampler`. |
| Citation | Walker 1977 alias tables; Vose 1991 alias method; Devroye 1986 non-uniform random variate generation. |
| Status | OPEN |

### BD-geant4-073  HP channel isotope selection allocates a temporary cross-section array per interaction

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/models/particle_hp/src/G4ParticleHPChannel.cc` |
| Lines | 226-318 |
| Hot-path % (profile-measured) | HP isotope/channel selection: per-line self% `OPEN:` pending HP inelastic/capture/elastic perf. |
| Category | 6 — Memory allocation |
| Current pattern | Snippet: `auto xsec = new G4double[niso]`, a loop fills weighted isotope cross sections, another loop samples the cumulative ratio, then `delete[] xsec`; elastic also calls `MakeChannelData()` before `ApplyYourself`. |
| Why slow | The per-interaction heap allocation and cumulative scan sit before every selected HP final state, and isotope counts are small/stable enough for fixed-capacity storage or cached cumulative weights. |
| Proposed fix | Replace the temporary array with a thread-local small buffer or stack-backed fixed vector, and cache isotope cumulative weights keyed by `(channel, material temperature, projectile energy bin)` with invalidation for DBRC/thermal changes. |
| Expected speedup | 1.05-1.3x for isotope-rich HP materials; allocator samples should drop sharply in reactor, shielding, and detector-moderator workloads. |
| Validation | Fixed-seed replay compares selected isotope `(A,Z,M)`, final-state pointer path, reaction whiteboard values, and final secondaries; distributional validation compares isotope frequencies. |
| Implementation target | `g4gpu-phase6-hp-isotope-selector-buffer`. |
| Citation | Berger et al. 2000 Hoard allocator; EASTL fixed_vector design notes. |
| Status | OPEN |

### BD-geant4-074  Doppler-broadened HP elastic cross section performs adaptive Monte Carlo integration per query

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/models/particle_hp/src/G4ParticleHPElasticData.cc` |
| Lines | 193-267 |
| Hot-path % (profile-measured) | HP elastic Doppler broadening: per-line self% `OPEN:` pending thermal-neutron elastic perf with Doppler enabled. |
| Category | 4 — Mathematical |
| Current pattern | Snippet: `GetThermalNucleus`, `boosted.Lorentz(...)`, `GetValue(theEkin, outOfRange)`, and velocity correction run inside a loop that doubles `size` until the running average changes by less than `0.03 * buffer`. |
| Why slow | Each cross-section query launches a stochastic integration whose iteration count depends on temperature and energy; repeated material/temperature states are not reused. |
| Proposed fix | Precompute Doppler-broadened cross-section tables per `(element/isotope, temperature grid, energy grid)` with deterministic quadrature or vectorized Monte Carlo at table-build time, leaving the current loop as validation oracle/fallback. |
| Expected speedup | 1.5-10x inside Doppler-enabled elastic lookup depending on convergence count; broad benefit for moderated-neutron transport. |
| Validation | Compare broadened cross sections over dense energy/temperature grids, then run thermal-scattering/elastic benchmarks and compare reaction rates, outgoing energy, and angular distributions. |
| Implementation target | `g4gpu-phase8b-hp-doppler-table`. |
| Citation | Cullen and Weisbin 1976 Doppler broadening; Davis and Rabinowitz 1984 numerical integration. |
| Status | OPEN |

### BD-geant4-075  HP inelastic material-element selection builds a heap cumulative array each call

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/models/particle_hp/src/G4ParticleHPInelastic.cc` |
| Lines | 129-207 |
| Hot-path % (profile-measured) | HP inelastic element selection: per-line self% `OPEN:` pending Hadr inelastic HP perf. |
| Category | 6 — Memory allocation |
| Current pattern | Snippet: for multi-element materials, `auto xSec = new G4double[n]`, per-element HP cross sections are accumulated with atom-density weights, then a linear `for (it = 0; it < n; ++it)` samples the element. |
| Why slow | Material composition is stable and `n` is usually small, but the hot path still allocates, fills, scans, and frees a cumulative array before every HP inelastic final-state call. |
| Proposed fix | Store per-material thread-local element-selection buffers and optionally precompute atom-density-weighted element tables for common energy bins; use a fixed small-vector path for `n <= 8`. |
| Expected speedup | 1.05-1.25x in HP inelastic calls for compounds; higher allocator reduction in hydrogenous shielding and detector materials. |
| Validation | Fixed-seed replay compares selected element index, target isotope assigned to `G4Nucleus`, and final-state secondaries; frequency validation checks element-selection histograms. |
| Implementation target | `g4gpu-phase6-hp-material-selector-buffer`. |
| Citation | Berger et al. 2000 Hoard allocator; Stroustrup 2012 data-oriented containers. |
| Status | OPEN |

### BD-geant4-076  Thermal scattering ApplyYourself repeatedly constructs lookup vectors and map traversals

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/models/particle_hp/src/G4ParticleHPThermalScattering.cc` |
| Lines | 304-585 |
| Hot-path % (profile-measured) | Thermal scattering reaction selection: per-line self% `OPEN:` pending thermal-neutron perf. |
| Category | 3 — Data structure |
| Current pattern | Snippet: the code scans material elements with repeated `getTS_ID(...)`, allocates `new G4DynamicParticle`, builds `std::vector<G4double> v_temp`, and re-enters nested `std::map::find` chains for inelastic/coherent/incoherent branches. |
| Why slow | The applicable thermal-scattering data, temperature brackets, and branch tables are stable for a `(material, element, temperature)` state, but are rediscovered and copied on every thermal scattering interaction. |
| Proposed fix | Build a compact per-material thermal-scattering descriptor containing the element ID, temperature bracket pointers, branch cross-section accessors, and pre-sized scratch spans; avoid per-call vector construction and duplicate map lookups. |
| Expected speedup | 1.1-1.6x in thermal scattering `ApplyYourself`; also lowers allocator traffic for cold-neutron moderation workloads. |
| Validation | Compare selected reaction branch, temperature bracket, secondary energy, mu, and momentum change for fixed seeds across inelastic/coherent/incoherent cases. |
| Implementation target | `g4gpu-phase6-thermal-scattering-descriptor`. |
| Citation | Stroustrup 2012 data-oriented containers; Cormen et al. 2009 search structures. |
| Status | OPEN |

### BD-geant4-077  Thermal inelastic energy-angle sampling rebuilds maps and samples both brackets per interaction

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/models/particle_hp/src/G4ParticleHPThermalScattering.cc` |
| Lines | 596-738 |
| Hot-path % (profile-measured) | Thermal inelastic final-state sampling: per-line self% `OPEN:` pending inelastic thermal scattering perf. |
| Category | 2 — Algorithm |
| Current pattern | Snippet: `sample_inelastic_E_mu` creates `std::map<G4double, G4int> map_energy` and `std::vector<G4double> v_energy`, calls `sample_inelastic_E` for lower and upper energy brackets, then calls `getMu` for both brackets before interpolation. |
| Why slow | Per-sample map/vector construction and dual lower/upper sampling are expensive for immutable grids; the CDF search in `sample_inelastic_E` is also linear. |
| Proposed fix | Precompute incident-energy bracket indices and CDF/alias tables inside the thermal descriptor, and use stochastic bracket selection or a validated coupled sampler instead of always sampling both brackets. |
| Expected speedup | 1.3-2.5x inside thermal inelastic energy-angle sampling; strongest for large S(α,β) tables. |
| Validation | Compare secondary energy and mu joint distributions for each material/temperature/incident-energy bin; validate coupled-sampler correlations, not just marginal histograms. |
| Implementation target | `g4gpu-phase8b-thermal-inelastic-table-sampler`. |
| Citation | Devroye 1986 non-uniform random variate generation; Walker 1977 alias tables. |
| Status | OPEN |

### BD-geant4-078  Legacy thermal secondary-energy path linearly integrates probabilities and rebuilds interpolated angular arrays

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/models/particle_hp/src/G4ParticleHPThermalScattering.cc` |
| Lines | 903-1016 |
| Hot-path % (profile-measured) | Thermal secondary-energy/angle interpolation: per-line self% `OPEN:` pending branch coverage with legacy helper paths. |
| Category | 2 — Algorithm |
| Current pattern | Snippet: `get_secondary_energy_from_E_P_E_isoAng` walks `for (G4int i = 0; i < n - 1; ++i)` accumulating probabilities, while `create_sE_and_EPM...` rebuilds `std::map`, `std::vector`, and interpolated `E_isoAng` arrays. |
| Why slow | The helper repeats CDF construction and angular interpolation for tables that are immutable after data load; it also performs multiple vector pushes during a sampling path. |
| Proposed fix | Store cumulative probabilities and interpolated-angle cache blocks per incident-energy bracket, with direct lookup by bracket index and reusable output storage. |
| Expected speedup | 1.2-2x when these helper paths are active; smaller if the newer stochastic interpolation path dominates. |
| Validation | Compare secondary-energy CDF inversion and interpolated `E_isoAng` arrays against the current helper over all table bins; event-level tests compare outgoing neutron spectra. |
| Implementation target | `g4gpu-phase8b-thermal-secondary-cdf-cache`. |
| Citation | Knuth 1998 cumulative distribution inversion; Lam, Rothberg, and Wolf 1991 locality optimization. |
| Status | OPEN |

### BD-geant4-079  Continuous energy-angle sampling linearly scans incident-energy bins and rebuilds interpolation objects

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/models/particle_hp/src/G4ParticleHPContEnergyAngular.cc` |
| Lines | 69-132 |
| Hot-path % (profile-measured) | HP continuous energy-angle final states: per-line self% `OPEN:` pending inelastic final-state perf. |
| Category | 3 — Data structure |
| Current pattern | Snippet: `for (i = 0; i < nEnergy; ++i)` finds the incident-energy bin, then the non-`PHP_AS_HP` path builds/interpolates `fCacheAngular` before sampling and recording mean energy. |
| Why slow | The incident-energy grids are sorted and immutable, so a linear scan and per-call interpolation-build path waste work for repeated queries in the same material/isotope channel. |
| Proposed fix | Replace the scan with cached bracket lookup and prebuild interpolation-ready angular descriptors for common energy brackets; keep `fCacheAngular` only as a mutable fallback. |
| Expected speedup | 1.1-1.8x in continuous HP final-state sampling depending on `nEnergy` and interpolation representation. |
| Validation | Compare selected bracket, outgoing energy-angle joint distributions, and mean emitted energy for all active final-state tables. |
| Implementation target | `g4gpu-phase6-hp-cont-energy-angular-cache`. |
| Citation | Cormen et al. 2009 binary search; Walker 1977 alias tables. |
| Status | OPEN |

### BD-geant4-080  Discrete two-body HP sampling constructs temporary stores and merges angular distributions per sample

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/models/particle_hp/src/G4ParticleHPDiscreteTwoBody.cc` |
| Lines | 87-331 |
| Hot-path % (profile-measured) | HP discrete two-body final states: per-line self% `OPEN:` pending two-body final-state perf. |
| Category | 6 — Memory allocation |
| Current pattern | Snippet: `auto result = new G4ReactionProduct`, a linear energy scan selects `it`, and LINLIN/LOGLIN branches construct `G4ParticleHPVector`/`G4InterpolationManager` temporaries, fill coefficient loops, merge stores, then call `theStore.Sample()`. |
| Why slow | Per-sample temporary vector construction and merge work repeat for immutable angular coefficient tables; output allocation also occurs before the sampled kinematics are known. |
| Proposed fix | Precompute per-energy-bracket angular samplers and interpolation descriptors at data-load time, and return sampled kinematics into a caller-provided reaction-product arena before committing ownership. |
| Expected speedup | 1.2-2.5x inside discrete two-body HP final-state sampling; allocator reduction composes with HP channel/secondary arenas. |
| Validation | Compare outgoing particle definition, kinetic energy, momentum direction, and angular distribution for every supported representation (`0`, `12`, `14`) against the current implementation. |
| Implementation target | `g4gpu-phase6-hp-two-body-sampler-cache`. |
| Citation | Berger et al. 2000 Hoard allocator; Vose 1991 alias method. |
| Status | OPEN |

## Next implementations after neutron-HP shard

1. `g4gpu-phase8b-hp-vector-alias-sampler` from BD-geant4-072: high-impact
   table-sampling primitive shared by several HP final-state paths.
2. `g4gpu-phase8b-hp-doppler-table` from BD-geant4-074: likely largest local
   speedup for moderated-neutron elastic transport, but needs careful physics
   validation.
3. `g4gpu-phase6-thermal-scattering-descriptor` from BD-geant4-076/077: removes
   repeated map/vector reconstruction and gives later samplers stable inputs.
4. `g4gpu-phase5d-hp-vector-segment-cache` from BD-geant4-071: low-risk lookup
   optimization useful across HP data tables.
5. `g4gpu-phase6-hp-isotope-selector-buffer` and
   `g4gpu-phase6-hp-material-selector-buffer` from BD-geant4-073/075: compact
   allocator-removal tasks that should be easy to validate by replaying chosen
   isotope/element IDs.
6. `g4gpu-phase6-hp-two-body-sampler-cache` from BD-geant4-080: good follow-up
   after the shared HP vector sampler exists.

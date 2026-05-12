# Geant4 hadronic proton/ion bottleneck database shard

Scope: structured source-review entries for Geant4 `v11.2.2` hadronic
proton and ion inelastic/cascade paths. This worker-3 lane-swap shard fills the
reserved `BD-geant4-121`--`130` range and intentionally avoids the completed
`BD-geant4-001`--`120` findings.

Source provenance: local mirror `/tmp/geant4-v11.2.2` exists for Geant4
`v11.2.2`; every source file, function anchor, and line range below was checked
against that mirror before writing the entry. The v11.2.2 proton inelastic
process is created as a `G4HadronInelasticProcess("protonInelastic", ...)` in
`G4ProtonBuilder`, not as a separate `G4ProtonInelasticProcess` source class.
No measured speedup or priority promotion is claimed here; every `Hot-path %`
remains `OPEN:` until Hadr01/Hadr03/TestEm proton-ion perf maps self-time to
exact lines.

## Entries

### BD-geant4-121  Proton inelastic builder rebuilds the model list through indirect builder calls

| Field | Value |
|-------|-------|
| File | `source/physics_lists/builders/src/G4ProtonBuilder.cc` |
| Lines | 46-69 |
| Hot-path % (profile-measured) | Proton inelastic process construction: per-line self% `OPEN:` pending physics-list startup profiles. |
| Category | 5 -- Control flow |
| Current pattern | Snippet: `for(i=theModelCollections.begin(); i!=theModelCollections.end(); i++)`, `(*i)->Build(theProtonInelastic)`, and `new G4HadronInelasticProcess( "protonInelastic", G4Proton::Definition() )`. |
| Why slow | Process construction is startup-only but repeated run-manager/worker initialization still walks a mutable builder vector and late-binds every registered proton model before adding the process. |
| Proposed fix | Generate a proton-inelastic registration descriptor for the selected physics list, with an audited generic fallback for user-injected builders. |
| Expected speedup | 1.02-1.15x in hadronic physics-list construction for workflows repeatedly creating run managers or worker-local physics tables. |
| Validation | Compare registered proton inelastic process name, model order, energy ranges, cross-section datasets, and process-manager ordering before/after for FTFP_BERT, QGSP_BIC, and custom lists. |
| Implementation target | `g4gpu-phase5d-proton-process-registration-descriptor`. |
| Citation | Futamura 1971 partial evaluation; Hoelzle, Chambers, and Ungar 1991 polymorphic inline caches. |
| Status | OPEN |

### BD-geant4-122  Hadronic cross-section store scans material elements and dataset fallbacks per query

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/cross_sections/src/G4CrossSectionDataStore.cc` |
| Lines | 68-124 |
| Hot-path % (profile-measured) | Hadronic material cross-section query: per-line self% `OPEN:` pending proton/ion stepping profiles. |
| Category | 3 -- Data structure |
| Current pattern | Snippet: `for(G4int i=0; i<(G4int)nElements; ++i)` accumulates atom-density weighted element cross sections, then isotope paths loop over `nIso` and dataset fallbacks. |
| Why slow | Material composition, isotope abundances, and dataset applicability are stable over many steps, but each query repeats vector growth checks, element scans, virtual applicability tests, and fallback logic. |
| Proposed fix | Build per-material/projectile dataset descriptors with prevalidated element/isotope applicability and direct function pointers for the active energy domain. |
| Expected speedup | 1.05-1.35x inside hadronic cross-section lookup for compounds and isotope-rich materials. |
| Validation | Exhaustively compare total material cross sections and cumulative element arrays over material, projectile, and log-energy grids; event-level validation compares reaction rates. |
| Implementation target | `g4gpu-phase6-hadronic-xs-descriptor-cache`. |
| Citation | Cormen et al. 2009 search structures; Stroustrup 2012 data-oriented containers. |
| Status | OPEN |

### BD-geant4-123  Hadronic target sampling linearly scans element and isotope cumulative weights

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/cross_sections/src/G4CrossSectionDataStore.cc` |
| Lines | 192-268 |
| Hot-path % (profile-measured) | Hadronic target `Z,A` sampling: per-line self% `OPEN:` pending inelastic-final-state perf. |
| Category | 2 -- Algorithm |
| Current pattern | Snippet: `cross = matCrossSection*G4UniformRand()`, a linear scan over `xsecelm`, optional `SelectIsotope`, and a second cumulative isotope scan through `xseciso`. |
| Why slow | The cumulative distributions are recomputed during the preceding cross-section query and then searched linearly during sampling, even when the same material/projectile state repeats. |
| Proposed fix | Store alias or binary-search CDF descriptors for element and isotope choices keyed by `(material, projectile, energy-bin, dataset)`; retain forced-element and exact legacy paths as guards. |
| Expected speedup | 1.1-1.8x in target selection for multi-element or isotope-rich media, with lower long-tail latency. |
| Validation | Fixed-seed fallback compares selected element/isotope IDs; accelerated mode validates selection frequencies against legacy CDFs with chi-square tests. |
| Implementation target | `g4gpu-phase8b-hadronic-target-alias-sampler`. |
| Citation | Walker 1977 alias tables; Vose 1991 alias method; Devroye 1986 non-uniform variate generation. |
| Status | OPEN |

### BD-geant4-124  BGG nucleon inelastic cross section carries low/mid/high energy branch ladders per call

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/cross_sections/src/G4BGGNucleonInelasticXS.cc` |
| Lines | 118-147 |
| Hot-path % (profile-measured) | BGG nucleon inelastic element query: per-line self% `OPEN:` pending Hadr proton/neutron cross-section profiles. |
| Category | 5 -- Control flow |
| Current pattern | Snippet: branch on hydrogen, `ekin <= fLowEnergy`, `ekin > fGlauberEnergy`, or `fNucleon->GetElementCrossSection(dp, Z)` before optional verbose logging. |
| Why slow | Stable projectile/energy regions carry all branches and dataset calls on every query, while proton workloads often revisit the same material and energy decade. |
| Proposed fix | Split low-energy Coulomb, mid-energy nucleon, and high-energy Glauber thunks during descriptor build, with direct region dispatch from cached energy bins. |
| Expected speedup | 1.05-1.25x inside BGG nucleon inelastic lookups; wall-clock depends on cross-section-query density. |
| Validation | Compare returned cross sections across Z=1..92 and log-energy grids, including region boundaries and proton/neutron parity. |
| Implementation target | `g4gpu-phase5d-bgg-nucleon-region-specialization`. |
| Citation | Futamura 1971 partial evaluation; Lam, Rothberg, and Wolf 1991 locality optimization. |
| Status | OPEN |

### BD-geant4-125  Hadron-nucleus Glauber-Gribov formula recomputes radii, logs, and nucleon terms per state

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/cross_sections/src/G4ComponentGGHadronNucleusXsc.cc` |
| Lines | 182-277 |
| Hot-path % (profile-measured) | Hadron-nucleus Glauber-Gribov query: per-line self% `OPEN:` pending high-energy proton/ion profiles. |
| Category | 4 -- Mathematical |
| Current pattern | Snippet: cache checks exact `kinEnergy`, then calls hadron-nucleon cross sections, radius helpers, `G4Log`, diffraction, inelastic, elastic, and production formulas. |
| Why slow | The one-entry exact-energy cache misses for drifting continuous energies, so expensive scalar formulas and nested cross-section calls repeat for nearby energy/material states. |
| Proposed fix | Build interpolation descriptors over log-energy bins per `(particle,Z,A,L)` with exact-formula fallback and cached nucleon-term/radius factors. |
| Expected speedup | 1.1-2x inside Glauber-Gribov hadron-nucleus cross sections when energy locality is present. |
| Validation | Compare total, elastic, inelastic, production, and diffraction cross sections over dense energy grids; event-level validation compares selected process rates. |
| Implementation target | `g4gpu-phase8b-gg-hadron-nucleus-table`. |
| Citation | Cormen et al. 2009 interpolation/search; Lam, Rothberg, and Wolf 1991 locality optimization. |
| Status | OPEN |

### BD-geant4-126  Nucleus-nucleus Glauber-Gribov cross section recomputes projectile/target geometry per query

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/cross_sections/src/G4ComponentGGNuclNuclXsc.cc` |
| Lines | 163-243 |
| Hot-path % (profile-measured) | Ion-ion Glauber-Gribov query: per-line self% `OPEN:` pending light-ion transport profiles. |
| Category | 4 -- Mathematical |
| Current pattern | Snippet: exact-cache check, projectile `Z/A/L` extraction, nuclear radii, Coulomb-barrier check, multiple hadron-nucleon calls, and `G4Log` formulas for total/inelastic/production cross sections. |
| Why slow | Ion transport revisits a small set of projectile/target species, but each energy query rebuilds geometry and scalar formula state unless it exactly matches the previous energy. |
| Proposed fix | Cache projectile-target geometry descriptors and tabulate smooth log-energy cross-section components, with exact formula replay at bin boundaries. |
| Expected speedup | 1.15-2x inside ion-ion cross-section calls; largest for repeated light-ion beams through fixed materials. |
| Validation | Compare cross sections and Coulomb-barrier zeroing over projectile/target species and energy-per-nucleon grids; validate reaction rates in ion examples. |
| Implementation target | `g4gpu-phase8b-gg-nucl-nucl-table`. |
| Citation | Davis and Rabinowitz 1984 numerical interpolation; Lam, Rothberg, and Wolf 1991 locality optimization. |
| Status | OPEN |

### BD-geant4-127  Shen ion cross section repeats nuclear-radius and Coulomb-barrier arithmetic per isotope query

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/cross_sections/src/G4IonsShenCrossSection.cc` |
| Lines | 78-129 |
| Hot-path % (profile-measured) | Shen ion cross-section query: per-line self% `OPEN:` pending light-ion physics-list profiles. |
| Category | 4 -- Mathematical |
| Current pattern | Snippet: compute `Ap/Zp`, kinetic energy per nucleon, `Z13` radii, nuclear masses, `Ecm`, Coulomb barrier `B`, `calCeValue`, and final `10*pi*R*R*(1-B/Ecm)`. |
| Why slow | Projectile and target isotope radii/masses are invariant, while the per-call path repeats scalar power, mass, and center-of-mass transforms for nearby energies. |
| Proposed fix | Precompute isotope-pair descriptors for radii/masses/barrier constants and evaluate a table-assisted energy function for `calCeValue` and final radius corrections. |
| Expected speedup | 1.1-1.8x inside Shen ion cross-section evaluation for light-ion workloads. |
| Validation | Compare cross sections over all active isotope pairs and energy-per-nucleon grids, including below-barrier zero regions. |
| Implementation target | `g4gpu-phase8b-shen-ion-xs-descriptor`. |
| Citation | Cormen et al. 2009 table lookup; Lam, Rothberg, and Wolf 1991 locality optimization. |
| Status | OPEN |

### BD-geant4-128  Binary light-ion reaction finalization allocates and corrects secondaries through long scalar loops

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/models/binary_cascade/src/G4BinaryLightIonReaction.cc` |
| Lines | 92-590 |
| Hot-path % (profile-measured) | Binary light-ion `ApplyYourself`/`Interact`: per-line self% `OPEN:` pending BIC light-ion event profiles. |
| Category | 6 -- Memory allocation |
| Current pattern | Snippet: `Interact`/`FuseNucleiAndPrompound`, heap `G4ReactionProductVector`/spectator/cascader containers, up to ten momentum-correction retries, and per-secondary `new G4DynamicParticle`. |
| Why slow | Reaction finalization mixes control decisions, conservation repair, spectator de-excitation, rotations, and heap secondary creation in one scalar path. |
| Proposed fix | Split low-energy fusion, cascade, spectator de-excitation, and secondary-emission finalizers; use arena-backed secondary buffers shared with generic hadronic final-state code. |
| Expected speedup | 1.05-1.4x inside BIC light-ion finalization, with larger allocator reduction in high-multiplicity ion cascades. |
| Validation | Fixed-seed replay compares secondaries, four-momentum, spectator A/Z, creator model IDs, and parent status; allocator counters should show fewer general heap calls. |
| Implementation target | `g4gpu-phase6-bic-light-ion-secondary-arena`. |
| Citation | Berger et al. 2000 Hoard allocator; Futamura 1971 partial evaluation. |
| Status | OPEN |

### BD-geant4-129  INCLXX interface resamples transparent/unphysical events and allocates conversion products one-by-one

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/models/inclxx/interface/src/G4INCLXXInterface.cc` |
| Lines | 176-552 |
| Hot-path % (profile-measured) | INCLXX `ApplyYourself`: per-line self% `OPEN:` pending INCL proton/ion event profiles. |
| Category | 5 -- Control flow |
| Current pattern | Snippet: model fallbacks, inverse-kinematics heap objects, a `do`/`while` retry loop around `processEvent`, per-particle `toG4Particle`, remnant validation, and de-excitation product allocation. |
| Why slow | Rare fallbacks, inverse kinematics, remnant validation, conservation checks, and product conversion all remain interleaved in the common event path. |
| Proposed fix | Preselect direct/inverse/fallback event thunks by projectile-target regime and emit products through a reusable conversion arena, keeping resampling checks as explicit guards. |
| Expected speedup | 1.05-1.3x inside INCLXX interface overhead; physics-core speedup depends on `processEvent` dominance. |
| Validation | Fixed-seed replay compares event accept/retry counts, secondary PDG/four-vectors, remnant fragments, de-excitation products, and tally outputs. |
| Implementation target | `g4gpu-phase6-inclxx-interface-specialization`. |
| Citation | Hoelzle, Chambers, and Ungar 1991 polymorphic inline caches; Berger et al. 2000 allocator design. |
| Status | OPEN |

### BD-geant4-130  Bertini intra-nuclear cascader iterates particle fate, recoil repair, clustering, and on-shell correction in one loop

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/models/cascade/cascade/src/G4IntraNucleiCascader.cc` |
| Lines | 361-650 |
| Hot-path % (profile-measured) | Bertini intra-nuclear cascade loop/finalization: per-line self% `OPEN:` pending proton/ion Bertini profiles. |
| Category | 5 -- Control flow |
| Current pattern | Snippet: `while (!cascad_particles.empty() && !model->empty())`, `generateParticleFate`, reflection/trapped-particle branches, recoil recomputation, cluster finding, sorting, and `output.setOnShell`. |
| Why slow | The inner cascade loop and final physical-acceptance repair share mutable AoS containers, repeated recoil recomputation, branchy escape/barrier logic, and late failure retries. |
| Proposed fix | Separate fate generation, escape/barrier handling, recoil accounting, and on-shell repair into profiled stages with reusable buffers and a deterministic failure/retry ledger. |
| Expected speedup | 1.05-1.35x inside Bertini proton/ion cascade overhead; larger if recoil recomputation or container churn dominates profiles. |
| Validation | Fixed-seed replay compares outgoing particles, recoil A/Z/four-momentum, cluster products, accept/retry status, and final energy-momentum residuals. |
| Implementation target | `g4gpu-phase6-bertini-cascade-staging`. |
| Citation | Stroustrup 2012 data-oriented containers; Lam, Rothberg, and Wolf 1991 locality optimization. |
| Status | OPEN |

## Next implementations after hadronic proton/ion shard

1. `g4gpu-phase6-hadronic-xs-descriptor-cache` from BD-geant4-122/123: shared
   proton/ion material and isotope lookup cache with strong regression surface.
2. `g4gpu-phase8b-gg-nucl-nucl-table` from BD-geant4-126: high-leverage smooth
   cross-section table for light-ion workloads after exact-grid validation.
3. `g4gpu-phase6-bic-light-ion-secondary-arena` from BD-geant4-128: compact
   allocator-removal target that composes with generic hadronic final-state work.
4. `g4gpu-phase6-inclxx-interface-specialization` from BD-geant4-129: guarded
   specialization around INCL, with physics-core left untouched.
5. `g4gpu-phase6-bertini-cascade-staging` from BD-geant4-130: stage separation
   before any algorithmic rewrite of the cascade itself.

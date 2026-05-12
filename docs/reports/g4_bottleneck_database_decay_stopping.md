# Geant4 decay/stopping bottleneck database shard

Scope: structured source-review entries for Geant4 `v11.2.2` decay,
radioactive-decay, and stopping-at-rest paths: `G4DecayPhysics`, generic
`G4Decay`, `G4RadioactiveDecay`, `G4StoppingPhysics`, `G4MuonMinusCapture`,
muonic-atom decay/capture, and precompound muon capture. This worker-4
lane-swap shard fills the queued `BD-geant4-091`--`100` gap and intentionally
avoids the completed `BD-geant4-001`--`090` and `BD-geant4-101`--`110`
findings.

Source provenance: LUNARC `/projects/hep/fs10/shared/nnbar/billy/geant4-fork`
reported `git describe --tags --always --dirty` = `v11.2.2` and short commit
`f840b5da3a`. The local mirror `/tmp/geant4-v11.2.2` was SHA-256 matched
against LUNARC for every file cited here before extracting line numbers. No
measured speedup or priority promotion is claimed here; every `Hot-path %`
remains `OPEN:` until Phase 5 or a decay/stopping benchmark maps self-time to
exact lines.

## Entries

### BD-geant4-091  Generic decay-channel selection recomputes viable branching sums and linearly scans channels

| Field | Value |
|-------|-------|
| File | `source/particles/management/src/G4DecayTable.cc` |
| Lines | 77-108 |
| Hot-path % (profile-measured) | Decay-channel selection: per-line self% `OPEN:` pending decay-rich resonance/radioisotope profiling. |
| Category | 2 — Algorithm |
| Current pattern | Snippet: `for (const auto channel : *channels)` first recomputes `sumBR`, then a second loop samples `br = sumBR * G4UniformRand()` with a `MAX_LOOP = 10000` retry guard. |
| Why slow | Channel lists are immutable for many particles after physics-table construction, but every decay rechecks parent-mass admissibility and performs an O(number-of-channels) cumulative scan. |
| Proposed fix | Build per-parent decay-table descriptors with sorted admissible-channel masks and prefix/alias sampling tables for common parent-mass regimes; keep the current scan as an out-of-domain fallback. |
| Expected speedup | 1.1-2x inside channel selection for isotope/resonance workloads with many decay channels; wall-clock depends on decay density. |
| Validation | Exhaustively compare selected-channel probabilities against the current selector for nominal and low dynamic parent masses; fixed-seed fallback must match and accelerated mode must pass chi-square/KS tests. |
| Implementation target | `g4gpu-phase8b-decay-channel-selector`. |
| Citation | Walker 1977 alias tables; Vose 1991 alias method; Devroye 1986 non-uniform random variate generation. |
| Status | OPEN |

### BD-geant4-092  Generic DecayIt allocates decay products and secondary tracks one-by-one

| Field | Value |
|-------|-------|
| File | `source/processes/decay/src/G4Decay.cc` |
| Lines | 180-383 |
| Hot-path % (profile-measured) | Generic decay execution: per-line self% `OPEN:` pending pion/kaon/resonance decay profiles. |
| Category | 6 — Memory allocation |
| Current pattern | Snippet: selected channels return `products = decaychannel->DecayIt(...)`; then each daughter becomes `new G4Track(products->PopProducts(), finalGlobalTime, currentPosition)` before `delete products`. |
| Why slow | The path allocates a `G4DecayProducts` container, pops daughters one at a time, copies the current position per daughter, and heap-allocates every `G4Track`, which creates allocator pressure in decay-rich showers. |
| Proposed fix | Introduce a decay-secondary arena or small-vector transfer path that reserves the known daughter count, reuses the parent position/touchable handle, and hands ownership to `G4ParticleChangeForDecay` without per-daughter general heap traffic. |
| Expected speedup | 1.05-1.4x inside generic decay finalization; strongest for high-multiplicity resonance/ion decay cascades and multi-threaded allocator contention. |
| Validation | Fixed-seed replay compares daughter PDG codes, four-vectors, times, touchable handles, creator process, and parent kill/deposit state; allocator counters should show fewer `G4Track`/container allocations. |
| Implementation target | `g4gpu-phase6-decay-secondary-arena`. |
| Citation | Berger et al. 2000 Hoard allocator; Stroustrup 2012 data-oriented containers. |
| Status | OPEN |

### BD-geant4-093  Radioactive-decay table loading parses text records and inserts sorted channels under a global lock

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/models/radioactive_decay/src/G4RadioactiveDecay.cc` |
| Lines | 523-895 |
| Hot-path % (profile-measured) | First-use RDM table load: per-line self% `OPEN:` pending activation/radioisotope startup profiles. |
| Category | 3 — Data structure |
| Current pattern | Snippet: `G4AutoLock lk(&radioactiveDecayMutex)`, `DecaySchemeFile.getline(inputChars, 120)`, repeated `new G4...Decay(...)`, `theDecayTable->Insert(...)`, and a normalization pass over `theDecayTable->entries()`. |
| Why slow | Lazy first-use table construction serializes all threads, parses ENSDF-derived text, creates each channel independently, and repeatedly performs sorted insertion before the table is cached. |
| Proposed fix | Precompile or memory-map immutable RDM table descriptors keyed by `(Z,A,level,float)` with prefix/alias metadata, load them outside the global critical section, and publish through a double-checked cache. |
| Expected speedup | 1.2-5x in radioisotope-heavy initialization/first-event startup; also reduces thread stalls when multiple isotopes decay early in a run. |
| Validation | Compare every loaded channel mode, daughter level, branching ratio, ARM flag, and normalized total against the current parser; stress multi-thread first-use with TSAN-style lock/order checks. |
| Implementation target | `g4gpu-phase6-rdm-table-descriptor-cache`. |
| Citation | Lam, Rothberg, and Wolf 1991 locality optimization; Herlihy and Shavit 2012 concurrent data structures. |
| Status | OPEN |

### BD-geant4-094  Radioactive DecayAnalog repeats product boost, model-ID lookup, and secondary allocation

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/models/radioactive_decay/src/G4RadioactiveDecay.cc` |
| Lines | 984-1103 |
| Hot-path % (profile-measured) | RDM analog finalization: per-line self% `OPEN:` pending activation and detector-material decay profiles. |
| Category | 6 — Memory allocation |
| Current pattern | Snippet: `products->Boost(...)`, `G4PhysicsModelCatalog::GetModelID(...)`, then `new G4Track(products->PopProducts(), finalGlobalTime, theTrack.GetPosition())` inside the secondary loop. |
| Why slow | RDM finalization repeats model-ID lookups, creates one track per daughter, and redoes position/touchable/weight setup for every secondary even when daughter counts and creator-model rules are mode-specific. |
| Proposed fix | Cache RDM creator-model IDs per mode and share the generic decay secondary arena from BD-geant4-092, with mode-specific metadata for IT and electron-capture atomic-relaxation daughters. |
| Expected speedup | 1.05-1.35x inside radioactive decay finalization; larger allocator reduction for activation events with gamma/electron cascades. |
| Validation | Fixed-seed replay compares daughter list, creator model IDs, weights, times, atomic-relaxation tagging, local deposit, and parent status; benchmark allocator samples before/after. |
| Implementation target | `g4gpu-phase6-rdm-secondary-arena`. |
| Citation | Berger et al. 2000 Hoard allocator; Lam, Rothberg, and Wolf 1991 locality optimization. |
| Status | OPEN |

### BD-geant4-095  Radioactive DoDecay and collimation take a scalar branchy path over every visible daughter

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/models/radioactive_decay/src/G4RadioactiveDecay.cc` |
| Lines | 1106-1223 |
| Hot-path % (profile-measured) | RDM channel execution and directional bias: per-line self% `OPEN:` pending biased-source profiles. |
| Category | 5 — Control flow |
| Current pattern | Snippet: `SelectADecayChannel(parentPlusQ)`, `theRadDecayMode = ...`, IT uses `decayIT->DecayIt(0.0)`, all modes call `CollimateDecay(products)`, and collimation loops over daughter particle definitions. |
| Why slow | Directional bias is usually disabled or has stable cone parameters, yet every decay enters the collimation gate; visible-daughter tests are a scalar chain over definitions. |
| Proposed fix | Split no-collimation, fixed-cone collimation, and generic collimation thunks at configuration time; precompute visible-daughter bitsets and pair with the channel selector descriptor from BD-geant4-091. |
| Expected speedup | 1.05-1.25x in biased radioactive-source workloads; near-zero risk no-collimation fast path for default simulations. |
| Validation | Compare channel mode, daughter directions, cone angular distribution, and no-bias exact output; accelerated no-collimation path must be bit-identical to current no-op behavior. |
| Implementation target | `g4gpu-phase5d-rdm-collimation-specialization`. |
| Citation | Futamura 1971 partial evaluation; Hoelzle, Chambers, and Ungar 1991 polymorphic inline caches. |
| Status | OPEN |

### BD-geant4-096  StoppingPhysics constructs and registers stopping processes by scanning all particles with long type ladders

| Field | Value |
|-------|-------|
| File | `source/physics_lists/constructors/stopping/src/G4StoppingPhysics.cc` |
| Lines | 95-177 |
| Hot-path % (profile-measured) | Stopping-process construction: per-line self% `OPEN:` pending physics-list startup profiles. |
| Category | 5 — Control flow |
| Current pattern | Snippet: `muProcess = new G4MuonMinusCapture()`, `while ((*myParticleIterator)())`, then pointer comparisons against anti-hadron and negative-hadron definitions before `AddRestProcess`. |
| Why slow | Initialization walks the whole particle table and evaluates a hard-coded branch ladder for a small fixed set of particles; repeated physics-list construction pays this setup cost and obscures the applicable set. |
| Proposed fix | Replace the scan/ladder with constexpr registration descriptors for mu-minus, Fritiof anti-hadron captures, and Bertini negative-hadron captures, while retaining the generic scan as a debug fallback. |
| Expected speedup | 1.05-1.3x in stopping-physics construction; mainly startup/worker initialization benefit for applications repeatedly constructing run managers. |
| Validation | Compare registered rest processes for every particle definition before/after; verify `G4MuonMinusCapture` is still installed only for `mu-` when enabled. |
| Implementation target | `g4gpu-phase5d-stopping-registration-descriptors`. |
| Citation | Futamura 1971 partial evaluation; Stroustrup 2012 data-oriented containers. |
| Status | OPEN |

### BD-geant4-097  Bound muon decay/capture recomputes rates and uses rejection loops before allocating daughters

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/stopping/src/G4MuonMinusBoundDecay.cc` |
| Lines | 79-177 |
| Hot-path % (profile-measured) | Muon bound decay/capture branch: per-line self% `OPEN:` pending stopped-muon profiles. |
| Category | 4 — Mathematical |
| Current pattern | Snippet: `GetMuonCaptureRate(Z, A)`, `GetMuonDecayRate(...)`, `-G4Log(G4UniformRand())/lambda`, nested rejection on `(3.0 - 2.0*x)*x*x`, then `new G4DynamicParticle(...)` for electron and neutrinos. |
| Why slow | Rates depend only on `(Z,A)` and the sampling distribution is fixed for a muonic-atom state, but each stopped muon recomputes rates and performs scalar rejection plus per-daughter heap allocation. |
| Proposed fix | Cache per-isotope bound-muon rate packs and replace the electron-energy rejection sampler with a tabulated inverse-CDF/alias sampler; emit daughters through a small fixed secondary bundle. |
| Expected speedup | 1.1-2x inside bound-decay sampling for stopped-muon workloads; strongest when many captures occur in a small material set. |
| Validation | Compare capture-vs-decay probabilities, decay-time distribution, electron energy, neutrino four-vectors, and daughter counts per `(Z,A)`; require KS p >= 0.05 for sampled spectra. |
| Implementation target | `g4gpu-phase8b-bound-muon-decay-sampler`. |
| Citation | Devroye 1986 non-uniform random variate generation; Walker 1977 alias tables; Berger et al. 2000 Hoard allocator. |
| Status | OPEN |

### BD-geant4-098  Muon capture/decay rate lookups linearly scan isotope tables and recompute empirical formulas

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/stopping/src/G4MuonMinusBoundDecay.cc` |
| Lines | 181-431 |
| Hot-path % (profile-measured) | Muonic-atom rate lookup: per-line self% `OPEN:` pending stopped-muon material scans. |
| Category | 3 — Data structure |
| Current pattern | Snippet: static `capRates[]` is scanned until `capRates[j].Z > Z`; missing entries call `GetMuonZeff(Z)` and evaluate powers/formula terms; decay rate recomputes `x = Z*fine_structure_const`. |
| Why slow | The tables and empirical formulas are immutable, and active simulations usually involve a small material isotope set, but every query repeats scans, effective-charge lookup, and polynomial arithmetic. |
| Proposed fix | Build an indexed `(Z,A)` rate table with precomputed capture, decay, `lambda`, and branch probability values for active isotopes; fall back to formula evaluation for unseen isotopes. |
| Expected speedup | 1.05-1.4x in rate lookup and lower variance in stopped-muon at-rest scheduling; wall-clock depends on muon capture density. |
| Validation | Exhaustively compare capture and decay rates for `Z=1..100`, known isotope table entries, and representative natural isotope masses; event validation compares stopped-muon lifetime spectra. |
| Implementation target | `g4gpu-phase6-muonic-rate-table`. |
| Citation | Cormen et al. 2009 table lookup; Lam, Rothberg, and Wolf 1991 locality optimization. |
| Status | OPEN |

### BD-geant4-099  Precompound muon capture repeatedly samples in-nucleus protons and allocates reaction-product vectors

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/stopping/src/G4MuMinusCapturePrecompound.cc` |
| Lines | 91-258 |
| Hot-path % (profile-measured) | Muon nuclear-capture precompound final state: per-line self% `OPEN:` pending stopped-muon capture profiles. |
| Category | 2 — Algorithm |
| Current pattern | Snippet: `fNucleus.Init(A, Z)`, repeated random `index=G4int(A*G4UniformRand())` until a proton is found, `do ... while(eEx <= 0.0)`, then `G4ReactionProductVector* rpv = fPreCompound->DeExcite(initialState)`. |
| Why slow | The algorithm rejection-samples protons and excitation-positive states in a loop, then allocates/deletes a reaction-product vector for every capture; material/isotope state is stable across many captures. |
| Proposed fix | Precompute proton-index lists or weighted proton samplers per `(A,Z)` nucleus, cap/diagnose excitation retries, and pass a reusable reaction-product buffer from the precompound model when ownership allows. |
| Expected speedup | 1.1-1.8x inside muon-capture final-state setup; also reduces long-tail retries for neutron-rich nuclei. |
| Validation | Fixed-seed fallback compares selected proton, excitation energy, neutrino energy, residual fragment, de-excitation products, and times; accelerated mode compares secondary multiplicity/energy spectra per isotope. |
| Implementation target | `g4gpu-phase6-muon-capture-proton-sampler`. |
| Citation | Devroye 1986 rejection sampling; Berger et al. 2000 Hoard allocator. |
| Status | OPEN |

### BD-geant4-100  MuonicAtomDecay duplicates generic decay/capture finalization and transforms secondaries one-by-one

| Field | Value |
|-------|-------|
| File | `source/processes/hadronic/stopping/src/G4MuonicAtomDecay.cc` |
| Lines | 151-554 |
| Hot-path % (profile-measured) | Muonic-atom decay/capture process: per-line self% `OPEN:` pending stopped-muon and conversion-electron profiles. |
| Category | 6 — Memory allocation |
| Current pattern | Snippet: DIO path repeats decay-table selection and `new G4Track(...)`; NC path retries `cmptr->ApplyYourself(...)`; `FillResult` rotates each secondary and creates `new G4Track(...)` inside the loop. |
| Why slow | The class carries a copy of generic decay finalization plus a hadronic-result conversion path, both with per-secondary transformations and heap track creation. It misses the arena/cached-model-ID work proposed for generic and RDM decays. |
| Proposed fix | Refactor muonic-atom DIO onto the shared decay selector/secondary-arena path and route capture secondaries through a reusable `FillResult` arena with cached rotation/transform state. |
| Expected speedup | 1.05-1.4x in stopped-muon muonic-atom finalization; highest benefit when capture produces many de-excitation secondaries. |
| Validation | Fixed-seed replay compares DIO/capture branch, decay products, capture secondaries, times, rotations, weights, parent state, and touchable handles against current output. |
| Implementation target | `g4gpu-phase6-muonic-atom-finalization-arena`. |
| Citation | Berger et al. 2000 Hoard allocator; Lam, Rothberg, and Wolf 1991 locality optimization. |
| Status | OPEN |

## Next implementations after decay/stopping shard

1. `g4gpu-phase8b-decay-channel-selector` from BD-geant4-091: shared selector
   infrastructure benefits generic decay, radioactive decay, and muonic DIO.
2. `g4gpu-phase6-decay-secondary-arena` from BD-geant4-092: compact allocator
   improvement that composes with RDM and muonic-atom finalization.
3. `g4gpu-phase6-rdm-table-descriptor-cache` from BD-geant4-093: startup and
   multi-thread first-use win for activation-heavy workloads.
4. `g4gpu-phase8b-bound-muon-decay-sampler` from BD-geant4-097: targeted
   sampler optimization for stopped-muon and proton-therapy shielding studies.
5. `g4gpu-phase6-muon-capture-proton-sampler` from BD-geant4-099: reduces
   capture rejection loops before expensive precompound de-excitation.
6. `g4gpu-phase6-muonic-atom-finalization-arena` from BD-geant4-100: removes
   duplicated finalization logic and shares validation with generic decays.

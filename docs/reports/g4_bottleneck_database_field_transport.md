# Geant4 bottleneck database — field-transport structured shard

Status: compact-safe worker-4 source-review iteration, 2026-05-12. This shard
adds `BD-geant4-141`--`BD-geant4-150` and intentionally avoids previously used
or reserved IDs `BD-geant4-001`--`BD-geant4-140`.

## Source provenance and profile basis

- LUNARC socket guard returned `Connected` before source discovery.
- LUNARC `/projects/hep/fs10/shared/nnbar/billy/geant4-fork` reported
  `git describe --tags --always --dirty` = `v11.2.2` and short commit
  `f840b5da3a` before later multiplexed SSH session attempts returned
  `Session open refused by peer` / keyboard-interactive denial.
- Exact line extraction therefore used the existing local Geant4 source mirror
  `/tmp/geant4-v11.2.2`, whose `CMakeLists.txt` declares version `11.2.2`.
- Cited local source hashes:
  - `G4Transportation.cc` 937 lines,
    `f44499e5d51e681cbdf429f3314c01cebb8bb3e8e9794891baa54ba2c014f688`
  - `G4PropagatorInField.cc` 885 lines,
    `ccdf72d37fc5f116ed594ddb64c1fb32e95315abdeba2965be842ef2746d9959`
  - `G4ChordFinderDelegate.icc` 414 lines,
    `dfea31de27e90f647c20ef76f5c11c7f8f8dd43d197197e27fbba9a538a1d750`
  - `G4ChordFinder.cc` 655 lines,
    `3b6ccee6e02af5595caee72eefd02950603e7847bcbfa2935eb2972789db90f4`
  - `G4IntegrationDriver.icc` 389 lines,
    `2da5e44eb9586ee9a031b3a2122f172d3bd728281a3456923f9b4a2d45be7602`
  - `G4RKIntegrationDriver.icc` 237 lines,
    `e469a51640a095bc05cdeea81097f1da53e616966911fc3a07e41aa08adf1ac3`
  - `G4FieldUtils.cc` 112 lines,
    `86c0a191212f9e6cb4f21ab05adeab23e84db6004c78fd427ecfd6ce4cd7d455`
  - `G4FieldTrack.icc` 385 lines,
    `62184ead2e934e3e29d213ab2070a99e7e84ea6ba2fb92ba201d95dd4c2e05b1`
  - `G4CachedMagneticField.cc` 108 lines,
    `f0e13b37441ce19a7eaa4e16637b5c8588e580c6ec0bf71548d2844d3a39dbd0`
- Hot-path weight remains `OPEN:` until Phase 5 perf maps field-rich
  workloads (muon spectrometer, CMS HCAL in field, proton therapy pencil beam,
  ATLAS pile-up) to exact source lines. The review still treats field
  propagation as generally useful because magnetic/electric field integration
  is shared by HEP, medical, and space-radiation Geant4 applications.
- Isolation check: documentation only. No `NNBAR_Detector/`,
  `nnbar_reconstruction/`, `scripts/`, `lunarc/`, `slurm/`, or `macro/` paths
  were modified.

## References used by entries

- Press, Teukolsky, Vetterling, and Flannery 1992, adaptive Runge--Kutta step
  control in *Numerical Recipes in C*.
- Hairer, Nørsett, and Wanner 1993, *Solving Ordinary Differential Equations I*.
- Futamura 1971/1983, partial evaluation and program specialization.
- Hoelzle, Chambers, and Ungar 1991, polymorphic inline caches.
- Lam, Rothberg, and Wolf 1991, cache locality/blocking transformations.
- Intel 2024, *64 and IA-32 Architectures Optimization Reference Manual*.
- Ericson 2005, *Real-Time Collision Detection* spatial coherence patterns.

## Entries

### BD-geant4-141  Field-manager lookup and reconfiguration are repeated on every charged step

| Field | Value |
|-------|-------|
| File | `source/processes/transportation/src/G4Transportation.cc`; `source/geometry/navigation/src/G4PropagatorInField.cc` |
| Lines | `G4Transportation.cc` 190-264; `G4PropagatorInField.cc` 122-219 |
| Hot-path % (profile-measured) | Field-transport setup: `OPEN:` pending Phase 5 field-rich profiles. |
| Category | 5 — Control flow |
| Current pattern | Snippet: `FindAndSetFieldManager(track.GetVolume())`, `fieldMgr->ConfigureForTrack(&track)`, then `RefreshIntersectionLocator()` on each field step. |
| Why slow | Most tracks remain in the same field manager and equation for many consecutive substeps, but the code still refreshes the manager, track-specific configuration hook, chord finder, and intersection locator every call. |
| Proposed fix | Add a volume/field-manager epoch descriptor cached on the transportation state; bypass lookup/configure/locator refresh while the physical volume and field-manager epoch are unchanged, with a compatibility slow path for custom `ConfigureForTrack`. |
| Expected speedup | 1.03-1.15x in field-heavy tracking; larger in geometries with many charged tracks crossing long same-field regions. |
| Validation | Fixed-seed replay with and without custom field-manager subclasses; assert identical field-manager pointers, equation charge/momentum/mass parameters, boundary statuses, and final track states. |
| Implementation target | `g4gpu-phase5d-field-manager-epoch-cache`; upstream Geant4 MR `transportation-field-manager-epoch`. |
| Citation | Hoelzle, Chambers, and Ungar 1991; Futamura 1971. |
| Status | OPEN |

### BD-geant4-142  FieldTrack object copies shuttle the same 12-component state through the propagation loop

| Field | Value |
|-------|-------|
| File | `source/processes/transportation/src/G4Transportation.cc`; `source/geometry/navigation/src/G4PropagatorInField.cc`; `source/geometry/magneticfield/include/G4FieldTrack.icc` |
| Lines | `G4Transportation.cc` 190-337; `G4PropagatorInField.cc` 122-370; `G4FieldTrack.icc` 31-79 |
| Hot-path % (profile-measured) | Field-state copy overhead: `OPEN:` pending per-symbol field profiles. |
| Category | 3 — Data structure |
| Current pattern | Snippet: `G4FieldTrack aFieldTrack(...)`, `G4FieldTrack CurrentState(pFieldTrack)`, `OriginalState = CurrentState`, and copy constructors manually assign `SixVector[0]` through `SixVector[5]`. |
| Why slow | Field propagation repeatedly materializes AoS-style `G4FieldTrack` objects with embedded vectors, times, charge state, and six-vector data even when the integrator immediately converts them back to raw arrays. |
| Proposed fix | Introduce an internal `FieldStateView` / `FieldStateArray` fast path for transportation + integrator handoff, with explicit conversion only at public API boundaries and debug dumps. |
| Expected speedup | 1.05-1.20x in propagation code that is currently copy/load/store bound; also unlocks SIMD-friendly field batches. |
| Validation | Unit tests compare every `G4FieldTrack` observable after each substep; event replay requires bit-identical end position, momentum, spin, time, and curve length for fixed seeds. |
| Implementation target | `g4gpu-phase6-field-state-soa`; reusable in libMCAccel field kernels. |
| Citation | Lam, Rothberg, and Wolf 1991; Intel 2024. |
| Status | OPEN |

### BD-geant4-143  Infinite proposed steps force a world-solid distance query inside field propagation

| Field | Value |
|-------|-------|
| File | `source/geometry/navigation/src/G4PropagatorInField.cc` |
| Lines | 122-219 |
| Hot-path % (profile-measured) | Field step initialization: `OPEN:` pending profiles for long-lived charged tracks. |
| Category | 2 — Algorithm |
| Current pattern | Snippet: if the proposed step is huge, compute `fNavigator->GetWorldVolume()->GetLogicalVolume()->GetSolid()->DistanceToOut(StartPointA, VelocityUnit)`. |
| Why slow | A field-limited track can repeatedly ask the world solid for the same coarse upper bound before adaptive integration and geometry intersection do finer work. |
| Proposed fix | Cache a per-track world-boundary upper limit and update it monotonically after accepted curve progress; fall back to the existing `DistanceToOut` query after volume relocation or direction changes above a tolerance. |
| Expected speedup | 1.01-1.08x for long steps in large world volumes; most useful for beamline/space-radiation runs with long same-direction charged tracks. |
| Validation | Compare proposed step caps, actual true path lengths, boundary hits, and world-exit status over straight, curved, and near-boundary tracks; require no missed boundary in randomized geometry tests. |
| Implementation target | `g4gpu-phase5d-field-world-bound-cache`. |
| Citation | Ericson 2005; Cormen et al. 2009 dynamic programming/memoization. |
| Status | OPEN |

### BD-geant4-144  Every non-first field substep relocates the navigator before chord intersection

| Field | Value |
|-------|-------|
| File | `source/geometry/navigation/src/G4PropagatorInField.cc` |
| Lines | 122-367 |
| Hot-path % (profile-measured) | Curved-trajectory geometry intersection: `OPEN:` pending field + geometry profiles. |
| Category | 2 — Algorithm |
| Current pattern | Snippet: `LocateGlobalPointWithinVolume(SubStartPoint)` for each non-first substep, followed by `AdvanceChordLimited(...)` and `IntersectChord(...)`. |
| Why slow | The substep start is usually the accepted endpoint from the previous substep in the same volume, but navigation state is still reconstructed before testing the next chord. |
| Proposed fix | Thread an explicit navigator-state token from `IntersectChord` to the next substep so same-volume continuation can skip relocation; invalidate on boundary, stuck-particle recovery, or changed touchable history. |
| Expected speedup | 1.05-1.25x in magnetic-field tracking where many short chords remain within one volume. |
| Validation | Differential test on field tracks grazing boundaries, daughters, replicas, and parameterised volumes; require identical located volume, touchable history, `fLastStepInVolume`, and post-step status. |
| Implementation target | `g4gpu-phase5d-field-navigator-state-token`. |
| Citation | Ericson 2005 spatial coherence; Lam, Rothberg, and Wolf 1991 locality. |
| Status | OPEN |

### BD-geant4-145  Delta-chord relaxation is rediscovered then reset inside each ComputeStep call

| Field | Value |
|-------|-------|
| File | `source/geometry/navigation/src/G4PropagatorInField.cc`; `source/geometry/magneticfield/include/G4ChordFinderDelegate.icc` |
| Lines | `G4PropagatorInField.cc` 122-527; `G4ChordFinderDelegate.icc` 88-175 |
| Hot-path % (profile-measured) | Chord-limited integration control: `OPEN:` pending profiler evidence. |
| Category | 4 — Mathematical |
| Current pattern | Snippet: after repeated loop iterations, `SetDeltaChord(GetDeltaChord() * 2.0)`; at return, `SetDeltaChord(deltaChord)`. `FindNextChord` separately updates `fLastStepEstimate_Unconstrained`. |
| Why slow | The algorithm learns that a track/region needs a relaxed chord criterion, uses it only inside the current call, then discards it even if the next call has the same curvature and safety regime. |
| Proposed fix | Persist a bounded per-track chord-control state keyed by field manager and curvature bin, with hysteresis and strict reset at boundaries or field-manager changes. |
| Expected speedup | 1.02-1.15x by reducing repeated rejected chord trials in difficult field regions. |
| Validation | Compare sagitta errors, accepted chord lengths, geometry intersections, and final state against the current reset-every-call behavior; include stress tests near volume boundaries. |
| Implementation target | `g4gpu-phase8a-adaptive-chord-controller`. |
| Citation | Hairer, Nørsett, and Wanner 1993 adaptive ODE control. |
| Status | OPEN |

### BD-geant4-146  Chord search reintegrates from the original state for every rejected trial length

| Field | Value |
|-------|-------|
| File | `source/geometry/magneticfield/include/G4ChordFinderDelegate.icc` |
| Lines | 88-175 |
| Hot-path % (profile-measured) | Chord-limited `FindNextChord`: `OPEN:` pending profiles of field-rich workloads. |
| Category | 2 — Algorithm |
| Current pattern | Snippet: `for (; noTrials < maxTrials; ++noTrials) { yEnd = yStart; QuickAdvance(yEnd, ..., stepTrial, ...) }`, reducing `stepTrial` until `dChordStep < chordDistance`. |
| Why slow | A failed chord trial discards the integrated state and repeats the same right-hand-side work from `yStart` at a shorter trial length. |
| Proposed fix | Prefer interpolation-capable drivers for curved tracks and add a generic bracketed chord search that reuses intermediate RK stage data or dense-output interpolation instead of restarting each trial. |
| Expected speedup | 1.1-1.5x inside difficult-field chord finding; negligible for tracks whose first trial is accepted. |
| Validation | Per-step comparison of selected chord length, sagitta, endpoint state, and intersection point against current `FindNextChord`; event-level validation uses fixed-seed replay plus KS tests on track curvature and boundary crossing spectra. |
| Implementation target | `g4gpu-phase8a-dense-output-chord-search`. |
| Citation | Press et al. 1992; Hairer, Nørsett, and Wanner 1993. |
| Status | OPEN |

### BD-geant4-147  Intersection-point refinement can re-advance the curve after a chord/geometry hit

| Field | Value |
|-------|-------|
| File | `source/geometry/magneticfield/src/G4ChordFinder.cc` |
| Lines | 427-640 |
| Hot-path % (profile-measured) | Boundary refinement after chord/geometry intersection: `OPEN:` pending field-boundary profiles. |
| Category | 4 — Mathematical |
| Current pattern | Snippet: `InvParabolic(...)`, clamp `test_step`, then `fIntgrDriver->AccurateAdvance(EndPoint, test_step, eps_step)`; the linear fallback computes `AE_fraction` and calls `AccurateAdvance` again. |
| Why slow | Once a chord intersects geometry, the code may run additional accurate advances solely to refine the boundary point, duplicating integration already performed for the enclosing chord. |
| Proposed fix | Use dense-output interpolation from the last accepted RK step to evaluate the curve at the candidate boundary parameter; only re-integrate when the driver advertises no reliable dense output. |
| Expected speedup | 1.05-1.3x for field tracks that cross many fine detector boundaries. |
| Validation | Compare refined boundary point, tangent, curve length, and relocated volume against current Brent/linear refinement over grazing, shallow-angle, and high-curvature tracks. |
| Implementation target | `g4gpu-phase8a-dense-output-boundary-refinement`. |
| Citation | Brent 1973 root finding; Hairer, Nørsett, and Wanner 1993 dense output. |
| Status | OPEN |

### BD-geant4-148  Integration drivers repeatedly dump/load FieldTrack state arrays around each RK step

| Field | Value |
|-------|-------|
| File | `source/geometry/magneticfield/include/G4IntegrationDriver.icc`; `source/geometry/magneticfield/include/G4FieldTrack.icc` |
| Lines | `G4IntegrationDriver.icc` 94-292; `G4FieldTrack.icc` 307-336 |
| Hot-path % (profile-measured) | RK step state marshalling: `OPEN:` pending per-symbol profiles. |
| Category | 3 — Data structure |
| Current pattern | Snippet: `track.DumpToArray(y)`, `QuickAdvance(...)`, `track.LoadFromArray(yOut, ...)`, plus `DumpToArray` writing position, momentum, energy, time, and polarization slots one by one. |
| Why slow | Public object state and integrator array state are converted back and forth inside hot loops, creating scalar stores/loads and preventing vectorized batches of same-stepper tracks. |
| Proposed fix | Keep integrator-owned state arrays live across substeps and expose a small adapter for public `G4FieldTrack` reads; batch same-stepper tracks into SoA blocks in the accelerator path. |
| Expected speedup | 1.05-1.25x in scalar Geant4 field integration; larger when combined with Phase 6 SoA batching. |
| Validation | Bitwise compare `DumpToArray`/`LoadFromArray` round trips and fixed-seed event endpoints; add ASan/UBSan coverage for aliasing and lifetime boundaries. |
| Implementation target | `g4gpu-phase6-integrator-state-soa`. |
| Citation | Lam, Rothberg, and Wolf 1991; Intel 2024. |
| Status | OPEN |

### BD-geant4-149  Step-size growth/shrink uses generic pow calls for order-fixed RK controllers

| Field | Value |
|-------|-------|
| File | `source/geometry/magneticfield/include/G4RKIntegrationDriver.icc`; `source/geometry/magneticfield/include/G4IntegrationDriver.icc` |
| Lines | `G4RKIntegrationDriver.icc` 41-83; `G4IntegrationDriver.icc` 217-266 |
| Hot-path % (profile-measured) | RK accepted/rejected step control: `OPEN:` pending field-step profiles. |
| Category | 4 — Mathematical |
| Current pattern | Snippet: `std::pow(error2, 0.5 * GetPshrnk())` and `std::pow(error2, 0.5 * GetPgrow())` inside shrink/grow decisions for every retrial or accepted step. |
| Why slow | The exponent is fixed by the chosen RK order and safety parameters for a run, but the generic libm `pow` path is used in the step-control loop. |
| Proposed fix | Specialize shrink/grow controllers per stepper order at construction time: fast paths for zero/tiny/large error, precomputed exponents, and optional polynomial/log2 approximations gated by an exact fallback. |
| Expected speedup | 1.02-1.10x in RK controller overhead; highest when field evaluation is cheap and many small accepted steps occur. |
| Validation | Exhaustively compare proposed `hnext` over logarithmic error grids and all supported RK orders; replay field-rich events requiring identical accepted/rejected step histories in exact-controller mode. |
| Implementation target | `g4gpu-phase5d-rk-step-controller-specialization`. |
| Citation | Press et al. 1992; Intel 2024. |
| Status | OPEN |

### BD-geant4-150  Field-value caching remembers only one scalar location/value pair

| Field | Value |
|-------|-------|
| File | `source/geometry/magneticfield/src/G4CachedMagneticField.cc`; `source/geometry/magneticfield/src/G4FieldUtils.cc` |
| Lines | `G4CachedMagneticField.cc` 87-108; `G4FieldUtils.cc` 38-88 |
| Hot-path % (profile-measured) | Field evaluation / error-estimate helper calls: `OPEN:` pending profiles for field maps and smooth analytic fields. |
| Category | 3 — Data structure |
| Current pattern | Snippet: compute `(newLocation - fLastLocation).mag2()`, return `fLastValue` if within one distance threshold, otherwise call `fpMagneticField->GetFieldValue(...)`; error helpers separately recompute momentum norms. |
| Why slow | Smooth fields and tabulated maps often revisit a small local neighborhood, but the cache is a single last-value slot and cannot serve RK stage neighborhoods, batches, or nearby tracks. |
| Proposed fix | Add an optional per-thread small stencil cache keyed by field-map cell / quantized position, returning exact values for repeated points and interpolation coefficients for smooth maps; keep the one-slot wrapper as the compatibility fallback. |
| Expected speedup | 1.05-1.4x for field-map dominated workloads with locality; no benefit for highly irregular user fields. |
| Validation | Compare every returned B-field vector against the original field for exact-cache hits; for interpolation coefficients, require bit-identical output when coefficients reproduce the same map lookup and physics-equivalent trajectories otherwise. |
| Implementation target | `g4gpu-phase8a-field-map-stencil-cache`; reusable by OpenMC/OpenCLAW field adapters if added later. |
| Citation | Lam, Rothberg, and Wolf 1991; Ericson 2005. |
| Status | OPEN |

## Next implementation candidates

1. `g4gpu-phase6-integrator-state-soa` (BD-geant4-142/148): low physics risk,
   direct data-layout win, and prerequisite for same-stepper batching.
2. `g4gpu-phase8a-dense-output-chord-search` (BD-geant4-146/147): removes
   repeated integration work in the most visibly algorithmic part of field
   propagation.
3. `g4gpu-phase5d-field-manager-epoch-cache` (BD-geant4-141): small upstreamable
   patch with narrow validation surface.
4. `g4gpu-phase8a-field-map-stencil-cache` (BD-geant4-150): high upside for
   field-map applications, but must be opt-in because user fields can be
   arbitrary.

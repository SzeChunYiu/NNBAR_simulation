# Geant4 bottleneck database — PIL / geometry structured shard

Status: compact-safe worker-4 iteration 6. This shard converts the legacy
Physics Interaction Length (PIL) and geometry hot-path review in
`docs/reports/g4_source_review_hotpaths.md` into structured bottleneck entries
without editing the near-cap main database
`docs/reports/bottleneck_database_geant4.md`.

## Source provenance and profile basis

- LUNARC socket guard returned `Connected` before remote inspection.
- Authoritative NNBAR Geant4 install check:
  `/projects/hep/fs10/shared/nnbar/billy/packages/hibeam_env/bin/geant4-config
  --version --prefix` reported Geant4 `11.2.2` at
  `/projects/hep/fs10/shared/nnbar/billy/packages/hibeam_env`.
- The install exposes headers under `include/Geant4`, but the implementation
  `source/` tree was not present at the checked prefix. This review therefore
  used the same read-only upstream Geant4 `v11.2.2` source tree at
  `/tmp/geant4-v11.2.2` as prior worker-4 Geant4 review shards.
- Hot-path weight follows the source-review spec: PIL is about 30% and
  geometry navigation about 25% aggregate Geant4 CPU. Per-line
  self-percentages are `OPEN:` until Phase 5 perf maps
  BasicExample/TestEm0/Hadr01 samples to exact source lines.
- Isolation check: documentation only. No `NNBAR_Detector/`,
  `nnbar_reconstruction/`, `scripts/`, `lunarc/`, `slurm/`, or `macro/` paths
  were modified.

## References used by entries

- Futamura 1971/1983, partial evaluation / projection work.
- Hoelzle, Chambers, and Ungar 1991, polymorphic inline caches.
- Intel 2024, *64 and IA-32 Architectures Optimization Reference Manual*.
- Bentley 1975, multidimensional binary search trees.
- Vose 1991, alias-method distribution sampling.
- Trefethen 2013, *Approximation Theory and Approximation Practice*.
- Stroustrup 2012, cache-friendly contiguous data-structure guidance.
- MacDonald and Booth 1990, surface-area heuristic for BVH construction.
- Wald et al. 2007, fast SAH-based BVH construction.
- Williams et al. 2005, robust ray-box intersection.

---

## Physics Interaction Length hot path

These entries cover the uncovered structured-PIL conversion from the legacy
PIL-01--PIL-10 and PIL-12 notes. Legacy PIL-11 overlaps the already-structured
secondary-allocation entry `BD-geant4-013`, so it is intentionally not
re-issued here.

### BD-geant4-032  PostStep GPIL scans every candidate process through an indirect call

| Field | Value |
|-------|-------|
| File | `source/tracking/src/G4SteppingManager.cc` |
| Lines | 465-512 |
| Hot-path % (profile-measured) | PIL family: about 30% aggregate Geant4 CPU per lane-spec basis; per-line self% `OPEN:` pending Phase 5 perf. |
| Category | 5 — Control flow |
| Current pattern | Snippet: `fCurrentProcess = (*fPostStepGetPhysIntVector)((G4int)np)` followed by `fCurrentProcess->PostStepGPIL(...)` for every PostStep candidate. |
| Why slow | A stable particle/material/physics-list configuration still pays vector lookup, null check, virtual GPIL target, condition writeback, and selected-process bookkeeping at every step. The process order is effectively invariant during ordinary tracking. |
| Proposed fix | Build a particle-specialized PostStep GPIL dispatch table at run initialization, using partial evaluation to hard-code active process order and monomorphic direct-call thunks while retaining a guard that falls back if process activation changes. |
| Expected speedup | 1.3-2.0x on PostStep GPIL dispatch overhead; 5-10% event CPU on PIL-heavy profiles if table interpolation remains the residual bottleneck. |
| Validation | Fixed-seed bit-exact comparison of proposed step length, selected process, interaction-length counters, secondary counts, and final event summaries; force fallback whenever a process vector mutates after initialization. |
| Implementation target | `g4gpu-phase5d-jit-poststep-gpil`. |
| Citation | Futamura 1971/1983; Hoelzle, Chambers, and Ungar 1991. |
| Status | OPEN |

### BD-geant4-033  Force-condition bookkeeping keeps a branch ladder in the inner step loop

| Field | Value |
|-------|-------|
| File | `source/tracking/src/G4SteppingManager.cc` |
| Lines | 477-503 |
| Hot-path % (profile-measured) | PIL PostStep selection: per-line self% `OPEN:` pending perf. |
| Category | 5 — Control flow |
| Current pattern | Snippet: `switch (fCondition)` assigns `InActivated`/`Forced` states, updates `SetProcessDefinedStep`, and may clear the remaining vector slots before returning. |
| Why slow | Most processes return `NotForced` in ordinary transport, but the hot loop still carries rare force cases, an exception-only branch, and a clearing loop for the exclusive case. These branches are difficult to predict across mixed physics. |
| Proposed fix | Split the common `NotForced`/minimum-step path from rare force handling by preclassifying processes with possible force conditions and generating a rare slow-path dispatcher for forced or exclusive processes. |
| Expected speedup | 1.1-1.3x inside PostStep selection on mixed-process workloads; small but broadly shared event-level gain because every step executes this ladder. |
| Validation | Unit replay over processes that return each `G4ForceCondition`, plus fixed-seed event comparisons where forced and non-forced processes both appear; verify selected DoIt vector states exactly match vanilla. |
| Implementation target | `g4gpu-phase5d-gpil-force-slowpath`. |
| Citation | Intel 2024 branch-prediction guidance; Futamura 1971/1983. |
| Status | OPEN |

### BD-geant4-034  AlongStep GPIL repeats selection branches and transportation delegation checks

| Field | Value |
|-------|-------|
| File | `source/tracking/src/G4SteppingManager.cc` |
| Lines | 526-580 |
| Hot-path % (profile-measured) | PIL AlongStep family: per-line self% `OPEN:` pending perf. |
| Category | 5 — Control flow |
| Current pattern | Snippet: `fCurrentProcess->AlongStepGPIL(...)`, then `if (physIntLength < PhysicalStep)`, `CandidateForSelection`, parallel-world, and transportation-last tests. |
| Why slow | The loop mixes a virtual GPIL call with several policy branches whose outcomes depend on process type and vector position rather than per-step physics. Transportation-last and parallel-world handling are stable configuration facts. |
| Proposed fix | Precompute an AlongStep policy table containing direct GPIL thunks, whether each process may win selection, whether it delegates to transportation, and whether it is the terminal transportation process. |
| Expected speedup | 1.2-1.6x on AlongStep GPIL control overhead; larger improvement when parallel worlds are disabled because delegate checks become compile-time false. |
| Validation | Replay geometry-boundary and non-boundary fixed seeds, checking physical step, `fStepStatus`, proposed safety, and process-defined-step identity against vanilla; include a parallel-world regression where delegation remains active. |
| Implementation target | `g4gpu-phase5d-alongstep-policy-table`. |
| Citation | Hoelzle, Chambers, and Ungar 1991; Intel 2024. |
| Status | OPEN |

### BD-geant4-035  Thin GPIL wrappers preserve virtual dispatch instead of exposing direct thunks

| Field | Value |
|-------|-------|
| File | `source/processes/management/include/G4VProcess.hh` |
| Lines | 464-489 |
| Hot-path % (profile-measured) | PIL wrapper overhead across PostStep/AlongStep/AtRest: per-line self% `OPEN:` pending perf. |
| Category | 9 — JIT specialization |
| Current pattern | Snippet: `AlongStepGPIL(...)` and `PostStepGPIL(...)` inline wrappers forward to virtual `*GetPhysicalInteractionLength` methods, with `PostStepGPIL` also multiplying by `thePILfactor`. |
| Why slow | Inlining removes the wrapper body but not the virtual target. The process manager already knows the concrete process list after physics initialization, so repeated dynamic dispatch is avoidable for monomorphic process vectors. |
| Proposed fix | Add an optional cached GPIL thunk table per process manager: each entry stores a direct function pointer or generated stub that applies the PIL factor and calls the concrete method, invalidated if the process manager changes. |
| Expected speedup | 1.1-1.4x across GPIL wrappers; composes with BD-geant4-032/034 by making generated loops direct-call friendly. |
| Validation | ABI-preserving fallback remains default; generated-thunk mode must pass fixed-seed bit-exact step-length and selected-process tests for electromagnetic, transportation, and hadronic process managers. |
| Implementation target | `g4gpu-phase5d-gpil-thunk-table`. |
| Citation | Futamura 1971/1983; Hoelzle, Chambers, and Ungar 1991. |
| Status | OPEN |

### BD-geant4-036  EM PostStep GPIL recomputes material/model/lambda state per step

| Field | Value |
|-------|-------|
| File | `source/processes/electromagnetic/utils/src/G4VEnergyLossProcess.cc` |
| Lines | 592-664 |
| Hot-path % (profile-measured) | PIL EM mean-free-path setup: per-line self% `OPEN:` pending TestEm0/BasicExample perf. |
| Category | 4 — Mathematical |
| Current pattern | Snippet: `DefineMaterial(...)`, `SelectModel(...)`, ion charge updates, `ComputeLambdaForScaledEnergy(...)`, `1.0/preStepLambda`, and exponential interaction-length bookkeeping. |
| Why slow | Material-cuts-couple, model choice, cross-section scale, and lambda cache state are often stable over runs of steps, but the routine repeats setup and scalar arithmetic before every candidate interaction length. |
| Proposed fix | Add a step-local EM PIL cache keyed by `(material-cuts-couple, model, scaled-energy bin, charge-state class)` with direct storage of lambda and inverse lambda; retain exact recomputation outside the cache tolerance. |
| Expected speedup | 1.2-1.8x inside EM PIL for tracks with repeated material/energy-bin locality; 2-5% wall-clock in EM-dominated benchmarks if cache hit rate is high. |
| Validation | Compare cached vs. vanilla `preStepLambda`, interaction-length-left, mean free path, selected process, and secondary spectra on a material/energy grid; require bit-exact values when using stored table nodes and bounded ULP deltas for inverse-lambda arithmetic. |
| Implementation target | `g4gpu-phase5d-em-pil-lambda-cache`. |
| Citation | Bentley 1975; Intel 2024 cache-locality guidance. |
| Status | OPEN |

### BD-geant4-037  Lambda-shape dispatch serializes every EM cross-section morphology case

| Field | Value |
|-------|-------|
| File | `source/processes/electromagnetic/utils/src/G4VEnergyLossProcess.cc` |
| Lines | 683-768 |
| Hot-path % (profile-measured) | EM lambda calculation: per-line self% `OPEN:` pending perf. |
| Category | 5 — Control flow |
| Current pattern | Snippet: `if(fXSType == fEmIncreasing) ... else if(fXSType == fEmOnePeak) ... else if(fXSType == fEmTwoPeaks) ... else ...` with repeated peak/deep tests. |
| Why slow | The cross-section type is configuration state, not a per-step random variable, yet all shape cases share one branch ladder. The two/three-peak path adds several early returns and data-dependent comparisons. |
| Proposed fix | Specialize lambda evaluators by cross-section type and material-cuts-couple at table-build time; dispatch once to a function pointer or JIT body instead of branching inside every PIL call. |
| Expected speedup | 1.2-1.5x for lambda evaluation; higher for two-peak tables where the current branch ladder is longest. |
| Validation | Exhaustive table sweep over `fEmIncreasing`, `fEmOnePeak`, `fEmTwoPeaks`, and no-integral modes; compare lambda, `mfpKinEnergy`, and downstream step selections with vanilla for fixed seeds. |
| Implementation target | `g4gpu-phase5d-em-lambda-shape-specialization`. |
| Citation | Futamura 1971/1983; Intel 2024. |
| Status | OPEN |

### BD-geant4-038  Lambda table access pointer-chases through physics tables and mutable bin state

| Field | Value |
|-------|-------|
| File | `source/processes/electromagnetic/utils/include/G4VEnergyLossProcess.hh` |
| Lines | 692-703 |
| Hot-path % (profile-measured) | EM lambda table access inside PIL: per-line self% `OPEN:` pending perf. |
| Category | 3 — Data structure |
| Current pattern | Snippet: `((*theLambdaTable)[basedCoupleIndex])->Value(e, idxLambda)` and `LogVectorValue(e, loge)` multiply table output by `fFactor`. |
| Why slow | Every lookup dereferences the table vector, the per-couple physics vector, and mutable cached-bin state. The memory layout is not friendly to vector prefetch or track batching by material-cuts-couple. |
| Proposed fix | Flatten hot lambda tables into a cache-aligned descriptor array keyed by `basedCoupleIndex`, storing vector pointer, type, edge bounds, scale, and last-bin cache in one compact object. |
| Expected speedup | 1.1-1.4x for lambda lookup latency; larger when combined with track batching by material-cuts-couple in Phase 6. |
| Validation | Golden-table tests over all material-cuts-couple indices comparing `Value`/`LogVectorValue` outputs and cached-bin progression; event replay must preserve selected process and step lengths. |
| Implementation target | `g4gpu-phase6-lambda-table-descriptor-soa`. |
| Citation | Stroustrup 2012; Intel 2024 data-layout guidance. |
| Status | OPEN |

### BD-geant4-039  PhysicsVector value lookup mixes cached-bin, bounds, and general-bin paths

| Field | Value |
|-------|-------|
| File | `source/global/management/include/G4PhysicsVector.icc` |
| Lines | 205-229 |
| Hot-path % (profile-measured) | Cross-section table interpolation across PIL: per-line self% `OPEN:` pending perf. |
| Category | 1 — Microarchitecture |
| Current pattern | Snippet: `if (idx + 1 < numberOfNodes && e >= binVector[idx] && e <= binVector[idx+1]) ... else if (e > edgeMin && e < edgeMax) ...`. |
| Why slow | The fast cached-bin path is excellent for monotone tracks, but misses fall through a branch ladder that mixes bounds handling with a generic `GetBin` dispatch. Branch predictability degrades for shower secondaries with scattered energies. |
| Proposed fix | Split bounded hot lookup from out-of-range handling and generate vector-type-specific lookup kernels; prefetch adjacent bins and record cache-miss counters for Phase 5 profile feedback. |
| Expected speedup | 1.2-1.8x for `G4PhysicsVector::Value` on scattered-energy table lookups; event gain tracks how much PIL time is interpolation rather than dispatch. |
| Validation | Exhaustive edge/min/max/bin-boundary tests for linear, log, and free vectors; fixed-seed EM/hadronic benchmark histograms must match vanilla within bit-exact or documented ULP tolerance. |
| Implementation target | `g4gpu-phase5d-physics-vector-hot-lookup`. |
| Citation | Intel 2024; Bentley 1975. |
| Status | OPEN |

### BD-geant4-040  PhysicsVector interpolation pays a division and spline branch per lookup

| Field | Value |
|-------|-------|
| File | `source/global/management/include/G4PhysicsVector.icc` |
| Lines | 125-149 |
| Hot-path % (profile-measured) | Cross-section interpolation inside PIL: per-line self% `OPEN:` pending perf. |
| Category | 4 — Mathematical |
| Current pattern | Snippet: `const G4double b = (e - x1) / dl`, then linear interpolation, then `if (useSpline)` adds spline curvature terms. |
| Why slow | Uniform or preprocessed tables can store inverse bin widths and linear coefficients, while spline-enabled and spline-disabled tables pay a runtime branch in the same hot inline function. |
| Proposed fix | Precompute `inv_dl`, slope, and optional spline coefficients during physics-table build; emit separate linear and spline evaluator objects so non-spline tables have no branch and no division in the hot path. |
| Expected speedup | 1.2-1.7x for table interpolation-heavy PIL sections; potentially larger on architectures where floating division remains high latency. |
| Validation | Table-by-table numerical equivalence tests at bin edges, midpoints, and random energies; require unchanged physics vectors on disk and event-level spectra agreement for EM and hadronic benchmarks. |
| Implementation target | `g4gpu-phase5d-physics-vector-coeff-cache`. |
| Citation | Trefethen 2013; Intel 2024. |
| Status | OPEN |

### BD-geant4-041  Tracking start/end hooks walk all processes for every track

| Field | Value |
|-------|-------|
| File | `source/processes/management/src/G4ProcessManager.cc` |
| Lines | 1163-1180 |
| Hot-path % (profile-measured) | Per-track PIL/process-management boundary: per-line self% `OPEN:` pending allocation/perf trace. |
| Category | 5 — Control flow |
| Current pattern | Snippet: `((*theProcessList)[idx])->StartTracking(aTrack);` and `((*theProcessList)[idx])->EndTracking();` after `GetAttribute(idx)->isActive` checks. |
| Why slow | Many processes have empty or cheap start/end hooks, but every track still pays a full active-process scan and virtual call opportunities before and after stepping. Secondary-heavy showers multiply this overhead. |
| Proposed fix | During process-manager finalization, build compact hook lists only for active processes with non-trivial tracking callbacks, plus a null fast path for particles whose process list has no hooks. |
| Expected speedup | 1.1-1.3x at the per-track lifecycle boundary; most visible in high-multiplicity showers with many short-lived secondaries. |
| Validation | Instrument vanilla and optimized hook calls to verify same process identity/order for particles with start/end side effects; fixed-seed event replay must preserve track status, secondaries, and process state. |
| Implementation target | `g4gpu-phase5d-process-hook-lists`. |
| Citation | Hoelzle, Chambers, and Ungar 1991; Intel 2024. |
| Status | OPEN |

## Geometry navigation hot path

These entries convert the legacy GEO-01--GEO-08 findings and split the
mixed normal/voxel daughter-transform finding so the cumulative Geant4
bottleneck database reaches the 50-entry methodology acceptance threshold.

### BD-geant4-042  Navigator dispatch chooses among geometry backends on every step

| Field | Value |
|-------|-------|
| File | `source/geometry/navigation/src/G4Navigator.cc` |
| Lines | 749-948 |
| Hot-path % (profile-measured) | Geometry navigation family: about 25% aggregate Geant4 CPU per lane-spec basis; per-line self% `OPEN:` pending Phase 5 perf. |
| Category | 5 — Control flow |
| Current pattern | Snippet: `switch( CharacteriseDaughters(motherLogical) )` dispatches to voxel, normal, regular, parameterised, replica, or external navigation paths. |
| Why slow | Daughter characterisation and backend choice are geometry-configuration facts, but every step carries the dispatch ladder plus relocation and exceptional regular-structure handling. Mixed detector geometries amplify branch misprediction. |
| Proposed fix | Attach a compact preclassified navigation-kernel descriptor to each logical volume, with direct function pointers for normal/voxel/regular/parameterised/external cases and a rare relocation slow path. |
| Expected speedup | 1.1-1.4x inside navigator dispatch; event-level gain depends on geometry fraction and how often steps enter volumes with stable daughter type. |
| Validation | Fixed-seed replay of boundary crossings, entered/exited volume identity, safety, exit normals, and stuck-track counters for canonical examples plus NNBAR-like nested volumes. |
| Implementation target | `g4gpu-phase5d-navigator-backend-descriptor`. |
| Citation | Hoelzle, Chambers, and Ungar 1991; Intel 2024. |
| Status | OPEN |

### BD-geant4-043  Normal navigation rebuilds daughter transforms inside the candidate loop

| Field | Value |
|-------|-------|
| File | `source/geometry/navigation/src/G4NormalNavigation.cc` |
| Lines | 63-182 |
| Hot-path % (profile-measured) | Geometry daughter scanning: per-line self% `OPEN:` pending perf. |
| Category | 3 — Data structure |
| Current pattern | Snippet: `G4AffineTransform sampleTf(samplePhysical->GetRotation(), samplePhysical->GetTranslation())` then `sampleTf.Invert()` for each daughter candidate. |
| Why slow | Rotation/translation transforms for static daughter placements are recomputed and inverted while scanning candidates. That repeats matrix work and scatters loads before every `DistanceToIn` test. |
| Proposed fix | Precompute per-daughter inverse transforms in a cache-aligned array owned by the logical volume/navigation descriptor; update only when geometry is modified. |
| Expected speedup | 1.2-1.8x for normal-navigation daughter scans in high-daughter volumes; broader event gain on detector regions without voxel headers. |
| Validation | Compare transformed local points/directions, selected daughter, safety, and step length against vanilla for random rays in each logical volume; require bit-exact transforms for static placements. |
| Implementation target | `g4gpu-phase5d-precomputed-daughter-transforms`. |
| Citation | Stroustrup 2012; Intel 2024. |
| Status | OPEN |

### BD-geant4-044  Voxel navigation repeats transform construction for voxel-contained candidates

| Field | Value |
|-------|-------|
| File | `source/geometry/navigation/src/G4VoxelNavigation.cc` |
| Lines | 87-206 |
| Hot-path % (profile-measured) | Voxel candidate scanning: per-line self% `OPEN:` pending perf. |
| Category | 3 — Data structure |
| Current pattern | Snippet: `fBList.BlockVolume(sampleNo)` followed by `G4AffineTransform sampleTf(...)`, `sampleTf.Invert()`, and solid `DistanceToIn` calls. |
| Why slow | Voxelization reduces the candidate set, but the remaining per-candidate work still allocates/register-spills transform temporaries and repeats inverse transforms. The blocked-volume list is a side structure touched on every candidate. |
| Proposed fix | Store voxel node contents as indices into precomputed daughter-transform and solid descriptor arrays, with a compact bitset for per-step blocking instead of a growable list. |
| Expected speedup | 1.2-1.7x inside voxel candidate scans; expected to compose with BD-geant4-045 if traversal reaches fewer voxels. |
| Validation | Ray replay through voxelized volumes comparing blocked candidates, selected daughter, safety, and local intersection coordinates; include exited-daughter blocking regressions. |
| Implementation target | `g4gpu-phase5d-voxel-candidate-descriptors`. |
| Citation | Stroustrup 2012; Intel 2024. |
| Status | OPEN |

### BD-geant4-045  Voxel-boundary marching recomputes target points and divides at each depth

| Field | Value |
|-------|-------|
| File | `source/geometry/navigation/src/G4VoxelNavigation.cc` |
| Lines | 473-611 |
| Hot-path % (profile-measured) | Voxel traversal: per-line self% `OPEN:` pending perf. |
| Category | 2 — Algorithm |
| Current pattern | Snippet: `targetPoint = localPoint+localDirection*currentDistance`, repeated `newDistance = (...)/localDirection(workHeaderAxis)`, and a descent loop over proxy headers. |
| Why slow | The traversal behaves like a scalar 3D-DDA over hierarchical slices but recalculates points, widths, divisions, and header metadata at each refinement depth. Division and pointer chasing dominate when tracks cross many voxel boundaries. |
| Proposed fix | Convert smart-voxel traversal to an explicit DDA state with precomputed reciprocal directions and cached header stride descriptors; longer term, benchmark SAH-BVH traversal for complex detector regions. |
| Expected speedup | 1.3-2.2x for voxel-boundary marches; larger in finely voxelized calorimeter or medical-physics geometries. |
| Validation | Exhaustive ray tests through synthetic voxel grids and canonical detector volumes comparing next-voxel identity, boundary distance, and leaving-mother decisions to vanilla. |
| Implementation target | `g4gpu-phase5d-voxel-dda-state`. |
| Citation | MacDonald and Booth 1990; Wald et al. 2007. |
| Status | OPEN |

### BD-geant4-046  Voxel safety recursively scans neighboring slices with scalar distance updates

| Field | Value |
|-------|-------|
| File | `source/geometry/navigation/src/G4VoxelSafety.cc` |
| Lines | 210-549 |
| Hot-path % (profile-measured) | Geometry safety computation: per-line self% `OPEN:` pending perf. |
| Category | 2 — Algorithm |
| Current pattern | Snippet: `SafetyForVoxelHeader(...)` recurses on child headers, updates `nextUp`/`nextDown`, and repeats distance comparisons until the interest radius is exhausted. |
| Why slow | Safety scans can revisit neighboring slice metadata recursively even when an acceleration structure could bound many nodes at once. The loop alternates pointer chasing with scalar distance arithmetic and branch-heavy up/down decisions. |
| Proposed fix | Add a bounding-volume hierarchy safety query that prunes whole node groups by lower-bound distance; keep smart-voxel recursion as the exact fallback and validation oracle. |
| Expected speedup | 1.3-2.5x for safety-heavy geometries, especially nested calorimeter or therapy-plan volumes with many nearby daughters. |
| Validation | Compare safety values over random points, boundary-near points, and worst-case overlap geometries; require conservative equality or smaller-safe-step behavior with no missed boundaries. |
| Implementation target | `g4gpu-phase8b-bvh-safety-query`. |
| Citation | MacDonald and Booth 1990; Wald et al. 2007. |
| Status | OPEN |

### BD-geant4-047  Smart-voxel build uses uniform slicing rather than traversal-cost optimization

| Field | Value |
|-------|-------|
| File | `source/geometry/management/src/G4SmartVoxelHeader.cc` |
| Lines | 741-1046 |
| Hot-path % (profile-measured) | Geometry setup affects all later navigation; runtime self% `OPEN:` pending build-vs-run amortization study. |
| Category | 2 — Algorithm |
| Current pattern | Snippet: `noNodesExactD = ((motherMaxExtent-motherMinExtent)*2.0/minWidth)+1.0`, then every candidate extent is inserted into uniform nodes. |
| Why slow | Uniform slice count follows daughter width and smartless heuristics rather than observed ray distribution or surface-area cost, so runtime traversal may see too many candidates in irregular geometries. |
| Proposed fix | Offer an SAH-BVH or SAH-guided smart-voxel builder that minimizes expected traversal cost, with build-time budget controls and fallback to existing smartless behavior. |
| Expected speedup | 1.2-2.0x in geometry navigation for irregular detector/medical geometries; setup cost amortizes over long runs. |
| Validation | Compare built acceleration structure coverage, daughter identity, and boundary distances for canonical geometries; benchmark build time and navigation time separately before enabling by default. |
| Implementation target | `g4gpu-phase8b-sah-geometry-builder`. |
| Citation | MacDonald and Booth 1990; Wald et al. 2007. |
| Status | OPEN |

### BD-geant4-048  Box DistanceToIn uses branchy scalar slab tests

| Field | Value |
|-------|-------|
| File | `source/geometry/solids/CSG/src/G4Box.cc` |
| Lines | 320-347 |
| Hot-path % (profile-measured) | CSG surface intersections within geometry navigation: per-line self% `OPEN:` pending perf. |
| Category | 1 — Microarchitecture |
| Current pattern | Snippet: `if ((std::abs(p.x()) - fDx) >= -delta && p.x()*v.x() >= 0) return kInfinity;` followed by axis-wise reciprocal and min/max slab calculations. |
| Why slow | Each ray-box query pays three early branches, three conditional reciprocals, and scalar min/max operations. Vector batches or branchless scalar code can evaluate slabs more predictably. |
| Proposed fix | Add a branchless ray-box evaluator using precomputed inverse direction and sign masks, with the existing tolerant edge handling retained for boundary cases. |
| Expected speedup | 1.2-1.8x for box intersection hot spots; common in calorimeter, shielding, and voxel-like geometries. |
| Validation | Exhaustive tolerance-surface tests plus randomized rays comparing distances to vanilla, including zero direction components, surface-touching rays, and away-from-surface early exits. |
| Implementation target | `g4gpu-phase5d-branchless-box-distance`. |
| Citation | Williams et al. 2005; Intel 2024. |
| Status | OPEN |

### BD-geant4-049  Tube DistanceToIn branch ladder duplicates z, radius, and phi cases

| Field | Value |
|-------|-------|
| File | `source/geometry/solids/CSG/src/G4Tubs.cc` |
| Lines | 708-1055 |
| Hot-path % (profile-measured) | CSG tube intersections within geometry navigation: per-line self% `OPEN:` pending perf. |
| Category | 5 — Control flow |
| Current pattern | Snippet: `if (std::fabs(p.z()) >= tolIDz)`, radial quadratic tests, optional phi checks, and recursive long-distance handling. |
| Why slow | Common full-tube and no-inner-radius cases still pass through a large routine with many branches for phi sections, inner radii, z caps, tangent cases, and long-distance precision corrections. |
| Proposed fix | Split specialized kernels for full tube/no-inner-radius, hollow tube, and phi-section cases; use direct dispatch from solid construction metadata and keep the generic routine as fallback. |
| Expected speedup | 1.2-1.6x for tube-heavy beamline and detector-support geometries; smaller in box-dominated examples. |
| Validation | Geometry unit tests over full, hollow, and phi-cut tubes comparing distances and normals at tolerance boundaries; event replay checks volume entry/exit identity. |
| Implementation target | `g4gpu-phase5d-tubs-specialized-distance`. |
| Citation | Futamura 1971/1983; Intel 2024. |
| Status | OPEN |

### BD-geant4-050  Touchable history access uses lazy thread-local scratch objects

| Field | Value |
|-------|-------|
| File | `source/geometry/management/src/G4TouchableHistory.cc` |
| Lines | 46-92 |
| Hot-path % (profile-measured) | Touchable transform access in navigation/hits: per-line self% `OPEN:` pending perf. |
| Category | 6 — Memory allocation |
| Current pattern | Snippet: `static G4ThreadLocal G4ThreeVector* ctrans = nullptr` and `static G4ThreadLocal G4RotationMatrix* rotM = nullptr` lazily allocate scratch objects. |
| Why slow | First access allocates thread-local heap objects, and later accesses return mutable scratch references that force defensive copies by callers. The pattern also complicates vectorized or batch navigation. |
| Proposed fix | Store fixed scratch members in the touchable/navigation context or return value types for nonzero-depth transforms under an ABI-reviewed overload, eliminating lazy heap allocation and mutable TLS aliasing. |
| Expected speedup | Small direct gain after warmup, but removes allocator samples and unlocks cleaner batch/touchable data layouts for Phase 6. |
| Validation | ABI-compatibility review plus tests for translation/rotation values at every history depth; threaded replay must show no cross-thread aliasing and identical hit touchables. |
| Implementation target | `g4gpu-phase6-touchable-context-scratch`. |
| Citation | Stroustrup 2012; Herlihy and Shavit 2012. |
| Status | OPEN |

## Next implementations after structured PIL / geometry conversion

1. `g4gpu-phase5d-jit-poststep-gpil` from BD-geant4-032/035: highest PIL
   dispatch leverage with bit-exact fallback semantics.
2. `g4gpu-phase5d-physics-vector-coeff-cache` from BD-geant4-039/040: local
   source patch, easy table-level validation, and cross-code reuse in OpenMC.
3. `g4gpu-phase8b-sah-geometry-builder` from BD-geant4-046/047: highest
   algorithmic geometry upside once Phase 5 perf confirms smart-voxel cost.
4. `g4gpu-phase5d-voxel-dda-state` from BD-geant4-045: compact navigation
   patch with exact distance validation.
5. `g4gpu-phase5d-branchless-box-distance` from BD-geant4-048: upstreamable
   microarchitecture patch for common CSG shapes.
6. `g4gpu-phase5d-em-lambda-shape-specialization` from BD-geant4-036/037/038:
   EM-heavy benchmark candidate once Phase 5 perf confirms lambda self-time.
7. `g4gpu-phase5d-alongstep-policy-table` from BD-geant4-034: validates the
   same generated-dispatch machinery needed for PostStep GPIL.
8. `g4gpu-phase5d-precomputed-daughter-transforms` from BD-geant4-043/044:
   low-risk geometry data-layout win.
9. `g4gpu-phase5d-tubs-specialized-distance` from BD-geant4-049: useful for
   beamline and support geometries after box-distance validation lands.
10. `g4gpu-phase5d-process-hook-lists` from BD-geant4-041: small upstreamable
    lifecycle optimization with low physics risk.

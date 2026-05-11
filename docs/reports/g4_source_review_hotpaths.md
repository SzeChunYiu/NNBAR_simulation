# Geant4 source review — hot paths

Status: partial, compact-safe iteration 1 of 5. This iteration covers hot path 1, Physics Interaction Length (PIL).

## Source provenance and lane notes

- LUNARC socket was active before SSH. `hibeam_env/bin/geant4-config --version --prefix` reported Geant4 `11.2.2` at `/projects/hep/fs10/shared/nnbar/billy/packages/hibeam_env`.
- The LUNARC install exposes headers, libraries, examples, and EasyBuild metadata, but no extracted `source/` tree for the Geant4 implementation files. To avoid editing or building anything on LUNARC, this review used the official upstream Geant4 GitLab archive tag `v11.2.2` downloaded read-only to `/tmp/geant4-v11.2.2`.
- Spec correction: `source/processes/management/src/G4SteppingManager2.cc` is not present in tag `v11.2.2`; the stepping implementation is `source/tracking/src/G4SteppingManager.cc`.
- Isolation policy check: this report is documentation-only. No files under `NNBAR_Detector/`, `nnbar_reconstruction/`, `scripts/`, `lunarc/`, `slurm/`, or `macro/` were modified.

## 1. PIL — Physics Interaction Length

### PIL-01 — `source/tracking/src/G4SteppingManager.cc:449-512` — PostStep GPIL virtual dispatch cascade

**Current snippet**: `fCurrentProcess->PostStepGPIL(...);`

**What is slow**: `G4SteppingManager::DefinePhysicalStepLength` walks the PostStep GPIL vector once per step. Each active process reaches a virtual GPIL implementation through the wrapper in `G4VProcess`, then updates a condition enum and selected-process vector. For a fixed particle/material/physics-list configuration, most candidate processes and force-state branches are stable across many steps.

**Optimization**: Generate a particle-specialized PostStep GPIL loop at run startup (LLVM ORC or Cling) that hard-codes the active process order, removes null checks for permanently active processes, inlines monomorphic GPIL targets where the concrete type is known, and emits a small fallback guard if a process is dynamically deactivated.

**Expected speedup**: 1.3--2.0x on PostStep GPIL dispatch overhead; roughly 5--10% event CPU on PIL-heavy profiles if physics-vector interpolation remains the dominant residual cost.

**Validation strategy**: Fixed-seed bit-exact comparison against vanilla Geant4 for step length, selected process, interaction-length counters, secondary counts, and final event summaries. The specialized loop must be disabled automatically if the process manager changes after initialization.

**Proposed task**: `g4gpu-phase5d-jit-poststep-gpil`

**Standard technique**: partial evaluation and polymorphic inline-cache driven devirtualization.

**Reference**: Futamura 1971/1983; Hölzle, Chambers & Ungar 1991.

### PIL-02 — `source/tracking/src/G4SteppingManager.cc:449-512` — Force-condition switch in the inner step loop

**Current snippet**: `switch (fCondition) { ... }`

**What is slow**: The normal case is usually `NotForced`, but every step still executes a multi-way force-condition switch, stores into `fSelectedPostStepDoItVector`, and carries an early-return path for `ExclusivelyForced`.

**Optimization**: Split the loop into a common no-forcing fast path plus a rare forcing slow path. The fast path only computes the minimum physical step and triggering process; the slow path is entered when any process reports a non-default force condition.

**Expected speedup**: 1.05--1.15x on PIL loop wall time for ordinary transport, mostly from fewer unpredictable branches and fewer selected-vector writes.

**Validation strategy**: Instrument the original and split loops to log `(process, condition, selected flag, PhysicalStep)` for fixed seeds. Require byte-for-byte identical logs, including forced/strongly-forced test cases.

**Proposed task**: `g4gpu-phase5d-gpil-force-fastpath`

**Standard technique**: trace splitting / hot-cold path separation.

**Reference**: Hölzle, Chambers & Ungar 1991.

### PIL-03 — `source/tracking/src/G4SteppingManager.cc:449-568` — AlongStep GPIL virtual calls and transportation special case

**Current snippet**: `fCurrentProcess->AlongStepGPIL(...);`

**What is slow**: The AlongStep loop repeats the same virtual dispatch pattern as PostStep GPIL, then branches on `CandidateForSelection`, process type, and the convention that transportation is last in the vector.

**Optimization**: Emit a specialized AlongStep loop for each particle class. Keep transportation as an explicit final call site, not a branch tested on every earlier process. Represent candidate-for-selection as a compile-time trait for known process types where possible.

**Expected speedup**: 1.2--1.6x on AlongStep GPIL dispatch overhead; smaller total-event effect than PostStep but still high leverage for charged-particle tracks.

**Validation strategy**: Step-level differential test comparing the proposed step, safety, GPIL selection flag, and process-defined-step pointer against vanilla for charged and neutral benchmark tracks.

**Proposed task**: `g4gpu-phase5d-jit-alongstep-gpil`

**Standard technique**: partial evaluation and branch hoisting.

**Reference**: Futamura 1971/1983; Aho, Sethi & Ullman 1986.

### PIL-04 — `source/processes/management/include/G4VProcess.hh:464-489` — Thin GPIL wrappers multiply through virtual calls

**Current snippet**: `return thePILfactor * PostStepGetPhysicalInteractionLength(...);`

**What is slow**: `PostStepGPIL`, `AtRestGPIL`, and `AlongStepGPIL` are inline wrappers, but the hot work remains a virtual call. `thePILfactor` is normally stable, yet multiplication is still fused with every call path.

**Optimization**: In the JIT-specialized process loop, resolve the wrapper target and hoist constant `thePILfactor` values. For `thePILfactor == 1`, emit a no-multiply path. Preserve a guard for user-modified factors.

**Expected speedup**: 1--3% of PIL CPU by itself, but it compounds with PIL-01/PIL-03 because it removes another operation from every process candidate.

**Validation strategy**: Add a conformance test that toggles non-unit PIL factors and verifies vanilla and specialized step lengths agree exactly, then run the normal unit-factor benchmark with the guard enabled.

**Proposed task**: `g4gpu-phase5d-pilfactor-specialization`

**Standard technique**: constant propagation and strength reduction.

**Reference**: Aho, Sethi & Ullman 1986.

### PIL-05 — `source/processes/electromagnetic/utils/src/G4VEnergyLossProcess.cc:592-664` — Per-step EM lambda setup and interaction-length arithmetic

**Current snippet**: `ComputeLambdaForScaledEnergy(...);`

**What is slow**: `PostStepGetPhysicalInteractionLength` performs material/model selection, bias checks, lambda computation, random-log sampling, reciprocal formation, and previous-step subtraction in one hot routine. Several inputs are constant for long runs of same-material same-particle steps.

**Optimization**: Cache the `(particle, material-cuts-couple, model, bias-region)` tuple in a compact per-track state block. Use a guarded fast path when the tuple is unchanged, and precompute reciprocal lambda where physics tables are unchanged.

**Expected speedup**: 1.1--1.4x inside EM PostStep GPIL, depending on material boundary frequency and how often model selection changes.

**Validation strategy**: Compare per-step `preStepLambda`, `currentInteractionLength`, and `theNumberOfInteractionLengthLeft` before/after. Run boundary-crossing tracks to ensure the guard invalidates at material changes.

**Proposed task**: `g4gpu-phase5d-em-gpil-state-cache`

**Standard technique**: memoization with guard invalidation and common-subexpression elimination.

**Reference**: Aho, Sethi & Ullman 1986.

### PIL-06 — `source/processes/electromagnetic/utils/src/G4VEnergyLossProcess.cc:684-768` — Branch ladder over cross-section shape types

**Current snippet**: `if (fXSType == ...) { ... } else if (...) { ... }`

**What is slow**: `ComputeLambdaForScaledEnergy` branches through increasing, one-peak, two-peak, and fallback cross-section shapes. The shape type and peak arrays are process/model properties, so the branch ladder is largely invariant for a concrete process.

**Optimization**: Split this routine into per-`fXSType` function objects or generated specializations. For the multi-peak case, prepack peak/deep values in a small contiguous struct loaded once per material couple.

**Expected speedup**: 1.1--1.3x for EM lambda computation; larger on branch-mispredict-heavy tracks with mixed materials.

**Validation strategy**: For each `fXSType`, sweep energy across peak/deep boundaries and require identical `preStepLambda` and `mfpKinEnergy` transitions to the reference implementation.

**Proposed task**: `g4gpu-phase5d-em-lambda-shape-specialization`

**Standard technique**: function multiversioning and data-oriented layout.

**Reference**: Aho, Sethi & Ullman 1986; Khuong & Morin 2015.

### PIL-07 — `source/processes/electromagnetic/utils/include/G4VEnergyLossProcess.hh:692-703` — Lambda table pointer chasing

**Current snippet**: `(*theLambdaTable)[basedCoupleIndex])->Value(...)`

**What is slow**: A lambda lookup dereferences a table pointer, indexes by material-cuts couple, then calls into a `G4PhysicsVector`. That adds dependent loads before the interpolation even begins.

**Optimization**: During physics-table finalization, flatten lambda vectors for the active process into a contiguous per-couple descriptor array containing data pointers, bin metadata, and interpolation constants. Preserve the existing table as the source of truth and generate the flat view as a read-only cache.

**Expected speedup**: 1.05--1.25x on lambda lookup latency, strongest when table data misses L1/L2.

**Validation strategy**: For every material-cuts couple, sample a deterministic energy grid and assert that flat-view lookup equals the original `G4PhysicsVector` lookup bit-for-bit.

**Proposed task**: `g4gpu-phase5d-flat-lambda-view`

**Standard technique**: cache-aware structure splitting / structure-of-arrays.

**Reference**: Khuong & Morin 2015.

### PIL-08 — `source/global/management/include/G4PhysicsVector.icc:205-248` — Cached-bin lookup falls back to general bin search

**Current snippet**: `idx = GetBin(e);`

**What is slow**: `G4PhysicsVector::Value(e, idx)` has a good last-bin fast path, but out-of-bin energies still branch through boundary checks and the general `GetBin` dispatcher. In showering events, energy changes can be monotone but not always within the previous bin.

**Optimization**: Add a monotone-neighbor fast path that checks `idx+1` and `idx-1` before the full dispatcher, then evaluate an Eytzinger or implicit-B-tree layout for non-local jumps.

**Expected speedup**: 1.1--1.5x for physics-vector lookup on smoothly changing energies; lower if energy jumps are random.

**Validation strategy**: Replay recorded energy sequences from vanilla Geant4 and compare selected bin index and interpolated value for every lookup. Include adversarial boundary energies to protect off-by-one behavior.

**Proposed task**: `g4gpu-phase5d-physicsvector-neighbor-bin`

**Standard technique**: branch-predicted locality cache plus cache-optimized search layout.

**Reference**: Khuong & Morin 2015.

### PIL-09 — `source/global/management/include/G4PhysicsVector.icc:161-200` — Binary/log/free-vector bin selection

**Current snippet**: `std::lower_bound(...);`

**What is slow**: `G4PhysicsVector::BinaryBin` uses comparison-based lower bound for free vectors. `LogBin` seeds from a scale table but can still linearly scan forward. Both paths introduce branchy, data-dependent control flow before interpolation.

**Optimization**: For static physics tables, generate a per-table direct bin mapper: uniform/log vectors use arithmetic mapping, while irregular free vectors use an Eytzinger layout or a minimal perfect hash over quantized bin intervals when table ranges are fixed.

**Expected speedup**: 1.2--2.0x on irregular-vector bin selection; direct arithmetic paths should remain unchanged for uniform/log vectors.

**Validation strategy**: Exhaustively test every bin interval boundary plus random in-bin values. The optimized mapper must return the same bin as `BinaryBin`/`LogBin` for all tested energies.

**Proposed task**: `g4gpu-phase5d-physicsvector-binmap`

**Standard technique**: cache-aware search layout and static perfect hashing.

**Reference**: Khuong & Morin 2015; Fredman, Komlós & Szemerédi 1984.

### PIL-10 — `source/global/management/include/G4PhysicsVector.icc:125-149` — Interpolation divides and spline branch

**Current snippet**: `const G4double b = (e - x1) / dl;`

**What is slow**: Each interpolation recomputes bin width, slope, and a division. It also carries a runtime `useSpline` branch, even though spline usage is a table property.

**Optimization**: Precompute per-bin inverse widths and slopes for linear tables; split spline and non-spline vectors into separate call paths. On CPU fallback, vectorize batches of lookup requests with the same vector type.

**Expected speedup**: 1.15--1.6x on interpolation arithmetic when lookup batches hit the same table; total speedup depends on how much time is spent in bin selection.

**Validation strategy**: Compare exact floating-point output with strict operation-order mode first; if FMA/vectorization changes rounding, gate the optimization behind a documented tolerance and KS/bitwise policy.

**Proposed task**: `g4gpu-phase5d-physicsvector-interp-precompute`

**Standard technique**: strength reduction and function multiversioning.

**Reference**: Aho, Sethi & Ullman 1986.

### PIL-11 — `source/processes/electromagnetic/utils/src/G4VEnergyLossProcess.cc:973-1081` — Secondary-track allocation inside EM PostStepDoIt

**Current snippet**: `G4Track* t = new G4Track(...);`

**What is slow**: While this is the DoIt side rather than GPIL, it is in the same EM process file and is reached after a selected PIL interaction. Every secondary allocation uses `new G4Track`, then the stepping manager later may delete zero-energy tracks.

**Optimization**: Use a per-event or per-thread track arena/pool for secondaries, with explicit lifetime handoff to the stack manager. Keep vanilla allocation behind a debug flag until the ownership model is fully audited.

**Expected speedup**: 1.1--1.4x for secondary-heavy EM interactions; negligible for tracks with no secondaries.

**Validation strategy**: Memory-safety tests with AddressSanitizer in a CPU build, plus fixed-seed equality of secondary kinematics, creator model IDs, weights, and stack counts.

**Proposed task**: `g4gpu-phase6-secondary-track-pool`

**Standard technique**: object pooling / arena allocation.

**Reference**: Wilson, Johnstone, Neely & Boles 1995.

### PIL-12 — `source/processes/management/src/G4ProcessManager.cc:1163-1180` — Per-track Start/EndTracking loop over all active processes

**Current snippet**: `((*theProcessList)[idx])->StartTracking(aTrack);`

**What is slow**: Each new track loops over the full process list and dispatches virtual start/end hooks for active processes. In high-secondary events, this setup/teardown cost is paid many times before any step loop runs.

**Optimization**: Build a compact active hook list containing only processes that override non-trivial `StartTracking`/`EndTracking`, then dispatch that list. In a JIT mode, inline known hooks and omit default no-op hooks.

**Expected speedup**: 1.05--1.2x on high-multiplicity events with many short tracks; modest effect on long tracks.

**Validation strategy**: Hook-count instrumentation must show identical calls for every process that overrides the hook. Run fixed-seed events with many secondaries and compare event output bit-for-bit.

**Proposed task**: `g4gpu-phase5d-active-tracking-hooks`

**Standard technique**: dead-code elimination through override detection and partial evaluation.

**Reference**: Futamura 1971/1983; Hölzle, Chambers & Ungar 1991.

## Next implementations from PIL review

1. `g4gpu-phase5d-jit-poststep-gpil` — highest dispatch win with bit-exact validation.
2. `g4gpu-phase5d-physicsvector-binmap` — attacks the shared cross-section lookup inner loop.
3. `g4gpu-phase5d-physicsvector-interp-precompute` — simple CPU fallback win if rounding policy is settled.
4. `g4gpu-phase5d-em-gpil-state-cache` — high EM-specific leverage with clear guard conditions.
5. `g4gpu-phase5d-jit-alongstep-gpil` — mirrors PostStep specialization for charged tracks.
6. `g4gpu-phase5d-flat-lambda-view` — low-risk data-layout cache for table lookup.
7. `g4gpu-phase5d-em-lambda-shape-specialization` — removes invariant branch ladders.
8. `g4gpu-phase5d-gpil-force-fastpath` — small but safe hot/cold branch split.
9. `g4gpu-phase5d-active-tracking-hooks` — helps short-track/high-secondary events.
10. `g4gpu-phase6-secondary-track-pool` — larger ownership audit, but important for DoIt-heavy showers.

## References

- Aho, Sethi & Ullman, *Compilers: Principles, Techniques, and Tools*, 1986 — constant propagation, common-subexpression elimination, and strength reduction.
- Fredman, Komlós & Szemerédi, "Storing a Sparse Table with O(1) Worst Case Access Time", *Journal of the ACM*, 1984 — static perfect hashing.
- Futamura, "Partial Evaluation of Computation Process — An Approach to a Compiler-Compiler", 1971 Japanese version / 1983 English publication — partial evaluation.
- Hölzle, Chambers & Ungar, "Optimizing Dynamically-Typed Object-Oriented Languages With Polymorphic Inline Caches", ECOOP 1991 — inline caches and devirtualization using runtime type feedback.
- Khuong & Morin, "Array Layouts for Comparison-Based Searching", 2015 — Eytzinger/implicit-B-tree search layouts and branch-free search.
- Wilson, Johnstone, Neely & Boles, "Dynamic Storage Allocation: A Survey and Critical Review", IWMM 1995 — allocation cost model and pool/arena design tradeoffs.

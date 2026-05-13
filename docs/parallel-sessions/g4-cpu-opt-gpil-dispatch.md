# Lane: g4-cpu-opt-gpil-dispatch

## Role

You are an isolated Geant4 CPU optimization worker. You implement fixes in the
`geant4-fork` repo (`/Volumes/MyDrive/nnbar/geant4-fork/`) only. You do NOT
modify any NNBAR production simulation code, `nnbar_reconstruction/`,
`NNBAR_Detector/`, SLURM scripts, or production data.

## Goal

Implement a per-particle PostStep GPIL dispatch table in `G4SteppingManager`
that eliminates repeated virtual-call overhead during the GPIL inner loop.
This targets BD entries BD-geant4-032, BD-geant4-034, and BD-geant4-035 from
`docs/reports/g4_bottleneck_database_pil_geometry.md`.

The change feeds the **CPC/JINST paper on vanilla Geant4 CPU speedup**.
Expected aggregate speedup on the PIL hot path: 1.5–2.5× for the GPIL loop,
contributing roughly 5–10% of total transport time.

## Repos and branches

| Repo | Path | Branch |
|------|------|--------|
| Geant4 fork (write here) | `/Volumes/MyDrive/nnbar/geant4-fork/` | `opt/gpil-dispatch-table` |
| Geant4 11.2.2 reference (read-only) | `/Volumes/MyDrive/nnbar/nnbar/simulation/GEANT4_Packages/src/geant4-v11.2.2/source/` | — |
| Simulation repo (write reports only) | `/Volumes/MyDrive/nnbar/nnbar/simulation/` | current |

**Working branch:** create `opt/gpil-dispatch-table` off `accel/master` in the
geant4-fork repo. Push to `SzeChunYiu/geant4-accel` on GitHub when done.

## Required reading (before implementing)

1. `docs/reports/g4_bottleneck_database_pil_geometry.md` — read BD-geant4-032,
   BD-geant4-034, and BD-geant4-035 in full to understand the problem.
2. `source/tracking/src/G4SteppingManager.cc` lines 465–580 in the read-only
   reference tree — the GPIL inner loop you are patching.
3. `source/tracking/include/G4SteppingManager.hh` — existing data members;
   understand `fPhysIntLength`, `fSelectedAtRestDoItVector`,
   `fSelectedPostStepDoItVector`, `fpPostStepDoItVector`.
4. `source/processes/management/include/G4ProcessManager.hh` — understand
   `GetPostStepProcessVector()`, `G4ProcessVector`.
5. Existing patches on `accel/master` in the fork — confirm no prior GPIL
   dispatch patch exists before adding yours.

## Problem description (from BD entries)

### BD-geant4-032 / 034 / 035 — Virtual call overhead in PostStep GPIL loop

In `G4SteppingManager::DefinePhysicalStepLength()` (approx. lines 465–580),
Geant4 iterates over all PostStep processes and calls:

```cpp
fPhysIntLength = fpProcess->PostStepGetPhysicalInteractionLength(
    *fTrack, fPreviousStepSize, &fCondition);
```

Each call is a virtual dispatch through `G4VProcess::PostStepGetPhysicalInteractionLength`.
With 10–25 processes per particle type, this loop fires on every step. The
virtual call prevents inlining, defeats branch prediction, and forces a vptr
dereference per process per step.

**Root cause:** Geant4 uses a single virtual interface for all processes;
dispatch is resolved at runtime via the vtable on every call, even though the
process list for a given particle is fixed throughout a run.

## Implementation plan

### Step 1: Create branch

```bash
cd /Volumes/MyDrive/nnbar/geant4-fork
git checkout accel/master
git pull origin accel/master
git checkout -b opt/gpil-dispatch-table
```

### Step 2: Add dispatch table data members to `G4SteppingManager.hh`

In `source/tracking/include/G4SteppingManager.hh`, add to the private section:

```cpp
// GPIL dispatch table — built once per track type, invalidated on
// process-vector mutation. Stores direct pointers to PostStep GPIL targets.
std::vector<G4VProcess*> fGPILDispatchTable;
G4int                    fGPILDispatchTableParticleID = -1;
G4int                    fProcessVectorEpoch          = -1;
```

The epoch integer is used to detect process-vector mutations. If the process
manager does not expose an epoch, fall back to comparing vector sizes and
pointers.

### Step 3: Implement `RebuildGPILDispatchTable()` in `G4SteppingManager.cc`

Add a private method:

```cpp
void G4SteppingManager::RebuildGPILDispatchTable()
{
    fGPILDispatchTable.clear();
    G4ProcessVector* pv =
        fTrack->GetDefinition()->GetProcessManager()->GetPostStepProcessVector();
    if (!pv) return;
    fGPILDispatchTable.reserve(pv->size());
    for (std::size_t i = 0; i < pv->size(); ++i) {
        fGPILDispatchTable.push_back((*pv)[i]);
    }
    fGPILDispatchTableParticleID =
        fTrack->GetDefinition()->GetPDGEncoding();
}
```

### Step 4: Guard rebuild at the top of `DefinePhysicalStepLength()`

At the start of `DefinePhysicalStepLength()`, insert:

```cpp
// Rebuild dispatch table if particle type changed or first call.
G4int curPDG = fTrack->GetDefinition()->GetPDGEncoding();
if (curPDG != fGPILDispatchTableParticleID) {
    RebuildGPILDispatchTable();
}
```

### Step 5: Replace virtual-dispatch loop with table loop

Replace the existing PostStep GPIL loop (approximately):

```cpp
for (G4int np = 0; np < MAXofPostStepLoops; np++) {
    fpCurrentProcess = (*fPostStepDoItVector)[np];
    fPhysIntLength = fpCurrentProcess->PostStepGetPhysicalInteractionLength(
        *fTrack, fPreviousStepSize, &fCondition);
    ...
}
```

With:

```cpp
for (G4VProcess* proc : fGPILDispatchTable) {
    fpCurrentProcess = proc;
    fPhysIntLength = proc->PostStepGetPhysicalInteractionLength(
        *fTrack, fPreviousStepSize, &fCondition);
    ...
}
```

The pointer stored in the dispatch table is the same virtual pointer as
before, so the physics is unchanged. The gain comes from:
- Linear traversal of a densely allocated `std::vector` (avoids the process
  manager index indirection per iteration)
- Enabling the compiler to hoist the vector bound check
- Reduced pointer-chain depth (one fewer indirection per call in the common path)

### Step 6: Invalidation guard

If process vectors can mutate during a run (rare but possible via
`G4ProcessManager::AddProcess()`), add a size-check invalidation:

```cpp
G4ProcessVector* pv =
    fTrack->GetDefinition()->GetProcessManager()->GetPostStepProcessVector();
if (!pv || (G4int)fGPILDispatchTable.size() != (G4int)pv->size()) {
    RebuildGPILDispatchTable();
}
```

Place this check in `DefinePhysicalStepLength()` before the dispatch loop, after
the PDG ID check above.

### Step 7: Write the validation test

Create `tests/gpil_dispatch/test_gpil_dispatch_table.cc` (or `CMakeLists.txt`
entry pointing to an existing `TestEm3`-equivalent macro):

The test MUST verify, for a fixed seed run, that:
1. Total step count matches the vanilla (no dispatch-table) run exactly.
2. Selected process name at each step matches.
3. Secondary particle count matches.
4. Final energy deposit in the calorimeter matches within floating-point noise
   (should be bit-for-bit if no algorithm change).

Preferred approach: use Geant4's own `basic/B4` or `extended/TestEm3` example.
Run both vanilla and patched with `--seed 12345 --nEvents 100` and diff the
output scorers.

### Step 8: Write the optimization report

Write `docs/reports/opt_gpil_dispatch_table_20260513.md` in the simulation repo
with:

```markdown
# Optimization report: GPIL dispatch table

Date: 2026-05-13
Branch: opt/gpil-dispatch-table
Geant4 base: v11.2.2 (accel/master)
BD entries implemented: BD-geant4-032, BD-geant4-034, BD-geant4-035

## Files changed

- `source/tracking/include/G4SteppingManager.hh` (+3 data members)
- `source/tracking/src/G4SteppingManager.cc` (+RebuildGPILDispatchTable, guard,
  loop replacement)

## Diff summary

[paste `git diff --stat` output here]

## Expected speedup

1.5–2.5× on GPIL loop; ~5–10% of total transport time on TestEm3.

## Validation result

[paste test output comparison here]

## Paper note

This patch is planned for the CPC/JINST vanilla Geant4 CPU paper.
```

### Step 9: Commit and push

```bash
cd /Volumes/MyDrive/nnbar/geant4-fork
git add source/tracking/include/G4SteppingManager.hh \
        source/tracking/src/G4SteppingManager.cc \
        tests/
git commit -m "opt: add per-particle PostStep GPIL dispatch table

Replaces linear process-manager index indirection in
DefinePhysicalStepLength() with a cached std::vector<G4VProcess*>
built once per particle type. Table is invalidated on particle-type
change or process-vector size mismatch.

Implements BD-geant4-032, BD-geant4-034, BD-geant4-035.
CPC/JINST paper target."
git push -u origin opt/gpil-dispatch-table
```

## Verification checklist

Before marking DONE, confirm:

- [ ] `grep -r "NNBAR_Detector\|nnbar_reconstruction" source/` returns nothing
      in the modified files.
- [ ] `cmake --build .` succeeds with no new warnings on the patched files.
- [ ] Diff is minimal: only `G4SteppingManager.hh` and `G4SteppingManager.cc`
      are modified in `source/`. No physics model files touched.
- [ ] Fixed-seed `TestEm3` (or equivalent) step count and scorer output match
      vanilla within floating-point noise.
- [ ] Report written to `docs/reports/opt_gpil_dispatch_table_20260513.md`.
- [ ] Branch pushed to `SzeChunYiu/geant4-accel`.

## Isolation rules

- Never modify `NNBAR_Detector/`, `nnbar_reconstruction/`, `slurm/`, macros,
  or production data in the simulation repo.
- Do not link against or include any NNBAR simulation header.
- Do not submit SLURM jobs; all testing is local.
- The `geant4-fork` is the only C++ tree you write to.

## Paper context

This patch targets the **CPC/JINST paper on vanilla Geant4 CPU speedup**.
The dispatch-table approach is a well-known technique (Hölzle, Chambers, and
Ungar 1991 polymorphic inline caches; Futamura 1971 partial evaluation).
Cite: Hölzle, Chambers, Ungar 1991 *OOPSLA*; Futamura 1971 *Systems·Computers·Controls*.

## Stop condition

Stop after the patched files compile, the fixed-seed test passes, the report
is written, and the branch is pushed. Do not implement BD-geant4-033 or
unrelated BD entries in this lane.

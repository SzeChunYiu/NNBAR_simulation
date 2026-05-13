# Fix: Cosmic bin5 indefinite stall — root cause and required changes

## Root cause (3 issues, confirmed by source inspection 2026-05-12)

### RC-1 (PRIMARY): G4RadioactiveDecayPhysics with no time threshold
**File:** `NNBAR_Detector/src/core/PhysicsList.cc` line 90

```cpp
RegisterPhysics(new G4RadioactiveDecayPhysics());  // no time cut
```

A 50–200 GeV proton/muon spallates lead glass (SF5, high-Z) and iron/B4C
shielding. This creates radioactive isotopes. Geant4 `G4RadioactiveDecayPhysics`
default behaviour tracks EVERY radioactive nucleus through its entire decay
chain with no time limit — including isotopes with half-lives of seconds, hours,
or longer. The affected event never calls `EndOfEventAction` and the job hangs
indefinitely. This is a well-known Geant4 pitfall; the fix is a one-line
threshold setting.

### RC-2 (SECONDARY): No G4UserLimits on LeadGlass or Scintillator volumes
**Files:** `NNBAR_Detector/src/detector/LeadGlass_geometry.cc`,
`NNBAR_Detector/src/detector/Scintillator_geometry.cc`

The TPC volumes set `SetUserMinEkine(1.0*keV)` and `SetUserMaxTime(10.0*ms)`.
LeadGlass and Scintillator have NO equivalent limits. Secondary neutrons and
low-energy EM particles produced in the dense lead glass (~5 g/cm³) can
scatter/drift with no kill threshold.

### RC-3 (PERFORMANCE): Global mutex in UserSteppingAction
**File:** `NNBAR_Detector/src/core/SteppingAction.cc` line 64

```cpp
G4AutoLock lock(&SteppingMutex);
```

A single global mutex serialises every step across every thread — completely
negating multi-threading. This is why THREADS=4 shows no speedup over THREADS=1.

---

## Required changes

### Change 1: PhysicsList.cc — add radioactive decay time cut

Replace:
```cpp
RegisterPhysics(new G4RadioactiveDecayPhysics());
```
With:
```cpp
G4RadioactiveDecayPhysics* rdp = new G4RadioactiveDecayPhysics();
RegisterPhysics(rdp);
// Kill radioactive nuclei with half-life > 1 µs (covers all HEP-relevant decays).
// Without this, spallation products with macroscopic half-lives stall the event.
G4EmParameters::Instance()->SetLoopingParticleWarningLevel(0);
```
AND in `PhysicsList::ConstructProcess()` or via the macro file, add:
```
/process/had/rdm/thresholdForVeryLongDecayTime 1000000 ns
```
(1 ms threshold — tracks decays faster than 1 ms, kills anything slower)

If the above macro command is not available at build time, use the C++ API:
```cpp
// In PhysicsList.cc, add after ConstructProcess() is called:
#include "G4RadioactiveDecay.hh"
#include "G4ProcessTable.hh"
// ...
void PhysicsList::ConstructProcess() {
    G4VModularPhysicsList::ConstructProcess();
    // Prevent tracking of long-lived radioactive isotopes
    auto* rdc = dynamic_cast<G4RadioactiveDecay*>(
        G4ProcessTable::GetProcessTable()->FindProcess("RadioactiveDecayBase","GenericIon"));
    if (rdc) {
        rdc->SetThresholdForVeryLongDecayTime(1.0e6 * ns);  // 1 ms
    }
}
```

Add the required include if not present: `#include "G4EmParameters.hh"` is
already included.

### Change 2: LeadGlass_geometry.cc — add G4UserLimits

At the end of the `LeadGlass::Construct_Volumes()` function, before `return`,
add limits to the main lead glass logical volume (the one named `LeadGlass_LV`
or equivalent — identify the correct `G4LogicalVolume*` variable for the active
crystal region):

```cpp
// Kill secondary particles that would otherwise scatter/drift indefinitely
// in the high-Z lead glass. Mirrors the protection already in TPC_geometry.cc.
#include "G4UserLimits.hh"  // add to includes at top of file
// ...
G4UserLimits* lgLimits = new G4UserLimits();
lgLimits->SetUserMinEkine(1.0 * keV);
lgLimits->SetUserMaxTime(100.0 * CLHEP::microsecond);
// Apply to every lead glass logical volume in LeadGlass_Construction_list:
for (auto* lv : LeadGlass_Construction_list) {
    lv->SetUserLimits(lgLimits);
}
G4cout << "LeadGlass: User limits set — min KE 1 keV, max time 100 µs" << G4endl;
```

### Change 3: Scintillator_geometry.cc — add G4UserLimits

Identify the scintillator bar logical volume variable (likely `ScintLV` or
equivalent) and add at the end of `Scintillator::Construct_Volumes()`:

```cpp
#include "G4UserLimits.hh"  // add to includes
// ...
G4UserLimits* scintLimits = new G4UserLimits();
scintLimits->SetUserMinEkine(1.0 * keV);
scintLimits->SetUserMaxTime(100.0 * CLHEP::microsecond);
// Apply to all scintillator logical volumes constructed:
for (auto* lv : scintLVs) {   // use the actual vector/list name
    lv->SetUserLimits(scintLimits);
}
G4cout << "Scintillator: User limits set — min KE 1 keV, max time 100 µs" << G4endl;
```

### Change 4: SteppingAction.cc — remove global mutex

Remove `G4AutoLock lock(&SteppingMutex);` at line 64 and the mutex declaration
at line 22 (`namespace {G4Mutex SteppingMutex = G4MUTEX_INITIALIZER;}`).

**Thread-safety audit result (2026-05-12 source inspection):**

- `ParquetOutputManager::WriteInteraction()`: ALREADY SAFE — has its own
  `std::lock_guard<std::mutex> lock(m_mutex)` on every write path.
- `GeometryManager::AddScintillatorEnergyDeposit()` and
  `GeometryManager::AddLeadGlassEnergyDeposit()`: NOT SAFE — no mutex declared
  in `GeometryManager.hh`, no lock in the implementation. These modify shared
  map state and will race without protection.
- Per-thread accumulators `fEdepTPC`, `fEdepScintillator`, `fEdepLeadGlass`,
  `fEdepOther`, `fPhotons*`: SAFE — member variables of `SteppingAction`, which
  is a per-worker-thread object in Geant4 MT.

**Required sub-changes:**

1. `NNBAR_Detector/include/util/GeometryManager.hh` — add private mutex member:
   ```cpp
   #include <mutex>
   // ...
   private:
     mutable std::mutex m_edepMutex;
   ```

2. `NNBAR_Detector/src/util/GeometryManager.cc` — add lock to the two edep
   methods:
   ```cpp
   void GeometryManager::AddLeadGlassEnergyDeposit(int32_t copyNumber, double energy) {
       std::lock_guard<std::mutex> lock(m_edepMutex);
       // existing body...
   }
   void GeometryManager::AddScintillatorEnergyDeposit(int32_t moduleCopyNo, int32_t barCopyNo, double energy) {
       std::lock_guard<std::mutex> lock(m_edepMutex);
       // existing body...
   }
   ```
   Also lock `ClearEventData()` and any other write methods on the same
   per-event accumulators.

3. `NNBAR_Detector/src/core/SteppingAction.cc` — remove lines 22 and 64:
   ```cpp
   // REMOVE line 22: namespace {G4Mutex SteppingMutex = G4MUTEX_INITIALIZER;}
   // REMOVE line 64: G4AutoLock lock(&SteppingMutex);
   ```

The per-thread energy accumulators (`fEdepTPC`, etc.) do NOT need a mutex —
they are `SteppingAction` member variables and `SteppingAction` is per-thread.

**Scope:** `NNBAR_Detector/include/util/GeometryManager.hh`,
`NNBAR_Detector/src/util/GeometryManager.cc`,
`NNBAR_Detector/src/core/SteppingAction.cc`

---

## Verification after fix

1. Run `bash -n` on any modified SLURM scripts.
2. Submit a small LUNARC test job using the known failing seeds:
   ```bash
   # seeds=1636877,2791681, cap=50 events, THREADS=1
   # Should complete in < 5 min with the fix applied
   ```
3. Confirm `EndOfEventAction` fires for events 238 and 491 (previously the
   stall events) — they should now complete within normal step counts.
4. Confirm Parquet output is non-stub (> 4 bytes).
5. Commit with `fix(sim): resolve cosmic bin5 indefinite stall (RC-1/RC-2/RC-3)`.

---

## Scope

- **Writable:** `NNBAR_Detector/src/core/PhysicsList.cc`,
  `NNBAR_Detector/src/detector/LeadGlass_geometry.cc`,
  `NNBAR_Detector/src/detector/Scintillator_geometry.cc`,
  `NNBAR_Detector/src/core/SteppingAction.cc`
- **Do not change:** physics list selection, geometry dimensions, Parquet
  schema, reconstruction code, SLURM scripts
- After fix is built and verified: update MASTER_PLAN cosmic proton bin5 and
  mu- bin5 rows from BLOCKED to NEXT and re-queue the production sbatch.

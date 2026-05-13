# Threading mutex audit: SteppingAction/EventAction

Date: 2026-05-12  
Lane swap: worker-0 consumed `codex-tasks/sim/worker-6.txt` because the task is C++/LUNARC simulation scope.

## Scope

Audited only the files named by the queue prompt:

- `NNBAR_Detector/src/core/SteppingAction.cc`
- `NNBAR_Detector/src/core/EventAction.cc`

No code changes, local builds, SLURM submissions, or production-output mutations were made.

## Search evidence

Command:

```bash
rtk rg -n "G4AutoLock|G4Mutex|std::mutex|std::lock_guard|std::unique_lock|pthread_mutex|omp_lock|\bmutex\b" NNBAR_Detector/src/core/SteppingAction.cc NNBAR_Detector/src/core/EventAction.cc
```

Result: the only match in either audited source file is the RC-3 explanatory comment in `SteppingAction.cc` saying the former global mutex was removed and that `ParquetOutputManager` / `GeometryManager` own any internal locking.

## Mutex inventory

| File / scope | Active mutex or lock found? | Serializes all worker threads? | Disposition |
|---|---:|---:|---|
| `SteppingAction.cc` includes / file scope | No | No | No global `G4Mutex`, `G4AutoLock`, or C++ mutex remains in file scope. |
| `SteppingAction::ResetEdep` | No | No | Calls `GeometryManager::ClearEventData()` without adding a file-level lock. Any locking is inside `GeometryManager`, outside this queue task. |
| `SteppingAction::UserSteppingAction` | No | No | Writes interaction records through `ParquetOutputManager::Instance().WriteInteraction(rec)` without a surrounding global `G4AutoLock`; no file-level serialization remains. |
| `EventAction.cc` includes / file scope | No | No | No global `G4Mutex`, `G4AutoLock`, or C++ mutex remains in file scope. |
| `EventAction::BeginOfEventAction` | No | No | No locks in the TPC drift / Celeritas begin-event branches. |
| `EventAction::EndOfEventAction` | No | No | No explicit lock around progress printing, Celeritas energy collection, or `ParquetOutputManager::WriteGPUEnergy(record)`. |
| `EventAction::SendEventToDisplay` | No | No explicit file-level serializer | The dashboard call is commented as thread-safe but this file does not declare or take a mutex. If dashboard builds still serialize, audit `DashboardWindow` / `EventDisplay` internals separately. |

## Conclusion

No remaining global `G4AutoLock` mutexes, `G4Mutex` declarations, or standard-library mutex wrappers are present in the two audited files. The RC-3 fix appears present at the source level for this scope: `SteppingAction` no longer wraps Parquet writes in a global lock, and `EventAction` contains no file-level lock that serializes all threads.

Recommended next step: if cosmic bin-5 stalls or throughput regressions persist after RC-4, audit internal locks in `ParquetOutputManager`, `GeometryManager`, and dashboard/event-display code, because those are the synchronization owners referenced or called by these files.

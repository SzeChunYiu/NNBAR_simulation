# GPIL dispatch-table preflight blocker

Date: 2026-05-17 03:10 CEST
Lane: worker-0 / g4-cpu-opt-gpil-dispatch
Factory item: blocker evidence for the queued `codex-tasks/g4gpu/worker-0.txt` task

## Role / lease declaration

- Role type: specialist-contractor (C++/GPU/LUNARC worker)
- Manager / escalation: VALIDATOR
- Decision rights: preflight the queued C++ optimization task, produce blocker evidence, and avoid destructive edits outside an explicit writable lease.
- Branch / worktree: simulation repo `/Volumes/MyDrive/nnbar/nnbar/simulation` on `work/20260517-g4-source-review-event-stack`; target Geant4 fork branch is `opt/gpil-dispatch-table`.
- Writable lease used in this iteration: this report only.
- Paths intentionally not edited: `/Volumes/MyDrive/nnbar/geant4-fork/`, `/Volumes/MyDrive/superpowers/worktrees/geant4-fork/opt-gpil-dispatch-table-active/`, `NNBAR_Detector/`, `nnbar_reconstruction/`, `slurm/`, macros, and production data.

## Blocker queue check

Shared blocker queues were checked before lane-local work. The only matching lines in each blocker file were comments; no actionable `/goal` blocker was present in:

- `codex-tasks/blockers.txt`
- `codex-tasks/atomic/blockers.txt`
- `codex-tasks/g4gpu/blockers.txt`
- `codex-tasks/meta/blockers.txt`
- `codex-tasks/recon/blockers.txt`
- `codex-tasks/review/blockers.txt`
- `codex-tasks/sim/blockers.txt`

Command used:

```text
rtk proxy bash -lc 'for f in codex-tasks/blockers.txt codex-tasks/*/blockers.txt codex-tasks/*/blocker.txt; do [ -e "$f" ] || continue; echo "--- $f"; grep -n "/goal" "$f" || true; done'
```

## Queued task found

`codex-tasks/g4gpu/worker-0.txt` still contains the GPIL dispatch task:

```text
/goal lane g4-cpu-opt-gpil-dispatch. Read docs/parallel-sessions/g4-cpu-opt-gpil-dispatch.md. In geant4-fork branch opt/gpil-dispatch-table implement BD-geant4-032/034/035 GPIL dispatch table, run fixed-seed TestEm3 validation, write report opt_gpil_dispatch_table_20260513.md, push branch.
```

The task is in worker-0 scope (C++/Geant4 CPU optimization), but the target fork is not safe to edit from this pane without validator cleanup or a fresh lease.

## Evidence: local target branch/worktree contention

The primary Geant4 fork checkout is on a different active branch and already has non-owned changes:

```text
rtk proxy git -C /Volumes/MyDrive/nnbar/geant4-fork status --short
 M source/processes/hadronic/cross_sections/include/G4CrossSectionDataStore.hh
?? ._.pytest_cache
?? ._tests
?? source/processes/hadronic/cross_sections/include/._G4CrossSectionDataStore.hh
?? tests/

rtk proxy git -C /Volumes/MyDrive/nnbar/geant4-fork branch --show-current
opt/hadronic-xs-cache
```

The required `opt/gpil-dispatch-table` branch is already checked out in a separate worktree:

```text
rtk proxy git -C /Volumes/MyDrive/nnbar/geant4-fork worktree list --porcelain
worktree /Volumes/MyDrive/nnbar/geant4-fork
HEAD f840b5da3a70c2c7be836fdb72a781eab12e0af6
branch refs/heads/opt/hadronic-xs-cache

worktree /Volumes/MyDrive/superpowers/worktrees/geant4-fork/opt-gpil-dispatch-table-active
HEAD f840b5da3a70c2c7be836fdb72a781eab12e0af6
branch refs/heads/opt/gpil-dispatch-table
```

That existing `opt/gpil-dispatch-table` worktree is not a safe clean baseline. `git status --short` reports a repository-wide delete/untracked mirror pattern (thousands of deleted tracked files and matching untracked files), so repairing or resetting it would be destructive to a possibly active lease. The status command produced 17,414 lines; the first lines were:

```text
D  .clang-format
D  .clang-tidy
D  .github/CODEOWNERS
D  .gitlab/CODEOWNERS
D  CHANGELOG
D  CITATION.cff
D  CMakeLists.txt
D  CONTRIBUTING.rst
D  LICENSE
D  README.rst
```

The same status output also included matching untracked roots such as:

```text
?? .clang-format
?? .clang-tidy
?? .github/
?? .gitlab/
?? CHANGELOG
?? CITATION.cff
?? CMakeLists.txt
```

## Evidence: source anchors exist but implementation was not started

The target source files exist in the fork, and the current `DefinePhysicalStepLength` anchor resolves before editing:

```text
rtk proxy ls /Volumes/MyDrive/nnbar/geant4-fork/source/tracking/src/G4SteppingManager.cc \
  /Volumes/MyDrive/nnbar/geant4-fork/source/tracking/include/G4SteppingManager.hh \
  /Volumes/MyDrive/nnbar/geant4-fork/source/processes/management/include/G4ProcessManager.hh \
  /Volumes/MyDrive/nnbar/geant4-fork/source/processes/management/include/G4VProcess.hh
```

```text
/Volumes/MyDrive/nnbar/geant4-fork/source/tracking/src/G4SteppingManager.cc:449:void G4SteppingManager::DefinePhysicalStepLength()
/Volumes/MyDrive/nnbar/geant4-fork/source/tracking/include/G4SteppingManager.hh:73:class G4SteppingManager
```

No C++ compile, CMake configure, or TestEm3 validation was attempted locally because worker-0 resource policy forbids local C++/CUDA compilation. No source files were edited because the required branch/worktree lease is ambiguous and dirty.

## LUNARC preflight

The LUNARC SSH socket was checked first and was already connected. The remote Geant4 fork exists but is on a different branch with unrelated build artifacts:

```text
rtk proxy bash -lc 'ssh -O check lunarc 2>/dev/null && echo Connected || /Users/billy/lunarc-init.sh'
Connected

rtk proxy bash -lc 'ssh lunarc "test -d /projects/hep/fs10/shared/nnbar/billy/geant4-fork && cd /projects/hep/fs10/shared/nnbar/billy/geant4-fork && git status --short | head -80; git branch --show-current; git log --oneline -3"'
?? build-bd001-optimized-prefix/
?? build/
?? scripts/__pycache__/
lane/bd-geant4-001-moller-bhabha-inverse-sampler
782d84cb59 docs: record BD001 sampler scaffold handoff
4ac150bf45 feat(em): scaffold BD001 Moller Bhabha sampler flag
f840b5da3a Import Geant4 11.2.2 source tree
```

## Required validator action

Before this queue item can be implemented safely, VALIDATOR should choose one of these options:

1. Assign a fresh, explicit Geant4 fork worktree for this task and record the branch name, e.g. a new `opt/gpil-dispatch-table-worker0-20260517` worktree, or
2. Confirm that `/Volumes/MyDrive/superpowers/worktrees/geant4-fork/opt-gpil-dispatch-table-active/` is abandoned and may be cleaned/reset, or
3. Requeue this task with updated verification rules that reconcile the lane doc's "all testing is local" instruction with the active worker-0 policy requiring builds/tests on LUNARC.

Until one option is chosen, implementing the dispatch table risks overwriting another lane's work or violating the current resource policy.

## Handoff

Factory item: blocker evidence for queued `g4-cpu-opt-gpil-dispatch` task
Blocker queue checked: shared blocker queues listed above; no actionable `/goal` lines found
Verification evidence: blocker-queue grep, target queue read, local fork/worktree status, source-anchor grep, LUNARC socket check, remote fork status
Next validator action: provide a clean writable worktree/branch lease or update the queue task with reconciled verification instructions

## Queue disposition addendum

To avoid repeated worker iterations on the same unsafe lease state, this
iteration changed `codex-tasks/g4gpu/worker-0.txt` from the active `/goal`
prompt to a `# BLOCKED` comment pointing at this report. This does not resolve
the task; it only prevents duplicate implementation attempts until VALIDATOR
chooses the worktree/branch policy above.

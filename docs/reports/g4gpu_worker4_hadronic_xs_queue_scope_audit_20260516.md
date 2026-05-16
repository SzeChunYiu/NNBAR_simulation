# G4GPU worker-4 queue scope audit: hadronic XS kernel

Date: 2026-05-16
Lane: worker-4 (G4GPU source-code review + research, isolated)
Role type: specialist-contractor
Manager / escalation: VALIDATOR (`docs/parallel-sessions/TEAM_PLAN.md`)
Branch/worktree: `main` at `/Volumes/MyDrive/nnbar/nnbar/simulation`
Writable lease used this iteration: this report only under `docs/reports/g4gpu_*.md`
Factory item: A1 / B1 blocker-watch evidence

## Start-of-iteration evidence

- Required factory blocker check: `docs/parallel-sessions/AI_FACTORY.md:7` says shared blockers in the active task directory outrank lane-local work.
- Active task directory evidence: `.codex-supervisor.toml:49` sets the G4GPU task directory to `codex-tasks/g4gpu`.
- Blocker queue checked: `codex-tasks/g4gpu/blockers.txt`; `grep -R -n "^/goal" codex-tasks/g4gpu/blockers.txt codex-tasks/blockers.txt` returned no matches.
- Lane charter evidence: `docs/parallel-sessions/worker-4.md:16` says worker-4 does not modify NNBAR or production G4GPU code and produces analyses, surveys, and recommendations. The allowed edit list is `docs/parallel-sessions/worker-4.md:86`--`91`.
- Active queue evidence: `codex-tasks/g4gpu/worker-4.txt:1` currently queues `/goal lane g4gpu-hadronic-xs-kernel ... create HadronicXSKernel.cu, HadronicXSKernel.hh, test, CMake wiring ... Push branch.`
- Task-spec mismatch evidence: `docs/parallel-sessions/g4gpu-hadronic-xs-kernel.md:5`--`6` defines an isolated G4GPU implementation worker working exclusively in `/Volumes/MyDrive/nnbar/geant4-gpu/`; `docs/parallel-sessions/g4gpu-hadronic-xs-kernel.md:26` lists that external repo as the write target.

## Finding

The queued hadronic XS kernel task is mechanically valid, but it is not a worker-4 source-review/research unit. Executing it from this lane would cross the worker-4 charter from documentation/recommendation output into production G4GPU implementation. I therefore did not edit `/Volumes/MyDrive/nnbar/geant4-gpu/`, did not create CUDA/CMake/test files, did not pop or rewrite the queue item, and did not mark any implementation status as done.

## Validator handoff

Recommended next action: requeue or leave `g4gpu-hadronic-xs-kernel` for an implementation lane whose charter explicitly writes `/Volumes/MyDrive/nnbar/geant4-gpu/` (for example the active G4GPU implementation panes), or update `docs/parallel-sessions/worker-4.md` if VALIDATOR wants worker-4 to become an implementation lane. Until then, worker-4 should continue source-review/survey tasks only.

Blocker type: lane-lease mismatch, not a shared stop-the-line blocker. The shared blocker queues are still empty of `/goal` lines, so other in-scope G4GPU work may proceed.

## Verification

```text
$ grep -R -n "^/goal" codex-tasks/g4gpu/blockers.txt codex-tasks/blockers.txt
# no output

$ bash scripts/validate-csup-queues.sh
files scanned: 54
prompt lines checked: 78
failures: 0
OK: every prompt line passes all mechanical checks.
```

No local builds, simulations, SLURM jobs, G4GPU source edits, NNBAR production edits, macros, or data files were touched.

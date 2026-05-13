# Lane: supervisor-protocol-refresh

## Goal

Reconcile the shared parallel-session protocol with the current six-prompt
supervisor batch (`worker-0`, `worker-1`, `worker-2`, `worker-3`, `worker-4`,
`planner`). A planner review found that `scripts/codex-supervisor/nnbar-gpu-batch-prompts.txt`
and `Makefile` now launch six panes, while the shared protocol still describes
legacy four-pane L0--L3 work.

## Files

- Modify: `docs/parallel-sessions.md`
- Modify: `docs/parallel-sessions/planner.md`
- Modify if needed: `docs/policies/g4gpu-isolation.md`
- Do not edit production code, C++, Python reconstruction, SLURM scripts, or
  queue contents except for status notes in `MASTER_PLAN.md` if necessary.

## Implementation steps

1. Re-read `docs/parallel-sessions.md`, `docs/parallel-sessions/planner.md`,
   `docs/parallel-sessions/worker-0.md` through `worker-4.md`, the prompts file,
   and `Makefile`.
2. Update the shared protocol so it accurately distinguishes:
   - legacy Wave-6 L0--L3 plan lanes, if still relevant;
   - active continuous lanes `worker-0`..`worker-4` plus `planner`;
   - each lane's writable scope and queue file.
3. Update planner queue-depth instructions so they mention `worker-2.txt` and
   the active G4GPU queues where appropriate; do not leave contradictory
   `worker-1 only` examples.
4. Update isolation policy applicability if it lists old lanes but omits
   `worker-3`/`worker-4`.
5. Keep prompt examples compact and validate all prompt lines.
6. Update `MASTER_PLAN.md` status/notes only after verification.

## Verification

Run:

```bash
rtk zsh -lc 'CODEX_SUPERVISOR_PROMPTS=scripts/codex-supervisor/nnbar-gpu-batch-prompts.txt ~/codex-supervisor.sh validate-prompts'
rtk rg -n "4 parallel|L0|worker-3|worker-4|worker-2.txt|worker-3.txt|worker-4.txt" docs/parallel-sessions.md docs/parallel-sessions/planner.md docs/policies/g4gpu-isolation.md
rtk wc -l docs/parallel-sessions.md docs/parallel-sessions/planner.md docs/policies/g4gpu-isolation.md docs/parallel-sessions/MASTER_PLAN.md
```

Expected: prompt validation passes; grep output shows no stale claim that the
active batch has only four panes; touched docs remain <= 500 lines.

## Stop condition

Stop after the documentation consistency fix is committed and MASTER_PLAN notes
are updated. Do not modify production code in this lane.

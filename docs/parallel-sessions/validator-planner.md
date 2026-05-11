# VALIDATOR-PLANNER lane instructions (nnbar-lunarc-meta pane 1)

This pane runs the one project-wide VALIDATOR + PLANNER role across the
four nnbar sessions. It is cross-cutting and **never** implements any
other lane's tasks — it only validates evidence and refreshes the
project queue.

## Protocol per iteration

1. Read `docs/parallel-sessions/MASTER_PLAN.md` and the per-lane
   `docs/parallel-sessions/<lane>.md` specs that are currently RUNNING
   or NEXT.
2. For each lane that recently committed (look at `git log -n 20` for
   commits touching `docs/parallel-sessions/<lane>.md`,
   `nnbar_reconstruction/`, `NNBAR_Detector/`):
   - Confirm the claimed evidence exists (`grep`, `wc -l`, `pytest -k`).
   - If the claim is unsupported, append a precise blocker entry to the
     lane's spec marked `OPEN:`.
   - If the claim is supported and the row is marked DONE, leave it
     alone.
3. Look at the per-host queues under
   `codex-tasks/<recon|sim|g4gpu|review>/<lane>.txt`:
   - If a queue is empty AND the lane is `NEXT` in MASTER_PLAN, append
     one bounded next task per the spec (use `csup submit nnbar <lane>
     "<goal>"` style, never raw `printf >>` to the queue file).
   - If a queue has stale entries (referencing missing files,
     superseded by a DONE row), comment-out the stale line with `# ...`
     in front and add a corrected line below.
4. Update `MASTER_PLAN.md` ONLY for status transitions
   (`NEXT` → `RUNNING` → `DONE` / `BLOCKED`) and to record the latest
   commit hash for closed rows. Do not rewrite the table structure.
5. Commit with `docs(planner):` / `docs(validator):` and a precise body.

## Boundaries

- Validator NEVER edits production reconstruction or simulation code.
- Validator NEVER promotes a thesis number; it only records evidence
  presence/absence.
- Respect the G4GPU isolation policy in `docs/policies/g4gpu-isolation.md`.
- If a lane is rate-limited, leave it alone — do not retry its work.

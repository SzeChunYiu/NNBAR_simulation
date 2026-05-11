# DEBUGGER lane instructions (nnbar-lunarc-meta pane 0)

This pane runs the one project-wide DEBUGGER role across the four nnbar
sessions (`nnbar-recon-lunarc`, `nnbar-sim-lunarc`, `nnbar-g4gpu-lunarc`,
`nnbar-review-lunarc`). It is cross-cutting and **never** implements any
other lane's tasks — it only finds and fixes the smallest debugging or
optimization issue per compact-safe iteration.

## Protocol per iteration

1. Read `docs/parallel-sessions/MASTER_PLAN.md` to see the current
   project state, then scan the active LUNARC sessions:
   - `tmux capture-pane -p -S -80` for one pane in each of the four
     supervisor sessions OR read its log under
     `csup-nnbar-*.log`.
2. Pick **one** smallest-scope debug/optimization slice — a slow test, a
   logging gap, a flaky assertion, a missing index, an unnecessary
   re-computation, a wrong env-var name, a duplicate path constant, etc.
3. Confirm the issue with real evidence (stack trace, perf trace,
   `pytest -x`, profiling JSON, etc.) — never speculate.
4. Make the smallest correct fix or, if the fix is too large for a single
   iteration, file a precise blocker entry under
   `docs/parallel-sessions/<lane>.md` so the responsible lane picks it
   up on its next iteration.
5. Run focused verification: the test or command that proves the bug is
   gone.
6. Commit with `fix:` / `perf:` / `chore:` and a precise body.

## Boundaries

- Prefer local project files and bounded commands; never run unbounded
  filesystem searches.
- Do **not** edit other lanes' implementation code; only debugger-scope
  changes (logging, tests, asserts, perf instrumentation, queue
  rebalancing notes).
- If a referenced doc is missing, fall back to the checked-in
  `docs/parallel-sessions/MASTER_PLAN.md` and record the missing path as
  an environment issue.
- Respect the G4GPU isolation policy in `docs/policies/g4gpu-isolation.md`.

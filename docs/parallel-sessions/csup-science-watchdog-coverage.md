# Lane: csup-science-watchdog-coverage

## Goal

Restore codex-supervisor configuration consistency after the current checkout
added an `nnbar-science-lunarc` host to `.codex-supervisor.toml` without
matching watchdog/prompt coverage.

## Root-cause evidence from planner

- Reproduced failure:
  `rtk proxy python -m pytest tests/test_csup_corruption_watchdog.py::test_watchdog_covers_every_lunarc_prompt_session -q`
  fails because the TOML host map includes
  `nnbar-science-lunarc=codex-prompts-science.txt`, while
  `scripts/csup-corruption-watchdog.sh` only maps recon/sim/g4gpu/review/meta.
- `codex-prompts-science.txt` is not present in the current local checkout, so
  the worker must first decide whether the science host is intended or a stale
  partial edit.
- Full planner check also fails at the same coverage assertion when running
  `rtk proxy bash -lc "python -m pytest tests/ -x -q 2>&1 | tail -20"`.

## Files to inspect/edit

- `.codex-supervisor.toml`
- `scripts/csup-corruption-watchdog.sh`
- `codex-prompts-science.txt` if the science host is intended
- `docs/parallel-sessions.md` and `docs/parallel-sessions/MASTER_PLAN.md` only
  if the active-session table must acknowledge or reject the science session
- `tests/test_csup_corruption_watchdog.py` only if an additional regression is
  needed; do not weaken the existing coverage test

## Implementation steps

1. Re-read `docs/parallel-sessions.md`, `docs/parallel-sessions/MASTER_PLAN.md`,
   and this spec.
2. Determine the intended topology from current prompts, queue dirs, and TOML:
   either keep a real science session or remove the partial science host.
3. Apply one consistency fix only:
   - If keeping science: create/validate `codex-prompts-science.txt`, add the
     watchdog mapping, and update active-session docs/queues consistently.
   - If not keeping science: remove the stale science host/config references
     and leave the five-session topology intact.
4. Preserve Bash 3.2 compatibility in `scripts/csup-corruption-watchdog.sh`.
5. Do not start or submit any LUNARC jobs.

## Test command

```bash
rtk proxy python -m pytest tests/test_csup_corruption_watchdog.py -q
rtk proxy bash -lc "python -m pytest tests/ -x -q 2>&1 | tail -20"
rtk proxy bash scripts/validate-csup-queues.sh
```

## Stop condition

Stop when the focused watchdog suite passes, the full suite no longer fails on
science/watchdog coverage, queue validation passes, and `MASTER_PLAN.md` records
whether `csup-science-watchdog-coverage` is `DONE` or `BLOCKED` with exact
evidence.

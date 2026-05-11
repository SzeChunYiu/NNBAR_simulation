# Lane: thesis-ledger-command-closure

## Goal

Make thesis reproduction ledger command and sample blockers machine-checkable so
rows cannot be cited as executable unless their sample path and command surface
are verified. This lane should produce an audit surface first, not regenerate
thesis figures.

## Writable scope

- Create: `nnbar_reconstruction/analysis/thesis_ledger_closure.py`
- Create: `tests/test_thesis_ledger_closure.py`
- Modify only for lane status: `docs/parallel-sessions/MASTER_PLAN.md`

Forbidden:

- Do not run simulations, submit SLURM jobs, or require unavailable thesis
  samples.
- Do not edit the ledger rows in bulk in the first iteration.
- Do not invent CLI commands or sample directories.
- Do not mark ledger rows `reproduced` unless artifacts and verifier output are
  present in this worktree.

## Required reading

1. `docs/parallel-sessions.md`
2. `docs/parallel-sessions/MASTER_PLAN.md`
3. `CODING_STANDARDS.md`
4. `docs/thesis_reproduction_ledger.md`
5. `docs/rebuild_plans/47_reproduction_ledger.md`
6. `docs/rebuild_plans/10_macro_and_sample_inventory.md`
7. `docs/rebuild_plans/03_dataset_registry.md`

Before committing any file, function, path, or command claim, apply the verifier
rules in `docs/parallel-sessions.md`. In particular, every `python -m
nnbar_reconstruction.<subcommand>` claim needs the help-command verifier.

## One compact-safe iteration

1. Claim the lane by changing its MASTER_PLAN row from `NEXT` to `RUNNING` and
   committing that status-only change.
2. Add a parser for the markdown ledger table that extracts row id, sample,
   reproducing command, status, and notes without changing the ledger file.
3. Add an audit result model that classifies each row as:
   - command placeholder or TODO;
   - Python command needing CLI verification;
   - macro/script command needing file-existence verification;
   - sample path missing or not checked;
   - ready for a future reproduction run.
4. Keep checks fail-closed: unknown command shapes and absent sample paths must
   produce blockers, not success.
5. Add tests with toy ledger rows for TODO commands, unsupported CLI commands,
   missing samples, and a verified local toy sample path.
6. Add one deterministic integration test against `docs/thesis_reproduction_ledger.md`
   that asserts the current ledger still reports blockers instead of silently
   claiming full executability.
7. Mark the MASTER_PLAN row `DONE` only after focused/full pytest and file-cap
   checks pass, with notes summarizing blocker counts and the next smallest fix.

## Verification command

```bash
rtk python -m pytest tests/test_thesis_ledger_closure.py -q
rtk proxy zsh -lc "python -m pytest tests/ -x -q 2>&1 | tail -20"
rtk proxy wc -l nnbar_reconstruction/analysis/thesis_ledger_closure.py tests/test_thesis_ledger_closure.py
```

## Stop condition

Stop after the ledger closure audit module/tests are committed, touched files
remain under 500 lines, and MASTER_PLAN records that exact thesis reproduction
remains blocked until row-specific commands and sample paths pass the verifier.

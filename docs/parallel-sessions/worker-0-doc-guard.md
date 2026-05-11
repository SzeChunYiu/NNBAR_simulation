# Lane: worker-0-doc-guard

## Goal

Fix the newly added worker-0 lane guide so it follows repository command rules:
all shell examples must use `rtk`/`rtk proxy`, and any LUNARC SSH instruction
must include the socket check/init guard before `ssh lunarc` work.

## Writable scope

- `docs/parallel-sessions/worker-0.md`
- `docs/parallel-sessions/MASTER_PLAN.md` only for marking this task DONE

Do not edit production code, queue files, SLURM scripts, or G4GPU sources in
this lane.

## Required reading

1. `docs/parallel-sessions.md`
2. `docs/parallel-sessions/MASTER_PLAN.md`
3. `docs/parallel-sessions/worker-0.md`
4. `/Users/billy/.codex/RTK.md`

## One compact-safe iteration

1. Update `worker-0.md` so every command example that would be run in this repo
   is prefixed with `rtk`, or uses `rtk proxy` for compound shell commands.
2. Replace any wording that says plain `ssh lunarc "cmd"` is sufficient with an
   explicit guard. Recommended pattern:
   ```bash
   rtk proxy bash -lc "ssh -O check lunarc 2>/dev/null && echo Connected || /Users/billy/lunarc-init.sh"
   ```
   Then run the intended `ssh lunarc ...` command, also through `rtk proxy` if
   it is a compound shell command.
3. Keep this as a documentation-only fix. Do not start or submit cluster work.
4. Keep the file compact and below 500 lines.

## Verification command

```bash
wc -l docs/parallel-sessions/worker-0.md
rg -n "ssh lunarc|git commit|sbatch|squeue|rsync|python -m|pytest|cmake|make" docs/parallel-sessions/worker-0.md
```

Inspect the `rg` output manually: remaining command examples should either be
prefixed with `rtk`/`rtk proxy` or be explanatory prose that clearly points to
the guarded pattern.

## Stop condition

Stop after the documentation guard fix is committed and `MASTER_PLAN.md` marks
`worker-0-doc-guard` DONE with the verification output summarized.

# Lane: cosmic-slurm-array-doc-split

## Goal

Keep the CRY/cosmic SLURM coordination docs inside the repository file-size
policy before the next status append. Planner review on 2026-05-12 first found the file near the split threshold;
a later pre-commit check after an active Worker-0 refresh ran
`wc -l docs/parallel-sessions/cosmic-slurm-array.md` and got:

```text
     471 docs/parallel-sessions/cosmic-slurm-array.md
```

`docs/parallel-sessions.md` says to split files before adding once they approach
450 lines, so this lane must move detailed proton-bin5 thread-probe chronology into
a companion document and leave a concise summary/link in the umbrella lane doc.

## Writable scope

- `docs/parallel-sessions/cosmic-slurm-array.md`
- `docs/parallel-sessions/cosmic-slurm-array-proton-bin5-thread-probe.md`
- `docs/parallel-sessions/MASTER_PLAN.md` only for this lane's status row

## Forbidden scope

- Do not edit production C++/Python code.
- Do not submit SLURM jobs, run simulations, mutate LUNARC outputs, or rsync.
- Do not edit other queue files or unrelated lane specs.

## Required reading

1. `docs/parallel-sessions.md`
2. `docs/parallel-sessions/MASTER_PLAN.md`
3. `docs/parallel-sessions/cosmic-slurm-array.md`

## Implementation steps

1. Create `docs/parallel-sessions/cosmic-slurm-array-proton-bin5-thread-probe.md`.
2. Move detailed proton-bin5 thread-probe/recovery chronology and handoff text
   out of `cosmic-slurm-array.md` into the new companion doc. Preserve existing
   timestamps, job IDs, row counts, exit codes, and stop/no-production rules
   verbatim unless you are only shortening prose.
3. Replace the moved detail in `cosmic-slurm-array.md` with a compact summary
   that links to the new companion doc and keeps the current authorization rule:
   no production proton-bin5 recovery until final thread-probe results are
   inspected.
4. Update this task's `MASTER_PLAN.md` row from `NEXT` to `DONE` with the
   verification output. Do not change unrelated rows.

## Verification command

Run from the repo root:

```bash
rtk proxy bash -lc 'wc -l docs/parallel-sessions/cosmic-slurm-array.md docs/parallel-sessions/cosmic-slurm-array-proton-bin5-thread-probe.md; test "$(wc -l < docs/parallel-sessions/cosmic-slurm-array.md)" -lt 430; grep -n "cosmic-slurm-array-proton-bin5-thread-probe.md" docs/parallel-sessions/cosmic-slurm-array.md; grep -n "3047491" docs/parallel-sessions/cosmic-slurm-array-proton-bin5-thread-probe.md'
```

## Stop condition

Stop after the verification command passes, `MASTER_PLAN.md` marks this lane
`DONE`, and your commit contains only the writable-scope files above.

# Lane: cosmic-muon-bin5-recovery

## Goal

Produce a guarded recovery decision for the timed-out CRY mu- bin5 job
`3040259_5` without touching the active proton-bin5 recovery. This compact unit
is for evidence and recovery planning first; submit a new job only if the checks
below prove there is no active duplicate and the recovery script is scoped to
mu- bin5 only.

## Required reading

1. `docs/parallel-sessions.md`
2. `docs/parallel-sessions/MASTER_PLAN.md`
3. `docs/parallel-sessions/cosmic-slurm-array.md`
4. `docs/parallel-sessions/cosmic-proton-bin5-recovery.md` for the current
   "do not duplicate proton bin5" rule

## Writable scope

- `docs/parallel-sessions/MASTER_PLAN.md` status notes for this lane only
- this lane spec, for a brief clarification if needed
- `NNBAR_Detector/slurm/` only if a mu- bin5-only recovery wrapper is created
- the matching queue file only to pop/claim this task

Do not edit reconstruction code, G4GPU code, production detector geometry, or
proton-bin5 recovery scripts. Do not submit or modify proton-bin5 job `3046812`.

## One compact-safe iteration

1. Run the LUNARC guard before any remote command:
   ```bash
   rtk proxy bash -lc 'ssh -O check lunarc 2>/dev/null && echo "Connected" || /Users/billy/lunarc-init.sh'
   ```
2. Inspect the mu- bin5 timeout evidence for the original array task:
   ```bash
   rtk proxy ssh lunarc "sacct -X -j 3040259 --format=JobID,State,ExitCode,Elapsed,MaxRSS%12 -P | grep -E 'JobID|3040259_5'"
   rtk proxy ssh lunarc "cd /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim && find build_lunarc slurm -maxdepth 4 -type f \\( -path '*mu*bin5*' -o -name '*3040259_5*' \\) -printf '%p %s bytes\\n' 2>/dev/null | sort"
   ```
3. Check for active duplicate mu- bin5 work before planning any recovery:
   ```bash
   rtk proxy ssh lunarc "squeue -u \$USER -o '%.18i %.30j %.10T %.10M %.40R' | grep -Ei 'mu|cosmic|3040259|bin5' || true"
   ```
4. Read stdout/stderr tails for the timed-out task and classify the blocker:
   slow event generation, missing output, invalid/stub Parquet, or another
   concrete failure mode.
5. If a valid non-stub mu- bin5 Parquet already exists, do not submit anything;
   update `MASTER_PLAN.md` with the evidence and stop.
6. If no valid output exists and no active duplicate is running, create the
   smallest mu- bin5-only recovery plan or wrapper. Preserve CRY particle index
   and energy-bin semantics from `cosmic-slurm-array.md`; do not broaden to
   other bins.

## Verification

Before committing any status or wrapper:

```bash
rtk wc -l docs/parallel-sessions/cosmic-muon-bin5-recovery.md docs/parallel-sessions/MASTER_PLAN.md
rtk proxy bash -lc 'git diff -- docs/parallel-sessions/cosmic-muon-bin5-recovery.md docs/parallel-sessions/MASTER_PLAN.md NNBAR_Detector/slurm'
```

If a wrapper is added, also run `bash -n` on that wrapper locally and record the
guarded LUNARC command used to stage or submit it. Do not claim completion from
queue state alone; cite the actual `sacct`, output-size, and log-tail evidence.

## Stop condition

Stop after one of these outcomes:

- `DONE/BLOCKED` evidence shows mu- bin5 already has a valid output or remains
  blocked by a named condition; or
- exactly one mu- bin5-only recovery wrapper/job is prepared or submitted with
  job ID, command, and no proton-bin5 interaction.

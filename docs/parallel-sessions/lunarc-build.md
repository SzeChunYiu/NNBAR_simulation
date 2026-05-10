# Lane: lunarc-build

## Goal

Install Geant4 via conda-forge into hibeam_env on LUNARC, fix the SLURM build script,
submit the build, and verify the simulation binary is produced.

## Pre-searched: Geant4 Status on LUNARC

**No usable Geant4 installation exists on LUNARC.** A comprehensive search was already done:
- `/projects/hep/fs12/nnbar/software/geant4-MT/install/` — DELETED (stale path in build script)
- `/projects/hep/fs8/` — only Geant4 v10.x installs, incompatible version
- `/home/scyiu/` — nothing
- `hibeam_env` conda — Geant4 not installed there yet
- Other users' envs — bmeirose has a trash conda cache, unusable

**Skip Step 1 search. Go directly to conda-forge install.**

## Worktree

`/Volumes/MyDrive/nnbar/nnbar/simulation` (main branch — SSH work only, no local file commits required)

## Writable Targets

- `/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/slurm/build_nnbar.slurm` (on LUNARC via SSH)
- `/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/slurm/run_signal.slurm` (on LUNARC via SSH)

## Iteration Cycle

1. Re-read `docs/parallel-sessions.md` and this file.
2. Do the next step below. One step per iteration.
3. If a step fails, diagnose and fix before moving on.

## Steps

### Step 1 — Install Geant4 via conda-forge

No usable Geant4 exists on LUNARC (pre-searched — skip any searching). Install directly:

```bash
ssh lunarc "/projects/hep/fs10/shared/nnbar/billy/packages/hibeam_env/bin/conda install -c conda-forge geant4 -y 2>&1 | tail -20"
```

This will take several minutes. When done, find the installed geant4.sh:
```bash
ssh lunarc "find /projects/hep/fs10/shared/nnbar/billy/packages/hibeam_env -name 'geant4.sh' 2>/dev/null"
ssh lunarc "find /projects/hep/fs10/shared/nnbar/billy/packages/hibeam_env -name 'geant4-config' 2>/dev/null"
```

Record the path — you'll need it for Step 2.

### Step 2 — Update build script

Edit `/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/slurm/build_nnbar.slurm` on LUNARC:
- Replace the broken `source .../geant4.sh` line with the correct path found in Step 1
- Update `module load` lines to match the toolchain that Geant4 was built with
- The Arrow library is bundled at `external/arrow-install-linux/` — CMake auto-detects it, no module needed

Use `ssh lunarc "sed -i '...' /path/to/build_nnbar.slurm"` or heredoc to rewrite.

Verify the fix:
```bash
ssh lunarc "cat /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/slurm/build_nnbar.slurm"
```

### Step 3 — Submit and monitor

```bash
ssh lunarc "sbatch /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/slurm/build_nnbar.slurm"
ssh lunarc "squeue -u scyiu -o '%.10i %.18j %.8T %.10M %.12l'"
```

Wait for the job to finish, then check the log:
```bash
ssh lunarc "tail -50 /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/slurm/build-*.out 2>/dev/null"
ssh lunarc "cat /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/slurm/build-*.err 2>/dev/null"
```

### Step 4 — Verify binary

```bash
ssh lunarc "ls -lh /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/build_lunarc/nnbar-detector-simulation* 2>/dev/null"
ssh lunarc "file /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/build_lunarc/nnbar-detector-simulation.bin 2>/dev/null"
```

The binary must be `ELF 64-bit LSB executable, x86-64`. If it's Mach-O, the old macOS binary was not overwritten — check cmake configured correctly.

### Step 5 — Submit signal run

Once binary is confirmed, submit a 1000-event test run:
```bash
ssh lunarc "cd /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/build_lunarc && mkdir -p mcpl_files && ln -sf /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/mcpl_files/NNBAR_rwag_signal_GBL_jbar_100k_9009.mcpl mcpl_files/ 2>/dev/null; true"
ssh lunarc "NEVENTS=1000 sbatch /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/slurm/run_signal.slurm"
```

## Stop Condition

Stop when Step 5 job is submitted and queued (or running). Write a one-line
`DONE` summary to stdout so the supervisor can detect goal completion.

## Key Facts

- LUNARC SSH: `ssh lunarc "cmd"` — pre-multiplexed, no auth needed
- SLURM account: `lu2026-2-51`, partition: `lu48`
- Source tree on LUNARC: `/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/`
- Build dir: `.../NNBAR_Detector_sim/build_lunarc/`
- Arrow is bundled at `.../NNBAR_Detector_sim/external/arrow-install-linux/` — no module needed
- Old Geant4 path (broken): `/projects/hep/fs12/nnbar/software/geant4-MT/install/`

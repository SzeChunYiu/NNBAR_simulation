# Lane: cosmic-proton-bin5-thread-probe

> **For Codex:** REQUIRED SUB-SKILL: use `systematic-debugging` before
> changing the SLURM wrapper. This lane prepares a guarded diagnostic wrapper
> only; it does not authorize a proton-bin5 job submission.

## Goal

Create a no-submit-by-default SLURM diagnostic wrapper for the CRY proton bin5
(`particleIdx=4`, `energyBin=5`, 50--200 GeV) failed seed paths. The wrapper
must compare the failed diagnostic seeds at `THREADS=1` and `THREADS=4` without
raising event caps, overwriting previous outputs, or submitting production
statistics.

## Required reading

1. `docs/parallel-sessions.md`
2. `docs/parallel-sessions/MASTER_PLAN.md`
3. `docs/parallel-sessions/cosmic-proton-bin5-recovery-design.md`
4. `docs/parallel-sessions/cosmic-proton-bin5-recovery.md`
5. `docs/parallel-sessions/cosmic-slurm-array.md`
6. `CODING_STANDARDS.md`

## Writable scope

- Create `NNBAR_Detector/slurm/cosmic_proton_bin5_thread_probe.sbatch`.
- Update `docs/parallel-sessions/MASTER_PLAN.md` status notes for this lane
  only.
- Add a short proton-bin5 handoff note to
  `docs/parallel-sessions/cosmic-slurm-array.md` only if the wrapper is
  verified.

Do not edit reconstruction code, detector C++ source, Geant4/G4GPU code,
macros, old recovery scripts, or any production data/output directory. Do not
submit a SLURM job in this compact unit; `sbatch --test-only` is allowed.

## One compact-safe iteration

1. Re-read the required docs and run the LUNARC socket guard before remote
   checks:
   ```bash
   rtk proxy bash -lc 'ssh -O check lunarc 2>/dev/null && echo "Connected" || /Users/billy/lunarc-init.sh'
   ```
2. Inspect the active checkout's existing cosmic SLURM wrappers before writing
   the new file. Reuse the current binary/module/output conventions; do not
   invent a new command surface.
3. Create `NNBAR_Detector/slurm/cosmic_proton_bin5_thread_probe.sbatch` with an
   early guard:
   ```bash
   if [[ "${PROTON_BIN5_THREAD_PROBE_APPROVED:-NO}" != "YES" ]]; then
       echo "Set PROTON_BIN5_THREAD_PROBE_APPROVED=YES to run this diagnostic."
       exit 2
   fi
   ```
4. Implement exactly eight array tasks, pairing each failed seed/cap path with
   both thread counts:

   | array task | source task | cap | seeds | threads |
   | ---: | --- | ---: | --- | ---: |
   | 0 | `3046812_1` | 100 | `1211161,2262629` | 1 |
   | 1 | `3046812_1` | 100 | `1211161,2262629` | 4 |
   | 2 | `3046812_2` | 250 | `1318440,2395842` | 1 |
   | 3 | `3046812_2` | 250 | `1318440,2395842` | 4 |
   | 4 | `3046812_5` | 500 | `1636877,2791681` | 1 |
   | 5 | `3046812_5` | 500 | `1636877,2791681` | 4 |
   | 6 | `3046812_6` | 1000 | `1750106,2931544` | 1 |
   | 7 | `3046812_6` | 1000 | `1750106,2931544` | 4 |

5. Write outputs only under a fresh namespaced folder such as
   `build_lunarc/output/cosmic_proton_bin5/thread_probe_${SLURM_ARRAY_TASK_ID}`
   (or the active checkout's equivalent output root). Never overwrite the root
   proton-bin5 file, first recovery shards, or `second_diagnostic_*` folders.
6. Log task id, source task, cap, seed pair, thread count, output folder, macro
   path, date, hostname, and the exact follow-up `sacct`/row-count commands a
   later pane should run.
7. Verify locally and remotely without submission:
   ```bash
   rtk proxy bash -lc 'bash -n NNBAR_Detector/slurm/cosmic_proton_bin5_thread_probe.sbatch'
   rtk proxy bash -lc 'PROTON_BIN5_THREAD_PROBE_APPROVED=NO bash NNBAR_Detector/slurm/cosmic_proton_bin5_thread_probe.sbatch >/tmp/proton_thread_probe_guard.out 2>&1; test $? -eq 2; grep -F PROTON_BIN5_THREAD_PROBE_APPROVED /tmp/proton_thread_probe_guard.out'
   rtk proxy ssh lunarc "cd /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim && sbatch --test-only --array=0-7 NNBAR_Detector/slurm/cosmic_proton_bin5_thread_probe.sbatch"
   ```

## Stop condition

Stop after the guarded wrapper exists, syntax/guard/test-only checks pass, and
`MASTER_PLAN.md` records this lane as `DONE` or records the concrete blocker.
Do not submit the diagnostic array. A later explicitly authorized compact unit
must decide whether to run the probe by setting
`PROTON_BIN5_THREAD_PROBE_APPROVED=YES`.

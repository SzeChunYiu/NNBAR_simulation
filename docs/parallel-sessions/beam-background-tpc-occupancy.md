# Lane: beam-background-tpc-occupancy

## Goal

Make the Appendix A beam-induced background and TPC occupancy assumptions
machine-auditable before any beam-background or TPC-rate claims are promoted.
This first compact-safe iteration produces an evidence report and blocker list;
do **not** run new simulations.

## Writable scope

- Create: `docs/reports/beam_background_tpc_occupancy.md`
- Optional helper only if it stays under 200 lines:
  `scripts/verify_beam_background_occupancy.py`
- Modify only for lane status: `docs/parallel-sessions/MASTER_PLAN.md`

Forbidden:

- Do not submit SLURM jobs or run detector simulations.
- Do not edit production C++ or Python reconstruction code in this audit-only
  iteration.
- Do not invent sample directories, commands, absorber settings, or table
  values; unresolved evidence must be marked `OPEN:`.
- Do not mark thesis Appendix A tables reproduced unless the input sample,
  command, output artifact, and normalization are all verified in this worktree.

## Required reading

1. `docs/parallel-sessions.md`
2. `docs/parallel-sessions/MASTER_PLAN.md`
3. `CODING_STANDARDS.md`
4. `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/12_Appendix_1.tex`
5. `docs/rebuild_plans/03_dataset_registry.md`
6. `docs/rebuild_plans/10_macro_and_sample_inventory.md`
7. `docs/rebuild_plans/45_systematics_taxonomy.md`

Before committing any file, function, path, or command claim, apply the verifier
rules in `docs/parallel-sessions.md`. Prefer quoted grep output over line-number
claims.

## One compact-safe iteration

1. Claim the lane by changing its MASTER_PLAN row from `NEXT` to `RUNNING` and
   committing that status-only change.
2. Verify the evidence files and current simulation surfaces before citing them:
   ```bash
   rtk proxy ls \
     "/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/12_Appendix_1.tex" \
     NNBAR_Detector/src/core/DetectorConstruction.cc \
     NNBAR_Detector/src/detector/beampipe_geometry.cc \
     NNBAR_Detector/slurm/run_cosmic_array.slurm \
     nnbar_reconstruction/config/nnbar_geometry.yaml
   rtk proxy grep -n -i "B4C\|LiF\|Cd\|50 ns\|25.*mu\|occupancy" \
     "/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/12_Appendix_1.tex"
   ```
3. Create `docs/reports/beam_background_tpc_occupancy.md` with these sections:
   - thesis Appendix A inputs: absorber configurations, beam-stop/default
     material assumptions, particle-intensity tables, and the TPC drift-time
     occupancy estimate;
   - current repo inventory: which checked files/macros/scripts could reproduce
     or configure those assumptions, and which surfaces are absent;
   - reproducibility blockers: incoming neutron dataset/version, random seeds,
     scorer definitions, absorber/material toggles, normalization, output table
     artifacts, and TPC occupancy calculation;
   - next smallest implementation task for turning the audit into an executable
     reproduction or fail-closed validator.
4. If you add the optional helper, keep it read-only and fail-closed: it may parse
   expected labels/numbers from Appendix A and check for local files, but it must
   not claim scientific reproduction.
5. Mark the MASTER_PLAN row `DONE` only after the report exists, touched files are
   under the file cap, and the notes summarize the remaining blockers.

## Verification command

```bash
rtk proxy wc -l docs/reports/beam_background_tpc_occupancy.md
rtk proxy grep -n "OPEN:\|B4C\|LiF\|Cd\|50 ns\|25"   docs/reports/beam_background_tpc_occupancy.md
# If the optional helper exists:
rtk python scripts/verify_beam_background_occupancy.py
rtk proxy wc -l scripts/verify_beam_background_occupancy.py
```

## Stop condition

Stop after committing the report and MASTER_PLAN status update, or after recording
a concrete blocker with `OPEN:` evidence. Leave any new simulation campaign,
SLURM submission, or production geometry/source-code change as a separate future
task.

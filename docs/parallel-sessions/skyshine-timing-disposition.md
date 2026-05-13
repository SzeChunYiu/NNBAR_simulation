# Lane: skyshine-timing-disposition

## Goal

Document the project's disposition of skyshine / groundshine: confirm it is
already covered by the cosmic + beam-background tasks via the Ch. 3 5 ms
fast-neutron timing cut, OR record an explicit blocker entry if not. Output is
an audit report plus a structured-blocker check (read-only otherwise). See
MASTER_PLAN.md row "Skyshine and ESS timing-cut disposition".

## Files

- Create: `docs/reports/skyshine_timing_disposition.md` (<= 300 lines)
- Modify (only if a natural extension exists, otherwise read-only):
  `nnbar_reconstruction/analysis/timing_window_audit.py`
- Update: `docs/parallel-sessions/MASTER_PLAN.md` (row status only)
- Read-only: `docs/reports/beam_background_tpc_occupancy.md`, existing
  timing-window code under `nnbar_reconstruction/analysis/`,
  `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/3_*.tex` (Ch. 3).

Do not edit C++. Do not submit SLURM. No simulation runs.

## Implementation steps

1. Re-read `docs/parallel-sessions.md`, this spec, `beam_background_tpc_occupancy.md`,
   `CODING_STANDARDS.md`, and the existing `timing_window_audit.py`.
2. Survey: grep for `skyshine`, `groundshine`, `5 ms`, `fast_neutron`,
   `timing_cut` across `nnbar_reconstruction/` and `docs/`. Record each hit
   plus context in the report.
3. Decide disposition for each skyshine source: (a) **covered** if the existing
   cosmic + beam-background pipeline applies the 5 ms timing cut at the right
   place, citing the file:line, OR (b) **blocked** with a precise gap statement.
4. Write `docs/reports/skyshine_timing_disposition.md` with sections:
   `Scope`, `Ch. 3 reference`, `Evidence inventory`, `Disposition` (per-source
   table), `Structured blockers` (if any), `Conclusion`.
5. If a natural extension exists in `timing_window_audit.py`, add a
   `skyshine_disposition_unverified` structured-blocker emitter that loads the
   disposition table and surfaces unresolved rows. Otherwise leave the module
   untouched and note it in the report.
6. Update MASTER_PLAN row: DONE (covered) or BLOCKED with concrete reason.

## Verification

```bash
rtk python -m pytest tests/ -k 'timing_window' -q
rtk zsh -lc 'python -m pytest tests/ -x -q 2>&1 | tail -20'
rtk wc -l docs/reports/skyshine_timing_disposition.md nnbar_reconstruction/analysis/timing_window_audit.py docs/parallel-sessions/MASTER_PLAN.md
```

Expected: existing timing-window tests stay green; report <= 300 lines; if the
audit module was edited it stays <= 500 lines.

## Stop condition

One compact-safe iteration: write the disposition report, optionally extend
the audit module with a structured-blocker emitter, update MASTER_PLAN row,
commit, stop. Do NOT expand into a new skyshine simulation campaign.

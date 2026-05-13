# Lane: photon-conversion-map

## Goal

Reproduce or fail-closed-audit the Ch. 5 photon-conversion fractions for a
100 MeV mono-energetic photon sample: **4.1% silicon**, **23.1% beampipe**,
**5.0% TPC**, **18.2% scintillator**, **49.6% lead glass**. If a 100 MeV
mono-photon sample does not already exist on disk, emit structured blockers
rather than launching new simulations. See MASTER_PLAN.md row
"Photon conversion map reproduction".

## Files

- Create: `nnbar_reconstruction/analysis/photon_conversion_audit.py` (<= 500 lines)
- Create: `tests/test_photon_conversion_audit.py` (<= 300 lines)
- Update: `docs/parallel-sessions/MASTER_PLAN.md` (row status only)
- Read-only: `nnbar_reconstruction/analysis/geometry_constants.py`,
  `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/5_*.tex` (Ch. 5),
  any existing photon Parquet under `build_lunarc/output/photon_*` on LUNARC.

Do not edit C++. Do not submit SLURM. Do not regenerate photon samples.

## Implementation steps

1. Re-read `docs/parallel-sessions.md`, this spec, `geometry_constants.py`,
   `CODING_STANDARDS.md`.
2. Define `THESIS_CH5_CONVERSION_FRACTIONS = {"silicon": 0.041, "beampipe":
   0.231, "tpc": 0.050, "scintillator": 0.182, "leadglass": 0.496}` as the
   pinned reference, with a doc-string citing Ch. 5.
3. Implement `discover_photon_sample(search_root) -> Optional[Path]` that
   looks for an existing 100 MeV mono-photon Parquet. If none, return None and
   the audit emits a `sample_missing` blocker. NEVER trigger a sim.
4. Implement `audit_conversion_fractions(parquet_path) -> AuditResult` that
   bins the first interaction subdetector (using `geometry_constants`), divides
   by total photons, and compares to the pinned fractions with a tolerance
   (default 1 absolute percentage point). Emit `conversion_fractions_unverified`
   on any per-volume mismatch with the actual vs expected delta in the reason.
5. Add `run_audit(search_root) -> AuditResult` orchestrating the above and
   producing one structured object suitable for MASTER_PLAN reporting.
6. Tests: (a) `sample_missing` path when search_root is empty,
   (b) synthetic Parquet matching all 5 fractions returns no blockers,
   (c) one-volume mismatch produces a single `conversion_fractions_unverified`
   blocker with the offending volume name in the reason.
7. Update MASTER_PLAN row with audit result (DONE, or BLOCKED + reason).

## Verification

```bash
rtk python -m pytest tests/test_photon_conversion_audit.py -q
rtk zsh -lc 'python -m pytest tests/ -x -q 2>&1 | tail -20'
rtk wc -l nnbar_reconstruction/analysis/photon_conversion_audit.py tests/test_photon_conversion_audit.py docs/parallel-sessions/MASTER_PLAN.md
```

Expected: tests pass; module and test each <= 500 lines.

## Stop condition

One compact-safe iteration: implement audit + tests, run, update MASTER_PLAN,
commit, stop. If `sample_missing` blocker fires, leave row BLOCKED with the
reason; do NOT submit any new photon simulation in this lane.

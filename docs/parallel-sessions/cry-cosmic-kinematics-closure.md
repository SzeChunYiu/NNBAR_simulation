# Lane: cry-cosmic-kinematics-closure

## Goal

Fail-closed audit (no new simulations) of every cosmic bin Parquet output
already produced. For each `(particle, energy_bin)`, verify the generated
kinetic-energy distribution, zenith-angle distribution, and rate normalization
match CRY thesis Ch. 6 expected shapes and 3-year expected counts. See
MASTER_PLAN.md row "CRY cosmic kinematics and rate closure".

## Files

- Create: `nnbar_reconstruction/analysis/cry_kinematics_audit.py` (<= 500 lines)
- Create: `tests/test_cry_kinematics_audit.py` (<= 300 lines)
- Update: `docs/parallel-sessions/MASTER_PLAN.md` (row status only)
- Read-only: existing LUNARC `build_lunarc/output/cosmic_*/Particle_output_0.parquet`,
  `docs/parallel-sessions/cry-integration.md` (Eq. 6.1 + N_{i,j} table),
  `docs/parallel-sessions/cosmic-weight-analysis.md`

Do not edit C++. Do not submit SLURM. Do not regenerate Parquet inputs.

## Implementation steps

1. Re-read `docs/parallel-sessions.md`, this spec, `cry-integration.md`,
   `CODING_STANDARDS.md`.
2. Define a `CryKinematicsAudit` dataclass with structured-blocker fields:
   `ch6_3yr_count_unverified`, `zenith_distribution_unverified`,
   `ke_distribution_unverified`, `parquet_missing`, `bin_underfilled`.
3. Implement `audit_bin(particle, ebin_idx, parquet_path) -> AuditResult` that:
   - loads the Parquet,
   - histograms KE inside [E_min, E_max] and asserts shape ~ E^{-spectral_index}
     (allow tolerance; otherwise emit `ke_distribution_unverified` with reason),
   - histograms zenith and compares to cos^2(theta) (CRY default) with chi-square,
   - computes expected 3-yr count from N_{i,j} and detector live time; emit
     `ch6_3yr_count_unverified` if the source N_{i,j} or live-time is not
     directly citeable from cry-integration.md.
4. Add a top-level `run_audit(output_dir)` that iterates the 27 nonzero bins
   and returns a list of `AuditResult`; never raises on missing input — emits
   `parquet_missing` blocker and continues.
5. Tests must cover: (a) all-blocker path when no Parquet exists, (b) synthetic
   in-memory Parquet that satisfies a single bin to prove the green path,
   (c) blocker emission when a bin contains fewer than 1000 events.
6. Run pytest; if green, append a one-line audit summary to MASTER_PLAN.md.

## Verification

```bash
rtk python -m pytest tests/test_cry_kinematics_audit.py -q
rtk zsh -lc 'python -m pytest tests/ -x -q 2>&1 | tail -20'
rtk wc -l nnbar_reconstruction/analysis/cry_kinematics_audit.py tests/test_cry_kinematics_audit.py docs/parallel-sessions/MASTER_PLAN.md
```

Expected: focused tests pass; full suite stays green; module and test file each
remain <= 500 lines.

## Stop condition

One compact-safe iteration: implement audit + tests, run, update MASTER_PLAN
row, commit, stop. Do NOT trigger any CRY regeneration even if blockers fire.

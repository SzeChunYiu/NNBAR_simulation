# Lane: signal-sample-kinematics

## Goal

Add a fail-closed kinematic audit helper that, given an MCPL or Parquet
annihilation signal sample, checks the Ch. 6 thesis distributions: foil
vertex radial distribution, photon/pi+-/proton kinetic-energy peaks, and
opening-angle biases. The thesis uses 50k events; the current plan only
verified a 1000-event run. This lane only adds the audit + tests — no
new simulations and no SLURM. The 50k sample is gated by the simulation
team; the audit must emit structured blockers when the sample is absent
or under-statistics.

## Files

- Prefer creating: `nnbar_reconstruction/analysis/signal_kinematics_audit.py` (<=500 lines)
- Test: `tests/test_signal_kinematics_audit.py`
- Read-only references:
  - LUNARC sample (do not copy): `/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/output/Particle_output_0.parquet` (1000-event run)
  - Ch. 6 extracted thesis text under `NNBAR_THESIS_EXTRACT_DIR` (skip-safe if unset)
  - `docs/parallel-sessions/hibeam-gnn-feature-contract.md` for fail-closed audit pattern
- Update: `docs/parallel-sessions/MASTER_PLAN.md` status/notes only (row
  `Signal sample kinematics validation` in PROPOSED TASKS — promote to a
  `NEXT`/`DONE` row in the NNBAR Reconstruction table on completion)

Do not edit C++, do not run new simulations, do not submit SLURM jobs unless
explicitly authorized. Do not invent numeric KE peak values — peaks must be
supplied by extracted Ch. 6 text or be blocked.

## Implementation steps

1. Re-read `docs/parallel-sessions.md`, this spec, `CODING_STANDARDS.md`, and
   the fail-closed pattern in
   `docs/parallel-sessions/hibeam-gnn-feature-contract.md`.
2. Define the audit's required evidence keys per sample: `sample_path`,
   `n_events`, `foil_radial_distribution`, `photon_ke_peak`,
   `pion_plus_ke_peak`, `pion_minus_ke_peak`, `proton_ke_peak`, and
   `opening_angle_distribution`. Add a `thesis_reference` field linking each
   to its Ch. 6 source.
3. Write failing tests first using small synthetic Parquet/MCPL-like
   fixtures: an evidence dict missing the file path yields `sample_missing`;
   a present sample without verified KE peaks yields `KE_peak_not_verified`;
   a present sample without radial-distribution evidence yields
   `vertex_distribution_unverified`; a complete (synthetic) evidence dict
   yields zero blockers.
4. Implement the audit as pure data inspection: load Parquet via existing
   `nnbar_reconstruction/data_pipeline/` readers when available, otherwise
   accept an in-memory evidence dict. Do not call MCPL converters or shell
   out. Do not auto-fit peak values — record whether thesis-side values are
   present and whether the sample provides enough events to compare.
5. Treat statistics as a blocker: `n_events < thesis_50k` must emit
   `under_statistics` rather than silently passing. Do not promote a 1000-event
   run to thesis-level validation.
6. Run focused and full pytest; confirm touched files are <=500 lines and the
   audit holds fail-closed on the current local repo (no thesis 50k sample
   present).
7. Update this lane's `MASTER_PLAN.md` row to `DONE` only after tests pass
   and blocker categories are recorded in the row notes.

## Verification

Run:

```bash
rtk python -m pytest tests/test_signal_kinematics_audit.py -q
rtk zsh -lc 'python -m pytest tests/ -x -q 2>&1 | tail -20'
rtk wc -l nnbar_reconstruction/analysis/signal_kinematics_audit.py tests/test_signal_kinematics_audit.py docs/parallel-sessions/MASTER_PLAN.md
rtk proxy bash -lc 'grep -nE "subprocess|os\\.system|sbatch|ssh lunarc" nnbar_reconstruction/analysis/signal_kinematics_audit.py tests/test_signal_kinematics_audit.py || echo OK_NO_SIDE_EFFECT'
```

Expected: focused tests pass; full test command exits 0; touched files
<=500 lines; no SLURM / SSH / subprocess side-effects in the audit module
or its tests; current local audit remains intentionally fail-closed with
`sample_missing` / `under_statistics` / `KE_peak_not_verified` /
`vertex_distribution_unverified` because the 50k sample is not local.

## Stop condition

Stop after one compact audit-helper + tests + MASTER_PLAN row update is
committed. Do not stage the 50k sample, do not run simulations, and do
not auto-fit Ch. 6 numeric peaks; leave each as a named blocker.

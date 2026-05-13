# π⁰ vertex acceptance summary

Generated: 2026-05-12 by pane-2 worker-2 lane-swap from `codex-tasks/recon/worker-6.txt`.

## Scope

This compact read-only iteration loaded the already-derived reconstructed π⁰ vertex-scan Parquets in `build_lunarc/output/pi0_reco_response/` and summarized the requested acceptance observables. No SLURM job, C++ source, reconstruction code, cuts, constants, or Parquet outputs were changed.

## Inputs checked

The eight expected response Parquets were present and readable:

- fixed radii: `pi0_reco_vertex_r0mev.parquet`, `pi0_reco_vertex_r5mev.parquet`, `pi0_reco_vertex_r10mev.parquet`, `pi0_reco_vertex_r15mev.parquet`, `pi0_reco_vertex_r20mev.parquet`, `pi0_reco_vertex_r25mev.parquet`, `pi0_reco_vertex_r30mev.parquet`
- disk sample: `pi0_reco_vertex_disk_r30.parquet`

Each file has the required audit columns `truth_vertex_r_cm`, `pi0_mass_mev`, `opening_angle_deg`, `reco_total_energy_mev`, and `n_pi0_candidates`.

## Fixed-radius acceptance

| Truth radius | Events | Sum `n_pi0_candidates` | `n_pi0_candidates / n_events` | Peak π⁰ mass [MeV] | Efficiency relative to r=0 |
| --- | ---: | ---: | ---: | --- | --- |
| 0 cm | 500 | 0 | 0.000000 | not measured | baseline is zero |
| 5 cm | 500 | 0 | 0.000000 | not measured | undefined: 0/0 |
| 10 cm | 500 | 0 | 0.000000 | not measured | undefined: 0/0 |
| 15 cm | 500 | 0 | 0.000000 | not measured | undefined: 0/0 |
| 20 cm | 500 | 0 | 0.000000 | not measured | undefined: 0/0 |
| 25 cm | 500 | 0 | 0.000000 | not measured | undefined: 0/0 |
| 30 cm | 500 | 0 | 0.000000 | not measured | undefined: 0/0 |

The requested relative efficiency curve cannot be promoted because the r=0 reference efficiency is zero. The correct fail-closed result is therefore not a flat acceptance curve; it is an unresolved reconstruction-response blocker.

## Disk sample cross-check

| Sample | Events | Sum `n_pi0_candidates` | `n_pi0_candidates / n_events` | Truth radius range [cm] | Peak π⁰ mass [MeV] |
| --- | ---: | ---: | ---: | --- | --- |
| disk r ≤ 30 cm | 5000 | 0 | 0.000000 | 0.614125–29.996538 | not measured |

The disk sample independently confirms zero reconstructed π⁰ candidates in the existing derived response output.

## Blockers and disposition

- `radius_bin_no_reco`: every fixed-radius bin has events but zero reconstructed π⁰ candidates.
- `relative_efficiency_zero_baseline`: r=0 efficiency is zero, so all radius/r=0 efficiency ratios are undefined.
- `mass_peak_unmeasured`: no bin has reconstructed candidates, so no π⁰ mass peak can be estimated.

Disposition: keep Study 1 fail-closed until the reconstruction response produces nonzero π⁰ candidates for at least the r=0 reference sample and one displaced-radius bin. This summary adds evidence only; it does not retune reconstruction.

## Verification evidence

- Parquet loader command computed the row counts, candidate sums, truth-radius ranges, schema presence, and zero mass-peak availability directly from `build_lunarc/output/pi0_reco_response/`.
- File cap check: this report is below the 500-line lane limit.
- Worker verification command: `python -m pytest tests/ -x -q 2>&1 | tail -20` reported 260 passed / 2 skipped in 10.25s.
- Queue validator: `bash scripts/validate-csup-queues.sh` scanned 27 files / 30 prompt lines with 0 failures.

# Lane: pi0-reco-on-vertex-scan

## Goal

Run `pi0_reco_driver.py` on the 8 newly-produced vertex scan samples, then run
`pi0_vertex_response_audit.py` on the resulting reco Parquets.  This closes the
Study 1 loop from `pi0-parametric-studies.md`.

## Context

Vertex scan samples are at:
```
build_lunarc/output/studies/
  pi0_vertex_scan_r0mev/
  pi0_vertex_scan_r5mev/
  pi0_vertex_scan_r10mev/
  pi0_vertex_scan_r15mev/
  pi0_vertex_scan_r20mev/
  pi0_vertex_scan_r25mev/
  pi0_vertex_scan_r30mev/
  pi0_vertex_disk_r30/   (5000-event disk average)
```

Each directory has `LeadGlass_output_0.parquet`, `Scintillator_output_0.parquet`,
`Particle_output_0.parquet`.  Vertex truth position columns are in
`Particle_output_0.parquet` as `x, y, z` (cm).

## Required output

Run `nnbar_reconstruction/analysis/pi0_reco_driver.py` (or its equivalent logic)
on each vertex scan sample to produce:

```
build_lunarc/output/pi0_reco_response/
  pi0_reco_vertex_r0mev.parquet
  pi0_reco_vertex_r5mev.parquet
  ...
  pi0_reco_vertex_r30mev.parquet
  pi0_reco_vertex_disk_r30.parquet
```

Each reco Parquet MUST include a `truth_vertex_r_cm` column computed from the
truth vertex x,y in the Particle_output: `truth_vertex_r_cm = sqrt(x**2 + y**2)`.

## Then run the audit

After producing the reco Parquets, run `pi0_vertex_response_audit.py` on them.
Write results to `docs/reports/pi0_vertex_response_results.md`.

The audit expects:
- Column `truth_vertex_r_cm` present
- pi0_mass_mev, opening_angle_deg, reco_total_energy_mev columns
- If any blockers fire, log them with their codes (e.g., `VERTEX_SAMPLE_MISSING`,
  `VERTEX_RECO_COLUMN_MISSING`)

## Constraints

- NO SLURM submissions
- Read-only on simulation outputs
- Write to `build_lunarc/output/pi0_reco_response/` and `docs/reports/`
- No changes to reconstruction code cuts

# LeadGlass energy containment vs vertex radius

Date: 2026-05-12
Lane: worker-1 / `lg-energy-containment`

## Method

For each sample, this audit reads local Parquet files only and performs no
SLURM, C++, reconstruction-code, raw-data, or training changes. The LeadGlass
energy column is `eDep` in MeV. Per event, the audit sums `LeadGlass_output_0`
by `Event_ID`, joins to the `PID=111` row from `Particle_output_0`, and computes

```text
E_total = pi0_KE + 134.977 MeV
containment = sum(LeadGlass eDep) / E_total
```

Events with no LeadGlass row are retained from `Particle_output_0` and assigned
zero LeadGlass energy. The vertex-scan samples all have mean pi0 KE of 150.000
MeV; the mono-energy samples have the expected 50, 150, and 250 MeV gun kinetic
energies.

## Mono-energy containment

| sample | n_events | E_gun_MeV | E_total_MeV | mean_LG_eDep_MeV | mean_containment | std | fraction_>80% |
|---|---:|---:|---:|---:|---:|---:|---:|
| mono_50 | 200 | 50.0 | 184.977 | 105.660 | 0.571 | 0.308 | 0.275 |
| mono_150 | 200 | 150.0 | 284.977 | 176.978 | 0.621 | 0.298 | 0.365 |
| mono_250 | 200 | 250.0 | 384.977 | 244.895 | 0.636 | 0.282 | 0.335 |

## Vertex-radius containment at 150 MeV

| sample | n_events | LG-hit events | E_gun_MeV | E_total_MeV | mean_containment | std | fraction_>80% | p10 | p90 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| r0 | 500 | 499 | 150.0 | 284.977 | 0.593 | 0.311 | 0.326 | 0.122 | 0.981 |
| r5 | 500 | 500 | 150.0 | 284.977 | 0.588 | 0.299 | 0.292 | 0.139 | 0.978 |
| r10 | 500 | 495 | 150.0 | 284.977 | 0.576 | 0.307 | 0.306 | 0.124 | 0.980 |
| r15 | 500 | 496 | 150.0 | 284.977 | 0.583 | 0.299 | 0.294 | 0.156 | 0.978 |
| r20 | 500 | 496 | 150.0 | 284.977 | 0.594 | 0.305 | 0.336 | 0.120 | 0.981 |
| r25 | 500 | 500 | 150.0 | 284.977 | 0.603 | 0.297 | 0.322 | 0.137 | 0.982 |
| r30 | 500 | 499 | 150.0 | 284.977 | 0.591 | 0.297 | 0.302 | 0.157 | 0.981 |
| disk_r30 | 5000 | 4977 | 150.0 | 284.977 | 0.605 | 0.297 | 0.326 | 0.165 | 0.982 |

## Key question: does containment drop at large radius?

The fixed-radius scan does **not** show a large-radius containment loss in these
local samples. Mean containment changes from 0.593 at `r0` to 0.591
at `r30`, a difference of -0.002. Across the seven fixed radii the minimum
mean is 0.576 at `r10` and the maximum is
0.603 at `r25`. The disk sample within
30 cm has mean containment 0.605, consistent with the
fixed-radius range rather than indicating a strong edge-loss tail.

The `fraction_>80%` column is stable rather than radius-degraded: fixed-radius
samples range from 0.292 to 0.336, and the disk sample is 0.326. Thus the
large-radius question is not the limiting effect in these samples. The mean
total-LG containment remains around 0.58--0.61, below an 80% mean-containment
benchmark in this geometry/output definition. This agrees with the previous
LeadGlass cluster-topology audit scale (150 MeV mono mean LG energy ≈177 MeV
against a 284.977 MeV pi0 total energy).

## Inputs

- `build_lunarc/output/pi0_mono_50mev/LeadGlass_output_0.parquet`, `build_lunarc/output/pi0_mono_50mev/Particle_output_0.parquet` — n_events=200, KE range 50.000--50.000 MeV
- `build_lunarc/output/pi0_mono_150mev/LeadGlass_output_0.parquet`, `build_lunarc/output/pi0_mono_150mev/Particle_output_0.parquet` — n_events=200, KE range 150.000--150.000 MeV
- `build_lunarc/output/pi0_mono_250mev/LeadGlass_output_0.parquet`, `build_lunarc/output/pi0_mono_250mev/Particle_output_0.parquet` — n_events=200, KE range 250.000--250.000 MeV
- `build_lunarc/output/studies/pi0_vertex_scan_r0mev/LeadGlass_output_0.parquet`, `build_lunarc/output/studies/pi0_vertex_scan_r0mev/Particle_output_0.parquet` — n_events=500, KE range 150.000--150.000 MeV
- `build_lunarc/output/studies/pi0_vertex_scan_r5mev/LeadGlass_output_0.parquet`, `build_lunarc/output/studies/pi0_vertex_scan_r5mev/Particle_output_0.parquet` — n_events=500, KE range 150.000--150.000 MeV
- `build_lunarc/output/studies/pi0_vertex_scan_r10mev/LeadGlass_output_0.parquet`, `build_lunarc/output/studies/pi0_vertex_scan_r10mev/Particle_output_0.parquet` — n_events=500, KE range 150.000--150.000 MeV
- `build_lunarc/output/studies/pi0_vertex_scan_r15mev/LeadGlass_output_0.parquet`, `build_lunarc/output/studies/pi0_vertex_scan_r15mev/Particle_output_0.parquet` — n_events=500, KE range 150.000--150.000 MeV
- `build_lunarc/output/studies/pi0_vertex_scan_r20mev/LeadGlass_output_0.parquet`, `build_lunarc/output/studies/pi0_vertex_scan_r20mev/Particle_output_0.parquet` — n_events=500, KE range 150.000--150.000 MeV
- `build_lunarc/output/studies/pi0_vertex_scan_r25mev/LeadGlass_output_0.parquet`, `build_lunarc/output/studies/pi0_vertex_scan_r25mev/Particle_output_0.parquet` — n_events=500, KE range 150.000--150.000 MeV
- `build_lunarc/output/studies/pi0_vertex_scan_r30mev/LeadGlass_output_0.parquet`, `build_lunarc/output/studies/pi0_vertex_scan_r30mev/Particle_output_0.parquet` — n_events=500, KE range 150.000--150.000 MeV
- `build_lunarc/output/studies/pi0_vertex_disk_r30/LeadGlass_output_0.parquet`, `build_lunarc/output/studies/pi0_vertex_disk_r30/Particle_output_0.parquet` — n_events=5000, KE range 150.000--150.000 MeV

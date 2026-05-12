# π0 mono-sample LeadGlass energy containment

Worker-2 lane-swap checked the local mono-energy π0 samples requested by
`docs/parallel-sessions/pi0-total-energy-containment.md`. No SLURM job, C++, or
reconstruction-code change was run; this report only reads local Parquet outputs
under `build_lunarc/output/`.

## Inputs and method

| Sample | Particle input | LeadGlass input | Particle rows | LeadGlass rows |
|---:|---|---|---:|---:|
| 50 MeV | `build_lunarc/output/pi0_mono_50mev/Particle_output_0.parquet` | `build_lunarc/output/pi0_mono_50mev/LeadGlass_output_0.parquet` | 200 | 467,320 |
| 150 MeV | `build_lunarc/output/pi0_mono_150mev/Particle_output_0.parquet` | `build_lunarc/output/pi0_mono_150mev/LeadGlass_output_0.parquet` | 200 | 772,193 |
| 250 MeV | `build_lunarc/output/pi0_mono_250mev/Particle_output_0.parquet` | `build_lunarc/output/pi0_mono_250mev/LeadGlass_output_0.parquet` | 200 | 1,065,549 |

For each sample, LeadGlass `eDep` was summed by `Event_ID`, joined to the π0
particle row, and divided by `E_total = KE + 134.977 MeV`. Direction dependence
uses `theta = arccos(|w|)` from the particle direction-cosine column.

## Per-sample containment

| n_events | E_gun_MeV | E_total_MeV | pi0 KE sanity | mean_contain | std | frac_90pct |
|---:|---:|---:|---|---:|---:|---:|
| 200 | 50 | 184.977 | PID 111, KE min=max=50.0 | 0.571 | 0.308 | 0.190 |
| 200 | 150 | 284.977 | PID 111, KE min=max=150.0 | 0.621 | 0.298 | 0.225 |
| 200 | 250 | 384.977 | PID 111, KE min=max=250.0 | 0.636 | 0.282 | 0.250 |

All 600 particle events have nonzero LeadGlass deposits. Event-level containment
spans nearly the full geometric acceptance range: the minima are 0.001--0.003,
and the maxima are approximately 1.0 for all three samples.

## 150 MeV direction dependence

| theta_range | mean_contain | std | n_events | frac_90pct |
|---|---:|---:|---:|---:|
| 0-30° | 0.375 | 0.286 | 26 | 0.077 |
| 30-60° | 0.588 | 0.307 | 67 | 0.224 |
| 60-90° | 0.701 | 0.258 | 107 | 0.262 |

Forward-going π0s (`theta < 30°`) do **not** have higher containment in this
sample. The transverse bin (`60-90°`) is highest, consistent with finite
LeadGlass angular coverage: barrel-like trajectories keep more shower energy in
instrumented LeadGlass, while forward trajectories lose more energy out of the
covered volume/end regions.

## Interpretation

The expected barrel containment band in the lane spec (roughly 80--95%) appears
only for the better-contained subset, not for the full isotropic-like event set.
The all-event means are much lower because the direction distribution includes
many forward/intermediate events with partial LeadGlass coverage. The requested
trend "lower energies should be higher" is not observed in the all-event means:
50 MeV averages 0.571, 150 MeV averages 0.621, and 250 MeV averages 0.636.
That difference is smaller than the broad event-by-event geometric spread, so it
should be treated as an acceptance-mixed validation result rather than a shower-
containment-only material-depth conclusion.


# Lane: pi0-total-energy-containment (sim)

## Goal
Verify energy conservation and LG containment for all three mono-energy pi0 samples
(50, 150, 250 MeV). This is a simulation validation check: total LG eDep should be
a fixed fraction of the pi0 total energy (KE + m_pi0).

## Data
- `build_lunarc/output/pi0_mono_50mev/LeadGlass_output_0.parquet`
- `build_lunarc/output/pi0_mono_150mev/LeadGlass_output_0.parquet`
- `build_lunarc/output/pi0_mono_250mev/LeadGlass_output_0.parquet`
- Corresponding `Particle_output_0.parquet` for each (to get pi0 KE)

LG energy column: `eDep` (MeV)
Particle columns: Event_ID, PID, KE (pi0 kinetic energy in MeV), u, v, w (direction cosines)

## Analysis

### Expected total energy per event
- E_total = pi0_KE + m_pi0 = pi0_KE + 134.977 MeV
  - 50 MeV gun: E_total = 184.977 MeV
  - 150 MeV gun: E_total = 284.977 MeV
  - 250 MeV gun: E_total = 384.977 MeV

### Steps
1. Load LG parquet, group by Event_ID: lg_edep_sum = sum(eDep) per event
2. Load Particle_output, verify pi0 KE is exactly gun setting (sanity check)
3. Compute containment = lg_edep_sum / E_total for each event
4. Per sample: mean_containment, std_containment, fraction > 0.9

### Also check: direction-dependent containment
- Load direction cosines (u, v, w) from Particle_output
- Compute polar angle θ = arccos(|w|) from beam axis
- Bin events by θ: 0-30°, 30-60°, 60-90°
- Compute mean containment per θ bin
- Do forward-going pi0s (θ < 30°) have higher containment? (photons may exit endcap)

### Expected values
- Containment should be ~80-95% for barrel hits (π0 going transverse)
- Forward hits may have lower containment due to LG geometry
- Containment should be higher for lower energies (shower fits in LG better)

### Output
Write `docs/reports/pi0_energy_containment_monosamples.md`:
- Table per sample: n_events | E_gun_MeV | E_total_MeV | mean_contain | std | frac_90pct
- Table per θ bin at 150 MeV: theta_range | mean_contain | n_events
- Notes on LG geometry (barrel vs endcap coverage)

## Constraints
- Python only, no SLURM, no code changes
- Read parquets from local `build_lunarc/output/` paths

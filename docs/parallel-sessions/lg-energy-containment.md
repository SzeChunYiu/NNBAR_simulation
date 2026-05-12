# Lane: lg-energy-containment

## Goal
Measure total LeadGlass energy containment for pi0 events across vertex radii and
mono-energy samples. LG acceptance is ~99% at all radii (measured), so containment
fraction is the key efficiency metric.

## Data
- `build_lunarc/output/studies/pi0_vertex_scan_r{0,5,10,15,20,25,30}mev/LeadGlass_output_0.parquet`
- `build_lunarc/output/studies/pi0_vertex_disk_r30/LeadGlass_output_0.parquet`
- `build_lunarc/output/pi0_mono_{50,150,250}mev/LeadGlass_output_0.parquet`

LG column for energy: `eDep` (float64, MeV).

## Analysis

### Expected pi0 total energy
For pi0 (KE=E_gun, rest mass=134.977 MeV):
- E_total = E_gun + 134.977  (e.g. 150 MeV gun → E_total = 284.977 MeV)
- Both decay photons share this energy
- LG containment fraction = sum(eDep) / E_total

### Per-sample steps
1. Load LG parquet, group by Event_ID, sum eDep → total_lg_edep per event
2. Load Particle_output_0.parquet, get pi0 KE (should match gun setting)
3. E_total = pi0_KE + 134.977
4. containment = total_lg_edep / E_total (per event)
5. Compute: mean containment, std, fraction of events with containment > 0.8

### Output
Write `docs/reports/lg_energy_containment.md`:
- Table: sample | E_gun_MeV | E_total_MeV | mean_containment | std | fraction_>80%
- For vertex scan at 150 MeV: table of containment vs radius
- Key question: does containment drop at large radius? (photon shower may miss LG edge)

## Constraints
- Python only, no SLURM, no reco code changes
- Particle_output has columns: Event_ID, PID, KE, angle, x, y, z, u, v, w, weight
- PID=111 is pi0; all entries in Particle_output are pi0 (decay photons not recorded)

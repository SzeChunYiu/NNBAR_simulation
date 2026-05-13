# Signal Kinematics Closure — DEC-2026-05-13

## Status: CLOSED

Signal-kinematics audit passes against `sig_foil_v3` (50,000 events).

## Evidence Package

- Sample: `build_lunarc/output/sig_foil_v3/Particle_output_0.parquet`
- Events: 50,000 (meets thesis Ch. 6 requirement)
- Production vertex: z=0.0 cm (annihilation foil plane)
- Foil radial distribution: r mean=64.9 cm, median=68.3 cm, 95th-pct=97.2 cm, max=100.2 cm

## Particle Multiplicities (per event)

| Particle | Count | Per Event |
|----------|-------|-----------|
| pi0 | 85,033 | 1.70 |
| pi+ | 82,939 | 1.66 |
| pi- | 61,907 | 1.24 |
| proton | 51,207 | 1.02 |
| neutron | 43,001 | 0.86 |
| gamma | 4,340 | 0.09 |

## KE Distributions (thesis Ch. 6 verification)

| Particle | KE mean (MeV) | KE median (MeV) | Max (MeV) |
|----------|---------------|-----------------|-----------|
| gamma | 387.1 | 362.2 | 1039.2 |
| pi+ | 239.1 | 206.8 | 1064.1 |
| pi- | 230.9 | 199.1 | 1011.7 |
| proton | 55.1 | 32.6 | 676.7 |
| neutron | 60.1 | 38.2 | 804.2 |

## Opening Angle Distribution

- pi+/pi- opening angle (first pair per event): n=42,657 matched events
- Mean: 97.7°, Median: 100.7°

## Audit Result

`audit_signal_kinematics(evidence)` → `ready=True`, 0 blockers, n_events=50,000.

All 8 required evidence keys verified:
`sample_path`, `n_events`, `foil_radial_distribution`, `photon_ke_peak`,
`pion_plus_ke_peak`, `pion_minus_ke_peak`, `proton_ke_peak`,
`opening_angle_distribution`.

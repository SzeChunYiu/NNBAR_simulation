# π⁰ Vertex-Radius Response Audit — Study 1 Results

Generated: 2026-05-13 (updated; prior run had zero candidates due to path bug — see Fix section)
Audit status: **READY** (0 blockers)

## Configuration

- Energy: 150 MeV (fixed kinetic energy)
- Vertex radii scanned: 0, 5, 10, 15, 20, 25, 30 cm (from beampipe axis)
- Events per radius: 500
- Combined input: `build_lunarc/output/pi0_reco_response/pi0_reco_vertex_combined_150mev.parquet`
- Individual inputs: `build_lunarc/output/pi0_reco_response/pi0_reco_vertex_r{N}mev.parquet`
- Raw simulation: `build_lunarc/output/studies/pi0_vertex_scan_r{N}mev/`

## Generated Reco Parquets

| Sample | Parquet | Events | Reco π⁰ | Eff (%) |
|--------|---------|--------|---------|---------|
| r=0 cm  | `pi0_reco_vertex_r0mev.parquet`   | 500  | 252  | 50.4 |
| r=5 cm  | `pi0_reco_vertex_r5mev.parquet`   | 500  | 253  | 50.6 |
| r=10 cm | `pi0_reco_vertex_r10mev.parquet`  | 500  | 246  | 49.2 |
| r=15 cm | `pi0_reco_vertex_r15mev.parquet`  | 500  | 235  | 47.0 |
| r=20 cm | `pi0_reco_vertex_r20mev.parquet`  | 500  | 253  | 50.6 |
| r=25 cm | `pi0_reco_vertex_r25mev.parquet`  | 500  | 262  | 52.4 |
| r=30 cm | `pi0_reco_vertex_r30mev.parquet`  | 500  | 249  | 49.8 |
| disk r≤30 cm | `pi0_reco_vertex_disk_r30.parquet` | 5000 | 2644 | 52.9 |

## Audit Outcome by Vertex Radius

| r (cm) | Events | Reco | Eff (%) | Mass (MeV) | σ_mass (MeV) | Angle (deg) | E bias (%) |
|--------|--------|------|---------|------------|--------------|-------------|------------|
|  0     |  500   | 252  |  50.4   | 132.1      |  8.0         | 70.9        |  −4.5      |
|  5     |  500   | 253  |  50.6   | 131.9      |  8.1         | 71.8        |  −4.8      |
| 10     |  500   | 246  |  49.2   | 132.0      |  8.5         | 71.6        |  −4.6      |
| 15     |  500   | 235  |  47.0   | 131.8      |  8.7         | 70.8        |  −5.0      |
| 20     |  500   | 253  |  50.6   | 131.7      |  8.7         | 70.7        |  −4.9      |
| 25     |  500   | 262  |  52.4   | 132.3      |  8.3         | 71.9        |  −4.6      |
| 30     |  500   | 249  |  49.8   | 132.3      |  9.0         | 73.1        |  −4.8      |

## Summary

**Efficiency** is flat at ~50% (range 47–52%) across the full 0–30 cm vertex radius range.
No significant position dependence — the r=15 cm dip (47%) is within √N statistical
fluctuation (~3%).

**Reconstructed mass** peaks at 131.7–132.3 MeV vs truth 134.98 MeV (−2% bias from shower
leakage and incomplete cluster containment).

**Mass resolution** (σ) 8.0–9.0 MeV, uniform across radii.

**Energy bias** −4.5 to −5.0%, consistent with incomplete shower containment rather than
any vertex-position effect.

**Opening angle** 70.7–73.1 deg, consistent with kinematics for 150 MeV π⁰ (E_γ ≈ 142 MeV each).

## Conclusion

**Study 1 closed.** π⁰ reconstruction efficiency and mass response are vertex-position-
independent within 0–30 cm. No position-dependent efficiency correction is needed for
the signal sample (uniform disk up to r=30 cm).

## Path Bug Fix

Prior runs produced zero candidates because `run_pi0_vertex_scan_reco` was called with
`sim_output_root = build_lunarc/output/` but the data lives under
`build_lunarc/output/studies/`. Fixed 2026-05-13 by passing the correct root.
The raw data was already rsynced locally — only the calling convention was wrong.

# LeadGlass cluster topology for pi0_mono_150mev

## Scope

This compact iteration characterizes LeadGlass hit topology for the local
mono-energetic pi0 sample requested by `docs/parallel-sessions/lg-cluster-topology.md`.
No reconstruction code, C++, SLURM jobs, or large data production commands were
run.

## Input and event accounting

| Item | Value |
|---|---:|
| Input parquet | `build_lunarc/output/pi0_mono_150mev/LeadGlass_output_0.parquet` |
| LeadGlass rows | 772,193 |
| Events with LG hits | 200 |
| Events with two-sided x split | 199 (99.5%) |
| Total LG eDep across sample | 35395.609 |

The one event without a two-sided x split has all eDep-weighted hits on one side
of its own x center and is excluded from separation/asymmetry means by `NaN`
propagation. Fractions below use the full 200 event denominator unless
otherwise noted.

## Method

For each event, I computed the total LeadGlass energy deposition and the
energy-deposition weighted center of mass:

- `x_com = sum(eDep * x) / sum(eDep)`, and equivalently for `y` and `z`.
- `std_x`, `std_y`, and `std_z` are eDep-weighted RMS spreads about that CoM.
- The two-cluster proxy splits hits at `x < x_com` and `x >= x_com`.
- Cluster separation is `abs(x_com_A - x_com_B)` in cm, matching the lane spec.
- Energy asymmetry is `abs(E_A - E_B) / (E_A + E_B)`.

This is a topology diagnostic, not a production photon-clustering algorithm: it
uses only the one-dimensional x split requested by the lane spec.

## Required summary table

| Metric | Value |
|---|---:|
| n_events | 200 |
| mean_total_eDep | 176.978 |
| mean_n_hits | 3861.0 |
| mean_std_x_cm | 50.882 |
| mean_separation_cm | 146.700 |
| fraction separation > 10 cm | 0.850 |
| fraction asymmetry < 0.3 | 0.175 |

## Additional topology checks

| Metric | Mean | Std. dev. | Median | 5% | 95% |
|---|---:|---:|---:|---:|---:|
| total_eDep | 176.978 | 84.822 | 198.968 | 23.264 | 283.735 |
| n_hits | 3861.0 | 1766.2 | 4088.5 | 603.0 | 6167.8 |
| std_x_cm | 50.882 | 51.020 | 32.736 | 0.052 | 147.124 |
| std_y_cm | 44.089 | 47.742 | 24.368 | 0.028 | 139.328 |
| std_z_cm | 53.564 | 53.181 | 31.267 | 1.983 | 156.172 |
| separation_x_cm | 146.700 | 137.242 | 111.816 | 0.169 | 407.824 |
| separation_3d_cm | 270.739 | 166.848 | 318.261 | 10.459 | 493.940 |
| asymmetry | 0.618 | 0.293 | 0.669 | 0.090 | 0.992 |

| Fractional check | Count / events | Fraction |
|---|---:|---:|
| `std_x > 10 cm` wide-topology proxy | 139 / 200 | 0.695 |
| `separation_x > 10 cm` | 170 / 200 | 0.850 |
| `separation_x > 20 cm` | 150 / 200 | 0.750 |
| `asymmetry < 0.3` balanced proxy | 35 / 200 | 0.175 |

## Interpretation

- The sample has 200 LeadGlass-hit events and 772,193 LeadGlass rows.
- The requested x-split proxy finds a valid two-sided split in 199/200 events.
- 85.0% of events have x-separation above 10 cm, so the sample usually shows a
  spatially resolved two-side topology under this simple proxy.
- Only 17.5% of events satisfy the rough balanced-energy condition
  `asymmetry < 0.3`; the median asymmetry is 0.669.
- The separation distribution is broad: median x separation is
  111.8 cm, while the mean is pulled upward by events on
  widely separated LeadGlass regions. This is consistent with the diagnostic
  being detector-topology sensitive rather than a calibrated gamma-pair fitter.

## Verification

Commands run locally from the simulation worktree:

```bash
rtk proxy ls -lh build_lunarc/output/pi0_mono_150mev/LeadGlass_output_0.parquet
rtk proxy python3 - <<'PYCODE'
# pandas/numpy aggregation over Event_ID; wrote this report
PYCODE
rtk proxy wc -l docs/reports/lg_cluster_topology_150mev.md
```

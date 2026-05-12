# Photon conversion fraction mismatch audit

Date: 2026-05-12  
Lane: `photon-conversion-fraction-mismatch` / worker-1  
Scope: read-only audit of the staged local `photon_100MeV_conversion` sample;
no simulation, SLURM submission, production code change, or constant retune.

## Inputs inspected

- Audit helper: `nnbar_reconstruction/analysis/photon_conversion_audit.py`
- Staged sample selected by `discover_photon_sample`:
  `build_lunarc/output/photon_100MeV_conversion/Interaction_output_0.parquet`
- Thesis target encoded in the audit helper: silicon 0.041, beampipe 0.231,
  TPC 0.050, scintillator 0.182, lead glass 0.496 with absolute tolerance 0.010.

The selected parquet has 894,560 rows and the columns
`Event_ID`, `Track_ID`, `Parent_ID`, `Name`, `Proc`, `Current_Vol`, `Origin`,
`m`, `KE`, `t`, `x`, `y`, `z`, `px`, `py`, `pz`.  Filtering `Proc == "conv"`
and `Name in {"e+", "e-"}`, then taking the earliest conversion row per
`Event_ID`, yields 49,446 conversion events.

## Audit result

`run_audit("build_lunarc/output/photon_100MeV_conversion")` is fail-closed:

| Volume | Count | Actual fraction | Thesis fraction | Delta | Binomial z vs thesis |
| --- | ---: | ---: | ---: | ---: | ---: |
| silicon | 1,591 | 0.032177 | 0.041000 | -0.008823 | -9.9 |
| beampipe | 9,639 | 0.194940 | 0.231000 | -0.036060 | -19.0 |
| TPC | 1,584 | 0.032035 | 0.050000 | -0.017965 | -18.3 |
| scintillator | 7,557 | 0.152833 | 0.182000 | -0.029167 | -16.8 |
| lead glass | 25,279 | 0.511245 | 0.496000 | +0.015245 | +6.8 |

The helper returns one `conversion_fractions_unverified` blocker.  The
mismatch is not explained by counting statistics: four volumes exceed the
0.010 tolerance, and the beampipe/TPC/scintillator deviations are O(17--19)
standard deviations relative to a binomial draw from the thesis fractions.

## Raw first-conversion volume labels

| Raw `Current_Vol` label | Count | Fraction | Audit canonical label |
| --- | ---: | ---: | --- |
| `LeadGlassPV` | 25,279 | 0.511245 | `leadglass` |
| `Beampipe_5_wall_PV` | 5,917 | 0.119666 | `beampipe` |
| `Scint_barPV_H` | 3,001 | 0.060692 | `scintillator` |
| `Scint_barPV_V` | 2,811 | 0.056850 | `scintillator` |
| `TPCPV` | 1,398 | 0.028273 | `tpc` |
| `Beampipe_5_coating_PV` | 1,369 | 0.027687 | `beampipe` |
| `Beampipe_8_wall_PV` | 1,020 | 0.020629 | `beampipe` |
| `SteelShield` | 984 | 0.019900 | `steelshield` |
| `SteelShield_side` | 914 | 0.018485 | `steelshieldside` |
| `Scint_FB_barPV_V` | 884 | 0.017878 | `scintillator` |
| `Scint_FB_barPV_H` | 861 | 0.017413 | `scintillator` |
| `SteelShield_back` | 670 | 0.013550 | `steelshieldback` |
| `siliconPV_1` | 647 | 0.013085 | `silicon` |
| `siliconPV_2` | 621 | 0.012559 | `silicon` |
| `SteelShield_front` | 558 | 0.011285 | `steelshieldfront` |
| `Beampipe_4_wall_PV` | 519 | 0.010496 | `beampipe` |
| all remaining labels | 3,493 | 0.070643 | see evidence script output |

The audit canonicalization is working for the major detector labels used by the
thesis target table: lead glass, beampipe, scintillator, TPC, and silicon are
all recognized from the raw labels above.

## Unmapped or out-of-table first-conversion volumes

3,796 / 49,446 first conversions (7.67%) land in labels outside the five
thesis target categories:

| Canonical label outside thesis table | Count | Fraction |
| --- | ---: | ---: |
| `steelshield` / `steelshieldside` / `steelshieldback` / `steelshieldfront` | 3,126 | 0.063220 |
| `leadshieldback` / `leadshieldfront` | 473 | 0.009566 |
| `carbonpv` | 153 | 0.003094 |
| `beamstopabsorberpv` / `beamstopmetalpv` | 44 | 0.000890 |

Renormalizing only over the five thesis categories does not close the mismatch:
lead glass becomes 0.553757, while beampipe/TPC/scintillator remain below their
thesis fractions.  Therefore the discrepancy is not just denominator leakage
from unmapped passive volumes.

## Classification

- **Sample statistics:** rejected.  The 49,446-event sample is large enough that
  the observed deviations are many statistical standard errors from the thesis
  target fractions.
- **Volume canonicalization:** partially relevant but not sufficient.  The audit
  maps all high-statistics detector labels into the five thesis categories, and
  the residual out-of-table passive/shield labels cannot explain the normalized
  lead-glass excess.
- **Geometry/material setup or scoring definition:** currently the leading
  unresolved cause.  The staged sample includes first conversions in steel
  shield, lead shield, carbon, and beam-stop volumes that are absent from the
  encoded five-bin thesis target.  There is no local evidence yet proving
  whether Ch. 5 excluded those volumes, assigned them to another category, used
  an older geometry/material stack, or scored a different interaction point.
- **Physics/modeling difference:** still open until the Ch. 5 scoring macro,
  geometry/material revision, and category definition are pinned.

## Recommendation

Keep photon-conversion map reproduction **BLOCKED**.  The next lane should
recover or reconstruct the Ch. 5 photon-conversion scoring definition: exact
macro, geometry/material commit or detector tag, and category policy for steel,
lead shield, carbon, and beam-stop conversions.  Only after that evidence exists
should a code change map/exclude passive volumes or a new production sample be
submitted.

OPEN: Missing evidence package `photon_conversion_ch5_scoring_v1` containing the
Ch. 5 macro, detector geometry/material revision, and detector-category mapping
for passive shield/carbon/beam-stop first conversions.

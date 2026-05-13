# Detector material budget from vertex to lead-glass face

Date: 2026-05-12.  Worker: PANE 2 / worker-2 lane-swap.

## Scope and assumptions

This is a compact, local geometry audit for `docs/parallel-sessions/detector-material-budget.md`.
No C++ source, macros, data products, SLURM jobs, or simulations were changed or run.

The budget below is for one representative transverse ray from the annihilation vertex at the
central carbon target outward to a side lead-glass active face.  It is therefore a **path
estimate**, not a full angular/material map.  The estimate uses code dimensions from the local
`NNBAR_Detector` geometry and standard radiation-length inputs from the lane spec where
available.  For code materials absent from the lane-spec table (Aluminum, B4C, Li6F, Ar/CO2),
standard approximate compound values are used and marked in the notes.

Geometry interpretation:

- Carbon uses the nominal 100 µm foil thickness.
- The side path crosses two silicon shells, the central Beampipe-5 coating/wall, one side
  Type-II TPC module, one 30 cm side scintillator stack, then the side lead-glass active face.
- World gaps are `Galactic` vacuum in the code and are ignored.  If treated as air, the
  extra contribution would be only O(10^-3--10^-2) X0 for the open gaps and does not change
  the conclusion.
- The lead-glass row is reported separately because the requested survival probability is
  "reaches LG without pre-conversion"; once inside the 25 cm active block, conversion is
  essentially guaranteed.

## Upstream material to the lead-glass active face

| Layer | Material | thickness_cm | X0_cm | t/X0 | cumulative_t/X0 | note |
|---|---:|---:|---:|---:|---:|---|
| Carbon foil | Carbon_target / graphite | 0.01 | 21.35 | 4.6838e-04 | 4.6838e-04 | nominal 100 µm foil thickness |
| Silicon Li6F coatings | Li6F | 0.2 | 18.48 | 0.0108225 | 0.0112909 | two 0.1 cm coatings; compound X0 approximated from mass fractions and density |
| Silicon sensors | Silicon | 0.4 | 9.37 | 0.0426894 | 0.0539803 | two 0.2 cm cylindrical silicon shells |
| Beampipe coating | B4C | 1 | 20 | 0.05 | 0.10398 | central Beampipe-5 neutron-absorber coating; approximate compound X0 |
| Beampipe wall | Aluminum | 2 | 8.897 | 0.224795 | 0.328775 | central Beampipe-5 wall, code material Aluminum |
| TPC entrance/exit walls | Aluminum | 0.4 | 8.897 | 0.044959 | 0.373734 | two 2 mm walls through a side Type-II TPC module |
| TPC drift gas | Ar/CO2 80/20 | 85 | 1.2794e+04 | 0.00664374 | 0.380378 | 85 cm drift region; X0 from mass-weighted Ar/CO2 at 1.70 mg/cm3 |
| Scintillator hodoscope | BC-408-like polystyrene | 30 | 42.4 | 0.707547 | 1.08793 | ten 3 cm scintillator layers on the side surface |

**Total upstream budget to LG active face:** `1.087925` X0.

**Photon survival without upstream conversion:**

\[
P_{survive} = \exp[-(7/9) \sum_i t_i/X_{0,i}] = 0.429058
\]

So the estimated upstream pre-conversion probability is `0.570942` (57.1%).
This is above the lane-spec thin-material rule of thumb: cumulative X0 > 0.5, so upstream
pre-shower/conversion is significant for this representative side path.

## Simplified lane-spec-only comparison

If the budget excludes the explicit beam-pipe and coating materials and keeps only the
high-level requested detector layers (Carbon, Silicon sensors, TPC, Scintillator), the total is
`0.802308` X0 and `P_survive = 0.535788`.  This still exceeds 0.5 X0
because the 30 cm scintillator stack alone contributes `0.707547` X0.

## Lead-glass active block

| Layer | Material | thickness_cm | X0_cm | t/X0 | cumulative_t/X0 including upstream | note |
|---|---:|---:|---:|---:|---:|---|
| LeadGlass active block | Schott-SF5-like lead glass | 25 | 2.74 | 9.124088 | 10.212013 | first active block thickness from geometry; X0 from lane spec |

Conditional on reaching the LG active face, the probability to convert within the first 25 cm
active block is approximately `0.999172`.  The survival probability through
upstream material plus one active LG block is `3.552544e-04`.

## Caveats / follow-up

1. A full photon-conversion map should integrate over generated photon directions and exact
   block intersections.  This compact audit only evaluates a representative side ray.
2. The active code material for TPC gas is Ar/CO2 80/20, while the lane-spec X0 table mentioned
   helium gas.  The table uses Ar/CO2 because that is what the local geometry defines.
3. The active code material for TPC and beam-pipe walls is Aluminum, not copper/stainless.  The
   table therefore uses Aluminum X0 for those walls.
4. The code lead-glass material definition uses a high-density Pb-rich composition, while the
   lane spec supplies Schott-SF5 X0 ≈ 2.74 cm.  This report uses the lane-spec X0 for the
   requested calculation; a later material-property audit can reconcile the code density and
   effective radiation length.

## Verification

Commands run locally from the simulation worktree:

```text
rtk wc -l docs/reports/detector_material_budget.md NNBAR_Detector/src/core/DetectorConstruction.cc
rtk rg -n "carbon_len|silicon_thickness|Beampipe_5_radius_1|Beampipe_5_radius_2|TPC_drift_len|TPC_wall_thickness|scint_bar_y|scint_layers|lead_glass_y" NNBAR_Detector/src/core/DetectorConstruction.cc NNBAR_Detector/src/detector/*.cc
rtk bash scripts/validate-csup-queues.sh
```

No SLURM, training, large pipeline, or simulation command was run.

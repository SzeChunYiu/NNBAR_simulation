# Lane: detector-material-budget (sim)

## Goal
Compute the radiation length (X0) budget from the annihilation vertex to the LG
active volume. Determines how much material a photon from pi0 → γγ traverses
before reaching the calorimeter, and whether showers start before LG.

## Steps

### Step 1: Read detector geometry
Read `NNBAR_Detector/src/core/DetectorConstruction.cc`
Extract:
- Layer name (Carbon, Silicon, TPC, Scintillator, LeadGlass)
- Material name (e.g., G4_C, G4_Si, G4_POLYSTYRENE, etc.)
- Thickness or outer/inner radius difference

Also read any header files or material definition files in NNBAR_Detector/include/ or src/

### Step 2: Material X0 values
Standard radiation lengths (NIST/PDG):
| Material | X0 (cm) |
|----------|---------|
| Carbon (graphite) | 21.35 |
| Silicon | 9.370 |
| Polystyrene (scintillator) | 42.4 |
| Air | 30420 |
| Lead glass (Schott SF5) | ~2.74 (density ~3.86 g/cm³) |
| Helium gas (TPC) | ~5.3e5 (negligible) |
| Copper/stainless (~TPC walls) | ~1.43 |

### Step 3: Compute material budget
For each layer from vertex outward:
- thickness t (cm)
- X0 material from table above
- material budget = t/X0

### Step 4: Identify early conversion probability
Photon conversion probability per radiation length: P_conv ≈ 7/9 per X0
- Probability of NOT converting in material budget t: P_survive = exp(-7t/9/X0)
- Report: probability that photon reaches LG without converting in upstream material

### Output
Write `docs/reports/detector_material_budget.md`:
- Table: layer | material | thickness_cm | X0_cm | t/X0 | cumulative_t/X0
- Total X0 budget from vertex to LG face
- Estimated photon survival probability (no pre-conversion) to LG
- Notes: if cumulative X0 > 0.5, significant pre-shower; < 0.1 is "thin"

## Constraints
- Read DetectorConstruction.cc and header files locally only
- No SLURM, no code changes, no running simulations
- If thickness not explicit in code (uses computed geometry), estimate from
  radius differences in the G4 volume definitions

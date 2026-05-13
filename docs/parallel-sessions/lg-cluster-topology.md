# Lane: lg-cluster-topology

## Goal
Characterize the spatial structure of LeadGlass hits for pi0 → γγ events.
Two-photon final states should produce two spatially separated clusters in LG.
Quantify cluster separation and multiplicity for the mono_150mev sample.

## Data
`build_lunarc/output/pi0_mono_150mev/LeadGlass_output_0.parquet`

LG columns: Event_ID, Track_ID, Parent_ID, Name, Proc, Step_info, Origin,
Module_ID, x, y, z, t, KE, eDep, photons

## Analysis

### Step 1: Per-event hit summary
For each event:
- Total LG eDep (sum of eDep)
- Total hit count
- CoM position: x_com = sum(eDep * x) / sum(eDep), same for y, z
- Spread: std(x), std(y), std(z) weighted by eDep

### Step 2: Find two-cluster structure
Use 1D projection along x-axis (transverse):
- For each event: build eDep-weighted histogram of x positions
- Fit or detect number of distinct peaks (2 expected for γγ)
- Simple approach: find events where std(x) > 10 cm (suggests two separated clusters)

### Step 3: Compute cluster separation
For each event split hits into two halves by x position:
- cluster_A: hits with x < x_com
- cluster_B: hits with x >= x_com
- E_A = sum(eDep for cluster_A), E_B = sum for cluster_B
- asymmetry = |E_A - E_B| / (E_A + E_B)
- separation = |x_com_A - x_com_B| in cm

### Expected results
- For 150 MeV pi0: opening angle ~57° minimum in lab frame
- Two clusters should be spatially separated by O(10-30) cm
- eDep asymmetry should follow sin²(θ_cm) distribution → mean ~0.5, std ~0.3

### Output
Write `docs/reports/lg_cluster_topology_150mev.md`:
- Table: n_events, mean_total_eDep, mean_n_hits, mean_std_x_cm, mean_separation_cm
- Fraction of events with separation > 10 cm
- Fraction of events with asymmetry < 0.3 (roughly balanced clusters)

## Constraints
- Python only, no SLURM, no reco changes
- All data is locally available at above path

# Signal Mass Bias — Atomic Truth-Matching Analysis

## Goal

Quantify the root cause of the +26 MeV high bias in the standalone signal
reconstruction (mean 160.8 MeV vs true 134.98 MeV) by splitting accepted
diphoton candidates into correctly-paired (same-pi0) vs cross-paired
(different-pi0) categories using truth parentage from the simulation output.

## Background

The signal reconstruction job (3053941) found 48,244 pi0 candidates with
mean mass 160.8 MeV — +26 MeV above true 134.98 MeV. The dominant
hypothesis is cross-pi0 cluster pairing:
- Signal events have ~1.70 pi0/event → ~3.4 photon clusters per event
- Greedy cone clustering (25°) cannot distinguish same-pi0 from cross-pi0 photons
- Cross-pi0 diphoton pairs have random opening angles, often > true pi0 daughters
- Larger opening angle → higher invariant mass → +26 MeV high bias

The calibrated LUNARC pipeline gives 133.5 MeV (−1.5 MeV) — consistent with
correct reconstruction after energy calibration. The standalone reco has no
energy calibration AND suffers cross-pairing.

## Data Available (on LUNARC)

`/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/build_lunarc/output/sig_foil_v3/`

Relevant parquet files and their key columns:

| File | Key columns |
|------|-------------|
| `LeadGlass_output_0.parquet` | Event_ID, Track_ID, Parent_ID, Name, x, y, z, eDep |
| `Scintillator_output_0.parquet` | Event_ID, Track_ID, Parent_ID, Name, x, y, z, eDep |
| `Interaction_output_0.parquet` | Event_ID, Track_ID, Parent_ID, Name, Proc, x, y, z, px, py, pz, m, KE |
| `TPC_output_0.parquet` | Event_ID, Track_ID (for trigger) |

## Analysis Plan

### Step 1: Build a pi0 truth table

From `Interaction_output_0.parquet`, select rows where `Name == "pi0"`.
For each (Event_ID, Track_ID) of a pi0, record its decay daughters
by finding rows with `Parent_ID == pi0_track_id` AND `Name == "gamma"`.

Result: dict mapping (Event_ID, pi0_track_id) → list of daughter photon Track_IDs.

### Step 2: Reproduce the cluster-level reco with Track_ID tracking

For each LG and Scint hit, carry the dominant Track_ID (by eDep) through the
cone clustering step. After forming each cluster, record which Track_ID
contributed the most energy — this is the "cluster identity."

### Step 3: Label each accepted diphoton candidate

For each accepted (mass in 60–240 MeV) diphoton pair:
- Check if both clusters' dominant Track_IDs share the same Parent_ID pi0
- If yes → correctly-paired (same-pi0)
- If no → cross-paired (different-pi0)

### Step 4: Compute per-category mass statistics

Report:
- N correctly-paired, mass mean/sigma
- N cross-paired, mass mean/sigma
- Fraction cross-paired = N_cross / (N_cross + N_correct)
- Plot both mass distributions (write JSON histograms for offline plotting)

### Step 5: Quantify energy calibration contribution

For correctly-paired events only, report the mass mean. Compare to 134.98 MeV.
Any remaining bias in correctly-paired events is pure energy calibration bias
(no cross-pairing contamination). This separates the two effects cleanly.

## Expected Outcomes

| Category | Predicted mass mean |
|----------|---------------------|
| All accepted | 160.8 MeV (observed) |
| Correctly-paired only | ~115–125 MeV (energy calibration undershoot) |
| Cross-paired only | ~170–200 MeV (large opening angle) |

If correctly-paired mean ≈ 115 MeV: confirms energy calibration undershoot
dominates the truly-paired sample, while cross-pairing pushes the overall mean
above 135 MeV.

## Output

Write `build_lunarc/output/sig_foil_v3_reco/truth_matching_report.json`:
```json
{
  "n_triggered_events": ...,
  "n_accepted_diphoton": ...,
  "n_correctly_paired": ...,
  "n_cross_paired": ...,
  "cross_pair_fraction": ...,
  "mass_mean_all_mev": 160.8,
  "mass_mean_correct_pair_mev": ...,
  "mass_mean_cross_pair_mev": ...,
  "mass_sigma_correct_pair_mev": ...,
  "mass_sigma_cross_pair_mev": ...,
  "mass_hist_correct_bins": [...],
  "mass_hist_correct_counts": [...],
  "mass_hist_cross_bins": [...],
  "mass_hist_cross_counts": [...]
}
```

## Implementation Notes

- Use pyarrow `pq.read_table(..., columns=[...], filters=[...])` — never load
  full parquet tables into memory
- Use `HIBENV=/projects/hep/fs10/shared/nnbar/billy/packages/hibeam_env`
- SLURM: `--mem=64G --time=02:00:00 --partition=lu48`
- Output logs to `build_lunarc/slurm/` NOT to `$HOME`
- Do NOT run on the login node — everything via sbatch

## Connection to Thesis

This analysis provides the atomically-complete explanation for the mass bias:
- Fraction cross-paired → quantifies the pairing contamination
- Correctly-paired mean → quantifies the residual energy calibration bias
- Together these explain why standalone reco gives +26 MeV while calibrated
  pipeline gives −1.5 MeV

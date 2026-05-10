---
id: 43_signal_efficiency
title: Signal efficiency — acceptance × selection × reconstruction
version: 0.1
status: draft
owner: Analysis WG
depends_on: [00_README, 04_statistical_uncertainty, 13_signal_model, 20_sample_signal, 30_subsystem_vertex, 37_subsystem_event_selection]
outputs:
  - {path: docs/rebuild_plans/43_signal_efficiency.md, schema: this file}
acceptance:
  - {test: efficiency factorisation produced (acceptance, reconstruction, selection) per stage, method: §1 deliverable, pass_when: each stage quantified}
  - {test: per-final-state-channel breakdown reported, method: §2 deliverable, pass_when: ≥ 5 channels}
  - {test: licentiate "≈ 70% signal acceptance" reproduced after reconstruction × selection, method: ledger row, pass_when: reproduces within stat unc}
risks:
  - {risk: per-channel efficiency is correlated; sum is not factorisable simply, mitigation: §1 explicit covariance reporting}
estimated_effort: M
last_updated: 2026-05-09
---

# Signal efficiency

*Charter.* Decompose the signal efficiency into its three factors and
report each separately. The headline number is the product; the
factorisation reveals where loss occurs.

## 1. Factorisation

The headline efficiency is measured as conditional factors on the same
registered signal sample, with covariance saved so reviewers can see
which loss term dominates:

```
epsilon_signal = epsilon_acceptance * epsilon_reconstruction * epsilon_selection
```

### 1.1 Runnable procedure

1. Build reconstruction tables for the frozen signal sample:

   ```bash
   python -m nnbar_reconstruction.cli summarize \
       NNBAR_Detector/output/sig_foil_v3 --all-runs \
       --table output/reco/sig_foil_v3/ --json output/reco/sig_foil_v3/summary.json
   ```

2. Compute the staged efficiency from truth parquet and reconstruction
   CSVs:

   ```bash
   python -m nnbar_reconstruction.cli signal-efficiency \
       --truth-particle NNBAR_Detector/output/sig_foil_v3/Particle_output_*.parquet \
       --truth-interaction NNBAR_Detector/output/sig_foil_v3/Interaction_output_*.parquet \
       --reco-vertices output/reco/sig_foil_v3/vertices.csv \
       --reco-events output/reco/sig_foil_v3/events.csv \
       --reco-charged output/reco/sig_foil_v3/charged.csv \
       --reco-photons output/reco/sig_foil_v3/photons.csv \
       --reco-pi0 output/reco/sig_foil_v3/pi0.csv \
       --geometry docs/rebuild_plans/16_geometry_and_alignment.md \
       --bootstrap 200 --out output/efficiency/sig_foil_v3/
   ```

3. Write `factorisation.json`, `factorisation.parquet`,
   `factorisation_covariance.npz`, and `factorisation_manifest.json`.
   The manifest stores input hashes, geometry/alignment scenario, event
   counts at each denominator, Wilson intervals (plan 04 §4), and
   jackknife uncertainties for conditional efficiencies (plan 04 §3).
4. Assert the product of conditional factors equals the direct
   `passes_preliminary_selection / n_generated` efficiency to `1e-12`
   in the saved JSON before uncertainties are attached.

### 1.2 Stage definitions, tolerances, and cross-references

| Stage | Numerator / denominator | Inputs from plan 09 | Tolerance / assertion | Ladder leaf | Ledger hook |
|---|---|---|---|---|---|
| acceptance | generated events with final-state pions entering TPC or lead-glass fiducial / all generated foil-origin events | `Particle_output` and `Interaction_output` truth plus plan 16 geometry | Wilson 68% interval saved; fiducial denominator must match manifest event count exactly. | S.1 precursor / E.1-E.2 | LIC-CH06 signal acceptance via plan 47 §1 |
| reconstruction | accepted events with V.5 vertex and at least one reconstructed charged, photon, or π0 object / accepted events | `vertices.csv`, `charged.csv`, `photons.csv`, `pi0.csv` | jackknife σ saved; zero missing `event_id` joins allowed. | V.5, C.1-C.6, P.1-P.7 | LIC-CH10-CUTFLOW |
| selection | reconstructed events passing `passes_preliminary_selection` / reconstructed events | `events.csv` per-cut booleans from plan 37 §1 | direct count must equal cumulative cut-flow S.6 exactly; Wilson interval saved. | S.1-S.6 | LIC-CH10-CUTFLOW |
| total signal efficiency | selected events / all generated foil-origin events | all above | product and direct ratio must agree to `1e-12`; quote with covariance, not independent-factor multiplication. | S.6 | licentiate ≈70% row in plan 47 |

Truth columns are used to define denominators and final-state acceptance
only. Reconstruction and selection numerators are computed from Class A
reconstruction outputs and cut-flow booleans.

## 2. Per-channel breakdown

Plan 13 §1 lists the major final-state channels. For each channel,
compute ε per stage:

- π⁺ π⁻ π⁰
- π⁺ π⁻ 2π⁰
- π⁺ π⁻ 3π⁰
- 2π⁺ 2π⁻
- 2π⁺ 2π⁻ π⁰
- (other)

Per-channel efficiency reveals which final states the detector
accepts well (high charged multiplicity favours TPC tracking; low
charged multiplicity disfavours).

## 3. Acceptance criteria

- §1 three numbers reported with uncertainties.
- §2 per-channel table produced.
- Reproducible from `sig_foil_v3` only.

## 4. Risks

- *Risk:* fiducial-volume definition is geometric and can drift if
  geometry changes.
  *Mitigation:* §1 acceptance is computed from the registered
  geometry (plan 16); sample re-registration on geometry change.

## 5. Dependencies

- **04** — uncertainty.
- **13, 20, 30, 37** — inputs.
- *Consumed by:* plan 47 (ledger), plan 50, plan 46 (significance).

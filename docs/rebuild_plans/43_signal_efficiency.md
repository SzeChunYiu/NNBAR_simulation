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
  - {test: licentiate "≈ 70% signal acceptance" reproduced after reconstruction × selection, method: ledger row plus §3.1 gates, pass_when: LIC-CH10-NUM-1 is green or yellow under plan 47 §2}
risks:
  - {risk: per-channel efficiency is correlated; sum is not factorisable simply, mitigation: §1 explicit covariance reporting}
estimated_effort: M
last_updated: 2026-05-10
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

Per-channel efficiencies use truth final-state topology for grouping and
the same staged numerators from §1 for acceptance, reconstruction, and
selection. The channel label is a diagnostic/ledger dimension; it is not
read by the reconstruction or selection path.

### 2.1 Runnable procedure

1. Reuse `output/efficiency/sig_foil_v3/factorisation_manifest.json`
   from §1 to ensure the event set and hashes are identical.
2. Run the channel breakdown using plan 13 topology labels:

   ```bash
   python -m nnbar_reconstruction.cli signal-efficiency \
       --truth-particle NNBAR_Detector/output/sig_foil_v3/Particle_output_*.parquet \
       --truth-interaction NNBAR_Detector/output/sig_foil_v3/Interaction_output_*.parquet \
       --reco-vertices output/reco/sig_foil_v3/vertices.csv \
       --reco-events output/reco/sig_foil_v3/events.csv \
       --reco-charged output/reco/sig_foil_v3/charged.csv \
       --reco-photons output/reco/sig_foil_v3/photons.csv \
       --reco-pi0 output/reco/sig_foil_v3/pi0.csv \
       --by-channel docs/rebuild_plans/13_signal_model.md \
       --bootstrap 200 --out output/efficiency/sig_foil_v3/by_channel/
   ```

3. Write `channel_efficiency.parquet`, `channel_efficiency.json`,
   `channel_covariance.npz`, and `channel_manifest.json`. The parquet
   has one row per `(channel, stage)` with denominator, numerator,
   conditional efficiency, Wilson interval, and jackknife uncertainty.
4. Assert at least five named channels plus `other` are present. Any
   named channel with fewer than 100 generated events is retained in the
   machine artifact but rolled into `other` for thesis-facing plots.

### 2.2 Channel rows, tolerances, and cross-references

| Channel group | Truth label rule | Reporting tolerance | Ladder leaf | Ledger/systematics hook |
|---|---|---|---|---|
| `pi+ pi- pi0` | exactly one π+, one π-, one π0 ancestry in `Interaction_output` | report if denominator ≥100; otherwise merge into `other` for plots. | E.9 / S.6 | plan 13 nominal, plan 47 §1 |
| `pi+ pi- 2pi0` | one π+, one π-, two π0 ancestors | same denominator rule; covariance with total efficiency saved. | E.9 / S.6 | plan 13 nominal, N5 |
| `pi+ pi- 3pi0` | one π+, one π-, three π0 ancestors | same denominator rule; selection loss must include S.2/S.3 cut contributions. | E.9 / S.6 | plan 13 nominal, N5 |
| `2pi+ 2pi-` | two π+ and two π- with no π0 ancestor | same denominator rule; reconstruction factor must cite charged-PID leaves C.1-C.6. | C.1-C.6 / S.6 | plan 29, plan 47 §1 |
| `2pi+ 2pi- pi0` | two π+, two π-, one π0 ancestor | same denominator rule; store charged and π0 reconstruction losses separately. | C.1-C.6, P.5-P.7 / S.6 | plans 29, 34-35 |
| `other` | all rare, resonant, η/ω/ρ/K-containing, or low-count groups | always reported; uncertainty can be asymmetric Wilson interval. | E.9 / S.6 | plan 13 §4, plan 45 N5 |

The sum of channel numerators and denominators must reproduce the
inclusive §1 counts exactly. A mismatch is a blocking event-join or
truth-labeling bug, not an uncertainty.

## 3. Acceptance criteria

- §1 three numbers reported with uncertainties.
- §2 per-channel table produced.
- Reproducible from `sig_foil_v3` only.

### 3.1 Machine-checkable gate mapping

The efficiency job is complete only when the manifest can answer each
ledger question below without a hand edit. These gates are assertions on
the artifacts produced by §§1-2, not new reconstruction logic.

| Gate | Required artifact field | Pass assertion | Ladder / subsystem cross-reference | Ledger row |
|---|---|---|---|---|
| factorisation closure | `factorisation.json:direct_total`, `product_total` | direct selected/generated ratio equals the conditional-factor product to the §1 `1e-12` tolerance. | S.6 with V.5, C.1-C.6, P.1-P.7 contributors | LIC-CH10-NUM-1 |
| uncertainty completeness | `factorisation_covariance.npz`, per-stage Wilson/jackknife fields | every stage in §1.2 has a central value, Wilson interval, jackknife uncertainty, and covariance entry. | plan 04 §3-§4; plan 38 observable budget | LIC-CH10-CUTFLOW |
| channel coverage | `channel_efficiency.parquet`, `channel_manifest.json` | the five named §2.2 channels plus `other` are present, and their summed counts reproduce the inclusive §1 counts exactly. | E.9/S.6, charged leaves C.1-C.6, π0 leaves P.5-P.7 | plan 47 §1 channel rows |
| sample provenance | `factorisation_manifest.json`, `channel_manifest.json` | dataset id is `sig_foil_v3`; truth, reco, geometry, and command hashes match between inclusive and by-channel runs. | plan 03 signal registry; plan 16 geometry | plan 47 `sample` and `command` fields |
| publication handoff | rendered Markdown table plus machine artifacts | the thesis-facing table quotes inclusive efficiency, staged factors, and channel rows from the machine artifacts without recomputation. | plans 43→46/47/50 | LIC-CH06/LIC-CH10 signal-efficiency rows |

If any gate fails, plan 47 marks the affected row `red` or
`not-attempted`; downstream significance in plan 46 must not consume the
headline signal efficiency.

## 4. Risks

- *Risk:* fiducial-volume definition is geometric and can drift if
  geometry changes.
  *Mitigation:* §1 acceptance is computed from the registered
  geometry (plan 16); sample re-registration on geometry change.

## 5. Dependencies

- **04** — uncertainty.
- **13, 20, 30, 37** — inputs.
- *Consumed by:* plan 47 (ledger), plan 50, plan 46 (significance).

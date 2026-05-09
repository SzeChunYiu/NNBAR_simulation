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

```
ε_signal = ε_acceptance × ε_reconstruction × ε_selection
```

| Stage | Definition | Sample to measure on |
|---|---|---|
| **acceptance** | fraction of generated antineutron annihilations whose final-state pions enter the detector fiducial (within TPC + LG geometric coverage) | `sig_foil_v3` truth |
| **reconstruction** | of those, fraction with a reconstructed vertex (V.5) and ≥ 1 reconstructed charged or photon object | `sig_foil_v3` reco |
| **selection** | of those, fraction passing the cut-flow (S.6) | `sig_foil_v3` reco + cuts |

Each stage carries statistical (plan 04 §3 jackknife) and systematic
(plan 45) uncertainties.

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

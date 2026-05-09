---
id: 20_sample_signal
title: Signal sample — n̄ annihilation on foil
version: 0.1
status: draft
owner: Sim Production
depends_on: [00_README, 03_dataset_registry, 13_signal_model, 16_geometry_and_alignment, 17_field_calibration, 19_simulation_validation_suite]
inputs:
  - {path: NNBAR_Detector/macro/signal/, schema: existing macros}
  - {path: data/registry/physics_list/nominal.yml, schema: physics list (plan 12)}
outputs:
  - {path: data/registry/sig_foil_v3/manifest.yml, schema: registered sample manifest}
  - {path: NNBAR_Detector/output/sig_foil_v3/*.parquet, schema: simulation outputs}
acceptance:
  - {test: thesis-grade statistics produced (≥ 100 000 events for primary plots), method: row count check, pass_when: events_produced ≥ 100k}
  - {test: per-SD sanity plots match plan 19 §2, method: closure check, pass_when: plots in plan 47}
  - {test: registry manifest is complete and frozen, method: plan 03 freeze acceptance, pass_when: status = frozen}
risks:
  - {risk: foil-vs-beampipe origin mixing, mitigation: §3 origin tagging in primary generator output}
  - {risk: sample size insufficient for tail studies (rare topologies), mitigation: §2 staged sizes; full statistics for thesis figures, smaller for fast iteration}
estimated_effort: M
last_updated: 2026-05-09
---

# Signal sample — n̄ annihilation on foil

*Charter.* Produce, register, and freeze the antineutron annihilation
samples that drive every signal-side number in the thesis. This is
the load-bearing dataset; plans 28, 29, 31, 32, 38, 47 all consume it.

## 1. Configuration

| Setting | Value | Source |
|---|---|---|
| Macro | `macro/signal/run_signal_100k.mac` (or replacement) | plan 10 §1.2 |
| Geant4 version | latest 11.x stable | plan 12 §3 |
| Physics list | `nominal` (FTFP_BERT, no _HP) | plan 12 §1 |
| `WITH_SCINTILLATION` | OFF (fast mode) for primary sample; ON for optical-mode variant | plan 11 §12 |
| `WITH_CELERITAS` | OFF for primary | plan 11 §5.3 |
| `MCPL_BUILD` | OFF (default ParticleGun mode) | plan 11 §2 |
| `TARGET_BUILD` | ON (carbon foil placed) | plan 11 §2 |
| Alignment scenario | `perfect` | plan 16 §3 |
| Digitiser | `default_identity_v1` | plan 02 §3 |
| Number of events | 100 000 (primary), 1 000 (smoke) | §2 |

## 2. Sample sizes

- *Primary sample* (`sig_foil_v3`): 100 000 events. Sufficient for
  every event-shape distribution and π⁰-mass fit at thesis precision.
- *High-statistics tail sample* (`sig_foil_highstat_v1`): 1 000 000
  events. Reserved for rare-topology studies (η/ω contamination,
  high-multiplicity events).
- *Smoke sample* (`sig_foil_smoke_v1`): 1 000 events. Fast-feedback
  for CI.
- *Optical-mode sample* (`sig_foil_optical_v1`): 100 000 events with
  `WITH_SCINTILLATION=ON` for plan 18 intercalibration.

## 3. Origin tagging

Per plan 13 §7, the primary generator emits the antineutron at the
foil. Annihilation can occur on the foil (carbon) or on beampipe
silicon if the antineutron escapes the foil. The sample manifest
(plan 03) records per-event origin via `Particle_output_*.parquet`'s
`Vx, Vy, Vz` truth columns.

Plan 47 ledger quotes foil-origin and beampipe-origin numbers
separately.

## 4. Acceptance criteria

- 100 000 events produced; row counts match across SDs.
- Sanity plots (plan 19 §2) green.
- Manifest in `data/registry/sig_foil_v3/` complete, hashed, frozen.
- Plan 47 ledger row "licentiate Ch 6 signal acceptance" reproduces
  the licentiate's value within statistical uncertainty.

## 5. Risks

- *Risk:* primary generator mode misconfigured.
  *Mitigation:* smoke sample run before primary; sanity plots compared
  against plan 19 baseline.
- *Risk:* legacy `run_signal*.mac` macros differ subtly from
  registered configuration.
  *Mitigation:* plan 03 hash check on macro file content.

## 6. Dependencies

- **03** — sample registry.
- **13** — signal-model branching ratios.
- **16** — geometry/alignment.
- **19** — sanity validation.
- *Consumed by:* plans 28, 29, 31, 32, 38, 47.

---
id: 22_sample_neutron_beam
title: Beam-induced neutron background sample
version: 0.1
status: draft
owner: Sim Production
depends_on: [00_README, 03_dataset_registry, 04_statistical_uncertainty, 12_physics_list_audit, 14_background_models, 19_simulation_validation_suite]
inputs:
  - {path: external HIBEAM beam-line MCPL, schema: ESS-supplied (TBD)}
outputs:
  - {path: data/registry/beam_neutron_hibeam_*/manifest.yml, schema: registered sample}
acceptance:
  - {test: beam source format chosen and recorded (MCPL or parameterised), method: §1 review, pass_when: format frozen}
  - {test: sub-channel breakdown (direct, scattered, capture-γ, secondaries) registered as separate samples, method: §3, pass_when: ≥ 4 sub-channels}
  - {test: time-correlation limitation documented (no pile-up), method: §4 review, pass_when: registered as L11 in plan 01}
risks:
  - {risk: beam MCPL not yet available from ESS team, mitigation: §1 parameterised fallback}
  - {risk: thermal-neutron capture-γ rate underestimated by missing shielding materials, mitigation: §3 paired sample with full shielding}
estimated_effort: M
last_updated: 2026-05-09
---

# Beam-induced neutron background sample

*Charter.* Produce, register, and freeze the beam-neutron-induced
background sample. The thesis must distinguish between cosmic and
beam-induced backgrounds because the experiment runs *only* when the
beam is on; signal/background ratios depend critically on this
sample.

## 1. Source

Two paths:

- *(a) MCPL file from ESS HIBEAM beam-line simulation.* Preferred.
  Codex-supervisor obtains the file from the HIBEAM team; the file
  hash and provenance are recorded in plan 03.
- *(b) Parameterised flux + spectrum sampled via GPS commands.*
  Fallback when MCPL is unavailable. Spectrum from the HIBEAM
  technical design report.

User decides between (a) and (b); a DEC entry (plan 05) records
the choice.

## 2. Physics-list configuration

Per plan 12 §2: **`G4HadronPhysicsFTFP_BERT_HP` ON** for beam neutron
samples. The high-precision neutron data is essential for
sub-20 MeV transport, capture, and thermalisation.

This is a separate `build_id` from the signal sample (which uses
non-HP).

## 3. Sub-channel decomposition

Plan 14 §2.2 defines the sub-channels. Each is registered as a
separate downstream sample for analysis:

| Sub-channel | How separated | Sample ID |
|---|---|---|
| Direct beam neutrons | events with primary neutron reaching detector volume | `beam_neutron_hibeam_direct_v1` |
| Scattered neutrons | events with neutron interaction in beampipe / collimator before detector | `beam_neutron_hibeam_scattered_v1` |
| Capture-γ cascade | events triggered on H/Fe/Pb capture in shielding | `beam_neutron_hibeam_captgamma_v1` |
| Secondary hadronic fragments | events with charged secondaries from neutron inelastic | `beam_neutron_hibeam_secondaries_v1` |

The decomposition uses truth columns (Class B) to label events;
plan 01 §5 marks these as `@labeling`-decorated derivations, not
production paths.

## 4. Time correlation limitation

Plan 01 limitation L11 (no pile-up): the simulation does not model
beam time-structure. Beam-induced backgrounds reported here are
*per-event rates*, not per-second rates. To convert: multiply by the
beam pulse rate (≈ 14 Hz at ESS) and the per-pulse expected event
yield.

Plan 47 ledger flags this caveat on every quoted beam-background
number.

## 5. Sample size

Beam-rate target: bound the beam-induced false-positive rate to
1 × 10⁻⁴ per pulse at 90% C.L. Per plan 04 §5, sample size scales
similarly to plan 21 §4. Codex-supervisor proposes a target after
the user chooses (a) vs (b) in §1.

## 6. Acceptance criteria

- §1 source decided with DEC entry.
- §2 build_id distinct from signal sample.
- §3 four sub-channel samples registered.
- §4 limitation L11 documented in every ledger row consuming this
  sample.

## 7. Risks

- *Risk:* MCPL file format changes or ESS revises the beam line.
  *Mitigation:* plan 03 registry hashes the input MCPL; an upstream
  update creates a new dataset version.
- *Risk:* shielding model incomplete; capture-γ rate
  under/over-estimated.
  *Mitigation:* §3 paired with shielding-on / shielding-off
  configurations to bound the systematic.

## 8. Dependencies

- **03** — sample registry.
- **12** — physics list with `_HP` ON.
- **14** — beam-background model definitions.
- *Consumed by:* plans 32 (selection), 39 (background taxonomy),
  41 (significance), 45 (systematics), 47 (ledger).

## 9. References

- HIBEAM technical design report.
- ESS beam line documentation.
- Geant4 G4NDL data documentation.

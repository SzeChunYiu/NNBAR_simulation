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

Current source-readiness status (2026-05-10): no beam-neutron macro or
beam-neutron MCPL file is present in the local L3 worktree. The MCPL
reader implementation exists, but the current `MCPL_BUILD=1` path is
not yet a general beam-neutron input seam because the source-observed
initialisation still points at a cosmic-muon MCPL filename. Therefore
plan 22 may define the desired dataset contract, but it must not mark
`beam_neutron_hibeam_*_v1` as `draft` until either:

1. an ESS/HIBEAM beam-line MCPL file is staged and the MCPL generator
   can select it by manifest/macro, or
2. a parameterised neutron-source macro is committed with explicit
   spectrum, angular, timing, and normalisation metadata.

The source choice is tracked by **DEC-2026-05-10-2 stub — beam-neutron
source path** in plan 14. Until that stub is promoted, every beam-row in
plan 47 remains `not-attempted` or `blocked-no-sample`.

## 2. Physics-list configuration

Per plan 12 §2: **`G4HadronPhysicsFTFP_BERT_HP` is required** for beam
neutron samples. The high-precision neutron data is essential for
sub-20 MeV transport, capture, and thermalisation.

This is a separate `build_id` from the signal sample (which uses
non-HP).

A+ source check: the current L3 `PhysicsList.cc` includes both the
ordinary and `_HP` Geant4 headers, but the registered hadronic physics
constructor is still the non-HP `G4HadronPhysicsFTFP_BERT`. The beam
sample is therefore blocked on a concrete physics-list registry entry
or build switch that actually registers `_HP`. Do not infer `_HP` from
the include alone.

Required beam `build_id` payload:

- `physics_tag: ftfp_bert_hp_neutron`
- `geant4_data: G4NDL version/hash`
- `mcpl_build: 1` for MCPL source or `0` for parameterised GPS source
- `target_build: 1` unless the DEC explicitly requests a beampipe-only
  stress run
- `source_choice_decision: DEC-2026-05-10-2`
- `pileup_model: none_per_event` until plan 14's time-structure
  limitation is lifted

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

Each sub-channel manifest must preserve the parent sample hash and add
only a deterministic filter expression. The raw beam sample is the
single source of truth; derived sub-channel manifests must not rerun the
simulation with different random seeds unless plan 03 registers them as
separate productions.

Minimum manifest fields for each sub-channel:

- `parent_dataset_id`
- `filter_expression`
- `truth_columns_used`
- `class_b_decorator: labeling`
- `events_parent`, `events_selected`, and Wilson interval for
  `events_selected / events_parent` per plan 04 §4
- `source_path` and `source_sha256` for MCPL mode, or
  `parameterised_source_config_sha256` for fallback mode

## 4. Time correlation limitation

Plan 01 limitation L11 (no pile-up): the simulation does not model
beam time-structure. Beam-induced backgrounds reported here are
*per-event rates*, not per-second rates. To convert: multiply by the
beam pulse rate (≈ 14 Hz at ESS) and the per-pulse expected event
yield.

Plan 47 ledger flags this caveat on every quoted beam-background
number.

The default ledger unit is therefore a per-primary or per-generated
event probability. Conversion to per-pulse or per-year expectations
must quote the pulse-rate and live-time model as an external factor,
not as a direct simulation output. If the source is parameterised,
normalisation uncertainty is a first-class systematic in plan 45.

## 5. Sample size

Beam-rate target: bound the beam-induced false-positive rate to
1 × 10⁻⁴ per pulse at 90% C.L. Per plan 04 §5, sample size scales
similarly to plan 21 §4. Codex-supervisor proposes a target after
the user chooses (a) vs (b) in §1.

Planning bounds:

- Smoke source-readiness run: ≤ 1 000 primaries; validates file/macro
  selection, SD outputs, and plan 19 sanity plots.
- Review production: enough events to populate all four sub-channels
  with nonzero counts, or else to place a Wilson upper bound on the
  empty channels.
- Thesis-grade production: sized from the false-positive target and
  the observed review-production pass rate. No thesis-grade count is
  frozen until the source DEC and `_HP` physics-list build are both
  source-backed.

If the review run observes zero selected false positives in `N` events,
the ledger records the Wilson 90% upper bound rather than reporting
zero background.

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

## 10. A+ verifier transcript

Re-run before changing the beam-neutron sample contract:

```bash
find . -maxdepth 3 \\( -iname '*beam*' -o -iname '*neutron*' -o -iname '*.mcpl' \\)
grep -R "G4HadronPhysicsFTFP_BERT_HP\\|G4HadronPhysicsFTFP_BERT\\|MCPL_BUILD\\|G4MCPLGenerator" -n CMakeLists.txt src include macro 2>/dev/null
```

Current 2026-05-10 L3 evidence:

- The only local neutron-oriented paths are cosmic-neutron batch/macro
  paths; no beam-neutron macro or beam-line MCPL file appears in the
  max-depth-three file scan.
- `G4MCPLGenerator` exists and `MCPL_BUILD` exists, but the observed
  MCPL initialisation is not yet a beam-neutron source selector.
- `PhysicsList.cc` includes the `_HP` header but registers the non-HP
  `G4HadronPhysicsFTFP_BERT`; `_HP` is a required future beam build,
  not the current default.

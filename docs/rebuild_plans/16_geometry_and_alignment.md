---
id: 16_geometry_and_alignment
title: Geometry truth and alignment-systematic seam
version: 0.1
status: draft
owner: Sim Production
depends_on: [00_README, 01_realism_contract, 07_simulation_atomic_walkthrough, 15_material_budget]
inputs:
  - {path: NNBAR_Detector/src/detector/*.cc, schema: geometry source}
  - {path: NNBAR_Detector/docs/Detector_Geometry_Reference.md, schema: reference text}
outputs:
  - {path: docs/rebuild_plans/16_geometry_and_alignment.md, schema: this file}
  - {path: nnbar_reconstruction/_alignment/, schema: alignment scenario configs}
acceptance:
  - {test: every active geometry builder has a §-entry, method: file ↔ doc cross-reference, pass_when: full coverage}
  - {test: geometry-audit CLI passes on current main, method: cli.geometry-audit invocation, pass_when: exit code 0}
  - {test: at least three alignment scenarios are registered, method: registry review, pass_when: ≥ 3}
risks:
  - {risk: geometry refactor silently changes a thesis-quoted dimension, mitigation: plan 53 CI runs geometry-audit on every PR}
  - {risk: alignment scenarios stay theoretical and never get exercised, mitigation: plan 47 ledger requires at least one alignment systematic for any quoted vertex resolution}
estimated_effort: M
last_updated: 2026-05-09
---

# Geometry truth and alignment-systematic seam

*Charter.* Lock the geometry as built today (already audited via the
`geometry-audit` CLI, plan 08 §10) and design a misalignment seam so
that future systematic studies can apply controlled perturbations
without touching the simulation source.

## 1. Geometry as built

Active source: `NNBAR_Detector/src/detector/*.cc` (plan 07 §5.4).
Per-builder summary:

| Builder | Source | Output volumes | Audit reference |
|---|---|---|---|
| `Beampipe` | `beampipe_geometry.cc` (35 KB) | beampipe-1..N | beampipe-5: r_in 1120 mm, r_out 1140 mm, len 5000 mm |
| `Beampipe_Shielding` | `beampipe_shielding_geometry.cc` (7 KB) | shielding LVs | per geometry doc |
| `Silicon` | `Silicon_geometry.cc` (8 KB) | silicon vertex layers | per geometry doc |
| `TPC` | `TPC_geometry.cc` (12 KB) | 12 TPC modules | Type I 854×1994×2520 mm; Type II 2284×854×2520 mm |
| `Scintillator` | `Scintillator_geometry.cc` (34 KB) | 792 scintillator modules | per geometry doc; module list in `Scintillator_Module_Position.txt` |
| `LeadGlass` | `LeadGlass_geometry.cc` (19 KB) | 17972 lead-glass blocks | per geometry doc |
| `CosmicShielding` | `Cosmic_Shielding_geometry.cc` (14 KB) | shielding LVs | per geometry doc |

Codex-supervisor expands each builder's volume list to the per-volume
position/dimension/material level in v0.2.

## 2. Geometry audit CLI

`python -m nnbar_reconstruction.cli geometry-audit . --fail-on-mismatch`
(plan 08 §10) cross-checks the builders against
`docs/Detector_Geometry_Reference.md`. Required to pass before any
sample is registered as `frozen` (plan 03 §6).

## 3. Alignment as a systematic

The current configuration is *perfect alignment* — every volume sits
at its nominal position and orientation. Real detectors carry
misalignments from survey, mounting, and operating environment.

The alignment seam plugs into the geometry just before placement
(`G4PVPlacement(rotation, translation, …)`) and applies a per-LV
perturbation drawn from a scenario file:

```yaml
# alignment_scenarios/<tag>.yml
seed: 12345
scenarios:
  TPC:
    translation_sigma_mm: {x: 0.5, y: 0.5, z: 1.0}
    rotation_sigma_mrad: {x: 0.3, y: 0.3, z: 0.5}
  Scintillator:
    translation_sigma_mm: {x: 1.0, y: 1.0, z: 1.0}
    rotation_sigma_mrad: {x: 0.5, y: 0.5, z: 0.5}
  LeadGlass:
    translation_sigma_mm: {x: 0.5, y: 0.5, z: 0.5}
    rotation_sigma_mrad: {x: 0.2, y: 0.2, z: 0.2}
```

Registered scenarios (v0.1):

| Tag | Source / motivation |
|---|---|
| `perfect` | identity; matches today |
| `nominal_survey` | hypothetical survey-grade misalignment |
| `worst_case_construction` | bracket for early-commissioning |

Plan 45 systematics consumes the scenario set to produce a vertex-
resolution and π⁰-mass-width systematic.

## 4. Implementation seam

The seam lives in the per-builder `Construct_Volumes(worldLV)`
methods. A `nnbar::Alignment::Apply(transform, lv_name, scenario)`
helper returns the perturbed transform.

In `perfect` mode the helper is a no-op (the transform is returned
unchanged), satisfying plan 02's identity-default discipline.

## 5. Acceptance criteria

- §1 builder list complete; per-builder volume-level details
  populated in v0.2.
- §2 audit passes on current `main`.
- §3 ≥ 3 scenarios registered (perfect, nominal_survey, worst_case).
- §4 implementation lands in the simulation source with paired DEC
  entry.

## 6. Risks and mitigations

- *Risk:* survey-grade alignment input is unavailable for HIBEAM
  before commissioning.
  *Mitigation:* `nominal_survey` is a placeholder driven by typical
  detector survey precision; revisited at commissioning.
- *Risk:* alignment perturbation breaks the geometry-audit (positions
  no longer match the reference doc).
  *Mitigation:* the audit is run only on `perfect` configurations;
  alignment-perturbed builds are registered separately in plan 03.

## 7. Dependencies

- **07** — geometry source.
- **15** — material budget consistency post-perturbation.
- *Consumed by:* plan 25 (vertex resolution), plan 33 (truth-
  substitution ladder), plan 45 (systematics), plan 47 (ledger).

## 8. References

- `NNBAR_Detector/docs/Detector_Geometry_Reference.md`.
- `nnbar_reconstruction/geometry_audit.py` (plan 08 §10).

---
id: 33_subsystem_photon_object
title: Subsystem — photon object (leaves P.3, P.4)
version: 0.1
status: draft
owner: EM-Object POG
depends_on: [00_README, 18_intercalibration, 24_reconstruction_question_tree, 30_subsystem_vertex, 31_subsystem_calorimeter_clustering, 32_subsystem_shower_shape, 38_truth_substitution_ladder, 40_closure_and_pulls]
outputs:
  - {path: docs/rebuild_plans/33_subsystem_photon_object.md, schema: this file}
acceptance:
  - {test: photon direction pull width within plan 40 §2, method: closure plot on cal_singlegamma_v1, pass_when: pass}
  - {test: photon energy bias < 1% on cal_singlegamma_v1 in linear regime, method: closure plot, pass_when: pass}
  - {test: scintillator-fed photons (no LG hits) are tagged with leadglass_fraction = 0, method: §2 review, pass_when: implemented}
risks:
  - {risk: photon merging by direction proximity (current code) loses well-separated π⁰ daughters at small opening angles, mitigation: §3 angular threshold tuned and DEC-logged}
estimated_effort: M
last_updated: 2026-05-09
---

# Subsystem — photon object

*Charter.* Owns leaves P.3 (direction), P.4 (energy). Builds the
photon four-vector from clusters classified neutral by plan 32.

## 1. Direction (P.3)

Direction = `(cluster_centroid - event_vertex) / |…|`.

Vertex from plan 30 (V.4). Cluster centroid energy-weighted (per
plan 31).

When no event vertex is reconstructed (sparse-table fallback), use
origin → centroid; this is the historical fallback per
`reconstruction.md` lines 88–94.

Truth canonical (plan 38 §3.1): gamma momentum direction at
production.

## 2. Energy (P.4)

Energy = `lead_glass_eDep + scintillator_descendant_eDep`.

The scintillator contribution comes from gamma-shower descendants
via the same ancestry currently used in plan 31 step 1 — this needs
to migrate to topological grouping when plan 31 lands.

Scintillator-only photons (no LG cluster) are emitted with
`leadglass_fraction = 0` so the thesis Ch 8 selection
(`leadglass_fraction ≥ 0.55`) does not accept them by construction.

## 3. Photon merging

Truth-labelled neutral gamma fragments with nearly identical
reconstructed directions are merged before pairing
(`photon_fragment_merge_angle_deg = 2°`). Class B read; migration:
geometric direction-proximity merging, blind to truth labels.

## 4. Closure

`cal_singlegamma_v1` (plan 23) at energies 50, 100, 200, 500, 1000
MeV:

- Direction pull width ∈ [0.9, 1.2]; \|μ\| < 0.05.
- Energy bias < 1% in linear regime.

## 5. Acceptance criteria

- §1, §2 produce photon four-vector with stated semantics.
- §3 truth-blind merging in place.
- §4 closure passes.

## 6. Dependencies

- **18, 24, 30, 31, 32, 38, 40** — inputs.
- *Consumed by:* plan 34 (π⁰ pairing), plan 36 (event variables),
  plan 38 (ladder leaves P.3, P.4).

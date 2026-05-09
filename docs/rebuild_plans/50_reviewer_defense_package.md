---
id: 50_reviewer_defense_package
title: Reviewer defence package — canonical answer set per result
version: 0.1
status: draft
owner: Reproducibility WG
depends_on: [00_README, 01_realism_contract, 03_dataset_registry, 38_truth_substitution_ladder, 45_systematics_taxonomy, 46_significance_protocol, 47_reproduction_ledger]
outputs:
  - {path: docs/rebuild_plans/50_reviewer_defense_package.md, schema: this file}
  - {path: output/defense/<row_id>.yml, schema: per-result defence package}
acceptance:
  - {test: every thesis-quoted result has a defence package, method: ledger row cross-reference, pass_when: full coverage}
  - {test: every package has the seven blocks in §1, method: per-package review, pass_when: complete}
risks:
  - {risk: package becomes a checkbox exercise, mitigation: §3 reviewer-question registry feeds back into §1 block list}
estimated_effort: M
last_updated: 2026-05-09
---

# Reviewer defence package

*Charter.* For every quoted result, a self-contained answer set that
addresses the foreseeable reviewer questions. The package is generated
automatically from the ledger row and the registries; reviewer
discovery of a new question (plan 51) loops back into expanding §1.

## 1. Package blocks

```yaml
result_id: LIC-CH10-NUM-1
quoted_value: 0.70 ± stat ± sys
defence:
  sample:
    id: sig_foil_v3
    hash: <sha>
    geant4_version: <ver>
    physics_list: nominal (FTFP_BERT, no _HP)
    digitiser: default_identity_v1
    build_id: build-prod-<rev>
  reproducing_command: |
    python -m nnbar_reconstruction.cli validate-reco \
        NNBAR_Detector/output/sig_foil_v3 --runs 0,1,...
  ladder_sensitivity:
    primary_observable: visible_invariant_mass
    dominant_leaves: [P.4, V.4, P.3]   # IV(L) sorted
    matrix_path: output/ladder/sig_foil_v3/visible_invariant_mass.yml
  calibration_sensitivity:
    nuisances: [N1 (TPC W-value), N2 (Scint yield), N3 (LG calibration)]
    bracket: ± 0.04 (sum-in-quadrature)
  background_sensitivity:
    surviving_channels: []
    upper_limits:
      - sub_channel: cosmic_muon
        FC_90CL: < X.X × 10⁻⁵
  acceptance_footprint:
    fiducial_volume_definition: <reference plan 43>
    blind_spots: <enumerate from acceptance map>
  limitations_flags:
    - L1 (no position smearing)
    - L2 (no timing jitter)
    - L3 (no electronic noise)
    - L11 (no pile-up)
    # ... select from plan 01 §6 those that bear on this result
  decision_log_entries: [DEC-YYYY-MM-DD-N, ...]
  validation_metrics:
    pull_mean: 0.02
    pull_width: 1.05
    closure_chi2_dof: 1.1
```

## 2. Mapping reviewer questions to blocks

Plan 51's reviewer-question registry feeds back into §1. Common
questions map:

- *"Did you use truth?"* → realism audit log; check `sample.digitiser`
  and the leaf-by-leaf `Class B` flag in the ladder matrix.
- *"Reproduce your old result"* → ledger row + `reproducing_command`.
- *"Where is your error budget?"* → `ladder_sensitivity` block.
- *"What if W-value is wrong?"* → `calibration_sensitivity` block.
- *"Is your π⁰ peak fit-bias-free?"* → `validation_metrics` block.
- *"Are your event-shape variables standard?"* → cite plan 48
  (Fox-Wolfram, Bjorken-Brodsky).
- *"What if the sample is unphysical?"* → `acceptance_footprint`
  + `limitations_flags`.

## 3. Generation

A defence package is generated automatically by codex-supervisor
when:

1. A ledger row reaches green status in plan 47.
2. A new reviewer question is added to plan 51 that affects an
   existing row.

The generator joins ledger rows × dataset manifests × ladder matrices
× nuisance registry × decision log to produce the YAML.

## 4. Acceptance criteria

- §1 schema instantiated; first three defence packages produced
  for the licentiate Ch 10 cuts.
- §2 mapping covered for every entry in plan 51 v0.1.
- §3 generation automated.

## 5. Dependencies

- **01, 03, 38, 45, 46, 47, 51** — inputs.
- *Consumed by:* plan 51 (loop back), thesis chapter writing.

## 6. References

- HIBEAM PhD reproducibility appendix — defence-package precedent.

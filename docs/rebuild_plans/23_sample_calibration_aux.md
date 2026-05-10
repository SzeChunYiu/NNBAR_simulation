---
id: 23_sample_calibration_aux
title: Auxiliary calibration samples — single-particle anchors
version: 0.1
status: draft
owner: Sim Production
depends_on: [00_README, 03_dataset_registry, 17_field_calibration, 18_intercalibration]
inputs:
  - {path: docs/rebuild_plans/10_macro_and_sample_inventory.md, schema: stale/planned calibration inventory}
  - {path: NNBAR_Detector/macro/, schema: current macro tree}
outputs:
  - {path: data/registry/cal_*/manifest.yml, schema: registered samples}
acceptance:
  - {test: e±, μ±, π±, p, γ samples at fixed energies registered, method: registry coverage, pass_when: ≥ 6 species samples}
  - {test: each sample has 100 000 events for calibration precision, method: row count, pass_when: ≥ 100k}
  - {test: calibration macro inventory reconciles against the source tree, method: §3 status, pass_when: every listed macro is present/promoted or explicitly blocked-absent}
risks:
  - {risk: calibration sample list mismatched with downstream consumers (plan 18, 27, 28), mitigation: §2 consumer cross-reference}
estimated_effort: M
last_updated: 2026-05-09
---

# Auxiliary calibration samples — single-particle anchors

*Charter.* Produce, register, and freeze the single-particle samples
that anchor every calibration in the rebuild. Plans 17 (TPC field /
W-value), 18 (intercalibration), 24 (charged PID likelihood, plan
57), 27 (dE/dx), 28 (range/stopping) all consume these.

## 1. Sample matrix

Source-readiness status (2026-05-10): the current local L3 macro tree
does **not** contain `macro/calibration/`. Plan 10 §1.4 lists desired
calibration macro names, but the A+ verifier sees only `macro/signal/`
and `macro/cosmic_macro/` subtrees. The table below is therefore a
registry target, not proof of runnable calibration samples.

| Species | Energy points | Origin | Sample ID | Statistics |
|---|---|---|---|---|
| e- | 50, 100, 200, 500, 1000 MeV | foil | `cal_singleelectron_v1` | 100k each |
| e+ | same | foil | `cal_singlepositron_v1` | 100k each |
| μ- | 50, 100, 200 MeV | foil | `cal_singlemuon_v1` | 100k each |
| μ+ | same | foil | `cal_singleantimuon_v1` | 100k each |
| π+ | 50, 100, 200, 400, 600 MeV | foil | `cal_singlepionplus_v1` | 100k each |
| π- | same | foil | `cal_singlepionminus_v1` | 100k each |
| p | 50, 100, 200, 300, 500 MeV | foil | `cal_singleproton_v1` | 100k each |
| γ | 50, 100, 200, 500, 1000 MeV | foil | `cal_singlegamma_v1` | 100k each |
| MIP π+ | momentum tuned to MIP | foil | `cal_singlepion_mip_v1` | 100k |

Each origin "foil" is shorthand for emission from the foil center,
isotropic direction. Specific energy / direction grids per species
are encoded in the macro.

Until calibration macros are restored, each row enters the registry as
`blocked-missing-macro`, not `draft`. A row can become `draft` only when
the manifest names a concrete macro path, macro hash, primary species,
energy grid, direction grid, event count, and output artifact set.

Minimum manifest payload per sample:

- `sample_id`
- `species` and charge
- `energy_points_mev` or momentum point for the MIP sample
- `origin_policy` and direction policy
- `macro_path` and `macro_sha256`
- `build_knobs` observed from plan 19/20 (`MCPL_BUILD`, `TARGET_BUILD`,
  `WITH_GEANT4_UIVIS`)
- `events_requested`, `events_produced`, and output parquet hashes
- `consumer_plans` copied from §2
- `status_reason` when blocked

## 2. Consumer cross-reference

| Consumer plan | Uses |
|---|---|
| plan 17 (TPC field) | `cal_singlepion_mip_v1` for W-value MIP cross-check |
| plan 18 (intercalibration) | `cal_singleelectron_v1`, `cal_singlepion_mip_v1` |
| plan 27 (dE/dx) | all charged-particle samples |
| plan 28 (range/stopping) | `cal_singleproton_v1`, `cal_singlepion*_v1` |
| plan 29 (charged PID) | all charged-particle samples for training likelihoods |
| plan 32 (event selection) | per-species samples for N-1 / ROC studies |
| plan 57 (MVA protocol) | charged PID likelihood / BDT training |

## 3. Existing-macro disposition

Plan 10 §1.4 lists a calibration macro subtree, but the current L3
worktree has no `macro/calibration/` directory. Every plan-10 calibration
macro name is therefore classified as **blocked-absent** until L3/Sim
Production restores the file or replaces it with a new reviewed macro.
When a macro exists, it is either:

- *Promoted* to a registered sample manifest above (preserving the
  invocation), or
- *Retired* with a DEC entry stating the reason.

| Macro | Disposition |
|---|---|
| `macro/calibration/calib_quick_leadglass.mac` | blocked-absent; if restored, retire as smoke-only after an equivalent plan 19 sanity test exists |
| `macro/calibration/calib_quick_scintillator.mac` | blocked-absent; if restored, retire as smoke-only after an equivalent plan 19 sanity test exists |
| `macro/calibration/gamma_energy_scan_full.mac` | blocked-absent; target promotion → `cal_singlegamma_v1` |
| `macro/calibration/leadglass/calib_electron_validation.mac` | blocked-absent; target promotion → `cal_singleelectron_v1` |
| `macro/calibration/leadglass/calib_gamma_all_surfaces.mac` | blocked-absent; target promotion → acceptance-map auxiliary sample |
| `macro/calibration/leadglass/calib_gamma_energy_scan.mac` | blocked-absent; target promotion → `cal_singlegamma_v1` |
| `macro/calibration/pi0_calib.mac` | blocked-absent; target promotion → π⁰ calibration auxiliary |
| `macro/calibration/run_all_calibrations.mac` | blocked-absent; if restored, retire orchestration wrapper in favour of plan 52 batch system |
| `macro/calibration/scintillator/calib_pion_energy_scan.mac` | blocked-absent; target promotion → `cal_singlepionplus_v1` / `cal_singlepionminus_v1` |
| `macro/calibration/scintillator/calib_pion_minus.mac` | blocked-absent; if restored, retire if it is a subset of the energy scan |
| `macro/calibration/scintillator/calib_pion_mip.mac` | blocked-absent; target promotion → `cal_singlepion_mip_v1` |

Replacement macros must live under `macro/calibration/`, not under the
legacy `macros/` spelling, unless plan 10 is updated in the same
commit. Each restored macro receives a one-row registry stub before any
large production run.

## 3.1 Restoration order

Restore in consumer-risk order:

1. `scintillator/calib_pion_mip.mac` for plan 18 TPC↔scintillator MIP
   closure and plan 17 W-value cross-check.
2. `leadglass/calib_electron_validation.mac` for plan 18 lead-glass
   linearity.
3. `leadglass/calib_gamma_energy_scan.mac` and
   `gamma_energy_scan_full.mac` for photon response and plan 47
   lead-glass rows.
4. `scintillator/calib_pion_energy_scan.mac` for charged PID/range
   plans 27--29.
5. `pi0_calib.mac` after charged and photon primitives are source-backed.

Any replacement should first run a ≤1 000-event smoke sample and publish
plan 19 sanity plots before requesting the 100k calibration production.

## 4. Acceptance criteria

- §1 registry entries created and frozen.
- §2 every consumer has at least one sample available.
- §3 every existing calibration macro has a status.
- Sanity plots per sample (plan 19 §2) green.

## 5. Risks

- *Risk:* energy grid coverage too coarse for non-linearity studies.
  *Mitigation:* §1 grid density chosen per consumer plan; finer
  binning added on demand.
- *Risk:* foil-only origin misses geometric effects elsewhere.
  *Mitigation:* §2 acceptance-map auxiliary uses
  `calib_gamma_all_surfaces.mac` style emission from many surfaces.

## 6. Dependencies

- **03** — registry.
- **17, 18** — calibration consumers.
- *Consumed by:* plans 27, 28, 29, 32, 57.

## 7. References

- Existing `macro/calibration/` macros for invocation patterns.
- Plan 10 §1.4 macro inventory.

## 8. A+ verifier transcript

Re-run before changing the auxiliary calibration sample contract:

```bash
find macro -maxdepth 3 -type d | sort
find macro/calibration -maxdepth 3 -type f 2>/dev/null | sort
grep -R "calib_\\|calibration\\|signal_particles" -n macro macros src include 2>/dev/null || true
```

Current 2026-05-10 L3 evidence:

- `find macro -maxdepth 3 -type d` returns `macro/signal` and
  `macro/cosmic_macro/...`; no `macro/calibration` directory.
- `find macro/calibration -maxdepth 3 -type f` returns no files.
- The grep for calibration commands returns no source hits in the
  checked macro/source trees.
- Therefore every calibration macro from plan 10 §1.4 is treated as a
  blocked target until restored, not as an existing runnable file.

---
id: 20_sample_signal
title: Signal sample — n̄ annihilation on foil
version: 0.1
status: draft
owner: Sim Production
depends_on: [00_README, 03_dataset_registry, 13_signal_model, 16_geometry_and_alignment, 17_field_calibration, 19_simulation_validation_suite]
inputs:
  - {path: NNBAR_Detector/macro/signal/, schema: existing macros}
  - {path: docs/rebuild_plans/12_physics_list_audit.md, schema: nominal physics-list contract}
outputs:
  - {path: data/registry/physics_list/nominal.yml, schema: planned physics-list registry entry}
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
| Source-observed macro | `macro/signal/run_signal.mac`; no `run_signal_100k.mac` in current tree | plan 10 §1.2 and §7 verifier |
| `MCPL_BUILD` | `0` for ParticleGun smoke, `1` for the source-observed MCPL replay mode | §7 verifier |
| `TARGET_BUILD` | `1` for carbon foil placed; `0` only for beampipe/stress variants | §7 verifier |
| `WITH_GEANT4_UIVIS` | `OFF` for production/headless CI, optional `ON` configure smoke | plan 19 §4 |
| unsupported knobs | no source-observed `WITH_SCINTILLATION` or `WITH_CELERITAS`; do not gate samples on them | §7 verifier |
| Alignment scenario | `perfect` | plan 16 §3 |
| Digitiser | `default_identity_v1` | plan 02 §3 |
| Number of events | 100 000 (primary), 1 000 (smoke) | §2 |

The current source tree supports a 50k MCPL replay macro, not a
thesis-grade 100k regenerator. The primary `sig_foil_v3` target is
therefore a *registry target* until the missing 100k macro or an
equivalent two-shard 50k recipe is registered and hash-sealed in plan
03. The plan must not cite `WITH_SCINTILLATION` or Celeritas variants as
existing sample modes until their build knobs appear in the source.

## 2. Sample sizes

- *Source-observed replay shard* (`sig_foil_replay50k_v1`): 50 000
  requested events through `macro/signal/run_signal.mac`, contingent on
  staging the referenced MCPL input file. This shard is useful for
  verifying schema, provenance, and sanity plots but is not by itself
  the thesis-grade primary sample.
- *Primary sample* (`sig_foil_v3`): 100 000 events. Sufficient for
  every event-shape distribution and π⁰-mass fit at thesis precision.
  Produced either by two independent 50k MCPL replay shards with
  disjoint run ids/input hashes or by a restored, reviewed 100k macro.
- *High-statistics tail sample* (`sig_foil_highstat_v1`): 1 000 000
  events. Reserved for rare-topology studies (η/ω contamination,
  high-multiplicity events).
- *Smoke sample* (`sig_foil_smoke_v1`): 1 000 events. Fast-feedback
  for CI, using ParticleGun mode if the MCPL input is unavailable.
- *Optical-mode sample* (`sig_foil_optical_v1`): blocked until a
  source-observed scintillation/optical build mode exists. Do not mark
  this sample `draft` in the registry while the current CMake tree lacks
  the knob.

## 2.1 Required provenance fields

Each signal manifest row must carry:

- `macro_path` and `macro_sha256` for `run_signal.mac` or its reviewed
  replacement.
- `mcpl_input_path`, `mcpl_input_sha256`, and a `staged_locally`
  boolean; a missing MCPL file blocks reproduction rather than falling
  back to an unspecified generator.
- `build_knobs`: `MCPL_BUILD`, `TARGET_BUILD`, and
  `WITH_GEANT4_UIVIS`; unsupported knobs are omitted, not set to
  guessed defaults.
- `events_requested`, `events_produced`, run-number span, and output
  parquet hashes per plan 03.
- `origin_tag_policy`: foil-origin and beampipe-origin events must be
  separable before plan 47 quotes any signal acceptance number.

The first `sig_foil_v3` freeze candidate must publish a short
`output/validation/sig_foil_v3/provenance.json` containing these fields
so plan 47 rows can cite a concrete artifact instead of the macro
contract alone.

## 3. Origin tagging

Per plan 13 §7, the nominal physics target is antineutron annihilation
on the foil. Annihilation can occur on the foil (carbon) or on beampipe
silicon if the antineutron escapes the foil. The sample manifest
(plan 03) records per-event origin using the best available truth
columns plus a deterministic volume classifier tied to plan 16 geometry.
If only `Vx, Vy, Vz` are available, the classifier and its tolerance must
be written to the manifest; do not silently infer "foil" from sample
name alone.

Plan 47 ledger quotes foil-origin and beampipe-origin numbers
separately.

## 3.1 Run-state acceptance gates

`sig_foil_v3` may advance through the plan 03 registry states only when:

1. `draft`: macro path exists, build knobs resolve, and the MCPL input
   is either staged or explicitly marked blocked.
2. `review`: a smoke run has produced all SD parquet families expected
   by plan 09 and the plan 19 sanity-plot list.
3. `frozen`: 100k thesis-grade event count is reached, output hashes are
   recorded, and plan 47 has at least one signal row updated from
   `not-attempted` to `reproduced` or honest `mismatch`.

If a 50k replay shard is the only locally runnable input, the registry
stays `draft` or `review`; it must not be relabelled as the 100k primary
sample.

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

## 7. A+ verifier transcript

Re-run this verifier before changing the signal-sample contract:

```bash
ls macro/signal/run_signal.mac macro/signal/BeamOn.mac CMakeLists.txt
test ! -e macro/signal/run_signal_100k.mac
grep -R "TARGET_BUILD\\|MCPL_BUILD\\|WITH_SCINTILLATION\\|WITH_CELERITAS\\|WITH_GEANT4_UIVIS" -n CMakeLists.txt src include macro 2>/dev/null
test -f mcpl_files/NNBAR_mfro_signal_GBL_jbar_50k_9001_HIBEAM_filtered.mcpl && echo signal_mcpl_present || echo signal_mcpl_absent
```

Current 2026-05-10 evidence from the L3 worktree:

- `macro/signal/run_signal.mac` and `macro/signal/BeamOn.mac` exist.
- `macro/signal/run_signal_100k.mac` is absent, matching plan 10 §1.2.
- `CMakeLists.txt` observes `WITH_GEANT4_UIVIS`, `MCPL_BUILD`, and
  `TARGET_BUILD`; no `WITH_SCINTILLATION` or `WITH_CELERITAS` hits
  appear in the checked source paths.
- The signal MCPL file named by `run_signal.mac` is not staged under
  `mcpl_files/` in the current local L3 worktree, so local reproduction
  is blocked until that input is restored or the macro is revised.

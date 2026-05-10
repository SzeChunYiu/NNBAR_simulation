---
id: 62_detector_aging_and_radiation_damage
title: Detector aging and radiation damage — dose, response drift, mitigation
version: 0.1
status: draft
owner: Sim Production
depends_on: [01_realism_contract, 15_material_budget, 18_intercalibration, 21_sample_cosmic_CRY, 22_sample_neutron_beam, 45_systematics_taxonomy, 63_calibration_drift_monitoring]
inputs:
  - {path: docs/rebuild_plans/15_material_budget.md, schema: material inventory}
  - {path: docs/rebuild_plans/18_intercalibration.md, schema: calibration closure procedures}
  - {path: docs/rebuild_plans/22_sample_neutron_beam.md, schema: beam-neutron dose source contract}
  - {path: docs/rebuild_plans/45_systematics_taxonomy.md, schema: nuisance registry}
  - {path: docs/rebuild_plans/63_calibration_drift_monitoring.md, schema: drift-monitoring contract}
outputs:
  - {path: docs/rebuild_plans/62_detector_aging_and_radiation_damage.md, schema: this file}
  - {path: data/registry/aging/aging_model_<tag>.yml, schema: planned aging model registry}
acceptance:
  - {test: every detector subsystem has a dose driver, response observable, and mitigation, method: §2 and §5 tables, pass_when: no blank rows}
  - {test: literature constants are either backed by a resolving bib key or marked TODO, method: §3 bib audit, pass_when: no unsupported numeric constants}
  - {test: degradation model feeds plan 63 rather than silently retuning reconstruction, method: §4 review, pass_when: every response shift maps to monitor/systematic action}
  - {test: plan 01 limitation L3 remains visible, method: §6 review, pass_when: noise/threshold/nonlinearity caveat is not hidden}
risks:
  - {risk: ESS/HIBEAM dose field is unavailable, mitigation: use plan 22 source contract and keep aging constants blocked until flux is source-backed}
  - {risk: vendor data gives optical constants but not irradiation damage constants, mitigation: separate material identity citations from damage-rate TODOs}
estimated_effort: L
last_updated: 2026-05-10
---

# Detector aging and radiation damage

*Charter.* Define a source-backed model for detector response drift
from radiation exposure and calendar aging. The plan connects dose
drivers, per-subsystem aging constants, mitigation actions, and the
calibration drift monitors that prevent stale detector response from
entering thesis numbers unnoticed.

This is a planning artifact. It does not claim the current simulation
models radiation damage dynamically. Any response degradation applied
to samples must be registered as a systematic variation and reflected
in plan 47 ledger rows.

## 1. Dose model

The dose model is built from exposure components:

| Component | Source plan | Dose proxy | Status |
|---|---|---|---|
| Beam-induced neutrons and capture gammas | plan 22 | fluence and energy deposition per subsystem | blocked until beam source is source-backed |
| Cosmic muons/neutrons/gammas | plan 21 | fluence and deposited-energy maps | draft cosmic contract |
| Signal annihilation products | plan 20 | local particle fluence near foil and inner detectors | source-grounded sample target |
| Electronics environment | plan 15 material/shielding inventory | total ionising dose proxy and neutron fluence | needs electronics placement map |

For each run period, the planned registry stores:

```yaml
run_id: <run>
live_time_seconds: null
beam_pulses: null
subsystem_dose:
  tpc:
    ionising_dose_gy: null
    neutron_fluence_cm2: null
  scintillator:
    ionising_dose_gy: null
    neutron_fluence_cm2: null
  lead_glass:
    ionising_dose_gy: null
    neutron_fluence_cm2: null
  electronics:
    ionising_dose_gy: null
    neutron_fluence_cm2: null
source_datasets: []
```

No dose value is promoted until the source datasets have registry
hashes and plan 22 resolves the beam-neutron source path.

## 2. Subsystem response observables

| Subsystem | Damage driver | Response observable | Monitor |
|---|---|---|---|
| TPC gas/readout | ionisation density, gas gain drift, electronics aging | electron count per deposited MeV, dE/dx scale, noise/threshold onset | plan 17 W-value and plan 63 TPC monitors |
| Scintillator | ionising dose, fiber/paint aging, PMT gain drift | photons-per-MeV equivalent and timing response | plan 18 scintillator-yield reconciliation |
| Lead glass | optical transmission loss, PMT aging, shower leakage sensitivity | reconstructed energy linearity and per-energy residual | plan 18 lead-glass linearity |
| PMTs and front-end electronics | total ionising dose and neutron fluence | gain, dark counts, dead/noisy channels | plan 63 drift registry, future DQM TODO |
| Passive shielding/materials | activation/capture-gamma changes and mechanical drift | background rate and material budget uncertainty | plans 15, 22, and 45 |

The response observables are analysis-level Class C monitors. They do
not become Class A detector facts until real calibration sources satisfy
plan 01's upgrade criteria.

## 3. Aging constants and citation status

The A+ rule is: a numeric damage constant must have a resolving source
or remain a TODO. Material identity citations are not automatically
damage constants.

| Constant | Initial value | Citation status | Use |
|---|---:|---|---|
| BC-408 scintillator identity / baseline optical data | source-backed material datasheet | `\cite{SaintGobainBC408DataSheet}` resolves in local `ref.bib` | material identity only; not a radiation-loss coefficient |
| SF5 lead-glass identity / optical data | source-backed material datasheet | `\cite{SchottSF5DataSheet}` resolves in local `ref.bib` | material identity only; not a radiation-darkening coefficient |
| HIBEAM/NNBAR calorimeter prototype reference | source-backed detector context | `\cite{Dunne2022CalorimeterPrototype}` resolves in local `ref.bib` | lead-glass/calorimeter context |
| scintillator light-yield loss per Gy | TODO(L2-bib): add irradiation-study key | no source-backed value yet | blocked systematic coefficient |
| lead-glass transmission loss per Gy | TODO(L2-bib): add glass irradiation-study key | no source-backed value yet | blocked systematic coefficient |
| PMT gain drift per integrated charge | TODO(L2-bib): add PMT aging key | no source-backed value yet | blocked systematic coefficient |
| electronics total-ionising-dose tolerance | TODO(L2-bib): add electronics/rad-hardness key | no source-backed value yet | blocked operational threshold |

Until the TODO constants resolve, the aging model can report exposure
and response-monitor drift, but it cannot forecast quantitative
end-of-run degradation as a source-backed thesis number.

## 4. Degradation model

For a source-backed constant, degradation is represented as:

```text
response_scale(run) = 1 - k_subsystem × dose_subsystem(run)
```

where `k_subsystem` is the damage coefficient with units matching the
dose proxy. If the monitor directly measures response drift, the
measured drift supersedes the forecast for ledger/status purposes, and
the forecast becomes a prior in plan 45.

Rules:

1. Forecast degradation never edits reconstructed rows in place.
2. Aged-response samples use a new registry tag.
3. Plan 63 monitors decide whether the nominal sample remains green,
   yellow, or blocked.
4. Plan 45 receives a nuisance id for each response-shift family.
5. Plan 47 rows quote both the nominal result and the aging systematic
   where the row consumes affected observables.

## 5. Mitigation and replacement schedule

| Subsystem | Warning action | Failure action | Replacement/recalibration cadence |
|---|---|---|---|
| TPC | weekly W-value/dE/dx closure review | block new TPC-dependent ledger rows | recalibrate per monthly drift review or after gas/readout intervention |
| Scintillator | rerun MIP/yield closure and widen plan 45 nuisance | block scintillator PID/timing rows | inspect light yield quarterly; replace/repair modules after persistent fail |
| Lead glass | rerun electron/gamma linearity scans | block calorimeter energy/π⁰ rows | recalibrate monthly; replace channels with persistent transmission loss |
| PMTs/electronics | flag noisy/dead channel map | mask channel only with DEC and ledger impact | review after weekly DQM/drift failures |
| Shielding/materials | rerun background-rate comparison | block beam/capture-gamma background claims | inspect after geometry/shielding changes |

The mitigation schedule is operational. It does not grant permission to
change physics thresholds without plan 05 decision-log approval.

## 6. Realism and limitation boundary

Plan 01 limitation L3 states that deposited energy currently carries no
noise, threshold, or non-linearity. Aging can interact with all three.
Therefore:

- an aging forecast is a limitation/systematic until a detector response
  implementation exists,
- a monitor failure can downgrade a ledger row even if the simulation
  source has not changed, and
- any attempt to apply aging as a deterministic correction must go
  through plan 02 digitisation seams and plan 05 governance.

This boundary prevents an aging plan from becoming an unreviewed
post-hoc correction.

## 7. Registry schema

```yaml
id: aging_model_<tag>
status: draft | source_backed | blocked_missing_constants
dose_sources:
  - dataset_id: null
subsystems:
  - name: scintillator
    dose_proxy: ionising_dose_gy
    response_observable: photons_per_mev
    coefficient:
      value: null
      source_key: null
      status: TODO
linked_monitors:
  - drift_monitoring_<tag>
linked_nuisances:
  - aging_scintillator_light_yield
```

The registry entry is `blocked_missing_constants` until every non-null
coefficient has a resolving source key and a units check.

## 8. A+ verifier transcript

Re-run before changing source or bibliography claims:

```bash
ls docs/rebuild_plans/15_material_budget.md \
   docs/rebuild_plans/18_intercalibration.md \
   docs/rebuild_plans/22_sample_neutron_beam.md \
   docs/rebuild_plans/45_systematics_taxonomy.md \
   docs/rebuild_plans/63_calibration_drift_monitoring.md
grep "^@.*{SaintGobainBC408DataSheet," /Users/billy/Desktop/projects/overleaf-hibeam-thesis/ref.bib
grep "^@.*{SchottSF5DataSheet," /Users/billy/Desktop/projects/overleaf-hibeam-thesis/ref.bib
grep "^@.*{Dunne2022CalorimeterPrototype," /Users/billy/Desktop/projects/overleaf-hibeam-thesis/ref.bib
```

Current 2026-05-10 evidence: all referenced local plans exist, and the
three non-TODO bibliography keys resolve in the local thesis `ref.bib`.
The irradiation-damage coefficients remain TODOs because no resolving
keys were found in the local bibliography during this pass.

## 9. Acceptance criteria

- §1 dose schema is populated by source-backed datasets before any
  quantitative aging forecast is quoted.
- §3 contains no unsupported numeric damage constants.
- §4 maps every degradation to a registry tag, monitor, nuisance, and
  ledger effect.
- §5 gives each subsystem a mitigation path.

## 10. Dependencies

- **01** — limitation and Class C upgrade boundary.
- **15** — material inventory.
- **18, 63** — calibration and drift monitors.
- **21, 22** — exposure/dose source samples.
- **45** — nuisance propagation.
- *Consumed by:* plan 47 (ledger), plan 63 (drift monitoring), plan 50
  (reviewer defense package).

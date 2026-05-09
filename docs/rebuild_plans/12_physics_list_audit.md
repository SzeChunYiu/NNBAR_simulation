---
id: 12_physics_list_audit
title: Geant4 physics-list audit
version: 0.1
status: draft
owner: Physics Modeling
depends_on: [00_README, 04_statistical_uncertainty, 07_simulation_atomic_walkthrough]
inputs:
  - {path: NNBAR_Detector/src/core/PhysicsList.cc, schema: current physics list source}
outputs:
  - {path: docs/rebuild_plans/12_physics_list_audit.md, schema: this file}
  - {path: data/registry/physics_list/<tag>.yml, schema: per-list configuration record}
acceptance:
  - {test: every Geant4 physics constructor registered in PhysicsList.cc has a §-justification, method: source ↔ doc cross-reference, pass_when: full coverage}
  - {test: alternative physics lists are named with a switching procedure, method: §3 review, pass_when: ≥ 2 alternatives documented}
  - {test: antineutron annihilation cross-section comparison against a literature reference is performed, method: closure plot in plan 13, pass_when: chi-square within tolerance}
risks:
  - {risk: FTFP_BERT (no _HP) misses low-energy neutron transport, mitigation: §4 cosmic-neutron and beam-neutron studies use FTFP_BERT_HP variant; result delta is a systematic in plan 45}
  - {risk: Celeritas + non-Celeritas EM physics quietly differ, mitigation: §5 paired-sample closure test}
estimated_effort: M
last_updated: 2026-05-09
---

# Geant4 physics-list audit

*Charter.* Lock the choice of Geant4 physics list, document the
justification per registered constructor, and enumerate the alternative
configurations used as model-systematic variations. The simulation's
output validity rests on this list; we name it explicitly rather than
inheriting the default.

## 1. Current configuration

Source: `NNBAR_Detector/src/core/PhysicsList.cc` (plan 07 §4). Verbatim
constructor list (lines 71–93):

| Constructor | Purpose | Justification |
|---|---|---|
| `G4EmStandardPhysics_option4` (or `G4EmStandardPhysics` if Celeritas active) | EM (e±, γ, ions) | option4 is the highest-accuracy EM list shipped by Geant4; switched to base `G4EmStandardPhysics` only because Celeritas does not handle option4's processes (line 75). |
| `G4DecayPhysics` | Particle decays | mandatory for π⁰, π±, K, etc. |
| `G4HadronElasticPhysics` | Elastic hadronic scattering | required separately because hadron physics list omits elastic |
| `G4HadronPhysicsFTFP_BERT` (line 86) | Hadronic inelastic | FTFP (Fritiof) at high E, BERT (Bertini cascade) at low E. The `_HP` variant is **disabled** with comment "_HP will slow down a lot". §4 audits this trade-off. |
| `G4StoppingPhysics` | Stopped-particle absorption | required for stopped π-, K- |
| `G4IonPhysics` | Light-ion processes | needed for nuclear fragments |
| `G4NeutronTrackingCut` | Tracking cut for thermal neutrons | timing/energy cut to bound CPU |
| `G4RadioactiveDecayPhysics` | Decays of radioactive isotopes | needed for downstream activation in shielding |
| `G4StepLimiterPhysics` | User step-limiter support | enables `G4UserLimits` via macros / detector code |
| `G4OpticalPhysics` (gated by `WITH_SCINTILLATION` and not Celeritas) | Optical photons | drives lead-glass Cerenkov + scintillator photon yield (plan 18) |

PAI ionisation model is *available* but not invoked (lines 196–235);
plan 27 dE/dx audit decides whether to enable it for the TPC region.

Production cuts (plan 07 §3.4): 1 keV–10 TeV; default cut value
1 mm for γ, e-, e+, proton.

## 2. The `_HP` decision

Comment at `PhysicsList.cc:86`: *"_HP will slow down a lot"*. The
non-HP `G4HadronPhysicsFTFP_BERT` does not use the High-Precision
neutron data (`G4NDL`) for `E < 20 MeV`. Consequences:

- Cosmic neutron transport (plan 21) misses sub-20 MeV inelastic
  detail, which can affect capture-gamma backgrounds.
- Beam neutron transport (plan 22) is in the same regime; the HIBEAM
  beam includes thermal neutrons where `_HP` matters most.

**Decision.** Plan 12 v0.1 keeps `_HP` off for the *signal* sample
(matches licentiate baseline; plan 47 reproduction requires this) but
**requires** `_HP` ON for cosmic neutron and beam neutron samples
(plans 21, 22). The two configurations are registered as separate
build_ids in plan 03.

The signal-sample configuration without `_HP` is acceptable because
the antineutron annihilation deposits its energy via FTFP at GeV-
scale; sub-20-MeV neutron physics is irrelevant for the primary
final state. This is documented as a `DEC-YYYY-MM-DD-N` in plan 05.

## 3. Alternative physics lists (model systematics)

For systematic comparison, the audit registers these alternatives:

| Tag | Variation | Use |
|---|---|---|
| `nominal` | Current configuration as in §1 | All baseline numbers |
| `nominal_hp` | Same with `G4HadronPhysicsFTFP_BERT_HP` | Cosmic + beam neutron baseline |
| `qgsp_bert` | `G4HadronPhysicsQGSP_BERT_HP` instead of FTFP | Hadronic-model systematic (plan 45) |
| `qgsp_bic` | `G4HadronPhysicsQGSP_BIC_HP` | Alternative cascade model |
| `em_opt0` | `G4EmStandardPhysics` (no option4) | EM systematic; same as Celeritas-on path |

Plan 45 (systematics taxonomy) names how these alternatives propagate
into final analysis numbers. Plan 47 (ledger) records which
alternative is used where.

## 4. Antineutron-physics audit

Geant4's antineutron physics is delivered via the FTFP/BERT chain
(§1) and `G4StoppingPhysics`. The stopping-antineutron annihilation
on light nuclei (carbon foil, beampipe silicon) drives the multi-pion
final state we measure.

The audit does not derive new cross-sections. It cross-checks Geant4's
output against known references:

- Bench data: KEK / Brookhaven antineutron-on-deuterium / -on-carbon
  cross-section measurements (citations in plan 13).
- Branching-ratio shape: published n̄p / n̄n branching tables
  (n̄p data exists; n̄-A is theory-extrapolated — see plan 13).

Codex-supervisor produces a closure plot of Geant4 final-state
multiplicity / energy spectra against the references; the χ²/dof is
the audit metric. A failure escalates to plan 13 (signal model) where
alternative weighting is applied.

## 5. Celeritas EM closure

When `WITH_CELERITAS=ON`:

- The EM constructor switches from `option4` to base
  `G4EmStandardPhysics` (§1).
- GPU-tracked e±/γ deposits flow into `GPUEnergy_output_*.parquet`
  (plan 09 §12) instead of the CPU SDs.

The audit demands a paired-sample closure test:
identical primaries, identical seeds, run with and without Celeritas.
The two parquet sets must agree on:

- Event-level total EM eDep within `± 1%` (or a stated tolerance).
- LeadGlass / Scintillator per-block eDep within `± 5%` block-by-
  block (Celeritas SD bypass uses a different bookkeeping path).
- Charged-track kinematics unchanged (hadrons are not Celeritas-
  offloaded).

A failure flags Celeritas as non-equivalent and prevents its use in
thesis-quoted samples until reconciled.

## 6. Acceptance criteria

- §1 table is complete and matches `PhysicsList.cc` constructor
  registrations.
- §3 alternatives are registered as build_ids in plan 03.
- §4 antineutron-physics closure plot is produced and the χ²/dof is
  recorded in plan 47.
- §5 Celeritas closure is run before any Celeritas-on sample is
  promoted to thesis-quoted status.

## 7. Risks and mitigations

- *Risk:* `_HP` toggling between samples produces inconsistent
  background estimates.
  *Mitigation:* plan 03 enforces per-sample physics-list tag;
  cross-sample background calculations explicitly state which list
  was used.
- *Risk:* Geant4 cross-section data update silently shifts numbers.
  *Mitigation:* plan 03 manifest records `G4DATA` directory
  identifiers (per-data-set hashes when feasible).

## 8. Dependencies

- **04_statistical_uncertainty** — physics-list alternative deltas
  are propagated via the conventions in plan 04 §6.
- **07** — current physics list source.
- *Consumed by:* plan 13 (signal model uses these alternatives),
  plan 14 (backgrounds same), plan 21 (cosmic neutron), plan 22
  (beam neutron), plan 45 (systematics taxonomy), plan 47 (ledger),
  plan 50 (defence package).

## 9. References

- Geant4 Physics Reference Manual (current release).
- `G4HadronPhysicsFTFP_BERT[_HP]` source headers.
- KEK / Brookhaven n̄p cross-section measurements (cited verbatim in
  plan 13).

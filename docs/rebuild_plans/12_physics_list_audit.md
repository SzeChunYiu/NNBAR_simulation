---
id: 12_physics_list_audit
title: Geant4 physics-list audit
version: 0.1
status: draft
owner: Physics Modeling
depends_on: [00_README, 04_statistical_uncertainty, 07_simulation_atomic_walkthrough]
inputs:
  - {path: NNBAR_Detector/src/PhysicsList.cc, schema: current physics list source}
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
last_updated: 2026-05-10
---

# Geant4 physics-list audit

*Charter.* Lock the choice of Geant4 physics list, document the
justification per registered constructor, and enumerate the alternative
configurations used as model-systematic variations. The simulation's
output validity rests on this list; we name it explicitly rather than
inheriting the default.

## 1. Current configuration

Source: `NNBAR_Detector/src/PhysicsList.cc` (plan 07 §4), verified in
the L3 worktree at `src/PhysicsList.cc`. Verbatim constructor list
from `PhysicsList::PhysicsList()` lines 59–79:

| Constructor | Purpose | Justification + citation |
|---|---|---|
| `G4EmStandardPhysics_option4` (line 59) | EM transport for e±, γ, and charged ions | `option4` is the precision EM configuration used when CPU Geant4 owns EM showers; it is appropriate for lead-glass/scintillator energy response because it enables the more detailed EM model choices documented by the Geant4 EM manual and LHC EM-validation updates `\cite{bagulya2017recent}`. No current `src/PhysicsList.cc` line registers base `G4EmStandardPhysics`; the `em_opt0` variant in §3 is therefore a planned systematic, not a source-observed Celeritas fallback. |
| `G4DecayPhysics` | Decays of unstable particles | Required because signal final states contain π⁰/π±, kaons, eta/omega/rho daughters, and muons. The Geant4 Physics Reference Manual decay chapter defines the standard decay-process registration used here. |
| `G4HadronElasticPhysics` | Elastic hadron scattering | Needed as a separate constructor so low-energy pions, protons, neutrons, and nuclear fragments scatter elastically in material before depositing energy; Geant4's hadronic manual treats elastic and inelastic processes as distinct components. |
| `G4HadronPhysicsFTFP_BERT` (line 63) | Hadronic inelastic interactions | Provides FTFP string fragmentation at high energy and Bertini intranuclear cascade at lower energy. This matches the signal's multi-hadron annihilation/transport needs and the cosmic/beam hadronic tail; cite Fritiof/Lund model papers `\cite{Andersson:1986gw,Nilsson-Almqvist:1986ast}`, QGS/string context `\cite{Kaidalov:1983ew}`, and Bertini validation `\cite{Wright:2015xia}`. The `_HP` variant is discussed in §2. |
| `G4StoppingPhysics` | Stopped-particle absorption/annihilation | Required for stopped negative hadrons and antinucleons, including the antineutron-at-rest signal topology. The Geant4 hadronic/stopping manual covers capture and annihilation at rest, while plan 13 supplies the signal-model bibliography. |
| `G4IonPhysics` | Ion and light-fragment interactions | Needed because antineutron annihilation and neutron captures can create deuterons, alphas, and heavier nuclear fragments that transport through the detector; Geant4's ion physics manual defines the light-ion process set. |
| `G4NeutronTrackingCut` | Time/energy control for neutrons | Bounds CPU cost from long-lived thermal neutrons while preserving explicit tracking until the configured cut; this constructor is documented in the Geant4 hadronic neutron-transport guidance. Any cut value becomes a plan-03/12 build parameter for neutron-background samples. |
| `G4RadioactiveDecayPhysics` | Decays of radioactive isotopes | Needed for activation/capture products in shielding and material studies even if not part of the first thesis-rate quote. The Geant4 Radioactive Decay manual is the governing citation. |
| `G4OpticalPhysics` (lines 71–79) | Optical photons from Cerenkov/scintillation/WLS | Required for optical-mode intercalibration and for Ch5 lead-glass/scintillator photon-yield figures. The Geant4 optical-photon manual covers Cerenkov, scintillation, WLS, and boundary processes. |

No `G4StepLimiterPhysics` registration is present in the verified
constructor block, so this plan no longer counts it as a registered
constructor. If user limits become required, they need a source change
and a separate DEC entry before plan 12 can cite them.

PAI ionisation model is *available* but not invoked (helper definitions
at lines 134–173; the `AddPAIModel("pai")` call is commented out at
line 68);
plan 27 dE/dx audit decides whether to enable it for the TPC region.

Production cuts (plan 07 §3.4): 1 keV–10 TeV; default cut value
1 mm for γ, e-, e+, proton.

## 2. The `_HP` decision

The source comment beside the line-63 registration says
*"_HP will slow down a lot"*. The
non-HP `G4HadronPhysicsFTFP_BERT` does not use the High-Precision
neutron data (`G4NDL`) for `E < 20 MeV`. Consequences:

- Cosmic neutron transport (plan 21) misses sub-20 MeV inelastic,
  elastic-scattering, thermalisation, and capture detail, which can
  affect capture-gamma backgrounds.
- Beam neutron transport (plan 22) is in the same regime; the HIBEAM
  beam includes thermal and epithermal neutrons where `_HP` matters
  most.
- Signal samples can still emit secondary low-energy neutrons, but
  the thesis reproduction target is dominated by the multi-pion
  antineutron-annihilation topology and not by delayed neutron capture.

Two build tags are therefore mandatory:

| Sample class | `FTFP_BERT` without `_HP` | `FTFP_BERT_HP` | Required tag / rationale |
|---|---|---|---|
| Signal foil sample (`sig_foil_v3`) | **Baseline.** Matches the licentiate-era production choice and preserves plan-47 reproduction comparability. | Systematic cross-check only; run a paired smoke/closure sample if low-energy neutron secondaries become visible in photon/capture rows. | `nominal`: use non-HP unless a ledger row explicitly studies neutron-capture tails. |
| Cosmic CRY sample (`cosmic_cry_essLund_*`) | Not acceptable for final rate rows because cosmic neutron/proton secondaries can thermalise and capture in shielding. | **Baseline.** Captures sub-20 MeV neutron transport and capture-gamma production. | `nominal_hp`: required by plans 14 and 21. |
| Beam-neutron sample (`beam_neutron_hibeam_*`) | Not acceptable except as an explicit CPU-speed comparison. It under-models the thermal/cold neutron regime most relevant to ESS beam tails. | **Baseline.** Required for beam-neutron direct/scattered/capture-gamma sub-channels. | `nominal_hp`: required by plans 14 and 22. |

**DEC-2026-05-10-3 stub — split HP policy.** Context: `_HP` improves
low-energy neutron transport but increases CPU cost. Decision: keep
`G4HadronPhysicsFTFP_BERT` without `_HP` for the signal reproduction
baseline, and require `G4HadronPhysicsFTFP_BERT_HP` for cosmic and
beam-neutron background baselines. Rationale: signal rows need legacy
comparability and are not driven by sub-20-MeV neutron transport,
whereas background rows are. Alternatives: all samples non-HP (faster,
under-models neutron backgrounds) or all samples HP (simpler, slower,
can drift from licentiate signal reproduction). Consequence: plan 03
must register separate build IDs, plan 47 rows must cite the physics
list tag, and plan 45 treats signal non-HP vs HP deltas as a model
systematic only where neutron-capture observables enter.

## 3. Alternative physics lists (model systematics)

For systematic comparison, the audit registers these alternatives:

| Tag | Variation | Use |
|---|---|---|
| `nominal` | Current configuration as in §1 | All baseline numbers |
| `nominal_hp` | Same with `G4HadronPhysicsFTFP_BERT_HP` | Cosmic + beam neutron baseline |
| `qgsp_bert` | `G4HadronPhysicsQGSP_BERT_HP` instead of FTFP | Hadronic-model systematic (plan 45) |
| `qgsp_bic` | `G4HadronPhysicsQGSP_BIC_HP` | Alternative cascade model |
| `em_opt0` | `G4EmStandardPhysics` (no option4) | Planned EM systematic; no source-observed Celeritas fallback is currently registered in `src/PhysicsList.cc`. |

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

When a `WITH_CELERITAS=ON` build path exists:

- The EM constructor must be line-cited before use. The 2026-05-10
  source audit only finds `G4EmStandardPhysics_option4` in
  `src/PhysicsList.cc`.
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

- Geant4 Physics Reference Manual (current release): EM, decay,
  hadronic elastic/inelastic, stopping, ion, neutron tracking-cut,
  radioactive-decay, optical-photon, and user-limits chapters.
- `G4HadronPhysicsFTFP_BERT[_HP]` source headers.
- `\cite{Andersson:1986gw,Nilsson-Almqvist:1986ast,Kaidalov:1983ew}`
  for the Fritiof/string-model side of FTFP.
- `\cite{Wright:2015xia,wright2015geant4}` for Bertini-cascade validation.
- `\cite{bagulya2017recent}` for Geant4 EM physics validation updates.
- KEK / Brookhaven n̄p cross-section measurements and antineutron
  model papers cited verbatim in plan 13.

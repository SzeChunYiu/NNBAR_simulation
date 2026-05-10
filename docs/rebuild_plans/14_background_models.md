---
id: 14_background_models
title: Background models — cosmic, beam-neutron, capture-gamma
version: 0.1
status: draft
owner: Physics Modeling
depends_on: [00_README, 04_statistical_uncertainty, 12_physics_list_audit]
inputs: []
outputs:
  - {path: docs/rebuild_plans/14_background_models.md, schema: this file}
  - {path: data/registry/background_models/<tag>.yml, schema: per-source flux/spectrum}
acceptance:
  - {test: every background source has a flux/spectrum citation, method: §-by-§ review, pass_when: full coverage}
  - {test: cosmic spectrum source is named (CRY) with location/date settings, method: plan 21 cross-reference, pass_when: settings recorded}
  - {test: beam-neutron source format is named (MCPL or parameterised), method: plan 22 cross-reference, pass_when: format recorded}
risks:
  - {risk: cosmic flux changes with solar cycle / location / date; choosing one fixes a number that is itself uncertain, mitigation: §1 settings recorded; plan 45 propagates a "cosmic-flux" systematic}
  - {risk: beam-induced background underestimated by missing pile-up, mitigation: limitation L11 in plan 01; plan 02 digitisation seam closes when commissioning}
estimated_effort: M
last_updated: 2026-05-09
---

# Background models — cosmic, beam-neutron, capture-gamma

*Charter.* For each background source, name the flux/spectrum
generator, the physics it captures, the alternatives used as
systematics, and the limitations. This plan provides the modelling
inputs to plans 21 (cosmic sample), 22 (beam-neutron sample), and
44 (background taxonomy).

## 1. Cosmic-ray background

### 1.1 Source: CRY (LLNL Cosmic-Ray Shower library)

Plan 21 integrates CRY. CRY parameters fixed here and cross-checked
against plan 21 §1:

| Parameter | Value | Justification / source |
|---|---|---|
| Latitude | 55.7° N | ESS Lund coordinate used by plan 21 §1. |
| Altitude | 10 m a.s.l. | Lund-site altitude used by plan 21 §1. |
| Date | 2026-06-01 | Provisional solar-modulation date; plan 21 marks this as user-confirmed before freeze. |
| Solar modulation | CRY default for date | Included in the CRY model; plan 45 carries the residual cosmic-flux nuisance. |
| Particle types enabled | µ, e±, γ, n, p | Atmospheric mixture needed for muon, EM, and hadronic sub-channels. |
| Sample box dimensions | full detector + 5 m overburden | Matches plan 21 §1 sample-box definition; overburden variants are in plan 21 §2. |
| Sample box top altitude | 10 m above ground | Plan 21 §1; separates site altitude from generator plane height. |

**DEC-2026-05-10-1 stub — CRY site/date freeze.** Context: CRY
flux depends on latitude, altitude, date, and solar modulation. Decision:
Wave 2 freezes the cosmic baseline at ESS Lund latitude 55.7° N,
altitude 10 m a.s.l., CRY date 2026-06-01, and CRY's default solar
modulation for that date. Rationale: this matches plan 21 §1 and makes
cosmic-rate rows reproducible while preserving a plan-45 cosmic-flux
systematic. Alternatives: use the legacy per-species macros only, or
scan several dates across the solar cycle. Consequence: `cosmic_cry_essLund_*`
manifest rows must include these values and cite this DEC stub until a
formal plan-05 entry is promoted.

### 1.2 Sub-channels

Cosmic-induced backgrounds enter the analysis as separate sub-channels
(plan 44):

- *Cosmic muon traversal.* The dominant rate; rejected by timing,
  topology, and energy.
- *Cosmic electron / gamma showers.* Lower rate; produce EM activity
  similar to π⁰ decays.
- *Cosmic neutrons / protons.* Hadronic contribution; rare but
  can mimic charged final states.

### 1.3 Comparison to current per-species macros

The licentiate's `macro/cosmic_macro/cosmic_<species>/run_<n>.mac`
set (plan 10 §1.3) emits each species independently from a
parameterised distribution. Plan 21 documents the differences:

- CRY emits an *atmospheric mixture* in correct flux ratios.
- Per-species macros are useful for studying the per-species
  acceptance but not for total cosmic rate.
- Plan 21 keeps both — CRY for the rate; per-species for the
  per-channel breakdown.

### 1.4 Limitations

- L6 (no beam time-structure) → no pile-up between cosmic and
  signal events.
- L7 (perfect alignment) → no cosmic-induced misalignment fakes.
- L8 (no ageing) → no environmental drift in cosmic veto.
- Solar-cycle / location / date sensitivity → §1.1 records a
  specific point; plan 45 includes a "cosmic flux" nuisance.

## 2. Beam-induced neutron background

### 2.1 Source

HIBEAM beam line at ESS. The beam neutrons that reach the NNBAR
detector are a tail of the spallation source spectrum, after the
beam line's optics, choppers, and shielding.

The simulation consumes either:

- An MCPL file produced by ESS beam-line simulation (preferred).
- A parameterised flux + spectrum sampled directly by
  `G4MCPLGenerator` or by GPS commands (`/source/...`).

Plan 22 chooses between these two paths and records the choice.

### 2.2 Sub-channels

- *Direct beam neutrons.* Penetrate to detector volume.
- *Scattered neutrons.* Off beampipe / collimator / shielding.
- *Capture-gamma cascade.* Neutron capture on hydrogenous shielding,
  iron, lead, etc., producing γ cascades that look EM-like.
- *Secondary hadronic fragments.* From neutron inelastic on detector
  materials.

Each sub-channel becomes a node in plan 44 background taxonomy.

### 2.3 Beam time-structure

The ESS beam is pulsed (≈ 14 Hz, ≈ 2.86 ms long pulse). Pile-up of
beam-induced neutrons within a pulse is the dominant rate-effect.

The current rebuild does *not* model beam time-structure (limitation
L6). Plan 22 documents the consequence: the simulation reports
per-event rates that must be folded with the beam structure when
quoting per-second rates.

### 2.4 Physics-list requirement

Beam neutron transport requires `_HP` per plan 12 §2 (low-energy
neutron data). Plan 22's build configuration sets
`G4HadronPhysicsFTFP_BERT_HP`.

## 3. Capture-gamma background

A subset of §2 but called out separately because it can mimic π⁰
decay photons. Sources:

- Thermal-neutron capture on hydrogenous shielding: 2.2 MeV gamma
  from H(n,γ) — well below the π⁰-mass window but contributes to
  pile-up scintillator energy.
- Thermal-neutron capture on iron: ≈ 7.6 MeV cascade — broad,
  affects scintillator and lead-glass.
- Capture on lead (Pb-208): broad multi-line cascade up to
  ≈ 7 MeV — affects lead-glass.

These are not generated *separately* from §2; they are output of
neutron transport plus capture physics in the simulation.

## 4. Other backgrounds (registered, lower priority)

- *Environmental gamma.* Room background; plan 01 limitation L7
  notes it is unmodelled.
- *Detector-internal.* Scintillator self-radioactivity, lead-glass
  spontaneous photoelectron emission. Unmodelled; see L4 and the
  digitisation seam in plan 02.
- *Beam-pipe activation.* Long-term n-induced activation; unmodelled
  (L8).

These are explicitly out of scope for the rebuild's first cycle and
appear in plan 01 §6 limitations registry.

## 5. Acceptance criteria

- §1.1 CRY parameters are recorded in
  `data/registry/background_models/cosmic_cry_essLund_v1.yml`.
- §2.1 beam-neutron source format is decided and recorded in
  `data/registry/background_models/beam_neutron_hibeam_v1.yml`.
- §1.2 and §2.2 sub-channel lists feed plan 44 background taxonomy.
- §3 capture-gamma channels are exercised by a closure plot in
  plan 47 ledger (ratio of capture-gamma vs neutron event rate).

## 6. Risks and mitigations

- *Risk:* cosmic-rate point estimate over- or under-states the
  background by ~10% due to solar cycle.
  *Mitigation:* plan 45 nuisance parameter "cosmic flux" with
  ±15% range.
- *Risk:* beam-neutron MCPL file format / sourcing changes between
  ESS releases.
  *Mitigation:* plan 22 freezes the input file's hash in the
  registry; an upstream update creates a new dataset version.

## 7. Dependencies

- **04** — uncertainty propagation.
- **12** — physics-list selection per source (HP for neutron sources).
- *Consumed by:* plan 21 (cosmic), plan 22 (beam), plan 44 (taxonomy),
  plan 45 (systematics), plan 46 (significance).

## 8. References

- LLNL CRY library: <https://nuclear.llnl.gov/simulation/>
- ESS Beam Line technical design (HIBEAM project documents).
- Geant4 G4NDL data documentation.

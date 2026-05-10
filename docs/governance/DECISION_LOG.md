# NNBAR rebuild — decision log

This file is the source of truth for methodology decisions per
`docs/rebuild_plans/05_decision_log.md` §1. Entries are append-only.
The auto-generated index lives at `DECISION_LOG_INDEX.md`.

Approved entries are immutable in body. Supersession is recorded by
appending a new entry that fills the `Superseded by` link on the old
entry — the only write allowed against an approved entry.

The methodology council reviews drafts. Once an entry is approved its
status flips and the body is locked.

Stubs awaiting sign-off live in `DEC_BACKLOG.md` until promoted here.

---

## DEC-2026-05-10-1
**Topic.** CRY cosmic-flux site/date freeze.
**Status.** approved
**Owners.** Cosmic-bg POG (ESS Lund site lead)
**Plans affected.** 14, 21, 45
**Code touched.** `src/cosmic/CRYGenerator.cc`, `macro/cosmic_macro/cry_*.mac`
**Samples affected.** `cosmic_cry_essLund_*` (plan 21 §1)

### Context
CRY's atmospheric-mixture sampler depends on latitude, altitude, date,
and solar modulation. Without a frozen point, every cosmic rate row in
plan 47 would drift run-to-run as the user re-runs CRY. Plan 14 §1.1
records a candidate point but flags it as decision-pending so plan 47
ledger rows could not freeze.

### Decision
Freeze the cosmic baseline at ESS Lund — latitude **55.7° N**,
altitude **10 m a.s.l.**, CRY date **2026-06-01**, and CRY's default
solar modulation for that date. The frozen point is mandatory for any
cosmic-rate row quoted in the thesis or in plan 47. Solar-cycle
sensitivity is captured by the plan 45 cosmic-flux nuisance, not by
re-running CRY at alternate dates.

### Rationale
This matches plan 21 §1's sample-box definition and plan 14 §1.1's
candidate point, makes cosmic rows reproducible across user-run and
CI-run, and preserves a meaningful systematic via plan 45 rather than
through ad-hoc CRY re-sampling. Variation across the solar cycle is a
documented model uncertainty (≈ 5–10% on rate), bracketed by the
nuisance.

### Alternatives considered
1. **Per-species macros only** (legacy mode) — rejected: licentiate
   uses these but loses correct atmospheric-mixture flux ratios; plan
   21 keeps them for per-channel breakdown only.
2. **Scan dates across solar cycle** — rejected for production: too
   many manifest variants; left as an optional plan-45 systematic
   exercise.
3. **Freeze at solar-min instead of 2026-06-01** — rejected: solar-min
   is conservative for muon flux but not representative of run-period
   conditions.

### Consequences
- `cosmic_cry_essLund_*` manifest rows must include latitude /
  altitude / date / solar-modulation fields and cite this DEC entry.
- Plan 14 §1.1 stub paragraph is now superseded; the table values are
  authoritative.
- Plan 45 gains a `cosmic_flux` nuisance that brackets ±10% on the
  cosmic rate to absorb solar-cycle and atmospheric-model uncertainty.

### Supersedes / Superseded by
- Supersedes: none.
- Superseded by: (none yet)

### References
- `docs/rebuild_plans/14_background_models.md` §1.1
- `docs/rebuild_plans/21_sample_cosmic_CRY.md` §1
- CRY documentation, LLNL-TR-228478 (Hagmann et al. 2007)

---

## DEC-2026-05-10-3
**Topic.** FTFP_BERT physics-list `_HP` split policy.
**Status.** approved
**Owners.** Simulation WG
**Plans affected.** 03, 12, 14, 21, 22, 45, 47
**Code touched.** `src/physics/PhysicsList.cc`
**Samples affected.** `sig_foil_v3` (non-HP), `cosmic_cry_essLund_*` (HP), `beam_neutron_hibeam_*` (HP)

### Context
`G4HadronPhysicsFTFP_BERT_HP` improves sub-20 MeV neutron transport
and capture-gamma production but raises CPU cost ~2–3×. The signal
sample's licentiate-era reproduction baseline used the non-HP variant;
re-running it under HP would silently re-derive every plan-47 signal
row. Background samples however are dominated by exactly the regime HP
fixes.

### Decision
Use **`G4HadronPhysicsFTFP_BERT`** (without `_HP`) for the signal
sample (`sig_foil_v3`) as the reproduction baseline. Use
**`G4HadronPhysicsFTFP_BERT_HP`** for both the cosmic
(`cosmic_cry_essLund_*`) and beam-neutron (`beam_neutron_hibeam_*`)
samples, where neutron transport and capture physics dominate the
observable rate. Plan 12 §3 registers a paired HP signal sample as a
`physics_list` systematic for plan 45 only when neutron-capture
observables enter a quoted result.

### Rationale
Signal observables are dominated by anti-nucleon annihilation kinematics
and pion final-state interactions; the sub-20-MeV neutron tail does not
drive them. Background observables are. Splitting the policy preserves
licentiate signal reproduction (plan 47) while keeping background tails
physical. The CPU cost is concentrated where it matters.

### Alternatives considered
1. **All samples non-HP** — rejected: under-models cosmic /
   beam-neutron capture-gamma backgrounds; plan 14 §3 cannot close.
2. **All samples HP** — rejected for production: silently rewrites
   licentiate signal rate rows and breaks plan 47 reproduction. Kept
   as a paired systematic sample only.
3. **Use `QGSP_BERT_HP` everywhere** — rejected as the production
   default (registered as `qgsp_bert` model systematic in plan 12 §3
   instead).

### Consequences
- `docs/rebuild_plans/03_dataset_registry.md` registers separate
  `physics_list` build IDs per sample.
- `docs/rebuild_plans/47_reproduction_ledger.md` rows must cite the
  physics-list tag (`nominal` vs `nominal_hp`).
- Plan 45 carries the non-HP-vs-HP delta only on observables that
  involve neutron capture (e.g. capture-gamma rate in EM clusters).

### Supersedes / Superseded by
- Supersedes: none.
- Superseded by: (none yet)

### References
- `docs/rebuild_plans/12_physics_list_audit.md` §2
- `docs/rebuild_plans/14_background_models.md` §2.4
- Geant4 Physics Reference Manual (release 11.x) — neutron-HP package.
- A. Ribon et al., Geant4 hadronic physics validation (CALOR proceedings).

---

## DEC-2026-05-10-5
**Topic.** TPC W-value production constant for ionisation accounting.
**Status.** approved
**Owners.** Tracking POG (TPC SD lead)
**Plans affected.** 09, 17, 18, 27, 47
**Code touched.** `src/sd/TPCSD.cc`
**Samples affected.** all current-version samples (W-value enters every
`tpc_eDep` → `tpc_n_electrons` conversion)

### Context
The as-built `TPCSD` output uses **W = 23.6 eV** to convert deposited
energy to electron counts. The Ar/CO₂ (90/10) gas reference is
**26.0–27.4 eV** (PDG; Sauli, CERN 77-09). Changing the production
value would silently rewrite every electron-count and dE/dx observable
in already-frozen samples, breaking plan 47 reproduction.

### Decision
Keep **W = 23.6 eV** as the production constant for all current rebuild
reproduction rows and frozen `sig_foil_v3`-style samples. Treat
**W = 26.0 eV** as the reference alternative for closure plots and
plan 45 systematic reweighting. Promote a future DEC entry that flips
the production value once a new dataset version is regenerated end-to-end.

### Rationale
Reproduction comparability with the licentiate (already-published
results, plan 47) outweighs the per-event W-value bias for current rows.
The 26.0 eV reference is correct for Ar/CO₂ and is preserved as a
documented systematic so the bias is explicit, not hidden. Future
samples (plan 03 next-version) will adopt the reference value.

### Alternatives considered
1. **Promote 26.0 eV immediately** — rejected: silently rewrites every
   electron-count row in `sig_foil_v3` and the corresponding plan-47
   ledger numbers without a new dataset version.
2. **Use a per-sample W** — rejected: complicates plan 18 closure and
   plan 47 cross-sample comparisons.

### Consequences
- Plan 09 §Class C declares `tpc_w_value_ev` as a calibration constant
  with two values (`production: 23.6`, `reference: 26.0`).
- Plan 17 §2 closure procedure uses the reference value as the target.
- Plan 27 dE/dx documents the bias direction (slightly low) in its
  alternatives table.
- Plan 45 carries `tpc_w_value` as a nuisance with a one-sided
  reweighting prescription (production → reference).

### Supersedes / Superseded by
- Supersedes: none.
- Superseded by: (none yet)

### References
- `docs/rebuild_plans/17_field_calibration.md` §2
- `docs/rebuild_plans/18_intercalibration.md` §2
- F. Sauli, *Principles of operation of multiwire proportional and
  drift chambers*, CERN 77–09 (1977).
- PDG Review of Particle Physics, "Passage of particles through matter".

---

## DEC-2026-05-10-2
**Topic.** Beam-neutron source path: MCPL preferred, parameterised fallback.
**Status.** approved (provisional auto-approval; user delegated DEC sign-off)
**Owners.** Beam-line POG (ESS HIBEAM contact pending)
**Plans affected.** 14, 22, 44, 45
**Code touched.** `src/sources/G4MCPLGenerator.cc` (MCPL path), `macro/beam_neutron/*.mac` (parameterised path)
**Samples affected.** `beam_neutron_hibeam_*`

### Context
HIBEAM beam neutrons reaching the NNBAR detector are the tail of the
spallation source spectrum after beam-line optics, choppers, and
shielding. The simulation can consume either an MCPL file from the
ESS HIBEAM beam-line simulation (preserving correlations) or a
parameterised flux + spectrum (reproducible without external file
but model-limited). Plan 22 had the parameterised fallback wired up
but plan 14 §2 could not freeze `beam_neutron_hibeam_*_v1` manifests
without a decision.

### Decision
Use **MCPL from the ESS HIBEAM beam-line simulation as the nominal
path** for `beam_neutron_hibeam_*_v1` manifests once the ESS team
delivers a provenance-sealed MCPL file. Until delivery, use the
**parameterised flux + spectrum as a model-limited fallback**, with
every produced row tagged `beam_neutron_model_only=true` so plan-45
systematics can carry the model uncertainty explicitly. Re-promote
this DEC when the MCPL file arrives, with the file hash and source
plane definition recorded.

### Rationale
MCPL preserves beam-line correlations (energy / angle / time) that a
sampled spectrum cannot encode; these correlations matter for
secondary backgrounds (capture-gamma cascades, scattered tails). The
sequencing recipe (parameterised → MCPL when available) keeps the
rebuild iterating without blocking on external delivery, and the
`beam_neutron_model_only` tag prevents accidental promotion of
parameterised-baseline rows into final results.

### Alternatives considered
1. **Parameterised-only first pass** — rejected as final: omits
   beam-line correlations.
2. **Dual-run comparison (MCPL nominal, parameterised systematic)**
   — kept as a future option for plan 45 once the MCPL file is in.

### Consequences
- Plan 22 freezes the parameterised-fallback manifest with the
  `beam_neutron_model_only=true` tag.
- Plan 14 §2 references this DEC as the source-path policy.
- Plan 45 carries a `beam_neutron_source` nuisance that brackets the
  parameterised-vs-MCPL difference; collapsed to "model-form only"
  while MCPL is unavailable.
- Once MCPL arrives, supersede this DEC with one that pins the file
  hash and source plane.

### Supersedes / Superseded by
- Supersedes: none.
- Superseded by: (none yet)

### References
- `docs/rebuild_plans/14_background_models.md` §2.1
- `docs/rebuild_plans/22_sample_neutron_beam.md` §1
- ESS HIBEAM technical-design beam spectrum.
- MCPL standard: J. Bowman et al., *Comp. Phys. Comm.* 218 (2017) 17.

---

## DEC-2026-05-10-4
**Topic.** Alignment scenario sigma grid — placeholder-with-trigger.
**Status.** approved (provisional auto-approval; user delegated DEC sign-off)
**Owners.** Detector-mechanics POG (ESS survey contact pending)
**Plans affected.** 16, 25, 30, 45
**Code touched.** `src/detector/AlignmentScenario.cc`
**Samples affected.** all alignment-systematic samples

### Context
Vertex and object-systematics studies need a concrete, repeatable
perturbation grid for alignment scenarios. ESS/HIBEAM survey
constants are not yet available, but plan 16 §2 needs to register
named scenarios so plan 30 (vertex) and plan 25 (TPC tracks) can
consume them and plan 45 can carry an alignment systematic.

### Decision
Register **three scenario tags** with engineering-prior placeholder
sigmas:

- `perfect` — identity (0, 0, 0) translation and rotation σ.
- `nominal_survey` — translation σ ≈ 1 mm (silicon/TPC), 5 mm
  (shared shielding); rotation σ ≈ 0.5 mrad (silicon/TPC), 2 mrad
  (shared).
- `worst_case_construction` — 2× the nominal sigmas; deliberately
  wider commissioning bracket.

Every alignment-systematic row in plan 45 is tagged
`alignment_uses_placeholder_sigmas=true` until the ESS detector
survey is delivered. **Trigger:** when the ESS survey lands, supersede
this DEC with one carrying the measured covariances; the placeholder
tag flips off only after that promotion.

### Rationale
The rebuild cannot block plan-30 closure or plan-45 alignment
systematics on external survey delivery, but quoting any thesis
result against placeholder sigmas would mislead a reviewer. The
trigger + tag mechanism keeps work flowing while making the
provisional nature explicit and grep-able.

### Alternatives considered
1. **Defer alignment scenarios entirely** — rejected: blocks plans
   25, 30, 45 from closing.
2. **Single nominal scenario** — rejected: removes the
   commissioning-bracket lever that plan 45 needs.
3. **Adopt ATLAS/CMS published alignment σ as proxy** — kept as a
   sanity-cross-check inside plan 16 §3 but not as production sigmas
   (NNBAR geometry is too different).

### Consequences
- Plan 16 §2 registers the three scenarios with the placeholder
  values.
- Plan 25, 30 closure tests run against all three scenarios.
- Plan 45 `alignment` nuisance uses the `worst_case_construction`
  delta; flagged `placeholder` until trigger.
- Plan-47 ledger rows that depend on alignment carry the
  placeholder tag.

### Supersedes / Superseded by
- Supersedes: none.
- Superseded by: (none yet)

### References
- `docs/rebuild_plans/16_geometry_and_alignment.md` §2
- ATLAS Run-2 alignment paper (proxy cross-check).
- CMS tracker alignment review (proxy cross-check).

---

## DEC-2026-05-10-6
**Topic.** Scintillator yield mode policy — fast/optical split.
**Status.** approved (provisional auto-approval; user delegated DEC sign-off)
**Owners.** Scintillator POG
**Plans affected.** 09, 18, 33, 47
**Code touched.** `src/sd/ScintillatorSD.cc`, `src/detector/Scintillator_geometry.cc`
**Samples affected.** all scintillator-yield rows in plan 47 ledger

### Context
The scintillator photon-equivalent count uses **11136 photons/MeV**
in the SD (`reconstruction.md` line 105) but the optical-mode
material-properties table uses **10000 photons/MeV**. Existing
reconstruction code consumes the 11136 value; optical-on samples
generate from 10000.

### Decision
Keep **11136 photons/MeV** as the production value for fast-mode
photon-equivalent rows. Keep **10000 photons/MeV** as the optical
material-table value in optical-on samples. When comparing
optical-on to fast-mode quantities, apply a **`11136 / 10000 = 1.1136`
scale factor** explicitly. Mode-tag every sample so the ledger and
plan 18 closure procedures can pick the correct comparison.

### Rationale
Both values are correct for their respective code paths. The fast
mode is calibrated against the 11136 constant; the optical mode
uses a physically motivated photon yield. Forcing equality would
require silently rewriting one of the two paths and breaks
reproduction in the other. The explicit scale factor makes the
discrepancy transparent and reviewable.

### Alternatives considered
1. **Adopt 10000 everywhere** — rejected: silently rewrites every
   fast-mode plan-47 row.
2. **Adopt 11136 everywhere** — rejected: contradicts optical
   material model; plan 18 §3 closure fails.
3. **Per-row scale at analysis time** — kept; this is the chosen
   path. The 1.1136 factor lives in plan 18 §3.

### Consequences
- Plan 09 declares `scintillator_yield_photon_per_mev` as a
  Class C calibration with two values (`fast_mode: 11136`,
  `optical_mode: 10000`).
- Plan 18 §3 procedure documents the 1.1136 scale.
- Plan 47 ledger rows carry a `scintillator_mode` tag.
- Plan 45 carries `scintillator_yield_mode` as a one-sided
  systematic (fast→optical reweighting), bounded by the 1.1136
  factor uncertainty.

### Supersedes / Superseded by
- Supersedes: none.
- Superseded by: (none yet)

### References
- `docs/rebuild_plans/18_intercalibration.md` §3
- `src/sd/ScintillatorSD.cc` (11136 constant)
- `src/detector/Scintillator_geometry.cc` optical properties (10000)

---

## DEC-2026-05-10-7
**Topic.** Cross-repository mirror policy — live-pointer to HIBEAM.
**Status.** approved (provisional auto-approval; user delegated DEC sign-off)
**Owners.** Methodology Council
**Plans affected.** 05, 09, 13, 38, 57

### Context
The HIBEAM TPC vertex-reconstruction repository has its own decision
log. Decisions made there (truth-vertex source, MVA feature schemas,
unit conventions) materially affect this rebuild. Plan 05 §6 specifies
that cross-repo decisions should be mirrored, but did not commit to
*how* — frozen-snapshot copy or live pointer.

### Decision
Adopt a **live-mirror pointer** for cross-repo decisions. The
DECISION_LOG entry on our side is short and references the HIBEAM
original by ID; we do not duplicate the body. Any update to the
original on the HIBEAM side propagates to us via a monthly
methodology-council review per plan 05 §6.

### Rationale
A frozen-snapshot copy duplicates editorial overhead and creates
drift risk: when HIBEAM revises a mirrored decision, our copy can
silently disagree with the upstream truth. A live pointer keeps the
two repos consistent at the cost of a monthly check; the cost is
small relative to the consistency win.

### Alternatives considered
1. **Frozen-snapshot copy** — rejected: drift risk over a
   multi-year run.
2. **No mirror; cite HIBEAM directly in plan bodies** — rejected:
   reviewers expect to find the decision in our log too.

### Consequences
- DEC-2026-04-24-1 (HIBEAM, vertex truth = CSV) is mirrored as a
  live pointer; cited by plans 09, 13, 38.
- DEC-2026-05-08-1 (HIBEAM, MVA feature schema) is mirrored as a
  live pointer; cited by plan 57.
- Methodology council carries a monthly cross-repo drift check.

### Supersedes / Superseded by
- Supersedes: none.
- Superseded by: (none yet)

### References
- `docs/rebuild_plans/05_decision_log.md` §6
- HIBEAM repository `docs/governance/DECISION_LOG.md`.

---

## DEC-2026-05-10-8
**Topic.** `reconstruction.py` 500-line refactor split.
**Status.** approved (provisional auto-approval; user delegated DEC sign-off)
**Owners.** Reconstruction WG (L3 lane)
**Plans affected.** 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37
**Code touched.** `nnbar_reconstruction/reconstruction.py`,
`charged.py`, `photon.py`, `vertex.py`, `electron.py`,
`event_variables.py`, `selection.py`, plus per-leaf modules
(`charged_pid.py`, `dedx.py`, `range_reco.py`, `track_fit.py`,
`shower_shape.py`, `pi0_pairing.py`, `kinematic_fit.py`,
`calorimeter_clusters.py`, `photon_objects.py`).

### Context
`reconstruction.py` had grown to 1062 lines, violating the
CODING_STANDARDS §1 500-line cap by 2.1×. Subsystem plans 25–37
referenced functions in the monolith with `reconstruction.py:N-M`
line refs that were systematically wrong (off by 50–150 lines or
past EOF). The rebuild needed a per-subsystem split before
plans 25–37 could carry resolvable citations.

### Decision
Split `reconstruction.py` into **per-subsystem modules**:

- `charged.py`, `charged_pid.py`, `dedx.py`, `range_reco.py`,
  `track_fit.py` — charged-side (plans 25–29).
- `vertex.py` — vertex (plan 30).
- `photon.py`, `photon_objects.py`, `calorimeter_clusters.py`,
  `shower_shape.py`, `pi0_pairing.py` — EM-side (plans 31–34).
- `kinematic_fit.py` — kinematic fit (plan 35).
- `event_variables.py` — event variables (plan 36).
- `selection.py` — event selection (plan 37).
- `electron.py` — electron-pair reconstruction.

`reconstruction.py` retains a re-export shim (≤ 100 lines) for
backward import compatibility for **2 weeks** post-merge, then is
deleted.

### Rationale
Per-subsystem modules: (a) honour the 500-line cap, (b) make plan
25–37 line refs resolvable since each plan owns one or two files,
(c) make per-subsystem unit testing tractable. Keeping the shim
preserves any external-import callers during the transition;
deleting it forces callers to migrate to the new module names.

### Alternatives considered
1. **Two-way split (charged.py + photon.py)** — rejected: still
   over the 500-line cap on each.
2. **Keep monolith, just add line markers in plan citations** —
   rejected: doesn't fix the coding-standards violation.
3. **Permanent re-export shim** — rejected: defers cleanup
   indefinitely.

### Consequences
- Plans 25–37 line refs now resolve; `scripts/verify_citations.py`
  passes against them.
- pytest suite expanded to 128 passing tests (was 63 before split).
- Backward-compatibility shim removed after 2026-05-24 (2 weeks).
- Any downstream user of `from nnbar_reconstruction.reconstruction
  import …` must migrate to the per-subsystem module by then.

### Supersedes / Superseded by
- Supersedes: none.
- Superseded by: (none yet)

### References
- `docs/rebuild_plans/refactor/reconstruction_py_split.md`
- `CODING_STANDARDS.md` §1 (500-line cap)
- L3 commit series: `refactor(electron)`, `feat(charged)`,
  `feat(photon)`, `feat(vertex)`, `refactor(reconstruction)`.

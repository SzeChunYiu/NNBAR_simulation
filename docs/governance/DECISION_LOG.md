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

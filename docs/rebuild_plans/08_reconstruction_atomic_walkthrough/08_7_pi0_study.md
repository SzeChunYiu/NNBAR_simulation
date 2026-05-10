---
id: 08_7
title: Reconstruction atomic walkthrough — pi0 study
version: 0.1
status: draft
owner: Reproducibility WG
depends_on: [08_reconstruction_atomic_walkthrough]
inputs:
  - {path: NNBAR_Detector/nnbar_reconstruction/pi0_study.py, schema: source file}
outputs:
  - {path: docs/rebuild_plans/08_reconstruction_atomic_walkthrough/08_7_pi0_study.md, schema: split walkthrough section}
last_updated: 2026-05-10
---

# π⁰ study — split from plan 08

This split file preserves and deepens plan 08 §7 so the main walkthrough
stays below the 500-line cap.

## 7. π⁰ study (pi0_study.py, 1974 lines)

The 2 KLOC file implements the truth-vs-reco π⁰ mass ladder used to
explain the thesis Chapter 8 selection and to prototype plan 38's
truth-substitution ladder. It is being documented in multiple logical
units.

Public surface currently detected from source:

- `two_photon_mass_mev(energy1, direction1, energy2, direction2)`
- `evaluate_pi0_mass_ladder(output_dir, run, reconstruction)`
- `event_rows(report)`

### 7.1 Constants and stage schema

- `PI0_MASS_MEV = 134.9768` (`pi0_study.py:16`) is the reference mass
  used by stage summaries.
- `MASS_STAGE_COLUMNS` maps ladder stage names to row columns for truth
  daughters, truth-direction/reco-energy, reco-direction/truth-energy,
  full reco, truth-matched full reco, global and cross-validated energy
  scales, photon-response scales, and containment-binned scales
  (`pi0_study.py:17–31`). These are study-output columns, not raw
  parquet columns.

### 7.2 `two_photon_mass_mev(energy1, direction1, energy2, direction2)`

**Source:** `NNBAR_Detector/nnbar_reconstruction/pi0_study.py:75–91`.

**Inputs:** two photon energies in MeV and two direction vectors supplied
by callers inside the study. No parquet columns are read directly by this
helper. In the larger ladder, energies and directions may come from Class
B truth daughters, reconstructed photon rows, or mixed truth/reco rungs;
those caller-specific column reads are documented with
`evaluate_pi0_mass_ladder` in later §7 units.

**Decision rule:** if either energy is non-finite or negative, return
`NaN` (`pi0_study.py:83–84`). Directions are normalized with
`_unit_vector`; zero or non-finite vectors return `NaN` (`pi0_study.py:85–88`).
The invariant mass assumes two massless photons:
`mass² = 2 * energy1 * energy2 * (1 - dot(u1, u2))`, with the dot product
clipped to [-1, 1] and negative roundoff protected by `max(mass2, 0)`
(`pi0_study.py:89–91`).

**Outputs:** one float mass in MeV, or `NaN` when inputs are unusable.

**Truth reads:** none directly.

### 7.3 `evaluate_pi0_mass_ladder(output_dir, run=0, reconstruction=None)`

**Source:** `NNBAR_Detector/nnbar_reconstruction/pi0_study.py:1876–1968`.

**Inputs:** an output directory, a run number, and optionally precomputed
reconstruction tables. The function loads raw parquet tables with `load_run`
(`pi0_study.py:1883–1885`) and uses `Particle`, `Interaction`, `LeadGlass`,
and `Scintillator` raw tables plus reconstructed `photons` and `pi0` tables
(`pi0_study.py:1887–1899`). Relevant raw columns are `Particle.Event_ID`,
`Particle.Name`, optional `Particle.Mass`, `Interaction.Event_ID`,
`Interaction.Track_ID`, `Interaction.Parent_ID`, `Interaction.Name`,
`Interaction.KE`, optional `Interaction.Proc`, and optional momentum
`px/py/pz` (`pi0_study.py:1459–1565`). Plan 09 classifies `Event_ID` as
Class A and particle/interaction identity, ancestry, momentum, kinetic energy,
and masses as Class B truth (§3–§4). Raw lead-glass and scintillator deposits
are grouped through `_leadglass_shower_sources` and `eDep` sums
(`pi0_study.py:1412–1456`). Reconstructed photon and π⁰ inputs use the plan 09
§14.4–§14.5 columns documented in plan 08 §3.5.

**Decision rule:** truth π⁰ events are the union of primary/intermediate rows
where `Name == "pi0"` in `Particle` or `Interaction` (`pi0_study.py:1459–1467`,
`1892`). Truth gamma records are selected from interaction rows named `gamma`
that either come from primary π⁰ decay (`parent_id == 1` and `Proc == "decay"`)
or have a π⁰ ancestor; records are sorted by descending energy and track id
(`pi0_study.py:1506–1565`). For each truth π⁰ event, `_row_for_event` builds a
truth/reco ladder row (`pi0_study.py:1900–1912`): it initializes a wide row
schema, records raw detector deposits for each truth gamma, computes truth-only
mass and opening-angle pass/fail, counts neutral reco photons, matches truth
gammas to reco photons by source-track aliases, computes truth-direction/reco-
energy and reco-direction/truth-energy masses, and selects either the exact
truth-matched reco π⁰ candidate or the nominal candidate closest to the π⁰ mass
(`pi0_study.py:1615–1873`).

After row construction, the function applies three reporting-only calibration
families: global/event-parity energy scale, photon-response scale, and
containment-binned scale (`pi0_study.py:1912–1915`; helper implementations begin
at lines 173, 244, and 435). It then computes photon diagnostics, quality
slices, candidate taxonomy, π⁰ selector scan, truth-gamma coverage, and
reco-only neutral lineage diagnostics (`pi0_study.py:1916–1926`). Stage summaries
are computed for every `MASS_STAGE_COLUMNS` entry against `PI0_MASS_MEV` with
`_stage_summary` (`pi0_study.py:1928–1934`). Event efficiencies are counts of
rows with finite `full_reco_mass` and `truth_matched_full_reco_mass` divided by
truth π⁰ event count (`pi0_study.py:1935–1956`).

**Outputs:** a JSON-safe dict with `run`, `truth_pi0_events`, matched/candidate
reco event counts and efficiencies, the three calibration summaries,
`candidate_taxonomy`, `pi0_selection_scan`, `truth_gamma_coverage`,
`reco_only_neutral_lineage`, `photon_diagnostics`, `quality_slices`, per-stage
mass summaries, and per-event rows (`pi0_study.py:1946–1968`).

**Truth reads:** extensive Class B truth reads by design: particle/interaction
names, masses, track ids, parent links, gamma kinetic energy/momentum, and
shower-source ancestry. This module is a validation/study ladder, not a live
reconstruction decision path.

### 7.4 `event_rows(report)`

**Source:** `NNBAR_Detector/nnbar_reconstruction/pi0_study.py:1971–1974`.

**Inputs:** the dict returned by `evaluate_pi0_mass_ladder`.

**Decision rule:** no filtering; returns `pd.DataFrame(report.get("events", []))`.

**Outputs:** one DataFrame containing the per-event mass-ladder row schema built
by `_row_for_event` and augmented by the calibration helpers.

**Truth reads:** none directly; truth dependence is already materialized in the
report rows.

### 7.5 Remaining private-helper detail

The public surfaces are now named here, but future passes should still deepen the
large private helper families if plan 38 needs exact formulas for the energy
scale, photon-response model, containment bins, quality slices, candidate
taxonomy, selector scan, and neutral-lineage diagnostics.

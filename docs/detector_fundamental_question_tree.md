# NNBAR Detector Fundamental Question Tree

Date: 2026-05-08

Scope: detector-related discussion for `/Volumes/MyDrive/nnbar/nnbar/simulation`.

This note recursively expands the detector questions from the top-level physics
goal down to the irreducible measurements. It separates questions already
answerable from the repository from questions that still require simulation or
calibration evidence.

## Evidence Anchors

- The active detector source is `NNBAR_Detector/src/detector/*.cc`; legacy
  `src/Detector_Module/*.cc` is not compiled.
- `python -m nnbar_reconstruction.cli geometry-audit . --fail-on-mismatch`
  passes under `/Users/billy/miniforge3/bin/python`.
- The audit verifies beampipe-5, TPC, scintillator, and lead-glass geometry
  against `NNBAR_Detector/docs/Detector_Geometry_Reference.md`.
- The shared YAML config is not a trustworthy detector-geometry authority yet:
  validation docs mark scintillator and lead-glass geometry values as outdated.

## Root Question

Can this detector configuration prove an antineutron annihilation candidate from
detector observables alone, without relying on simulation truth labels?

Current answer: not yet. Geometry is now machine-checkable, and reconstruction
interfaces exist, but the fundamental proof still depends on measured detector
response, truth-free reconstruction closure, and background rejection evidence.

## 1. What Must Be Observed?

Question: what is the minimal detector evidence for an annihilation?

Answer now: a credible candidate needs a foil-compatible vertex near `z=0`,
multiple charged or neutral final-state objects, calorimeter/scintillator energy
consistent with annihilation debris, and event-shape variables that distinguish
multi-particle topology from beam, cosmic, gamma, or secondary backgrounds.

Deeper question: which observables are essential rather than convenient?

Working answer:
- TPC: charged track directions, dE/dx, and vertex constraint.
- Scintillator: timing, range, and visible energy.
- Lead glass: electromagnetic shower energy and photon/pi0 reconstruction.

Next measurement: build a per-event information-gain table showing which
detector observables change signal/background separation most.

## 2. Is The Geometry Reliable?

Question: is the implemented detector geometry internally consistent?

Answer now: yes for the audited surfaces. The live audit verifies:
- beampipe-5: inner radius `1120 mm`, outer radius `1140 mm`, length `5000 mm`.
- TPC: 12 modules in front/back rings, with Type I `854 x 1994 x 2520 mm`
  and Type II `2284 x 854 x 2520 mm`.
- scintillator: 792 modules total; lead glass: `17972` blocks.

Deeper question: does correct construction imply correct physics acceptance?

Answer now: no. Construction correctness only proves the detector was built as
specified. It does not prove uniform acceptance, alignment tolerance, dead
regions, threshold robustness, or background leakage.

Next measurement: generate acceptance maps by particle type, energy, direction,
surface, and origin radius; report blind spots, not only average efficiency.

## 3. Can The TPC Carry The Vertex?

Question: can TPC hits reconstruct primary charged tracks without truth?

Answer now: partially. The reconstruction docs support charged-track candidates,
foil-plane projection, and vertex reconstruction. Existing notes also say
primary `Parent_ID=0` tracks are the right truth target for training/evaluation,
not for final reconstruction logic.

Deeper question: is the TPC response physically calibrated enough?

Known concern: the validation report flags a W-value mismatch. `TPCSD.cc` uses
`23.6 eV` per electron-ion pair, while the TPC material comments and validation
discussion point to about `26-27.4 eV` for the Ar/CO2 mixture. This affects
electron counts and therefore dE/dx-like features.

Fundamental question: what is the minimum TPC evidence that a vertex is real?

Working answer: at least two independent reconstructed track directions should
project consistently to the foil with angle- and quality-dependent residuals,
and with no truth label in the decision path.

Next measurements:
- run a truth-free clustering/vertex closure study with truth used only after
  reconstruction for scoring.
- replace empirical vertex angular uncertainty with binned residual lookup.
- audit TPC electron-count calibration under CPU, Garfield, and GPU modes.

## 4. Can Scintillator Separate Charged Energy From Neutral Contamination?

Question: what does scintillator actually measure?

Answer now: the sensitive detector records deposited energy and converts it to a
photon-like count using `11136 photons/MeV`. The material optical table uses
`10000 photons/MeV` when scintillation is enabled and `0` when fast mode disables
optical photons. This means eDep-derived and optical-derived response surfaces
must not be mixed without calibration.

Deeper question: can scintillator alone identify charged particles?

Answer now: no. The PID docs report that most scintillator energy in pi0 events
can come from gamma interactions. Scintillator is useful for timing/range/energy,
but charged-neutral separation needs TPC and lead-glass context.

Working answer: it should constrain event time, charged-particle range, and
global visible energy. It should not be the only authority for particle charge.

Next measurement: compare charged primary, gamma-conversion, neutron, and cosmic
scintillator response in the same reconstruction format and tune timing/range
cuts from that study.

## 5. Can Lead Glass Carry Neutral Reconstruction?

Question: is lead-glass geometry and readout present?

Answer now: geometry is verified, position files fail closed when missing, the
sensitive detector records lead-glass energy deposits, and PMT readout exists
for optical photons in a narrow energy window.

Deeper question: is the current lead-glass response usable in all run modes?

Answer now: no. A validation baseline records zero lead-glass hits because
optical photons were disabled. That baseline cannot validate neutral
reconstruction or pi0 performance.

Working answer: a neutral object needs a shower centroid, calibrated energy,
direction from a reconstructed vertex, charged-track veto, timing compatibility,
and pi0 mass closure when paired with a second photon.

Next measurements:
- run paired samples with optical off/on and compare eDep, Cerenkov photon, and
  PMT surfaces.
- validate charged-cluster veto with TPC-projected charged tracks.
- measure pi0 mass bias by separating direction error from energy response.

## 6. Are We Avoiding Truth Leakage?

Question: does reconstruction use truth columns to make final decisions?

Answer now: the reconstruction docs describe a transition toward geometry-based
matching, with truth labels retained for validation and sparse-table fallback.
That is the right direction, but it needs an explicit no-truth-leakage gate.

Deeper question: what is allowed to use truth?

Working answer:
- Allowed: training labels, validation scores, diagnostics, acceptance maps.
- Not allowed: production candidate selection, event vertexing, charged-neutral
  matching, or final PID decisions.

Next measurement: add a reconstruction audit that fails if `Name`, `Track_ID`,
  or `Parent_ID` changes final candidate decisions outside declared validation
  or fallback modes.

## 7. What Backgrounds Must Be Beaten?

Question: which false candidates are structurally dangerous?

Working answer:
- gamma conversions that look like charged activity.
- secondary hadronic fragments near the foil.
- cosmic rays that cross several detector layers with convincing timing.
- beamline or material interactions upstream/downstream of the target plane.
- optical-disabled or GPU-fallback modes that silently change observables.

Answer: a background is irreducible only if it produces the same joint
distribution in vertex, timing, PID, shower topology, energy, and event shape
after detector calibration. Anything else should become a measured veto or a
quantified systematic.

Next measurement: construct background-specific control samples and score them
with the same truth-free reconstruction used for signal.

## 8. Measurement Priority

The next detector work should be ordered by dependency:

1. Geometry acceptance maps, because all later efficiency claims depend on them.
2. Calibration consistency audit for TPC W-value, scintillator yield, lead-glass
   response, and YAML-vs-source drift.
3. Truth-free reconstruction closure on MCPL annihilation events.
4. Background control samples scored through the same reconstruction chain.
5. Ablation study ranking TPC, scintillator, lead-glass, and timing features by
   signal/background separation power.

Completion criterion for this phase: a detector-readiness table where every
candidate observable is marked as one of `geometry verified`, `response
calibrated`, `truth-free validated`, `background-veto validated`, or `blocked`.

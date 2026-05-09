---
id: 01_realism_contract
title: Realism contract — what reconstruction is allowed to read
version: 0.1
status: draft
owner: Software Quality
depends_on: [00_README]
inputs:
  - {path: NNBAR_Detector/output/*.parquet, schema: simulation outputs, produced_by: 07_simulation_atomic_walkthrough}
outputs:
  - {path: docs/realism_contract.md, schema: column-class table + audit spec}
  - {path: nnbar_reconstruction/_realism.py, schema: decorator markers}
  - {path: tests/test_realism_audit.py, schema: CI audit gate}
acceptance:
  - {test: every parquet column is classified A/B/C, method: full enumeration in §3, pass_when: classification table covers all columns}
  - {test: reco function reading Class B outside marked context, method: static AST audit, pass_when: zero violations}
  - {test: limitations registry is complete, method: review by Methodology Council, pass_when: signed by supervisor}
risks:
  - {risk: Class C calibration drift goes unnoticed, mitigation: every Class C column carries a "would change with real data" flag and a calibration-source citation}
  - {risk: audit too strict, breaks legitimate diagnostic flows, mitigation: explicit @diagnostic_only and @validation_only decorators}
estimated_effort: M
last_updated: 2026-05-09
---

# Realism contract — what reconstruction is allowed to read

*Charter.* This plan partitions every column in every simulation output
file into three classes and specifies the static audit that fails if a
reconstruction function reads a truth-only column outside an explicitly
marked diagnostic or validation context. It is the load-bearing rule
that prevents the rebuild from drifting into truth-leaked reconstruction
without notice. Every other plan inherits this contract.

## 1. Why this exists

The simulation writes both *sensor-equivalent* outputs (energy deposits,
hit positions, hit times, optical photon counts) and *Monte Carlo truth*
(`Track_ID`, `Parent_ID`, particle name, primary momentum, particle ancestry).
Both live in the same parquet files, side by side, because Geant4 has no
reason to separate them. A reconstruction function that calls
`hit_table["Parent_ID"]` is silently using truth and looks identical to a
function that calls `hit_table["edep_MeV"]`. A reviewer cannot tell from
the function body alone which class the function depends on.

The contract makes the class explicit at the column level, enforces it
with a static audit, and gives the rebuild a defensible answer to the
single most damaging reviewer question: *"are you using truth?"*

## 2. The three classes

### Class A — experiment-equivalent

A column is Class A iff, in a real HIBEAM/NNBAR detector with a
realistic DAQ, an analogue of this column would appear in the recorded
data. Class A is what a reconstruction algorithm is allowed to use in
its decision path.

Examples (per current schemas, full enumeration in §3):

- `x_mm`, `y_mm`, `z_mm` of a TPC hit (sensor coordinates)
- `t_ns` of a hit (timing)
- `edep_MeV` of a calorimeter cluster (deposited energy)
- `n_optical_photons` recorded by a PMT
- `cluster_id` derived purely from Class A inputs

A simulation step that records the *exact* MC truth in a column that
also has a Class A counterpart (e.g. true position vs. reconstructed
position) is *Class B*. Position is Class A iff there is a
sensor-resolution path that produces it; in the perfect-detector
configuration we currently run, Class A position equals MC truth
position. This identity is documented as a known limitation
(§6 limitations registry, item L1) but does not promote the column to
Class B because a future digitisation seam (plan 02) will degrade it
without changing the column name.

### Class B — truth-only

A column is Class B iff it has *no* sensor-equivalent. It is truth.
Reconstruction is *forbidden* to read Class B columns in its decision
path. Validation, diagnostics, and label generation may read Class B
under explicit decorators (§5).

Examples:

- `Track_ID`, `Parent_ID` (Geant4 internal book-keeping)
- `Name` (PDG particle name)
- `primary_kinetic_energy_MeV` of the truth particle
- `MCPL_event_index`
- entries in the `Interaction` table (decay/process ancestry)

### Class C — MC-tuned calibration constants

A column or constant is Class C iff it is a calibration value derived
from the simulation that, in a real detector, would be replaced by a
data-driven calibration. Class C is *allowed* in reconstruction but
must carry:

- a `would_change_with_real_data: true` flag in the schema documentation,
- a citation to the calibration source (file, line, source publication),
- a propagated uncertainty (per plan 04 statistical uncertainty).

Examples:

- TPC W-value (`23.6 eV` in `TPCSD.cc`; ionisation energy per electron-ion
  pair; in real detector, derived from gas calibration)
- Scintillator photon yield (`11136 photons/MeV`; in real detector,
  tied to MIP response calibration)
- Lead-glass energy calibration (linearity & non-linearity; in real
  detector, anchored to test-beam electron energy)
- PMT quantum efficiency curve

## 3. Per-attribute partition

The full classification table is maintained in plan 09 (IO schema /
data dictionary). The current realism contract delegates the *per-column*
listing to plan 09 and constrains itself to *rules* for classification:

1. *Position columns* on hits — Class A (with limitation L1).
2. *Timing columns* on hits — Class A (with limitation L2: no jitter modelled).
3. *Energy deposit / charge / photon-count columns* on hits — Class A
   (with limitation L3: no electronic noise, no threshold, no
   non-linearity, no saturation). 
4. *MC particle identifiers* (`Track_ID`, `Parent_ID`, `Step_ID`) — Class B.
5. *MC particle attributes* (`Name`, `pdg_code`, primary kinematics,
   creation process) — Class B.
6. *Ancestry tables* (`Interaction`, parent maps, decay chains) — Class B.
7. *Geometry-derived constants* (volume IDs, module indices) — Class A
   when they are read from sensor identifiers a real DAQ would produce
   (channel ID, module ID); Class B when they are Geant4-internal volume
   pointers without a DAQ analogue.
8. *Calibration constants* compiled into the simulation (W-value, photon
   yield, calibration curves) — Class C.
9. *Reconstruction outputs* — derived class equal to the *worst*
   (least-realistic) input class. A reco column built from any Class B
   input is Class B and must live in a `*_truth` or `*_diagnostic` table.

Plan 09 instantiates these rules against every concrete column produced
today. Codex-supervisor refuses to merge changes to plan 09 that
contradict the §3 rules without an accompanying decision-log entry
(plan 05) explaining the exception.

## 4. The static audit

The audit is a Python AST-walking script that runs in CI (plan 53). It
reads every module under `nnbar_reconstruction/` and:

1. Enumerates every read access of a parquet column (subscripts on
   DataFrames, calls to `.column(...)`, `.field(...)`, attribute access
   on row objects, etc.).
2. Resolves the column name against plan 09's classification table.
3. Walks up the AST to find the enclosing function.
4. Inspects the function's decorators (§5).
5. Emits a violation when a Class B column is read inside a function
   without a permissive decorator.

Audit invocation:

```bash
python -m nnbar_reconstruction.audit.realism \
    --schema docs/rebuild_plans/09_io_schema_data_dictionary.md \
    --source nnbar_reconstruction/ \
    --json output/audits/realism.json \
    --fail-on-violation
```

Exit codes:

- `0` — no violations.
- `1` — one or more Class B reads outside permissive decorators.
- `2` — schema/source unparseable; the audit refuses to run rather than
  pass spuriously.

The audit is added to the CI matrix in plan 53. Pull requests that
introduce a violation are blocked.

## 5. Decorator markers

Three decorators in `nnbar_reconstruction/_realism.py` mark functions
that are permitted to read Class B columns:

- `@validation_only` — the function exists to score reconstruction
  against truth (e.g. `pi0_mass_validation`). It is never called from
  the production reconstruction path. The audit verifies no
  non-validation function transitively calls a `@validation_only`
  function on a non-validation code path.
- `@diagnostic_only` — the function emits diagnostic columns into a
  diagnostic table that the production selection cut-flow does not
  consume. Diagnostic columns are namespaced with a `diag_` prefix.
- `@labeling` — the function generates training labels for an MVA
  (plan 57). Labels are written into a dedicated label table that
  inference code never reads.

Codex-supervisor maintains the canonical list. New decorators require a
plan revision (00 §8) and a decision-log entry (05).

## 6. Limitations registry

The simulation does not model the following effects. Each becomes a
known limitation that downstream plans cite when reporting numbers, and
each closes when the corresponding upgrade lands (plan 02, plan 47).

| ID | Limitation | Where it bites | Closes when |
|---|---|---|---|
| L1 | Position is exact MC truth (no sensor resolution) | Vertex resolution, π⁰ mass width, TPC track angles | digitisation seam (plan 02) installs hit-position smearing |
| L2 | Time is exact MC truth (no jitter) | Timing-window cuts, in-time/out-of-time energy split, photon-flight-time consistency | digitisation seam installs timing jitter |
| L3 | Deposited energy carries no noise, threshold, or non-linearity | Calorimeter resolution, scintillator threshold efficiency, lead-glass linearity at high E | digitisation seam installs energy noise model |
| L4 | No electronic dead channels or hot channels | Acceptance maps, fiducial cuts | digitisation seam installs channel-mask layer |
| L5 | No DAQ trigger, no readout dead-time, no buffer overflow | Live-time fraction, instantaneous-rate effects | trigger/DAQ model added (out of current scope) |
| L6 | No beam time-structure / bunch structure | Pile-up, bunch-crossing identification | beam-structure model added (plan 22, partial) |
| L7 | No real alignment systematics; geometry is exact | Vertex bias, track-to-cluster matching | alignment scenarios applied (plan 16) |
| L8 | No detector ageing / temperature drift | Long-run stability | ageing model (out of current scope) |
| L9 | No B-field (TPC drift only) | Charge-sign determination, momentum measurement | B-field option added (plan 17, future) |
| L10 | Calibration constants are MC-tuned (Class C, not data-tuned) | All energy-calibrated observables | data-tuned calibration available (post-commissioning) |
| L11 | No pile-up between cosmic and signal events | Joint cosmic+signal occupancy | beam-time-structure model + overlay infrastructure |
| L12 | Optical-photon path on/off changes the lead-glass observable | Photon energy via Cerenkov vs eDep | intercalibration plan 18 closes the gap |

Every quoted result in the rebuild references the limitations that
apply to it. Plan 50 (reviewer defence package) reads this registry and
attaches the relevant entries to each result automatically.

## 7. Realism upgrade gate

A Class C column is upgraded to Class A only after:

1. A real-detector calibration source is named and accessible
   (test-beam, gas calibration, MIP fit on data, etc.).
2. The calibration uncertainty is propagated through plan 04 and
   reflected in the result's reviewer-defence package (plan 50).
3. A decision-log entry (plan 05) records the upgrade, the supersession
   of any prior simulation-tuned constant, and the new uncertainty.
4. Plan 09 (data dictionary) is updated; the audit re-runs green.

Codex-supervisor blocks the upgrade if any of (1)–(4) is missing.

A Class C column is *not* upgraded merely because the calibration is
fitted on a Geant4 sample. Self-consistency in MC is not data
calibration; it remains Class C with a clearer source citation.

## 8. Acceptance criteria

The plan is considered signed (status: signed) when:

- Every column in every parquet output (current and planned) is listed
  in plan 09 with an A/B/C classification and a §3 rule citation.
- The static audit runs in CI on every PR and is green on the current
  `main`.
- Every Class C column has a `would_change_with_real_data: true` flag
  and a calibration-source citation.
- The limitations registry §6 has been reviewed by the Methodology
  Council and signed by the supervisor.
- A worked example showing a Class B violation being caught by the
  audit lives in `tests/test_realism_audit.py`.

## 9. Risks and mitigations

- *Risk:* the audit catches false positives because column-name
  resolution is incomplete (DataFrame aliases, `getattr`, dynamic
  column lookup).
  *Mitigation:* the audit conservatively flags any unresolved access on
  a parquet-derived object and requires the developer to annotate or
  refactor. False positives are treated as a code-clarity defect, not
  an audit defect.
- *Risk:* Class C drift — a constant marked Class C is silently used as
  if it were Class A, e.g. a calibration result is promoted into a
  publication number without uncertainty propagation.
  *Mitigation:* the reviewer-defence package (plan 50) computes a
  calibration-sensitivity bracket for every result; missing brackets
  block sign-off.
- *Risk:* limitations registry rots — the simulation gets a feature
  closing L4 but the registry isn't updated.
  *Mitigation:* the simulation walkthrough (plan 07) cross-references
  the registry; CI fails if a closed limitation is still referenced.

## 10. Dependencies

- **00_README** — defines the plan ID space and sign-off chain.
- *Consumed by:* plan 02 (digitisation seam respects this contract),
  plan 09 (instantiates the partition per column), plan 50 (reviewer
  defence package consumes the registry), plan 53 (CI runs the audit).

## 11. Out of scope

- Real-data calibration (plan operates on simulation outputs only).
- Trigger / DAQ realism (handled by future plan, not in this rebuild).
- Detector commissioning effects (alignment, ageing) beyond what plans
  16–17 cover.

## 12. Open questions

- Should the audit be advisory or blocking on a first pass? *Default:
  blocking on the foundational set of modules; advisory on
  `pi0_fake_study.py` and `charged_study.py` which already have
  truth-aware code paths. Codex-supervisor proposes the cutover plan.*
- Do we want a Class D for "experiment-equivalent in principle but
  unmodelled today" (e.g. a sensor channel that exists in real DAQ but
  is not simulated)? *Default: no, fold into limitations registry.*

## 13. References

- `docs/detector_fundamental_question_tree.md` §6 — *"Are we avoiding
  truth leakage?"* This plan is the answer to that question's
  *next-measurement* line.
- `13_HIBEAM_reproducibility_appendix.tex` — claim-evidence ledger
  pattern; this plan supplies the truth-leakage audit that the ledger
  cites.

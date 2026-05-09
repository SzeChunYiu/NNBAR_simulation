---
id: 00_README
title: NNBAR simulation & reconstruction rebuild — master plan
version: 0.1
status: draft
owner: Methodology Council
depends_on: []
inputs: []
outputs:
  - {path: docs/rebuild_plans/, scope: full plan set}
last_updated: 2026-05-09
---

# NNBAR simulation & reconstruction rebuild — master plan

This document is the single entry point for the rebuild of the NNBAR Geant4
simulation and offline reconstruction. Everything else in `docs/rebuild_plans/`
is consumed in the order this plan declares.

The goal is not "ship code." The goal is to produce a simulation +
reconstruction framework whose every numeric claim, figure, and method choice
can be defended in front of a thesis committee, a HIBEAM/NNBAR collaboration
review, and a referee at a particle-physics journal. We organise the work the
way ATLAS and CMS organise theirs: explicit working groups, explicit sign-off
chains, explicit decision logs, explicit reproducibility artefacts.

This plan does not contain implementation. Implementation is performed by the
codex-supervisor project against the plans listed below. Plans are normative;
code follows.

---

## 1. Mission and scope

### 1.1 Mission statement

Reproduce every numeric and graphical result in chapters 5–10 of the licentiate
thesis and the live PhD thesis (Sze Chun Yiu, "HIBEAM/NNBAR annihilation
detector development — Towards a computational framework for the experiment").
Then improve every reconstruction method in a controlled, evidence-driven way
where each improvement is scored against a fixed truth-substitution ladder and
does not regress any reproduction-ledger row that has already turned green.

### 1.2 Scope — in

- The Geant4 detector simulation under `NNBAR_Detector/` (chapters 5, 6).
- The offline reconstruction under `nnbar_reconstruction/` (chapters 7, 8, 9).
- The cut-based event selection (chapter 10 *Event_selection*).
- Cosmic-ray background (CRY-based regeneration + thorough study rework).
- Beam-induced neutron background (regeneration + thorough study rework).
- Auxiliary single-particle calibration samples needed by the reconstruction.
- All process artefacts: dataset registry, decision log, reproduction ledger,
  reviewer-question registry, ATLAS-INT-style notes, CI regression suite.

### 1.3 Scope — out (explicit)

- The HIBEAM TPC vertex-reconstruction GNN study (chapter 10
  `10_HIBEAM_TPC_vertex_reconstruction.tex` of the live PhD thesis). That study
  belongs to a separate HIBEAM repository with its own decision log and its own
  reproducibility appendix (chapter 13). It is referenced here only when the
  NNBAR reconstruction borrows an algorithmic concept from it.
- Real detector commissioning, data-taking, and trigger/DAQ work. The rebuild
  assumes a perfect detector now (see plan 01) with a designed seam for a
  realistic upgrade later (see plan 02).
- Final ESS engineering decisions. The simulation reflects the current best
  HIBEAM/NNBAR detector concept; updates are tracked through plan 11.

### 1.4 Two coupled deliverables

Every plan in this set produces output along two axes:

1. **Reproduction.** The thesis-as-written must be reproducible from the code
   on the named samples. Reproduction is gated by plan 42.
2. **Improvement.** Methods are improved only against a measured error budget
   (plan 33), not against intuition.

Plans that improve a method without first reproducing it are rejected at
review. Plans that reproduce without explaining the leaf-level error budget
are accepted but flagged as incomplete.

---

## 2. Reading order

A new reader (codex-supervisor, supervisor, examiner, future maintainer)
should read in this order:

1. **00 (this file)** — what we are doing, who owns what, how we sign off.
2. **01, 02** — the realism contract that bounds every other plan.
3. **05, 06** — how decisions are recorded and reviewed.
4. **03, 04** — the data and uncertainty conventions every numeric claim uses.
5. **07–11** — *what currently is*: forensic, atomic walkthrough of the
   existing Geant4 simulation and reconstruction. Read this before any
   improvement plan.
6. **12–15** — the input physics; everything downstream is a transformation of
   these.
7. **24** — the recursive decomposition of reconstruction. Subsystem plans
   (25–37) are dependent leaves of this tree.
8. **38, 39, 40** — the validation instruments. These define what "improved"
   means quantitatively.
9. **20–23** — sample regeneration. Cannot start before 24 stabilises observable
   acceptance criteria; can start in parallel with 16–19.
10. **16–19** — simulation-engineering inputs to the samples.
11. **25–37** — subsystem deep dives.
12. **41–46** — analysis-level studies.
13. **47–51** — reproduction, accountability, reviewer defence.
14. **52–56** — operations and packaging.
15. **57** — MVA protocol (referenced by 29, 32, 37).

Anyone reading without going through 00–06 first will mis-execute. The
foundational plans are the rules that prevent silent drift.

---

## 3. Working-group structure

We mirror ATLAS/CMS practice with explicit Physics Object Groups (POG),
Combined Performance (CP), Production, Analysis, Reproducibility, and Software
Quality groups. Each group has a charter, an owned set of plans, and a
defined sign-off authority. Membership in this rebuild may be small (the user
plus codex-supervisor instances), but the *roles* are kept distinct because
defensibility depends on role separation.

### 3.1 Working groups

| WG | Charter | Owns plans |
|---|---|---|
| **Methodology Council** | Cross-cutting decisions, plan revisions, gate sign-off | 00, 05, 06, 24, 48, 49 |
| **Sim Production** | Sample generation, run orchestration, hash sealing, baseline simulation walkthrough | 03, 07, 10, 11, 16, 17, 19, 20, 21, 22, 23, 52 |
| **Physics Modeling** | Geant4 physics list, signal/background channels, material budget | 12, 13, 14, 15 |
| **Tracking POG** | TPC hits → tracks, fit quality, vertex | 25, 26, 30 |
| **Charged-PID POG** | dE/dx, range/stopping, π/p separation | 27, 28, 29 |
| **EM-Object POG** | Calorimeter clustering, shower shape, photons, π⁰ | 31, 32, 33, 34 |
| **Combined Performance** | Kinematic fit, event variables, ladder, closure | 35, 36, 38, 39, 40, 41, 42 |
| **Analysis WG** | Event selection, efficiency, background, systematics, significance | 37, 43, 44, 45, 46 |
| **Reproducibility WG** | Baseline reconstruction walkthrough, IO dictionary, intercalibration, ledger, reviewer defence, archival | 08, 09, 18, 47, 50, 51, 54 |
| **Software Quality** | Realism contract, digitisation seam, CI, INT notes, glossary, MVA protocol | 01, 02, 06, 53, 55, 56, 57 |

### 3.2 Charter language (template)

Each WG plan opens with a charter paragraph following this template:

> *Charter.* This working group owns the planning and sign-off authority for
> [scope]. It does not unilaterally change [out-of-scope items]. It reports
> to the Methodology Council, which arbitrates conflicts with adjacent WGs.
> Decisions are recorded in plan 05 (decision log) with WG attribution.

### 3.3 Cross-WG conflicts

When two WGs disagree (e.g. Tracking POG wants a TPC clustering change that
the Physics Modeling WG flags as physics-list-coupled), the conflict is
recorded as a `DEC-YYYY-MM-DD-N` entry and arbitrated by the Methodology
Council. Codex-supervisor does not implement either side until the conflict
is resolved.

---

## 4. Plan-file inventory

Each plan below is one paragraph of charter. The full file lives in
`docs/rebuild_plans/<id>.md` and follows the file metadata schema in §7.

### 4.1 Foundations (rules)

- **00_README.md** — *(this file)* master index, working-group structure,
  sign-off matrix, plan revision protocol.
- **01_realism_contract.md** — partitions every parquet column into Class A
  (experiment-equivalent), Class B (truth-only), Class C (MC-tuned
  calibration), and specifies the static audit that fails if a reco function
  reads Class B outside marked diagnostic contexts. Hosts the limitations
  registry.
- **02_digitization_seam.md** — designs the interface where a future
  realism layer (energy smearing, timing jitter, hit efficiency, dead
  channels, electronic noise) plugs in without touching reconstruction code.
  Specifies on/off switch, parameter file, and upgrade-gate criteria.
- **03_dataset_registry.md** — schema and freeze policy for every simulated
  sample. Sample ID, generator command, parameter snapshot, file SHA-256,
  Geant4 version, physics list, geometry hash, status (draft/frozen).
- **04_statistical_uncertainty.md** — bootstrap, jackknife, Feldman-Cousins,
  Wilson interval conventions. Calibration-uncertainty propagation rules.
  Every numeric claim cites a convention from this plan.
- **05_decision_log.md** — append-only `DEC-YYYY-MM-DD-N` entry format.
  Context / decision / rationale / alternatives / consequences / supersession.
  Cross-referenced from plans, code, and ledger rows.
- **06_governance_and_review.md** — review gates (single-reviewer vs.
  two-reviewer changes), meeting cadence, sign-off chain
  (codex-supervisor → user → supervisor), escalation, plan revision workflow.

### 4.2 Baseline understanding (what currently is — descriptive, no improvement proposals)

These five plans freeze a forensic accounting of the existing simulation
and reconstruction. They are *living documents*: every PR that touches the
simulation or reconstruction must update the relevant section.
Improvement-class plans (12+) cite these baselines instead of re-deriving
them.

- **07_simulation_atomic_walkthrough.md** — every component of
  `NNBAR_Detector/`: build configuration, Geant4 version, physics list,
  every geometry volume with material/dimensions/position, every
  sensitive detector and what it records, every primary generator mode,
  RunAction/EventAction outputs, hit classes, optical physics paths,
  GPU paths, every macro. With file paths and line numbers.
- **08_reconstruction_atomic_walkthrough.md** — every function of
  `nnbar_reconstruction/`: I/O layer, reconstruction core (in pipeline
  order), CLI commands, validation metrics, calibration scans, geometry
  audit, study modules. Inputs/outputs/decision rules per function.
  Allowed and used truth columns explicitly listed per function.
- **09_io_schema_data_dictionary.md** — every column in every parquet
  output file: name, dtype, units, semantics, provenance class
  (A/B/C from plan 01), upstream producer, downstream consumers. The
  authoritative reference for what data exists.
- **10_macro_and_sample_inventory.md** — every `.mac` macro and every
  CLI command currently in use: purpose, invocation, output files,
  sample size, run-id assignment, reproducibility status.
- **11_build_and_runtime_environment.md** — CMake configuration, FetchContent
  dependencies, Geant4 version pin, Python environment, parquet-writer
  vendoring, MCPL vendoring, ACTS vendoring, build-tree layout
  (`build`, `build-codex`, `build-codex-native`, `build-codex-setup2`),
  OS targets, GPU/CUDA paths.

### 4.3 Physics modelling assessment

- **12_physics_list_audit.md** — Geant4 physics-list selection (current
  source per plan 07; alternatives must be named and justified).
  Antineutron annihilation cross-section bench-data comparisons.
  Neutron capture and inelastic channels.
- **13_signal_model.md** — antineutron-on-carbon (and silicon, in beampipe)
  annihilation final-state branching ratios with citation chain. Multi-pion
  topology distributions. Where the model is data-driven vs. theoretical.
  Defines the alternative models used as the signal-model systematic.
- **14_background_models.md** — cosmic-ray spectrum (CRY at ESS Lund
  coordinates, geomagnetic cutoff documented), beam-neutron spectrum
  (HIBEAM-specific, source MCPL or parameterisation), capture-gamma channels,
  beam-pipe and collimator interaction products.
- **15_material_budget.md** — radiation-length and nuclear-interaction-length
  inventory of every detector volume. Tracking-material map: how much
  material a nominal pion at a nominal angle traverses before reaching
  the calorimeter. Drives multiple-scattering and conversion estimates.

### 4.4 Simulation engineering

- **16_geometry_and_alignment.md** — geometry truth (already audited via
  `geometry_audit` CLI) plus a designed misalignment seam used for the
  systematic study at gate-3.
- **17_field_calibration.md** — TPC drift field uniformity, drift velocity
  vs E/n, gas-gain calibration, magnetic field if present.
- **18_intercalibration.md** — cross-calibration in overlap regions.
  TPC dE/dx anchored to charged stopping in scintillator; lead-glass energy
  anchored to electron beam-test references; scintillator photon yield
  anchored to MIP response.
- **19_simulation_validation_suite.md** — sanity plots (eDep distributions,
  hit multiplicities, primary kinematics), unit/integration/regression
  tests, performance regression budget.

### 4.5 Sample regeneration

- **20_sample_signal.md** — Ch 5/6 antineutron annihilation samples on the
  carbon foil. Statistics required for thesis-grade reproduction. Splits
  (training/validation/test) with seed and scope. Output column schema.
- **21_sample_cosmic_CRY.md** — CRY integration (LLNL Cosmic-Ray Shower
  library), geometry-of-origin (altitude, latitude, date for geomagnetic
  cutoff), overburden model, generator-to-Geant4 interface (CRY → MCPL → G4
  vs. direct primary generator), livetime windowing, sample-size derivation
  from target cosmic-rejection upper limit, full inventory of cosmic-related
  thesis claims and which study reproduces each.
- **22_sample_neutron_beam.md** — HIBEAM beam-spectrum source (MCPL or
  parameterisation), sub-channel breakdown (scattered neutrons, secondary
  hadronic fragments, capture gammas), time-correlation flagged as
  unmodelled because of the perfect-detector assumption.
- **23_sample_calibration_aux.md** — single-particle samples (e±, µ±, π±,
  p, γ) at fixed energies for calibration anchors and PID-likelihood
  training. Statistics, splits, hash sealing.

### 4.6 Reconstruction — atomic decomposition

- **24_reconstruction_question_tree.md** — recursive decomposition mirroring
  `docs/detector_fundamental_question_tree.md`. Every leaf has inputs
  (Class A columns), decision rule, allowed truth use, outputs, downstream
  consumers. Subsystem plans 25–37 freeze their leaf identities from this
  tree.

### 4.7 Subsystem deep dives (post-24)

- **25_subsystem_tpc_hits_to_tracks.md** — clustering, track finding
  (compare Hough, Legendre, Kalman seeded by Hough seeds), seed quality
  metrics.
- **26_subsystem_track_fit_and_pulls.md** — fit residuals, χ², pull
  distributions per coordinate, bias diagnostics.
- **27_subsystem_dedx.md** — Bethe–Bloch reference, truncated-mean estimator,
  saturation handling, calibration anchor from plan 18.
- **28_subsystem_range_and_stopping.md** — Bragg-peak modelling,
  scintillator stopping range, layer-by-layer energy profile.
- **29_subsystem_charged_pid.md** — π/p separation, likelihood-ratio path
  combining dE/dx + range + scintillator response. Default-cut path retained
  as fallback for sparse tables.
- **30_subsystem_vertex.md** — Billoir-style χ² vertex fit vs. current
  mean-of-projections; covariance treatment; foil-plane constraint as
  optional vs. mandatory.
- **31_subsystem_calorimeter_clustering.md** — sliding-window vs.
  topological vs. particle-flow-style clustering for lead-glass and
  scintillator showers.
- **32_subsystem_shower_shape.md** — moments, depth, lateral spread.
  Charged-vs-neutral discriminant feeding plan 33.
- **33_subsystem_photon_object.md** — neutral-test, direction (vertex →
  centroid), energy.
- **34_subsystem_pi0_pairing.md** — photon-pair selection, mass, opening
  angle, accidental rejection.
- **35_subsystem_kinematic_fit.md** — π⁰ mass-constrained fit and
  vertex-constrained event fit; pull distributions.
- **36_subsystem_event_variables.md** — sphericity, Fox-Wolfram moments,
  thrust, EL/ET, visible mass, calorimeter sums.
- **37_subsystem_event_selection.md** — Ch 10 cut-flow rebuild with
  N-1 plots and ROC curves wired through plan 41.

### 4.8 Validation instruments

- **38_truth_substitution_ladder.md** — protocol; canonical truth definition
  per leaf (production / first-conversion / detector-entry choice for photon
  direction etc.); factorisation choice (additive along fixed leaf order vs.
  Shapley permutation averaging); RNG/seed binding; output matrix schema.
  In a Geant4-only world, this also defines the **oracle upper bound** for
  every reconstruction algorithm.
- **39_fast_mc_sanity_check.md** — smear-truth → match-reco closure test.
  Independent of the ladder because both ladder modes share reco code.
- **40_closure_and_pulls.md** — per-leaf closure test schedule. Pull
  distributions for each fitted quantity. Bias and width acceptance bands.

### 4.9 Analysis-level studies

- **41_n_minus_1_and_roc_studies.md** — N-1 plots for every selection cut,
  ROC curves for every continuous variable, optimal-cut scans.
- **42_unfolding_protocol.md** — particle-level vs. detector-level
  observables; response matrix construction; iterative-Bayesian and SVD
  regularisation; closure tests for unfolded distributions.
- **43_signal_efficiency.md** — acceptance × selection × reconstruction
  factorisation; per-stage cut-flow; per-final-state-channel breakdown.
- **44_background_taxonomy.md** — every background channel as a tree node:
  source, sample, sub-channel, expected rate, selection survivor count,
  upper-limit treatment if zero survivors.
- **45_systematics_taxonomy.md** — named uncertainty list (calibration,
  modelling, statistical, theoretical), correlation/anticorrelation
  matrix, propagation tree from inputs to final selection efficiency and
  background rate.
- **46_significance_protocol.md** — Z₀ definition, expected/observed limit
  framework, finite-sample handling (Feldman-Cousins, CLs).

### 4.10 Reproduction & accountability

- **47_reproduction_ledger.md** — every Ch 5–10 number AND figure as a
  ledger row: source, reproducing command, reproduced value, comparison
  status, notes. Numeric and graphical equality protocols.
- **48_prior_art_survey.md** — written survey of methods we may borrow:
  ACTS (tracking), PandoraPFA (particle flow), Belle II / GlueX
  kinematic fits, CMS PF, ALICE TPC clustering, NA62 π⁰ reconstruction,
  Fox-Wolfram and thrust references.
- **49_targeted_improvements.md** — improvement protocol: an improvement
  proposal cites a leaf identified by plan 38 as a dominant contributor,
  proposes a method (often from plan 48), is scored before/after on the
  same ladder, and must not regress green ledger rows in plan 47.
- **50_reviewer_defense_package.md** — for every quoted result, the
  canonical answer set: sample ID, reproducing command, ladder sensitivity,
  calibration sensitivity, background sensitivity, acceptance footprint,
  limitations flags.
- **51_reviewer_question_registry.md** — living, append-only registry of
  every question asked by supervisors, examiners, collaborators, or
  referees. Each question routes to the gate(s) that should already have
  answered it.

### 4.11 Operations

- **52_run_orchestration.md** — batch system used (LUNARC SLURM per
  existing skills), seed strategy, output partitioning, hash sealing.
- **53_ci_regression_suite.md** — automated tests on every change.
  Performance budget. Failure categorisation.
- **54_open_data_archival.md** — Zenodo / DOI / RECAST-style preservation
  plan for samples, plots, ledger, code at thesis-freeze.
- **55_internal_note_template.md** — ATLAS INT-note-style template
  (motivation / method / result / cross-check / systematics / reviewer
  notes). Every plan-set deliverable becomes an INT note.
- **56_glossary.md** — terms maintained alongside code, supersedes the
  thesis chapter 14 glossary for code-level usage.

### 4.12 Method protocols (cross-cutting)

- **57_mva_method_protocol.md** — when an MVA discriminant is appropriate
  (only after the cut-based baseline reproduces the thesis), training/
  validation/test split discipline with seed and scope, overtraining
  diagnostics, calibration-monotonicity gates, feature-schema decision-log
  entries (mirroring HIBEAM `DEC-2026-05-08-1`), inference-vs-training
  feature-schema audit. Cross-cutting plan consumed by 29, 32, 37 and
  any future MVA upgrade.

---

## 5. Dependency DAG

The DAG below is the *write* order; the *read* order in §2 is different
(read-order is for someone consuming the finished plan set). Codex-supervisor
follows the write order to avoid rework.

```
                              00 (this file)
                                   │
              ┌────────────────────┼─────────────────┐
              ▼                    ▼                 ▼
            01,02               53,55,56         (operations
              │                                     foundations)
              ▼
            03,04
              │
              ▼
            05,06
              │
              ▼
       07,08,09,10,11        ← BASELINE UNDERSTANDING (forensic)
              │
              ▼
       12,13,14,15           ← physics modelling assessment
              │
              ▼
       16,17,18,19           ← simulation engineering
              │
              ▼
       24                    ← reconstruction question tree (gate)
              │
       ┌──────┴──────┐
       ▼             ▼
   38,39,40       20,21,22,23   ← validation / samples (parallel)
       │             │
       └──────┬──────┘
              ▼
       25–37 in parallel       ← subsystem deep dives (gated by 24)
              │
              ▼
       41,42,43,44,45,46       ← analysis-level studies
              │
              ▼
       47,48,49,50,51          ← reproduction & accountability
              │
              ▼
            52,54              ← orchestration + archival
              │
              ▼
            57                 ← MVA protocol (used by 29, 32, 37)
```

The DAG implies these properties:

- 01 and 02 are siblings: realism contract and digitisation seam are designed
  together so the seam respects the contract.
- 03 and 04 must precede 05 because every decision logged needs a sample
  reference (03) and an uncertainty convention (04).
- **07–11 (baseline understanding) are written before any improvement-class
  plan.** Improvements cite the baseline; without it, improvement proposals
  re-derive what is already in the code and waste cycles.
- 24 (reconstruction question tree) gates everything reconstruction-side.
  Codex-supervisor refuses to start 25–37 until 24 is signed off.
- 38–40 must precede 49; "improvement" is undefined without the ladder.
- 54 (archival) is last because it ingests the frozen versions of all the
  earlier outputs.
- 57 (MVA protocol) is cross-cutting; it can be drafted in parallel with
  the baseline-understanding plans because it does not depend on any
  specific subsystem.

---

## 6. Sign-off matrix

A plan is *drafted* by its WG, *reviewed* by an adjacent WG, *signed off*
by the Methodology Council, and *executed* by codex-supervisor only after
the supervisor (Milstead/Meirose) has approved the plan-set state.

| Plan class | Drafted by | Reviewed by | Signed off by | Executes against |
|---|---|---|---|---|
| Foundations (00–06) | Methodology Council + Software Quality | Reproducibility WG | Supervisor | Codex-supervisor |
| Baseline understanding (07–11) | Sim Production + Reproducibility WG | Methodology Council | Supervisor | Codex-supervisor |
| Physics modelling (12–15) | Physics Modeling | Methodology Council | Supervisor | Codex-supervisor |
| Sim engineering (16–19) | Sim Production | Physics Modeling | Methodology Council | Codex-supervisor |
| Samples (20–23) | Sim Production | Methodology Council | Supervisor | Codex-supervisor |
| Decomposition (24) | Methodology Council | All POGs | Supervisor | Codex-supervisor |
| Subsystems (25–37) | Owning POG | Adjacent POG + CP | Methodology Council | Codex-supervisor |
| Validation (38–40) | Combined Performance | Methodology Council | Supervisor | Codex-supervisor |
| Analysis (41–46) | Analysis WG | Combined Performance | Supervisor | Codex-supervisor |
| Reproduction (47–51) | Reproducibility WG | Methodology Council | Supervisor | Codex-supervisor |
| Operations (52–56) | Software Quality | Sim Production | Methodology Council | Codex-supervisor |
| MVA protocol (57) | Software Quality + CP (joint) | Methodology Council | Supervisor | Codex-supervisor |

The supervisor sign-off is a hard gate. Codex-supervisor reads the
`status` field in each plan's YAML header and refuses to execute plans
whose status is not `signed`.

---

## 7. File metadata schema

Every plan file in `docs/rebuild_plans/` opens with this YAML header:

```yaml
---
id: NN_short_name
title: Human-readable title
version: 0.N
status: draft | review | signed | superseded
owner: <Working Group>
supersedes: NN_old_short_name (or null)
depends_on: [NN_a, NN_b, ...]
inputs:
  - {path: ..., schema: ..., produced_by: NN_x}
outputs:
  - {path: ..., schema: ..., consumed_by: [NN_y, NN_z]}
acceptance:
  - {test: ..., method: ..., pass_when: ...}
risks:
  - {risk: ..., mitigation: ...}
estimated_effort: <S|M|L|XL>
last_updated: YYYY-MM-DD
---
```

Codex-supervisor parses this header to schedule execution. Missing or
malformed headers are a blocking error.

---

## 8. Plan revision protocol

Plans are not frozen. They are versioned. The protocol:

1. **Revision request.** Anyone (codex-supervisor, user, supervisor)
   raises a revision by editing the plan file, bumping `version` (e.g.
   `0.1` → `0.2`), setting `status: review`, and recording the change
   in plan 05 (decision log) with reference to the bumped version.
2. **Review.** The reviewer named in §6 confirms or rejects. A rejection
   reverts `status` to `draft` with a comment in plan 05.
3. **Sign-off.** On approval, `status` becomes `signed` and codex-supervisor
   may resume execution against the plan.
4. **Supersession.** A plan that is structurally replaced (not just
   versioned) gets `status: superseded`, `supersedes: <new_id>`, and the
   replacement plan cites the original via its own `supersedes` field.

In-flight executions against a plan whose `status` flips to `review` are
checkpointed and paused. They do not roll back unless the new version
explicitly asks for rollback.

---

## 9. Status board

A single status table lives at the top of this README and is regenerated
from each plan's YAML header. Codex-supervisor refreshes it after every
write.

```
 id   title                                       status     ver  owner            updated
 00   master plan                                 draft      0.1  Methodology      2026-05-09
 01   realism contract                            draft      0.0  Software Quality 2026-05-09
 02   digitisation seam                           draft      0.0  Software Quality —
 ...
```

The "status" column is the gating signal for execution. The "updated" column
catches stale plans the council should re-review.

---

## 10. Reviewer reading checklist

A reviewer (supervisor, examiner, referee) reading the plan set should be
able to answer these questions in order:

1. *What is the scope?* — answered by §1.
2. *Who decides what?* — answered by §3 and §6.
3. *What rules constrain every plan?* — answered by 01 and 02.
4. *What samples does anything quote against?* — answered by 03.
5. *What uncertainty does any number carry?* — answered by 04.
6. *Is the input physics defensible?* — answered by 07–10.
7. *Is the reconstruction decomposition complete?* — answered by 19.
8. *What does "improved" mean quantitatively?* — answered by 33.
9. *Can I reproduce a thesis number?* — answered by 42.
10. *What questions has this work already answered?* — answered by 46.

If any of these is unclear from the plan set, the plan set is incomplete
and the gap is the next priority for the Methodology Council.

---

## 11. Open questions for the user

These need user input before some downstream plans can be finalised. They
are tracked here, not in individual plans, so they are visible at a glance:

1. **Licentiate-defence examiner feedback.** Is there written feedback
   from the licentiate defence? If yes, it seeds plan 46. If no, plan 46
   starts empty and grows from supervisor meetings. *(Affects plan 46.)*
2. **Digitisation seam scope.** Confirm the seam is *designed* now, *built*
   later. Concretely: do we need a stub implementation that is a no-op
   identity transform, or only a documented interface? *(Affects plan 02.)*
3. **CRY altitude/latitude/date defaults.** ESS Lund coordinates are well
   defined (≈10 m a.s.l., ≈55.7°N), but the date sets the geomagnetic
   cut-off. Choose: thesis-defence date, beam-on-target target date, or
   a fixed reference date. *(Affects plan 16.)*
4. **Cosmic-rejection upper-limit target.** The licentiate abstract states
   "approximately 70% signal acceptance with no surviving cosmic-ray
   background events" as a finite-sample upper limit. The PhD plan should
   declare the *target* upper limit on cosmic survival rate; the CRY
   sample size in plan 16 derives from it. *(Affects plan 16, plan 41.)*
5. **Beam neutron source.** Does the HIBEAM line provide an MCPL file we
   ingest, or a parameterised flux we sample? *(Affects plan 17.)*
6. **Run resources.** Confirm LUNARC SLURM is the production system;
   confirm storage budget for new sample regeneration; confirm Geant4
   version pin. *(Affects plan 47.)*
7. **HIBEAM repo coordination.** The HIBEAM TPC vertex chapter cites
   `reco_io.py`, `metrics.py`, and `docs/governance/DECISION_LOG.md` from
   a separate repo. Do those decision-log entries need to be mirrored into
   plan 05 of this rebuild, or only cross-referenced? *(Affects plan 05.)*
8. **Supervisor cadence.** Are weekly reviews realistic? If not, the
   meeting cadence in plan 06 must be relaxed accordingly. *(Affects plan 06.)*

---

## 12. Glossary anchor

Authoritative terminology lives in plan 51. This README uses the following
shorthand without further definition:

- **POG** — Physics Object Group
- **CP** — Combined Performance
- **WG** — Working Group
- **DAG** — Directed Acyclic Graph (plan dependencies)
- **DEC-YYYY-MM-DD-N** — decision-log identifier (plan 05)
- **gate** — a sign-off boundary that must close before downstream work starts
- **leaf** — an irreducible reconstruction decision in the question tree
  (plan 19)
- **ladder** — the truth-substitution validation instrument (plan 33)
- **ledger** — the thesis reproduction ledger (plan 42)
- **registry** — either the dataset registry (plan 03) or the
  reviewer-question registry (plan 46), disambiguated by context

---

## 13. References

- `docs/detector_fundamental_question_tree.md` — the detector-side companion
  to plan 19. This rebuild mirrors its discipline.
- `/Users/billy/Desktop/projects/overleaf-hibeam-thesis/13_HIBEAM_reproducibility_appendix.tex` —
  HIBEAM reproducibility appendix; template for plan 42 and plan 45.
- `/Users/billy/Desktop/projects/overleaf-hibeam-thesis/0_main.tex` — thesis
  chapter ordering, including PhD additions.
- `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/` — frozen licentiate
  thesis used as the historical baseline in plan 42.
- ATLAS Physics Object Group structure (used as the organisational
  template for §3).
- LLNL CRY library (cited in plan 16).

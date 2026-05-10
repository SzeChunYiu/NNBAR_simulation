---
id: 59_strange_baryon_contamination
title: Strange-baryon contamination from beam-neutron interactions
version: 0.1
status: draft
owner: Backgrounds POG
depends_on: [00_README, 01_realism_contract, 14_background_models, 22_sample_neutron_beam, 24_reconstruction_question_tree, 30_subsystem_vertex, 34_subsystem_pi0_pairing, 36_subsystem_event_variables, 37_subsystem_event_selection, 44_background_taxonomy, 45_systematics_taxonomy, 47_reproduction_ledger]
outputs:
  - {path: docs/rebuild_plans/59_strange_baryon_contamination.md, schema: this file}
  - {path: output/strange_baryon/<study_id>/v0_candidates.parquet, schema: §5 V0-candidate table}
  - {path: output/strange_baryon/<study_id>/contamination_summary.parquet, schema: §8 contamination summary}
acceptance:
  - {test: K_s/Lambda/Sigma channels have PDG branching estimates, method: §2 table review, pass_when: each channel has a source id and branch fraction}
  - {test: strange production source is tied to beam-neutron nodes, method: §3 review, pass_when: no unregistered source channel is used}
  - {test: V0 topology, displaced vertex, and rejection cuts are explicit, method: §§5-6 review, pass_when: every variable has a production-input boundary}
  - {test: closure uses a Lambda-enriched beam-neutron slice, method: §7 closure, pass_when: contamination intervals and rejection efficiency are saved}
risks:
  - {risk: Geant4 strange-particle production may be under-sampled in the first beam-neutron sample, mitigation: §7 requires an enriched slice and treats nominal rows as upper-limit constrained until populated}
  - {risk: PDG branching fractions are mistaken for production yields, mitigation: §3 separates decay branching from source yield and cross-section normalisation}
  - {risk: V0 rejection uses generated particle names, mitigation: §§5-6 make production variables geometry/timing based and keep truth labels in validation sidecars}
estimated_effort: M
last_updated: 2026-05-10
---

# Strange-baryon contamination

*Charter.* Quantify whether neutral strange particles from beam-neutron
interactions on foil, beampipe, collimator, shielding, or detector
material can fake the NNBAR signal topology after reconstruction and
plan-37 event selection. The first scope covers K_S^0, Lambda, and Sigma
states because they produce displaced vertices, charged pions/protons,
neutrons, gammas, and pi0-like EM activity that can leak into the
charged, photon, pi0, event-variable, and selection leaves.

## 1. Scope and contamination hypothesis

Beam-induced neutron interactions can produce strange hadrons in or near
the detector material. If the strange particle decays after travelling a
measurable distance, the reconstructed event can contain:

- a displaced V0-like two-prong vertex from K_S^0 or Lambda decay;
- a proton/pion pair whose charged PID resembles signal annihilation
  products;
- a neutron or gamma leg that deposits energy in scintillator or
  lead-glass without an obvious charged track;
- a pi0-like EM topology from K_S^0 -> pi0 pi0 or Sigma/Lambda decay
  chains;
- timing and vertex residuals that are inconsistent with a foil-origin
  NNBAR event but may pass a loose cut-flow if not audited.

This plan does not claim an absolute production rate yet. It defines the
source channels, PDG decay weights, V0 observables, rejection cuts, and
closure artifacts required before plan 44 can include or exclude strange
contamination in a background sum.

### 1.1 Source-node boundary

All strange-contamination rows must be children of the plan-44
beam-neutron nodes:

| Parent node | Strange sub-study role | Initial status |
|---|---|---|
| `beam_neutron.direct_beam_neutron` | prompt material interactions near the detector volume | candidate once source DEC exists |
| `beam_neutron.scattered_neutron` | off-axis V0 candidates from beampipe/collimator/shielding scatters | primary target for Lambda-enriched closure |
| `beam_neutron.secondary_hadronic` | inelastic fragments that can include K, Lambda, and Sigma states | candidate, rate blocked until sample is populated |
| `beam_neutron.capture_gamma` | EM-only comparison for pi0-like fake rejection | diagnostic control, not a strange source by itself |

Rows from cosmic samples may be used as topology controls, but they do
not define the beam-neutron strange production rate.

## 2. PDG branching estimates

The v0.1 study uses Particle Data Group decay values as decay weights,
not as production yields. Values below are rounded review inputs from
PDG Live / Review of Particle Physics pages checked on 2026-05-10. The
implementation must store the PDG edition or page id in each manifest so
a future PDG update can be replayed.

| Particle / decay | Branching estimate | PDG source id | Detector signature |
|---|---:|---|---|
| K_S^0 -> pi+ pi- | 69.20 +/- 0.05 % | PDG Live K_S^0 constrained fit, node S012 | two displaced charged pions, V0 topology |
| K_S^0 -> pi0 pi0 | 30.69 +/- 0.05 % | PDG Live K_S^0 constrained fit, node S012 | four photons / pi0-like EM clusters |
| Lambda -> p pi- | 64.1 +/- 0.5 % | PDG Live Lambda page, node S018 | displaced proton plus negative pion |
| Lambda -> n pi0 | 35.8 +/- 0.5 % | PDG Live Lambda page / baryon table, node S018 | neutron plus pi0-like EM activity |
| Sigma+ -> p pi0 | 51.5 +/- 0.3 % | PDG Live Sigma+ page, node S019 | proton plus pi0-like EM cluster |
| Sigma+ -> n pi+ | 48.3 +/- 0.3 % | PDG Review Sigma table, node S019 | neutron plus positive pion |
| Sigma- -> n pi- | 99.848 +/- 0.005 % | PDG Live Sigma- page, node S020 | neutron plus negative pion |
| Sigma0 -> Lambda gamma | approximately 100 % | PDG Live Sigma0 page, node S021 | prompt gamma followed by Lambda topology |

Branching rows carry uncertainties. They are not allowed to absorb the
uncertainty in strange-particle production, beam-neutron flux, material
composition, or detector response. Those remain separate nuisance inputs
in plan 45.

### 2.1 Branching-weight fixture

| Field | Required content | Review rule |
|---|---|---|
| `branching_row_id` | stable key such as `pdg2025_lambda_p_piminus` | unique |
| `pdg_node` | PDG page or particle id | non-null |
| `decay_mode` | human-readable final state | must match the stored daughter list |
| `branching_fraction` | central value in [0,1] | never used as production yield |
| `branching_uncertainty` | absolute uncertainty or null with reason | propagated separately |
| `visible_signature` | charged, neutral, EM, or mixed | maps to §5 variables |
| `manifest_source` | PDG edition / access date | required before closure |

## 3. Production-yield separation

A strange background contribution has two factors:

1. **Production yield:** probability that a beam-neutron interaction
   creates K_S^0, Lambda, Sigma, or a parent state in the relevant
   material and kinematic region.
2. **Decay and reconstruction survival:** PDG decay branch multiplied by
   detector acceptance, V0 reconstruction, rejection cuts, and plan-37
   survival.

The first factor comes from Geant4 truth sidecars or a dedicated
beam-neutron enriched generator. The second factor is measured by this
plan. A row with PDG branching but missing production yield is a
`decay_survival_only` row and cannot enter plan-44 expected rates.

| Source factor | Owner | Required artifact |
|---|---|---|
| beam-neutron flux / per-pulse normalisation | plans 22 and 44 | signed source DEC and rate row |
| strange production in material | plan 59 + L3 generator/audit | strange-yield table by material and parent node |
| decay branching | plan 59 | §2 branching fixture |
| reconstruction survival | plans 30, 34, 36, 37 | V0/selection closure rows |
| statistical interval | plan 46 | F-C or Wilson interval row |

## 4. Source material and topology map

| Material / region | Likely source | Candidate strange state | Observable risk |
|---|---|---|---|
| foil / target support | secondary hadronic fragments | Lambda, Sigma0 | displaced p/pi or gamma+Lambda near signal vertex |
| beampipe / collimator | scattered beam neutron | K_S^0, Lambda | V0 with off-axis origin and delayed timing |
| shielding | inelastic or capture-adjacent cascades | Sigma, Lambda | neutron/gamma plus charged pion contamination |
| lead-glass front material | hadronic secondary entering calorimeter | K_S^0, Sigma+ | EM cluster and pi0-like fake |
| scintillator support | neutron-induced secondary | Sigma-, Lambda | charged-pion track plus neutron energy |

The first implementation bins source material using the geometry volume
name in validation sidecars. Production rejection must not use the
volume truth label; it uses reconstructed displacement, pointing,
timing, and energy-balance variables.

## 5. V0 topology and displaced-vertex observables

A V0 candidate is a pair or neutral-plus-charged topology consistent
with a long-lived neutral decay away from the foil. The production
variables are reconstructed-only:

| Variable | Definition | Purpose |
|---|---|---|
| `v0_decay_radius_cm` | transverse radius of secondary vertex from reconstructed tracks | separates foil-origin signal from displaced decay |
| `v0_decay_z_cm` | z position of secondary vertex | rejects beampipe/shielding origins |
| `v0_pointing_angle_deg` | angle between reconstructed V0 momentum and vector from foil vertex to V0 | displaced-parent consistency |
| `v0_dca_tracks_cm` | distance of closest approach between daughter tracks | two-prong quality |
| `v0_impact_to_foil_cm` | impact parameter of daughter tracks to foil vertex | rejects prompt signal-like tracks |
| `v0_invariant_mass_hypothesis` | mass under K_S^0, Lambda, or Sigma daughter assignments | identifies likely strange class |
| `v0_timing_residual_ns` | daughter-hit timing residual against prompt signal hypothesis | delayed/off-axis guard |
| `v0_neutral_energy_mev` | associated neutron/gamma/pi0-like calorimeter energy | catches neutral strange decay legs |

Truth labels define validation categories only. They cannot be used to
select or reject events in the production event table.

### 5.1 V0-candidate table

| Column | Meaning |
|---|---|
| `event_id`, `candidate_id` | stable candidate identity |
| `candidate_hypothesis` | `ks0`, `lambda`, `sigma_plus`, `sigma_minus`, `sigma_zero`, or `unknown_v0` |
| `daughter_track_ids` | reconstructed daughter object ids |
| `neutral_object_ids` | reconstructed neutron/gamma/pi0-like object ids when present |
| `decay_vertex_x_cm`, `decay_vertex_y_cm`, `decay_vertex_z_cm` | secondary vertex |
| `displacement_cm` | distance from primary/foil vertex |
| `pointing_angle_deg` | V0 pointing angle |
| `mass_hypothesis_mev` | reconstructed mass under the selected hypothesis |
| `passes_v0_rejection` | production rejection decision from §6 |
| `v0_rejection_reasons` | ordered reason tokens |
| `truth_match_label` | validation sidecar only; null in production output |

## 6. Rejection cuts

The baseline strange-veto candidate is a sidecar rejection, not a
replacement for plan-37 selection. It is reviewed by comparing the
signal-efficiency loss against the strange-contamination reduction.

| Cut id | Production rule | Reason token | Target background |
|---|---|---|---|
| `v0_displacement_min` | reject if a two-prong secondary vertex is displaced beyond the prompt-vertex envelope and points back to off-foil material | `displaced_v0` | K_S^0, Lambda |
| `lambda_mass_window` | reject Lambda-hypothesis pairs near the PDG Lambda mass with p/pi daughter assignment | `lambda_mass` | Lambda, Sigma0 |
| `ks0_mass_window` | reject pi+/pi- pairs near the K_S^0 mass | `ks0_mass` | K_S^0 |
| `sigma_neutral_leg` | reject Sigma-like charged+neutral topologies with inconsistent prompt timing | `sigma_neutral_leg` | Sigma+, Sigma-, Sigma0 |
| `pointing_off_foil` | reject if V0 momentum points to beampipe/shielding instead of foil | `off_foil_pointing` | scattered-neutron strange states |
| `timing_late_strange` | reject if associated neutral energy is late relative to prompt signal | `late_neutral` | neutron/gamma strange daughters |

No §6 row carries a production numeric threshold in v0.1. Each row is a
named rejection *axis* whose operating point is blocked until the §7
closure scan writes a cut-config row with signal-loss and strange-survivor
intervals. Any numerical threshold that becomes production-facing must be
recorded in a plan-05 DEC and copied to a machine-readable cut-config row.

| Cut-config field | Required value before production use |
|---|---|
| `cut_id` | one of the §6 stable cut ids |
| `threshold_expression` | explicit numeric bound(s), units, and inclusive/exclusive convention |
| `scan_result_id` | §7 closure or sideband scan row that selected the operating point |
| `signal_loss_interval_id` | interval row on `sig_foil_v3`, not a point estimate |
| `background_survivor_interval_id` | interval row on the enriched strange sample |
| `decision_dec_id` | signed `DEC-59-V0-REJECTION` or successor |
| `production_status` | `blocked`, `diagnostic`, `candidate`, or `approved` |

### 6.1 Physics derivation for strange-contamination rejection

#### Physics derivation

Plan 59 physically estimates whether strange hadrons produced by
beam-neutron interactions can survive reconstruction and the plan-37
selection. The truth-side quantity is the production and decay of
K_S^0, Lambda, and Sigma states in detector material; the production
estimator observes only reconstructed daughter tracks, neutral objects,
secondary vertices, timing residuals, and event variables. PDG branching
fractions fix decay weights, while Geant4/beam-neutron samples must
provide the production yield; those two factors must never be merged
\cite{ParticleDataGroup:2024RPP,Agostinelli2003}.

The estimator is therefore a V0/topology sidecar: reconstruct displaced
secondary vertices, evaluate mass hypotheses and pointing/timing
compatibility, and measure strange survival after both V0 rejection and
the baseline selection. Dominant uncertainty is strange production yield
in material, followed by branching uncertainties, vertex resolution,
charged/neutral daughter efficiency, mass-window calibration, and
signal-efficiency loss from any veto. Truth labels may enrich closure
samples but cannot drive production V0 decisions.

The Wave-6 strange-channel derivation ledger is:

| Strange leaf | Truth-side quantity | Estimator rationale | Dominant uncertainty | Closure assertion |
|---|---|---|---|---|
| `strange.ks0_charged` | K_S^0 production times `K_S^0 -> pi+ pi-` decay survival after selection | displaced two-prong V0 mass, DCA, and pointing observables directly test the charged K_S^0 topology without truth labels | production yield and V0 mass/window calibration | K_S sideband closure records signal loss and residual survivors before any rate enters plan 44 |
| `strange.ks0_neutral` | K_S^0 production times `K_S^0 -> pi0 pi0` EM leakage | four-photon/pi0-like final states are audited through plan-34/37 EM and visible-mass leaves | photon pairing and neutral-energy response | neutral K_S rows cite P.5/P.6 closure and remain separate from charged V0 rows |
| `strange.lambda_charged` | Lambda production times `Lambda -> p pi-` survival | p/pi mass hypothesis plus displaced vertex is the canonical Lambda V0 signature | proton/pion PID leakage and vertex resolution | Lambda-enriched slice must pass sidecar-drop and signal-loss checks |
| `strange.lambda_neutral` | Lambda production times `Lambda -> n pi0` leakage | neutral leg plus pi0-like EM energy tests strange decays that do not form a charged V0 pair | neutron/gamma response and pi0 reconstruction | neutral-Lambda rows stay blocked until neutral-object closure and production yield exist |
| `strange.sigma_chain` | Sigma production feeding pions, neutrons, gammas, or Lambda daughters | Sigma modes are treated as parent-chain hypotheses whose visible daughters map to V0, neutral-leg, and timing observables | branching chain composition and production under-sampling | Sigma rows report chain id and cannot reuse Lambda/K_S yields as production rates |

These leaves keep decay branching, production yield, reconstruction
survival, and plan-37 survivor intervals as separate factors. A
strange-contamination row becomes a background-rate input only when all
four factors are present with intervals and signed source conventions.

#### Logic gaps

| Parameter | Status before production | Closure study / target date |
|---|---|---|
| PDG branching snapshot and uncertainties | `OPEN:` values are prose-checked but need a replayable manifest | Freeze `DEC-59-PDG-BRANCHING-SNAPSHOT` with source ids and access date; target 2026-06-20 |
| strange production yield by beam-neutron node/material | `OPEN:` missing or under-sampled in nominal beam-neutron rows | Build Lambda/K_S/Sigma enriched sidecars and yield table by plan-44 node; target 2026-07-05 |
| V0 displacement, pointing, DCA, timing, and mass-window thresholds | `OPEN:` axes named but no numeric production thresholds | Scan each threshold on Lambda-enriched, K_S sideband, and signal samples; target 2026-07-05 |
| signal-efficiency loss budget for V0 veto | `OPEN:` must be measured before veto promotion | Propagate veto candidates through S.6 and assign plan-45 residual nuisance; target 2026-07-10 |
| residual strange-contamination interval | `OPEN:` no plan-44 rate inclusion until production yield and intervals exist | Combine yield, branching, survival, and F-C/Wilson intervals in §8 summary; target 2026-07-10 |

#### Closure test for the derivation

1. Build PDG branching rows and a strange-yield table keyed to plan-44
   beam-neutron nodes and source-material bins.
2. Create Lambda-enriched, Sigma-chain, and K_S sideband validation
   slices; drop truth labels before running V0 reconstruction.
3. Scan displacement, pointing, mass, timing, and neutral-leg cuts,
   recording signal loss on `sig_foil_v3` and residual strange survivors.
4. Verify sidecar-drop hashes: production V0 candidates, rejection
   reasons, and plan-37 survival must not change without truth labels.
5. Hand off measured or upper-limit contamination rows to plan 44 and
   residual nuisance/signal-loss rows to plan 45.

## 7. Closure on a Lambda-enriched beam-neutron slice

The required closure sample is a Lambda-enriched slice derived from the
beam-neutron secondary-hadronic sample. Enrichment may be truth-filtered
only when building a validation dataset; the production V0 rejection is
then run after dropping truth labels.

1. Select beam-neutron events with validation-sidecar evidence of a
   generated Lambda or Sigma0 -> Lambda gamma in material near the
   detector.
2. Record the parent plan-44 node, material label, generated momentum,
   and decay branch in a validation manifest.
3. Drop truth labels and run the V0 candidate builder on reconstructed
   tracks, neutral objects, vertices, and event variables.
4. Evaluate the §6 rejection cuts and plan-37 S.1-S.6 survival.
5. Report Lambda reconstruction efficiency, rejection efficiency,
   signal-efficiency loss on `sig_foil_v3`, and residual survivor
   counts with intervals.
6. Repeat on a K_S^0-enriched sideband if the Lambda closure passes but
   pi0-like leakage remains.
7. Save sidecar-drop hashes proving that production decisions do not
   depend on generated particle names or ancestry.

### 7.1 Closure rows

| Closure row id | Dataset | Observable | Pass rule |
|---|---|---|---|
| `lambda_enriched_rejection_v0` | `beam_neutron_hibeam_secondaries_v1:lambda_enriched` | Lambda-tagged survivor fraction after V0 cuts | survivor interval below plan-44 allocated strange budget |
| `sigma0_lambda_gamma_v0` | `beam_neutron_hibeam_secondaries_v1:sigma0_chain` | gamma+Lambda leakage into EM variables | leakage row has interval and caveat |
| `ks0_pipi_v0` | `beam_neutron_hibeam_scattered_v1:ks0_enriched` | K_S^0 two-prong rejection | K_S^0 mass/displacement veto efficiency measured |
| `signal_v0_veto_loss_v0` | `sig_foil_v3` | signal S.6 loss from strange veto | loss assigned as plan-45 nuisance if nonzero |

## 8. Contamination summary and handoff

| Field | Required content |
|---|---|
| `study_id` | stable strange-contamination study key |
| `source_node_id` | plan-44 parent node |
| `particle_class` | K_S^0, Lambda, Sigma+, Sigma-, Sigma0, or mixed |
| `production_yield_status` | `measured`, `upper_limit`, `missing`, or `not_applicable` |
| `branching_row_ids` | PDG rows from §2 |
| `n_generated_or_enriched` | denominator for closure |
| `n_v0_candidates` | reconstructed V0 candidates |
| `n_after_rejection` | survivors after §6 cuts |
| `n_after_s6` | survivors after plan-37 selection |
| `interval_method` | Wilson or Feldman-Cousins |
| `handoff_status` | `ready_for_plan44`, `diagnostic_only`, or `blocked` |

Plan 44 consumes only rows with measured or upper-limit production yield
and complete intervals. Plan 45 consumes the residual uncertainty and
signal-veto loss. Plan 50 consumes the caveat text when rows remain
blocked.

## 9. Decision-log stubs

| DEC id | Decision to freeze | Required evidence |
|---|---|---|
| `DEC-59-STRANGE-SOURCE-MODEL` | choose nominal strange-production source and material bins | beam-neutron source DEC, strange-yield table, material map |
| `DEC-59-V0-REJECTION` | approve V0/displacement rejection for production use | Lambda-enriched closure, K_S sideband, signal-loss interval |
| `DEC-59-PDG-BRANCHING-SNAPSHOT` | freeze PDG edition and branching rows | PDG source ids, access date, replay manifest |
| `DEC-59-RESIDUAL-NUISANCE` | map residual strange contamination into plan 45 | summary intervals and covariance flags |

## 10. A+ verifier transcript

Before this plan was committed, the supporting local plan files were
checked for existence and source sections, and PDG values were checked
against official PDG Live / Review pages in the browser. This plan does
not specify any runnable nnbar reconstruction module command.

| Claim | Verifier |
|---|---|
| plan 14 strange-capable beam-neutron subchannels exist | `grep -nE "Secondary hadronic|Capture-gamma" docs/rebuild_plans/14_background_models.md` |
| plan 44 beam-neutron nodes exist | `grep -n "beam_neutron" docs/rebuild_plans/44_background_taxonomy.md` |
| plan 01 truth-use boundary exists | `grep -n "Class B" docs/rebuild_plans/01_realism_contract.md` |
| PDG K_S^0 branches checked | PDG Live node S012, constrained fit information |
| PDG Lambda branches checked | PDG Live node S018 |
| PDG Sigma branches checked | PDG Live nodes S019, S020, S021 / Review table |
| no stale code citation | no `*.py:<line>` citation appears in this plan |

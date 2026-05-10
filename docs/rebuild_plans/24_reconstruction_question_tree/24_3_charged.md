---
id: 24_3_charged_branch
title: Reconstruction question tree - charged-object branch
version: 0.1
status: draft
owner: Methodology Council
parent: 24_reconstruction_question_tree
last_updated: 2026-05-10
---

# Reconstruction question tree - charged-object branch

This file is a split-out branch of `docs/rebuild_plans/24_reconstruction_question_tree.md`
created to keep each plan file under the 500-line cap. It inherits the
truth-leakage gate, acceptance criteria, dependencies, and references from
plan 24.

## 3. Charged-object branch

**What is the irreducible TPC + scintillator evidence that a track is a
charged primary pion or proton?**

Answer now: a TPC-reconstructed track with scintillator-energy
matching consistent with a charged-track ray, characterised by dE/dx
and stopping range that distinguish π from p.

### 3.1 Leaves under charged

| Leaf ID | Decision |
|---|---|
| `C.1` | What constitutes a charged track candidate (post-V.1)? |
| `C.2` | How is dE/dx estimated from TPC step records? |
| `C.3` | How is stopping range estimated from scintillator hits? |
| `C.4` | How are scintillator hits associated to a TPC track? |
| `C.5` | How is the π/p decision made from {dE/dx, range, scintillator E}? |
| `C.6` | When is a candidate rejected (e.g. EM lineage)? |

**Owning subsystem plans:** 25 (V.1 reuse), 27 (dE/dx), 28 (range/
stopping), 29 (charged PID).

Plan 08 §3.4 documents the current code path. Plan 01 §4 audit
flags the current `Name`-gated PID as a Class B violation; the leaf
C.1 exit criterion is the migration of that gate.

Leaf C.1: V.1/V.2 tracks → charged-track candidates
  inputs (Class A): V.1 candidate-track table, V.2 direction table,
                    and referenced TPC columns
                    (Event_ID, x, y, z, t, eDep, photons, px, py,
                    pz, xHitID, module_ID, step_info, vol_name)
  forbidden (Class B): Name, Track_ID, Parent_ID, origin_vol_name,
                       particle_x, particle_y, particle_z
  decision rule: admit reconstructed track candidates by Class A
                 quality cuts (hit count, fitted direction, χ²/ndf,
                 and detector geometry) rather than by truth particle
                 name; plan 08 §3.4/§3.7 documents the current
                 `Name` gate that must move to validation only.
  output schema: {event_id: int64, charged_candidate_id: int64,
                  candidate_id: int64, anchor_xyz: float64[3],
                  direction_xyz: float64[3], n_tpc_hits: int32,
                  track_quality: float64,
                  charged_candidate_valid: bool}
  allowed truth use: validation_only
  downstream consumers: C.2, C.3, C.4, C.5, C.6; plans 27, 28, 29

#### C.1 Physics derivation

- **What is physically measured:** C.1 decides whether a reconstructed TPC
  track candidate is a charged-particle object eligible for PID, using only
  detector observables and not truth names or `Track_ID` labels.
- **Estimator rationale:** in a TPC, a charged particle is evidenced by a
  coherent ionisation trajectory with finite fitted direction and enough hit
  support for downstream dE/dx/range observables. TPC measurement and tracking
  practice support this detector-only candidate definition, while PDG passage
  material sets the charged-particle energy-loss context
  \cite{rubbia1977liquid,alice2014performance,ParticleDataGroup:2024RPP}.
- **Statistical character:** inefficiency is dominated by sparse tracks and
  detector-edge leakage; fake rate is dominated by EM conversions, neutral
  artefacts, and merged V.1 candidates. Robustness comes from quality/geometry
  flags rather than species-name preselection.
- **Citation:** `rubbia1977liquid`, `alice2014performance`, and
  `ParticleDataGroup:2024RPP` are resolved in the thesis bibliography.

#### C.1 Logic gaps

1. **Minimum TPC hit count:** OPEN: derive from V.1/V.2 closure by scanning hit
   count versus charged-candidate efficiency and fake rate; target resolution
   date 2026-05-24.
2. **Track-quality threshold / chi2 gate:** OPEN: scan with plan-26 residuals
   and C.2/C.3 downstream validity as the figure of merit; target resolution
   date 2026-05-24.
3. **Containment / edge buffer:** OPEN: import plan-60 TPC fiducial states and
   decide whether edge rows are `warn` or `fail`; target resolution date
   2026-05-31.
4. **EM/neutral pre-rejection boundary:** OPEN: decide which reconstructed
   topology/shower flags belong in C.1 versus C.6; target resolution date
   2026-06-07.

#### C.1 Closure test for the derivation

1. Build C.1 rows from frozen V.1/V.2 candidates after dropping `Name`,
   `Track_ID`, `Parent_ID`, and `origin_vol_name`.
2. Validate charged-candidate efficiency and fake rate only in a
   `validation_only` scorer that can inspect truth particle labels.
3. Pass when production C.1 rows are invariant to Class-B column removal and
   every rejected candidate has a detector-quality or geometry reason rather
   than a hidden truth species gate.

Leaf C.2: charged-track candidates → dE/dx estimator
  inputs (Class A): C.1 charged-candidate table plus referenced TPC
                    step columns (Event_ID, eDep, TrackLength, x, y,
                    z, t, photons, step_info)
  forbidden (Class B): Name, Track_ID, Parent_ID, origin_vol_name,
                       particle_x, particle_y, particle_z
  decision rule: compute per-step `eDep / TrackLength` in a
                 detector-only track slice, then form the plan 27
                 truncated mean (drop top 30%, bottom 10% until
                 calibration retunes it); the current plan 08 §3.4
                 `dedx` output remains valid only after the C.1
                 truth-name gate is removed.
  output schema: {event_id: int64, charged_candidate_id: int64,
                  dedx_mev_per_cm: float64, estimator: string,
                  n_steps_used: int32, path_length_cm: float64,
                  low_truncation_fraction: float64,
                  high_truncation_fraction: float64,
                  calibration_source: string}
  allowed truth use: validation_only
  downstream consumers: C.5, C.6; plans 27, 29

#### C.2 Physics derivation

- **What is physically measured:** C.2 estimates the specific ionisation
  energy loss per unit path length for a charged candidate in the TPC gas. The
  truth-side validation quantity is the particle βγ/species curve; production
  uses only energy deposits and path-length estimates.
- **Estimator rationale:** charged-particle ionisation follows Bethe-Bloch with
  Landau-like high tails in finite samples, so a truncated mean of per-step
  `eDep / step_length` is the robust near-optimal estimator for PID inputs.
  PDG passage-of-particles material establishes the Bethe-Bloch and straggling
  picture, and ALICE documents TPC dE/dx truncation practice
  \cite{ParticleDataGroup:2024RPP,alice2014performance}.
- **Statistical character:** high-side Landau tails dominate raw-mean variance;
  low-side threshold losses and path-length errors bias the estimator. The
  truncation fractions trade robustness against bias for short NNBAR tracks.
- **Citation:** `ParticleDataGroup:2024RPP` and `alice2014performance` are
  resolved in the thesis bibliography.

#### C.2 Logic gaps

1. **Low/high truncation = 10% / 30%:** OPEN: scan low fractions 0-20% and high
   fractions 10-50% on `cal_singlepion_50to600MeV_v2` and
   `cal_singleproton_50to500MeV_v2`; figure of merit is Bethe-Bloch residual
   plus C.5 π/p separation; target resolution date 2026-05-17.
2. **Minimum selected steps:** OPEN: set the minimum after the truncation scan;
   report bias/variance versus `n_steps_used`; target resolution date
   2026-05-17.
3. **Path-length source:** OPEN: choose between raw `TrackLength`, V.2 geometry,
   and class-A coordinate differences; figure of merit is dE/dx residual by
   angle and lever arm; target resolution date 2026-05-24.
4. **TPC W-value / calibration scale:** OPEN: propagate plan-17 W-value and gas
   calibration choices into `calibration_source`; target resolution date
   2026-05-24.

#### C.2 Closure test for the derivation

1. Build frozen C.2 rows on pion and proton calibration samples using only C.1
   candidates and Class-A TPC deposits/path lengths.
2. Join validation-only βγ/species labels after the C.2 table is frozen and
   fit the Bethe-Bloch residual curve in βγ bins.
3. Pass when residuals stay within the plan-27 5% closure band or the dominant
   calibration limitation is recorded without retuning the production PID
   threshold silently.

Leaf C.3: charged-track candidates + scintillator hits → stopping range
  inputs (Class A): C.1 charged-candidate table, V.2 direction table,
                    matched-scintillator columns (Event_ID, x, y, z,
                    t, eDep, photons, module_ID, vol_name, step_info),
                    and `Scintillator_Module_Position.txt`
                    geometry side-car
  forbidden (Class B): Name, Track_ID, Parent_ID, origin_vol_name,
                       particle_x, particle_y, particle_z
  decision rule: after C.4 supplies geometrically associated
                 scintillator hits, project each hit onto the track
                 direction and report the maximum positive projected
                 distance from the TPC entry/anchor; plan 28 keeps the
                 current plan 08 §3.4 range estimator and adds a
                 Bragg-peak closure before using it as a PID input.
  output schema: {event_id: int64, charged_candidate_id: int64,
                  range_cm: float64, range_edep_mev: float64,
                  n_scintillator_hits: int32,
                  last_hit_module_id: int32,
                  bragg_peak_position_cm: float64,
                  range_valid: bool}
  allowed truth use: validation_only
  downstream consumers: C.5, C.6; plans 28, 29

#### C.3 Physics derivation

- **What is physically measured:** C.3 estimates the charged candidate's
  stopping range through the scintillator stack and the Bragg-profile endpoint
  from Class-A scintillator hit positions and energy deposits.
- **Estimator rationale:** range is the maximum forward path length along the
  reconstructed V.2 direction for associated scintillator hits; for stopping
  protons, CSDA/PSTAR tables provide the validation expectation, and the Bragg
  peak follows from increasing stopping power near the endpoint
  \cite{NISTSTAR,ParticleDataGroup:2024RPP}.
- **Statistical character:** bias comes from missed/extra associated hits,
  scintillator pitch, edge leakage, and V.2 direction error; variance is
  granularity-limited once hit association is fixed. Robust rows must separate
  no-hit, edge-loss, and invalid-fit failures.
- **Citation:** `NISTSTAR` and `ParticleDataGroup:2024RPP` are resolved in the
  thesis bibliography.

#### C.3 Logic gaps

1. **Forward projection cut = `projection >= 0`:** derived from the definition
   of downstream range along the reconstructed track direction.
2. **Association angle 10 deg / distance 15 cm:** OPEN: C.4 must retune these
   with range residual and fake-association rate as the figure of merit; target
   resolution date 2026-05-24.
3. **Bragg minimum hits = 3:** OPEN: scan 2-5 associated hits and require stable
   endpoint bias versus PSTAR; target resolution date 2026-05-24.
4. **Range closure tolerance = max(1 cm, one bar pitch):** OPEN: bind the bar
   pitch to plan-16/60 geometry and update the tolerance if the geometry tag
   changes; target resolution date 2026-05-31.

#### C.3 Closure test for the derivation

1. Build C.3 rows on `cal_singleproton_50to500MeV_v2` using frozen C.1/V.2 rows
   and Class-A scintillator hits only.
2. Join validation-only kinetic energy/path labels after the range table is
   frozen, then compare `range_cm` to PSTAR/CSDA expectations in energy bins.
3. Pass when mean range closes within the plan-28 tolerance and the Bragg peak
   is resolved within one bar pitch for stopping protons, with edge failures
   reported separately from nominal rows.

Leaf C.4: charged-track candidates + scintillator hits → hit association
  inputs (Class A): C.1 charged-candidate table, V.2 direction table,
                    scintillator hit columns (Event_ID, x, y, z, t,
                    eDep, photons, module_ID, vol_name, step_info),
                    and scintillator geometry side-car
  forbidden (Class B): Track_ID, Parent_ID, Name, origin_vol_name,
                       particle_x, particle_y, particle_z
  decision rule: associate scintillator hits to a TPC track by
                 ray-to-hit angle, closest-approach distance, and
                 optional timing consistency using the
                 ReconstructionConfig thresholds cited in plan 08
                 §3.4; exact `Track_ID` matching is not a production
                 association rule and is retained only for validation
                 of sparse legacy tables.
  output schema: {event_id: int64, charged_candidate_id: int64,
                  scintillator_hit_indices: int64[],
                  match_angle_deg: float64,
                  closest_approach_cm: float64,
                  time_residual_ns: float64,
                  matched_edep_mev: float64, match_method: string,
                  association_valid: bool}
  allowed truth use: validation_only
  downstream consumers: C.3, C.5, C.6; plans 28, 29

Leaf C.5: dE/dx + range + scintillator energy → π/p PID decision
  inputs (Class A): C.1 charged-candidate table, C.2 dE/dx table,
                    C.3 range table, C.4 scintillator association
                    table, and ReconstructionConfig PID thresholds
  forbidden (Class B): Name, Track_ID, Parent_ID, origin_vol_name,
                       particle_x, particle_y, particle_z, truth PID
                       labels from calibration tables
  decision rule: apply the cut-based plan 29 §1 baseline
                 (`dedx >= proton_dedx_min` or short-range +
                 lower-dE/dx proton rule) to every valid charged
                 candidate; likelihood-ratio or MVA replacements
                 must be scored on the plan 38 C.5 ladder before
                 replacing the baseline.
  output schema: {event_id: int64, charged_candidate_id: int64,
                  pid: string, proton_score: float64,
                  pion_score: float64,
                  dedx_threshold_mev_per_cm: float64,
                  range_threshold_cm: float64,
                  decision_rule_version: string,
                  pid_valid: bool, decision_reason: string}
  allowed truth use: validation_only
  downstream consumers: C.6, E.9, S.2; plans 29, 36, 37

#### C.5 Physics derivation

- **What is physically measured:** C.5 estimates whether a charged candidate is
  pion-like or proton-like from frozen C.2 dE/dx, C.3 range, C.4 association,
  and scintillator energy observables.
- **Estimator rationale:** Bethe-Bloch ionisation plus stopping range provide
  complementary π/p separation; the cut-based baseline approximates a
  likelihood decision boundary, while the target likelihood-ratio classifier is
  the calibrated extension for correlated observables \cite{ParticleDataGroup:2024RPP,alice2014performance,Fisher1936Discriminant,Pedregosa:2011Scikit}.
- **Statistical character:** threshold bias dominates near stopping-proton and
  low-dE/dx boundaries; variance comes from C.2/C.3 measurement errors and
  calibration-sample size. Robustness requires frozen calibration artifacts and
  rule-versioned scores, not truth labels during production scoring.
- **Citation:** `ParticleDataGroup:2024RPP`, `alice2014performance`,
  `Fisher1936Discriminant`, and `Pedregosa:2011Scikit` are resolved in the
  thesis bibliography.

#### C.5 Logic gaps

1. **Cut thresholds (`proton_dedx_min`, `short_range_cm`,
   `short_range_proton_dedx_min`):** OPEN: scan on locked pion/proton
   calibration samples with balanced F1, ROC AUC, and plan-38 ladder delta as
   figures of merit; target resolution date 2026-05-24.
2. **Likelihood-ratio promotion threshold:** OPEN: choose only after plan 57
   train/validation/test split hashes exist; target resolution date 2026-05-31.
3. **Feature covariance between C.2 and C.3:** OPEN: estimate from calibration
   residuals and include in the likelihood score uncertainty; target resolution
   date 2026-05-31.
4. **Invalid C.2/C.3 handling:** OPEN: decide whether null dE/dx/range rows are
   rejected, down-weighted, or scored as `unclassified`; target resolution date
   2026-05-24.

#### C.5 Closure test for the derivation

1. Freeze C.1/C.2/C.3/C.4 production tables, then run the cut-based and
   likelihood-ratio C.5 scorer without truth labels in the scoring input.
2. Use labeling-only calibration splits to tune thresholds, then validation-only
   labels to compute π/p confusion matrices, ROC curves, and balanced F1.
3. Pass when the rule-versioned C.5 table is invariant to dropping truth labels
   and any promoted classifier beats the cut baseline without regressing plan-47
   reproduction rows.

Leaf C.6: PID candidates + topology → rejected-candidate mask
  inputs (Class A): C.1-C.5 charged outputs, lead-glass / shower
                    shape observables from P.1/P.2 when available,
                    TPC pair topology, hit timing, and geometry
                    side-cars for beampipe/silicon material regions
  forbidden (Class B): Name, Track_ID, Parent_ID, origin_vol_name,
                       Interaction ancestry, particle_x/y/z truth
                       origins, truth PID labels
  decision rule: reject a charged candidate only with observable
                 evidence (EM-like lead-glass match, conversion-pair
                 topology, invalid C.1-C.5 quality gates, or geometry
                 inconsistency); the plan 29 §3 replacement for the
                 current truth-name filter must keep every rejection
                 reason auditable and Class A.
  output schema: {event_id: int64, charged_candidate_id: int64,
                  rejected: bool, rejection_flags: string[],
                  rejection_primary_reason: string,
                  pid_before_rejection: string,
                  pid_after_rejection: string,
                  rejection_rule_version: string}
  allowed truth use: validation_only
  downstream consumers: E.9, S.2; plans 29, 32, 36, 37

### Next measurement (charged branch)

Per-species reconstructed efficiency on `cal_singlepion*` and
`cal_singleproton` samples (plan 23), broken down by C.1–C.6.

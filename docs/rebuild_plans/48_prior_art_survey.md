---
id: 48_prior_art_survey
title: Prior-art survey — methods we may borrow
version: 0.2
status: draft
owner: Methodology Council
depends_on: [00_README, 24_reconstruction_question_tree]
outputs:
  - {path: docs/rebuild_plans/48_prior_art_survey.md, schema: this file}
acceptance:
  - {test: each leaf in plan 24 has at least one prior-art entry, method: leaf cross-reference, pass_when: full coverage}
  - {test: each entry has a citation that resolves to a paper or codebase, method: link verification, pass_when: zero broken refs}
risks:
  - {risk: borrowed method ports incorrectly because of NNBAR-specific geometry / physics, mitigation: §5 adaptation notes}
estimated_effort: M
last_updated: 2026-05-10
---

# Prior-art survey

*Charter.* For each reconstruction leaf in plan 24, list candidate
methods drawn from existing HEP, detector-reconstruction, and
n--nbar-search practice that could be borrowed when plan 49 selects an
improvement target. The survey is descriptive; selection, ranking, and
implementation ownership are plan 49's job.

This version is citation-gated: every promoted literature citation below
uses a BibTeX key that was verified in the thesis bibliography on
2026-05-10. Web-only sources are clearly labelled and are not used as
BibTeX citations until a key is added by the bibliography owner.

## 1. Prior-art source classes

| Source class | Verified citation(s) | What it can safely inform | What it must not decide |
|---|---|---|---|
| Free n--nbar beam searches | `Baldo-Ceolin:1994hzw`, `Gudkov:2021wvn`, `phillips2016neutron` | annihilation-target constraints, quasi-free beam logic, detector acceptance vocabulary | NNBAR reconstruction thresholds without plan 38/40 closure |
| Bound-nucleon searches | `Abe:2020ywm` | final-state topology and multi-prong event-selection analogies | free-neutron detector geometry or foil acceptance |
| ESS / HIBEAM / NNBAR design papers | `HIBEAM_NNBAR_at_ESS`, `Santoro2024NNBARCDR`, `Santoro2025HIBEAMInstrument`, `sym14010076`, `Backman_2022`, `Barrow:2021deh` | detector-specific constraints, expected topology, software and simulation scope | unverified code-level implementation claims |
| TPC and charged-particle tracking | `rubbia1977liquid`, `alice2014performance`, `Ester:1996DBSCAN`, `Kalman:1960new`, `Fruehwirth:2007AdaptiveVertex` | cluster finding, fit covariance, vertex-fit patterns | momentum-from-curvature claims in the no-B-field NNBAR geometry |
| PID and multivariate classification | `alice2014performance`, `Fisher1936Discriminant`, `Breiman2001RandomForests`, `Friedman2001GradientBoosting`, `Pedregosa:2011Scikit` | dE/dx templates, calibrated scores, classifier validation protocol | training labels inside production reconstruction |
| Event-shape and statistical interpretation | `BjorkenBrodsky1970`, `DasguptaSalam2004`, `Cowan:2011Likelihood` | sphericity/thrust style variables, likelihood-ratio reporting | substituting asymptotic significance for reproduction closure |
| Recent reviews | `Broussard2025NNBARTheory`, `Abele2023ParticlePhysicsESS`, `phillips2016neutron` | examiner-facing context and future-proofing | changing leaf definitions without plan 05 decision logging |

### 1.1 MURMUR handling

The MURMUR experiment is relevant as a neutron-hidden-neutron / passing-
through-walls comparison, not as direct n--nbar reconstruction prior art.
The live bibliography has no verified MURMUR BibTeX key yet. Therefore
this plan records the source as a bibliography-maintenance gap instead
of inventing a key:

- source needing a future key: *Probing neutron-hidden neutron
  transitions with the MURMUR experiment*, DOI
  `10.1140/epjc/s10052-021-08829-y`;
- owner: Methodology Council plus bibliography maintainer;
- rule: no plan may write a MURMUR BibTeX citation command until the key
  is present and grep-verifies in the bibliography.

## 2. Search-context lessons for NNBAR plans

| Context | Citation | Rebuild lesson | Consumed by |
|---|---|---|---|
| ILL direct free-neutron search | `Baldo-Ceolin:1994hzw` | treat target acceptance, annihilation containment, and quasi-free conditions as explicit denominators, not prose | plans 13, 37, 43, 60 |
| PF1B / ILL proposal | `Gudkov:2021wvn` | separate beamline geometry, magnetic environment, and detector acceptance when forecasting sensitivity | plans 11, 13, 43, 60 |
| Super-K bound-neutron search | `Abe:2020ywm` | multi-prong event classification needs topology robustness and channel breakdowns | plans 37, 41, 43, 47 |
| Theory and experimental prospects review | `phillips2016neutron` | examiner-facing claims should separate free-neutron limits, bound-neutron limits, and nuclear suppression factors | plans 13, 43, 50 |
| Nuclear-matrix / BSM review | `Broussard2025NNBARTheory` | cite theory motivation without letting BSM prior expectations tune reconstruction | plans 13, 48, 50 |
| HIBEAM/NNBAR ESS program | `HIBEAM_NNBAR_at_ESS`, `Santoro2024NNBARCDR`, `Santoro2025HIBEAMInstrument` | use ESS-specific detector and beamline constraints as design context | plans 11, 16, 37, 43, 60 |
| Existing NNBAR annihilation-detector studies | `sym14010076`, `Backman_2022`, `Barrow:2021deh` | preserve thesis-reproduction observables before proposing improvements | plans 08, 24, 36, 37, 47 |

## 3. Leaf coverage matrix

Every plan-24 leaf has at least one borrowable prior-art family below.
Plan 49 may rank these candidates, but it must not select an improvement
unless the relevant closure plan can test it.

| Leaf | Borrowable method family | Verified citation(s) | NNBAR adaptation note | Plan-49 hook |
|---|---|---|---|---|
| V.1 TPC hits to track candidates | density clustering + straight-line Hough/seed finding | `Ester:1996DBSCAN`, `alice2014performance` | no curvature term; cluster in detector coordinates and keep hit provenance | track-candidate finder |
| V.2 track fit/residuals/pulls | Kalman-style state covariance, but with straight-line propagation | `Kalman:1960new`, `alice2014performance` | no momentum-from-B-field; covariance is for direction/position residuals | track-fit covariance |
| V.3 foil-plane projection | line-plane geometry with propagated covariance | `Kalman:1960new` | propagate V.2 covariance to foil intercept uncertainty | foil projection |
| V.4 event vertex estimate | adaptive vertex fit / weighted aggregation | `Fruehwirth:2007AdaptiveVertex` | outlier weights must use reconstructed residuals only | vertex aggregation |
| V.5 foil-compatible vertex flag | acceptance denominator discipline from direct searches | `Baldo-Ceolin:1994hzw`, `Gudkov:2021wvn` | fiducial cuts become plan 60 profiles, not hidden selection constants | fiducial policy |
| C.1 charged-track candidates | TPC object-building practice | `rubbia1977liquid`, `alice2014performance` | charged candidate is a reconstruction object, not a truth-particle alias | charged-object schema |
| C.2 dE/dx estimator | truncated-mean dE/dx | `alice2014performance` | truncation fractions are calibration constants validated on plan 23 samples | dE/dx robustness |
| C.3 range/stopping observables | range tables plus detector-response closure | `sym14010076`, `Dunne2022CalorimeterPrototype` | range is observable scintillator path, not truth kinetic energy | stopping-range closure |
| C.4 scintillator association | nearest compatible hit / particle-flow-style association | `alice2014performance`, `sym14010076` | association must persist hit sidecars for audit | charged-hit association |
| C.5 π/p PID decision | likelihood or calibrated classifier | `Fisher1936Discriminant`, `Breiman2001RandomForests`, `Friedman2001GradientBoosting` | labels are allowed only for training/validation artifacts, never online production rows | PID scorer |
| C.6 rejection mask | calibrated rejection plus topology veto | `Cowan:2011Likelihood`, `Pedregosa:2011Scikit` | rejection threshold must be chosen on frozen validation splits | charged rejection |
| P.1 EM/neutral clusters | calorimeter clustering / particle-flow decomposition | `sym14010076`, `Dunne2022CalorimeterPrototype` | combined lead-glass + scintillator requires explicit energy-weight policy | EM clustering |
| P.2 photon-like discriminant | shower-shape and charged-track veto | `sym14010076`, `Dunne2022CalorimeterPrototype` | charged veto uses reconstructed C.4 links only | photon tagging |
| P.3 photon direction | vertex-constrained direction from cluster centroid | `sym14010076` | direction changes when V.4 changes; store vertex version | photon direction |
| P.4 photon energy | calorimeter calibration closure | `Dunne2022CalorimeterPrototype`, `sym14010076` | no truth-energy substitution outside validation | photon energy |
| P.5 π0 pair candidates | invariant-mass pair enumeration | `sym14010076` | pair candidates must keep all combinatorics until a documented veto stage | pi0 pairing |
| P.6 accidental-pair veto | likelihood-style compatibility test | `Cowan:2011Likelihood` | veto uses reconstructed isolation and timing only | pi0 accidental veto |
| P.7 kinematic-fit π0 candidates | constrained fit / covariance propagation | `Kalman:1960new`, `Fruehwirth:2007AdaptiveVertex` | mass constraint is an improvement candidate, not baseline reproduction | pi0 kinematic fit |
| E.1 total calorimeter energy | calorimeter energy accounting | `sym14010076`, `Dunne2022CalorimeterPrototype` | sum must declare included subsystems and calibration profile | visible-energy table |
| E.2 hemisphere energy split | direct-search acceptance bookkeeping | `Baldo-Ceolin:1994hzw`, `sym14010076` | hemisphere definition must be geometry-versioned | energy-balance split |
| E.3 longitudinal energy | event-shape projection | `BjorkenBrodsky1970`, `DasguptaSalam2004` | axis definition is reconstructed-only | event variables |
| E.4 transverse energy | event-shape projection | `BjorkenBrodsky1970`, `DasguptaSalam2004` | shares the same reconstructed axis as E.3 | event variables |
| E.5 sphericity | classic event-shape tensor | `BjorkenBrodsky1970`, `DasguptaSalam2004` | inputs are reconstructed object momenta/proxies only | sphericity robustness |
| E.6 Fox-Wolfram / thrust-like moments | event-shape moments and thrust reviews | `DasguptaSalam2004` | if Fox-Wolfram-specific citation is added later, verify its key first | event-shape extension |
| E.7 visible invariant mass | multi-object mass reconstruction | `sym14010076`, `Backman_2022` | use reconstructed four-vectors with propagated object uncertainties | visible mass |
| E.8 timing split | detector-response quality split | `Dunne2022CalorimeterPrototype`, `Santoro2024NNBARCDR` | timing thresholds belong to DQM/calibration plans, not hidden constants | timing variables |
| E.9 object multiplicities | multi-prong topology classification | `Abe:2020ywm`, `sym14010076` | multiplicities are reconstructed-object counts, not truth particle counts | topology table |
| S.1 pre-selection flags | target/fiducial acceptance accounting | `Baldo-Ceolin:1994hzw`, `Gudkov:2021wvn` | pre-selection must expose numerator and denominator separately | preselection |
| S.2 pion multiplicity cut | Super-K multi-prong event practice + NNBAR detector studies | `Abe:2020ywm`, `sym14010076` | pion labels derive from C/P reconstruction, not truth names | pion cut |
| S.3 visible-mass cut | invariant-mass signal window | `sym14010076`, `Backman_2022` | threshold changes require plan 05 decision logging | mass cut |
| S.4 event-shape cut | sphericity/thrust style variables | `BjorkenBrodsky1970`, `DasguptaSalam2004` | cut must be scanned by plan 41 before promotion | shape cut |
| S.5 hemisphere-balance cut | calorimeter balance / containment | `sym14010076`, `Dunne2022CalorimeterPrototype` | split definition must be frozen before ROC scans | balance cut |
| S.6 final cut-flow and uncertainty | likelihood/significance reporting | `Cowan:2011Likelihood`, `Abe:2020ywm` | final quote still depends on reproduction ledger and plan 43 efficiency | final selection |

## 4. Method-family notes

### 4.1 Tracking and vertexing

- **DBSCAN / density clustering** (`Ester:1996DBSCAN`) is a defensible
  starting point for V.1 because the current Geant4-derived TPC rows are
  sparse and a density method can label noise without using truth IDs.
  Plan 49 must rank it against simpler straight-line seeding and must
  store the DBSCAN radius/min-sample parameters in the manifest.
- **TPC practice from ALICE** (`alice2014performance`) is useful for
  vocabulary and dE/dx/tracking quality patterns. It is not a geometry
  copy: NNBAR lacks the ALICE magnetic-field/momentum setting.
- **Kalman filtering** (`Kalman:1960new`) is a covariance pattern, not a
  curvature requirement. NNBAR can borrow state propagation and residual
  bookkeeping while using a straight-line transport model.
- **Adaptive vertex fitting** (`Fruehwirth:2007AdaptiveVertex`) is the
  V.4 upgrade candidate when multiple charged candidates point to the
  foil. Its weights must be driven by reconstruction residuals only.

### 4.2 Charged PID and rejection

- **dE/dx truncated means** from TPC practice (`alice2014performance`)
  are the preferred C.2 improvement family because they reduce tail
  sensitivity while staying interpretable.
- **Linear and multivariate classifiers** (`Fisher1936Discriminant`,
  `Breiman2001RandomForests`, `Friedman2001GradientBoosting`,
  `Pedregosa:2011Scikit`) are valid C.5/C.6 candidates only inside the
  plan 57 protocol: fixed train/validation splits, frozen features,
  calibration curves, and no truth-label reads at inference time.
- **Likelihood-style reporting** (`Cowan:2011Likelihood`) may guide score
  calibration and final reporting, but it cannot replace plan 40 closure
  or plan 47 reproduction-ledger sign-off.

### 4.3 EM objects and event variables

- The detector papers (`sym14010076`, `Backman_2022`,
  `Dunne2022CalorimeterPrototype`) are the primary source for practical
  NNBAR calorimeter constraints. Generic collider EM algorithms may be
  considered later, but only after their input assumptions are mapped to
  lead-glass plus scintillator geometry.
- Event-shape variables use the classic sphericity/event-shape lineage
  (`BjorkenBrodsky1970`, `DasguptaSalam2004`). In NNBAR they are
  reconstructed-object summaries and therefore inherit all C/P object
  uncertainties.
- Any kinematic fit for π0 candidates must persist input covariance,
  fit status, and pre-fit values. A mass-constrained fit is an
  improvement candidate, not the reproduction baseline.

### 4.4 Selection and efficiency context

- Direct searches (`Baldo-Ceolin:1994hzw`, `Gudkov:2021wvn`) make the
  acceptance denominator visible. L0 plans 43 and 60 should therefore
  report generated, fiducial, reconstructed, and selected counts as
  separate factors.
- Super-K (`Abe:2020ywm`) contributes topology discipline: final-state
  categories and systematic variations must be explicit. It does not
  license importing water-Cherenkov thresholds into NNBAR.
- ESS/HIBEAM reviews and CDR material (`Abele2023ParticlePhysicsESS`,
  `HIBEAM_NNBAR_at_ESS`, `Santoro2024NNBARCDR`,
  `Santoro2025HIBEAMInstrument`) are context for reviewer defence and
  future detector interfaces.

## 5. NNBAR-specific adaptation rules

1. **No magnetic field.** Any tracking prior art that assumes curvature
   can donate only clustering, covariance, or residual machinery unless
   a plan 05 decision introduces an observable momentum proxy.
2. **Truth labels are Class B.** Training, validation, and diagnostic
   closures may use labels under the plan 01 decorators; production
   rows may not read `Name`, `Track_ID`, `Parent_ID`, or truth vertices.
3. **Geant4-only calibration.** Borrowed detector-response methods carry
   an MC-only limitations entry until real calibration data exist.
4. **Acceptance denominators are first-class.** Direct-search context
   requires every efficiency plot to expose its denominator and fiducial
   profile.
5. **No web-only method promotion.** Web pages or papers without a
   verified BibTeX key can be recorded as gaps, but cannot support a
   promoted method row.
6. **Closure before improvement.** A method is not selectable in plan 49
   until the corresponding plan 40/41/43 closure can measure its effect.

## 6. Citation resolver table

The keys below were grep-verified in the thesis bibliography during this
iteration. Future edits must repeat this check before adding or retaining
citation keys.

| Key | Used for |
|---|---|
| `Abe:2020ywm` | Super-K n--nbar topology and bound-neutron comparison |
| `Abele2023ParticlePhysicsESS` | ESS particle-physics context |
| `Backman_2022` | NNBAR experiment development and detector constraints |
| `Baldo-Ceolin:1994hzw` | ILL direct free-neutron search |
| `Barrow:2021deh` | HIBEAM/NNBAR simulation framework |
| `BjorkenBrodsky1970` | sphericity/event-shape origin |
| `Breiman2001RandomForests` | classifier baseline |
| `Broussard2025NNBARTheory` | recent BNV/nuclear-matrix review context |
| `Cowan:2011Likelihood` | likelihood/significance reporting |
| `DasguptaSalam2004` | event-shape review |
| `Dunne2022CalorimeterPrototype` | calorimeter prototype context |
| `Ester:1996DBSCAN` | density clustering |
| `Fisher1936Discriminant` | linear discriminant baseline |
| `Friedman2001GradientBoosting` | boosted classifier baseline |
| `Fruehwirth:2007AdaptiveVertex` | adaptive vertex fitting |
| `Gudkov:2021wvn` | PF1B / ILL proposal |
| `HIBEAM_NNBAR_at_ESS` | ESS HIBEAM/NNBAR program |
| `Kalman:1960new` | covariance/state-estimation pattern |
| `Pedregosa:2011Scikit` | scikit-learn validation tooling reference |
| `Santoro2024NNBARCDR` | HighNESS CDR / NNBAR experiment design |
| `Santoro2025HIBEAMInstrument` | current HIBEAM instrument context |
| `alice2014performance` | TPC tracking and dE/dx practice |
| `phillips2016neutron` | n--nbar theory/experimental prospects review |
| `rubbia1977liquid` | TPC detector concept |
| `sym14010076` | NNBAR annihilation-detector design and observables |

## 7. Plan-49 handoff

Plan 49 consumes this file by creating one improvement proposal per
method family, not one proposal per citation. Each proposal must record:

1. plan-24 leaf ID(s);
2. citation key(s) from §6;
3. expected ladder leaf delta from plan 38;
4. closure command or blocked L3 owner;
5. validation-only truth use, if any;
6. non-regression guard against plan 47 reproduction rows.

## 8. Acceptance criteria

- §3 covers all V.*, C.*, P.*, E.*, and S.* leaves from plan 24.
- Every promoted citation key appears in §6 and grep-verifies in the
  bibliography.
- The MURMUR source remains a named bibliography-maintenance gap until
  the bibliography contains a verified key.
- Every adaptation note names the NNBAR-specific assumption that prevents
  direct copying.
- Plan 49 can rank candidates without re-discovering literature.

## 9. Dependencies

- **24** — leaf identities and truth-use classes.
- **38, 40, 41, 43** — validation ladder, closure, and efficiency gates.
- **49** — consumes this survey to rank targeted improvements.
- **50** — consumes the search-context table for reviewer defence.
- **57** — governs classifier-style PID or event-tagging methods.

## 10. References

The canonical references are the BibTeX keys in §6 plus the web-only
MURMUR DOI source in §1.1. No uncited prose reference is intentionally
left in this version.

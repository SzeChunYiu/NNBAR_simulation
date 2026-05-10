---
id: 34_subsystem_pi0_pairing
title: Subsystem — π⁰ pairing (leaves P.5, P.6)
version: 0.1
status: draft
owner: EM-Object POG
depends_on: [00_README, 24_reconstruction_question_tree, 33_subsystem_photon_object, 38_truth_substitution_ladder, 40_closure_and_pulls]
outputs:
  - {path: docs/rebuild_plans/34_subsystem_pi0_pairing.md, schema: this file}
acceptance:
  - {test: π⁰ mass peak μ within 5 MeV of PDG 134.977 MeV on cal sample, method: §2 closure, pass_when: pass}
  - {test: every selection cut (mass window, total E, scint E, LG E, LG fraction, opening angle) appears as an individual passes_* column, method: schema review, pass_when: present}
  - {test: accidental rate measured on cal_singlepion_mip_v1 (no π⁰), method: §3 fake-rate, pass_when: rate documented}
risks:
  - {risk: combinatorial pairing scales O(N²) and may pick wrong partner in high-multiplicity events, mitigation: §3 best-mass-match heuristic + kinematic-fit χ² (plan 35)}
estimated_effort: M
last_updated: 2026-05-10
---

# Subsystem — π⁰ pairing

*Charter.* Owns leaves P.5 (pairing) and P.6 (accidental
rejection). Forms π⁰ candidates from photon objects.

## 1. Leaf P.5/P.6 input/output schema and pairing rule

Leaf P.5/P.6: photon objects → π⁰ candidates and accidental tags

- **Inputs (production, Class A only):** plan-33 photon objects with
  `event_id`, `object_id`, `ux/uy/uz`, `energy_mev` (or
  `total_energy` in the current table), `leadglass_edep`,
  `scintillator_edep`, `leadglass_fraction`, and P.2 neutral-pass
  status. Plan-35 fit quantities may be joined downstream, not used
  to form raw pairs.
- **Current implementation evidence:** the compact current source
  implements π⁰ pairing and the strict six-cut AND inside
  `find_pi0_candidates` (`photon.py:204-263`). The configured
  thresholds live in `ReconstructionConfig` (`reconstruction.py:14-41`).
  The current output emits only
  `passes_selection`, so the individual `passes_*` cut columns below
  are a required plan-34 remediation target rather than a current
  source guarantee.
- **Decision rule:** for each event, list photon objects from plan 33,
  form all pairs `(γ_i, γ_j)` with `i < j`, compute invariant mass
  `M`, total energy `E`, opening angle `α`, `Σ_scint`, `Σ_LG`, and
  `Σ_LG / (Σ_LG + Σ_scint)`, then evaluate the cut columns in §2.
- **Outputs:** one row per pair with photon ids, `mass`,
  `opening_angle_deg`, `total_energy`, `leadglass_edep`,
  `scintillator_edep`, `leadglass_fraction`, each `passes_*` cut
  column from §2, strict `passes_selection`, and
  `selection_failure_reasons`. Diagnostic-only provenance columns
  copied from plan 33 may be written for fake/root-cause studies.
- **Truth-use boundary:** truth parentage defines validation labels
  for accidental-rate measurement only; it must not remove or accept
  a production candidate.

### 1.1 Current-to-target photon energy input map

The current pair builder consumes each photon row's `total_energy` for
`M_γγ` and writes the pair-level `total_energy` column in
`find_pi0_candidates` (`photon.py:204-263`). The rebuild target may
receive plan-33 `energy_mev`, but ingestion must normalize exactly one
photon-energy field into the §1 pair calculation before any cuts run.
If both `energy_mev` and `total_energy` are present, the chosen source
and `energy_method` must be recorded; mixed production
`cluster_sum` and legacy-alias inputs fail schema validation instead
of being silently combined.

### 1.2 Machine-readable P.5/P.6 π⁰ fixture

The π⁰ fixture stores one row per photon pair and makes the raw pairing
and cut decision reproducible:

| Field | Required content | Review rule |
|---|---|---|
| `event_id`, `candidate_id` | stable candidate key | deterministic from ordered photon ids and method id |
| `photon1_id`, `photon2_id` | ordered plan-33 photon ids | no photon may pair with itself |
| `pairing_method_id` | `all_unordered_pairs` or approved replacement | replacement requires `DEC-34-PAIRING-RULE` |
| `mass`, `opening_angle_deg`, `total_energy` | raw pair kinematics | finite and recomputable from photon four-vectors |
| `leadglass_edep`, `scintillator_edep`, `leadglass_fraction` | energy components | additive with the selected photon-energy source |
| `energy_source_field` | `energy_mev` or legacy `total_energy` | mixed sources fail schema validation |
| `passes_*` cut columns | six booleans from §2 | must decompose the final strict AND |
| `passes_selection` | strict AND of the six booleans | no truth-parent override is allowed |
| `selection_failure_reasons` | ordered reason tokens from §2.1 | empty only when all cut columns pass |

Fixture review recomputes every cut boolean, final AND, and failure
reason list from the stored kinematics. Truth parent labels may be added
only to validation sidecars for accidental-rate studies.

### 1.3 Current-to-target π⁰ candidate key map

The current `find_pi0_candidates` rows (`photon.py:204-263`) are
identified by `event_id`, `photon1_id`, and `photon2_id`; they do not
emit a stable `candidate_id`. The rebuild bridge must derive
`candidate_id` from the ordered photon ids, `pairing_method_id`, and
cut-config id before plan 35 consumes the row. Row ordinal, truth
parentage, and generated π⁰ ids are diagnostic-only and cannot enter
that key.

## 2. Selection per candidate

Thesis Ch 8 defaults are held in the current `ReconstructionConfig`
range cited in §2.2; the compact current implementation evaluates the
strict six-cut AND in `find_pi0_candidates` (`photon.py:204-263`).

| Cut column | Default | Thesis source | Code citation |
|---|---|---|---|
| `passes_mass_window` | 100 ≤ M ≤ 180 MeV | thesis Ch 8 | config field verified in §2.2; current strict AND verified in `find_pi0_candidates` (`photon.py:204-263`) |
| `passes_total_energy` | E ≤ 720 MeV | thesis Ch 8 | config field verified in §2.2; current strict AND verified in `find_pi0_candidates` (`photon.py:204-263`) |
| `passes_scintillator_energy` | Σ_scint ≤ 250 MeV | thesis Ch 8 | config field verified in §2.2; current strict AND verified in `find_pi0_candidates` (`photon.py:204-263`) |
| `passes_leadglass_energy` | Σ_LG ≤ 980 MeV | thesis Ch 8 | config field verified in §2.2; current strict AND verified in `find_pi0_candidates` (`photon.py:204-263`) |
| `passes_leadglass_fraction` | LG_fraction ≥ 0.55 | thesis Ch 8 | config field verified in §2.2; current strict AND verified in `find_pi0_candidates` (`photon.py:204-263`) |
| `passes_opening_angle` | α ≥ 30° | thesis Ch 8 | config field verified in §2.2; current strict AND verified in `find_pi0_candidates` (`photon.py:204-263`) |

Strict `passes_selection` = AND of all six.

### 2.1 Per-cut failure-reason contract

The individual cut columns are auditable only if the final strict AND
can be decomposed without rerunning reconstruction. Each candidate row
therefore carries a deterministic `selection_failure_reasons` list
computed from the six booleans in §2:

| Failing column | Reason token |
|---|---|
| `passes_mass_window` | `mass_window` |
| `passes_total_energy` | `total_energy` |
| `passes_scintillator_energy` | `scintillator_energy` |
| `passes_leadglass_energy` | `leadglass_energy` |
| `passes_leadglass_fraction` | `leadglass_fraction` |
| `passes_opening_angle` | `opening_angle` |

If all six booleans are true, `selection_failure_reasons = []` and
`passes_selection = true`. If one or more booleans are false,
`passes_selection = false` and the list preserves the §2 table order.
No truth-label or parentage field may add or suppress a failure reason.

The current compact source does not yet emit per-cut failure reasons,
source-alias diagnostics, or prompt-timing π⁰ diagnostics. Those are
target outputs for this plan or downstream validation artifacts, and
must remain diagnostic-only per plan 01.

### 2.2 Machine-readable cut-config fixture

Each π⁰ candidate row references a cut-config record so Ch 8 baseline
thresholds are reproducible before retuning:

| Field | Required content | Review rule |
|---|---|---|
| `cut_config_id` | stable key for the six-cut tuple | referenced by every P.5/P.6 candidate row |
| `mass_window_mev` | `[100, 180]` for the Ch 8 baseline | changes require `DEC-34-RETUNED-PI0-CUTS` |
| `total_energy_max_mev` | 720 | copied from the reviewed baseline |
| `scintillator_energy_max_mev` | 250 | copied from the reviewed baseline |
| `leadglass_energy_max_mev` | 980 | copied from the reviewed baseline |
| `leadglass_fraction_min` | 0.55 | copied from the reviewed baseline |
| `opening_angle_min_deg` | 30 | copied from the reviewed baseline |
| `decision_dec_id` | `DEC-34-PI0-CUT-BASELINE` or retune DEC | draft DEC keeps row provisional |
| `config_status` | `baseline`, `candidate`, or `blocked` | only baseline/promoted rows may feed plan 35 |

Initial config row: `ch8_pi0_baseline_v0` uses the values above with
`config_status = baseline`.

Initial cut-config examples:

| `cut_config_id` | Cut tuple | Intended study | Decision status | Downstream rule |
|---|---|---|---|---|
| `ch8_pi0_baseline_v0` | six Ch 8 thresholds exactly as listed in §2 | thesis reproduction and plan-47 baseline | `baseline` under `DEC-34-PI0-CUT-BASELINE` | may feed plan 35/36 once per-cut columns are emitted |
| `mass_window_loose_diag_v0` | widen only the mass window while preserving all other Ch 8 thresholds | N-1 / sideband diagnostic for P.5 pairing | `candidate` under `DEC-34-RETUNED-PI0-CUTS` | cannot overwrite baseline `passes_*` columns |
| `prompt_timing_veto_diag_v0` | add timing-residual veto after the six Ch 8 cuts | accidental-rejection comparison using plan-36 timing sums | `candidate` pending timing calibration DEC | diagnostic until efficiency and fake-rate closure pass |
| `truth_parent_oracle_blocked` | reject pairs by generated π⁰ parentage | validation upper bound only | `blocked` by truth-use boundary | never feeds production pair, fit, or selection rows |

Candidate configs write new candidate columns or sidecar rows. They do
not change `ch8_pi0_baseline_v0` or its plan-47 reproduction counts.

### 2.3 A+ citation audit for current cut implementation

Current-source claims in §1-§2 were re-checked against the L3 worktree
before this plan was committed:

| Cited contract | Verifier evidence | Status |
|---|---|---|
| π⁰ threshold defaults | `class ReconstructionConfig` resolves at `reconstruction.py:14`, inside the cited `reconstruction.py:14-41` range. | keep citation |
| raw pair construction and strict six-cut AND | `def find_pi0_candidates` resolves at `photon.py:204`, inside the cited `photon.py:204-263` range. | keep citation |
| optional prompt-timing veto source | `def annotate_timing_windows` resolves at `vertex.py:86`, inside the cited `vertex.py:86-160` range. | keep citation |

Plan 34 does not specify a runtime CLI command, and it does not cite the
removed legacy split-study files. Any future CLI-facing π⁰ study row must
first pass the L3 `--help` verifier from the parallel-session protocol.

Closure on truth π⁰s is specified in §5; plan 35 separately
measures the post-fit mass resolution.

## 3. Accidental rejection (P.6)

Accidentals are pairs where the two photons came from different
parents in truth. Two ways to bound the accidental rate:

- *Truth-side* (validation only): pairs whose truth daughters do
  not share a π⁰ parent in the `Interaction` table → `@validation_only`
  metric.
- *Reco-side* (production): kinematic-fit χ² (plan 35); high χ²
  rejects accidentals.

Plan 47 ledger quotes both.

### 3.1 Machine-readable accidental-rate fixture

Accidental-rate studies write an aggregate validation row that is kept
separate from the production pair fixture:

| Field | Required content | Review rule |
|---|---|---|
| `accidental_metric_id` | stable key for the study row | referenced by plan-47 ledger entries |
| `pairing_method_id`, `cut_config_id` | plan-34 pairer and cut tuple | must match the production fixture under test |
| `dataset_id` | signal truth-π⁰ or no-π⁰ control sample | sample role must be declared |
| `truth_label_source` | evaluator-only parentage table or null for no-π⁰ controls | never copied into production pair rows |
| `n_raw_pairs`, `n_selected_pairs` | denominators after production cuts | recomputed without truth labels |
| `n_accidental_selected` | selected pairs failing the truth-parent match or selected in no-π⁰ sample | validation-only numerator |
| `accidental_rate` | numerator divided by selected-pair or event denominator | denominator convention must be named |
| `interval_method` | Wilson or plan-04 exact interval | finite interval required, including zero-count rows |
| `production_hash_without_truth` | hash of pair list and cut columns after truth drop | must match the original production hash |
| `metric_status` | `pass`, `fail`, or `diagnostic_only` | diagnostic rows cannot promote retuned cuts |

The row is rejected if truth parentage changes any production kinematic,
cut, or `passes_selection` output.

Initial accidental-rate examples:

| `accidental_metric_id` | `dataset_id` | Numerator definition | Denominator convention | Required guard |
|---|---|---|---|---|
| `sig_wrong_parent_selected_v0` | `sig_foil_v3:wrong_parent_pairs` | selected pairs whose photons fail the evaluator-only shared-parent test | `n_selected_pairs` after Ch 8 cuts | production hash unchanged after truth/provenance drop |
| `no_pi0_selected_rate_v0` | `cal_singlepion_mip_v1` | selected candidates in a no-π⁰ control sample | `n_events` and `n_raw_pairs` both reported | finite interval even if numerator is zero |
| `fit_ranked_accidental_diag_v0` | `sig_foil_v3` | wrong-parent selected pairs after plan-35 fit ranking | selected pairs before fit ranking | diagnostic until fit covariance DEC is signed |

These rows measure fake/accidental behavior only. They cannot reject
production pairs by truth ancestry, and they cannot promote retuned cuts
without the §5 closure rows and DEC evidence.

## 4. Alternative comparison matrix

| Leaf | Candidate | Decision rule | Current/source citation | Class-A status | Comparison metric |
|---|---|---|---|---|---|
| P.5 | **All unordered pairs (current)** | Pair every neutral photon pair once by object-id ordering. | Current implementation is `find_pi0_candidates` (`photon.py:204-263`). | Production-eligible; O(N²). | π⁰ efficiency, candidate multiplicity, runtime. |
| P.5 | **Best mass match per photon** | Build all pairs, then greedily keep pairs closest to `m_π⁰` without reusing photons. | Replacement after raw pair enumeration. | Eligible; mass threshold DEC required. | Correct-pair efficiency and high-multiplicity fake rate. |
| P.5 | **Kinematic-fit ranked pairing** | Rank raw pairs by plan-35 χ² and mass pull. | Consumes plan-35 fit outputs after raw pair construction. | Eligible once fit covariance is validated. | Mass resolution and accidental rejection at fixed efficiency. |
| P.6 | **Six-cut selection (current)** | Apply mass, total-energy, scintillator-energy, lead-glass-energy, LG-fraction, and opening-angle cuts. | Thresholds and strict AND are verified once in §2.2; current compact implementation is `find_pi0_candidates` (`photon.py:204-263`). | Production-eligible; thresholds must be thesis-cited or DEC-logged. | Signal efficiency, fake rate, N-1 sensitivity. |
| P.6 | **Prompt-timing veto** | Require photon time residuals near zero before accepting prompt π⁰s. | New veto would consume timing annotations from `annotate_timing_windows` (`vertex.py:86-160`) after photon construction. | Eligible after timing calibration and DEC. | Accidental-rate reduction vs efficiency loss. |
| P.6 | **Truth-parent label** | Reject pairs whose photons do not share a truth π⁰ parent. | Validation-only diagnostic inherited from source aliases. | Not production-eligible. | Upper-bound accidental rejection only. |

Plan 38 records P.5 pairing and P.6 accidental-rejection choices
separately so a better ranking can be adopted without changing the
thesis six-cut baseline.

## 5. Closure-test specification

1. **Dataset ids:** use `sig_foil_v3` truth π⁰ decays for signal
   closure and `cal_singlepion_mip_v1` as the no-π⁰ accidental
   sample; truth parentage labels are evaluator-only.
2. **Observable:** raw and selected `M_γγ`, opening angle, selected
   candidate multiplicity, per-cut pass fractions, correct-pair
   efficiency, and accidental-pair rate.
3. **Fitter / estimator:** fit the selected `M_γγ` peak with a
   Gaussian core plus sideband background; quote bootstrap uncertainty
   on the peak mean and width, and Wilson intervals for accidental
   rates.
4. **Pass criterion:** selected mass peak `|μ - 134.977 MeV| < 5 MeV`,
   raw selected width `< 35 MeV`, post-plan-35 width `< 25 MeV`, and
   no-π⁰ accidental selected-candidate rate documented with a finite
   confidence interval.
5. **Audit hook:** rerun after dropping photon truth/provenance
   columns. The raw pair list, kinematic quantities, cut booleans, and
   `passes_selection` must be unchanged.

### 5.1 Machine-readable π⁰ closure fixture

Each pairing/cut candidate writes one closure-result row per dataset and
selection configuration:

| Field | Required content | Review rule |
|---|---|---|
| `pairing_method_id`, `cut_config_id` | raw pairer and cut tuple under test | must match §1/§2 fixture fields |
| `dataset_id` | `sig_foil_v3` or `cal_singlepion_mip_v1` | signal and no-π⁰ accidental samples both required |
| `n_events`, `n_raw_pairs`, `n_selected_pairs` | denominators and selected counts | zero denominators fail closure |
| `mass_peak_mean_mev`, `mass_peak_width_mev` | selected mass fit outputs | compared to §5 pass criterion |
| `correct_pair_efficiency` | signal truth-label evaluator metric | validation-only, never a production input |
| `accidental_selected_rate` | no-π⁰ or wrong-parent selected rate | reported with finite interval |
| `per_cut_pass_fractions` | map for the six §2 cut columns | proves the strict AND decomposes correctly |
| `class_b_drop_hash` | rerun artifact without photon truth/provenance | pair list and cut hashes must match |
| `closure_status` | `pass`, `fail`, or `diagnostic_only` | only `pass` rows can support production cuts |

Rows whose truth labels affect the pair list, kinematics, or cut booleans
are invalid even if their evaluator-only efficiency numbers improve.

Required closure row-key inventory:

| `dataset_id` | Sample role | Required row purpose | Acceptance guard |
|---|---|---|---|
| `sig_foil_v3` | signal truth π⁰ decays | mass peak, correct-pair efficiency, and per-cut pass fractions | measured §5.1 metrics present; Class-B drop hash matches |
| `cal_singlepion_mip_v1` | no-π⁰ accidental control | selected accidental-pair rate and finite interval | accidental interval present even for zero selected pairs |
| `sig_foil_v3:wrong_parent_pairs` | signal-topology accidental sideband | wrong-parent selected-rate diagnostic | validation-only labels cannot affect production pair/cut outputs |

The inventory defines the minimum closure components. It does not freeze
any pairing or cut decision until measured §5.1 rows and the relevant
DEC evidence are attached.

Initial π⁰-closure failure examples:

| `closure_case_id` | Failing pattern | Required status | Review guard |
|---|---|---|---|
| `missing_no_pi0_control` | signal row exists but `cal_singlepion_mip_v1` accidental row is absent | `fail` | π⁰ efficiency without accidental rate cannot approve P.6 |
| `mass_peak_bias_fail` | selected `M_γγ` peak mean misses the §5 window | `fail` | retuned cuts cannot hide a biased photon/π⁰ reconstruction |
| `accidental_interval_missing` | zero selected accidental pairs reported without a finite interval | `fail` | zero-survivor convention mirrors plan-44/46 interval handling |
| `truth_parent_pair_drift` | dropping truth/provenance changes pair list or selected booleans | `fail` | evaluator labels may not influence pair construction |

### 5.2 Decision-log stubs for π⁰ pairing and cuts

P.5/P.6 choices change candidate multiplicity and the Ch 8 π⁰
baseline, so threshold or ranking changes require plan-05 approval:

| DEC stub | Decision to freeze | Required evidence before approval |
|---|---|---|
| `DEC-34-PAIRING-RULE` | Retain all unordered pairs or select a best-pair / fit-ranked pairing policy | §5 correct-pair efficiency, candidate multiplicity, and runtime comparison |
| `DEC-34-PI0-CUT-BASELINE` | Freeze the six thesis Ch 8 cuts and their default thresholds as reproduction columns | plan-47 reproduction row plus per-cut pass fractions from §5 |
| `DEC-34-RETUNED-PI0-CUTS` | Approve any mass, energy, fraction, opening-angle, or prompt-timing retune | N-1/ROC evidence and explicit preservation of the Ch 8 baseline columns |
| `DEC-34-ACCIDENTAL-LABELING` | Restrict truth-parent labels to validation-only accidental-rate estimates | plan-01 audit and rerun showing pair/cut outputs unchanged without truth columns |

Initial π⁰ approval examples:

| `approval_case_id` | Pair/cut pattern | Allowed use before DEC approval | Promotion guard |
|---|---|---|---|
| `all_pairs_ch8_baseline` | all unordered photon pairs plus the six Ch 8 cuts | reproduction baseline and plan-35 input | requires plan-47 pass fractions before final quote |
| `best_mass_pair_diag` | choose one candidate per event by closest raw π⁰ mass | diagnostic ladder row only | cannot replace P.5 without `DEC-34-PAIRING-RULE` correct-pair evidence |
| `prompt_timing_veto_diag` | add timing residual veto beside the six Ch 8 cuts | accidental-rate study only | needs timing calibration and `DEC-34-RETUNED-PI0-CUTS` approval |
| `truth_parent_label_audit` | attach generated-parent labels after pair decisions | validation-only accidental label | plan-01 rerun must show unchanged pair and cut outputs |

Until approval, alternative pair rankings and retuned cuts are plan-38
ladder rows only; `passes_selection` remains the Ch 8 reproduction
baseline.

### 5.3 Initial downstream-handoff examples

The first rebuild handoffs from plan 34 must make the boundary between
production π⁰ candidates, diagnostics, and validation labels explicit:

| `handoff_case_id` | Downstream consumer | Required payload | Required guard |
|---|---|---|---|
| `pi0_candidate_pass_to_p35` | plan 35 kinematic fit | ordered photon ids, candidate id, four-vector inputs, six cut booleans, and Ch 8 `passes_selection` | row is produced without truth-parent labels and references an approved cut-config id |
| `baseline_cut_columns_to_p37` | plan 37 event selection | per-candidate `passes_mass_window`, energy/fraction cuts, opening-angle cut, and final strict AND | selection may aggregate these columns but may not recompute a different π⁰ baseline |
| `prompt_timing_shadow` | plan 36 timing/event variables and plan 38 ladder | timing-veto score or residual sidecar keyed by candidate id | diagnostic-only until timing calibration and retuned-cut DEC approval exist |
| `truth_label_sideband_only` | plan 44/47 accidental-rate studies | evaluator-only shared-parent or wrong-parent label keyed by production candidate id | label must be droppable with unchanged pair list, kinematics, and cut booleans |

Any downstream table that cannot distinguish these four handoff modes is
blocked from promoting a π⁰-pairing change. The default production handoff
is `pi0_candidate_pass_to_p35`; the other rows are shadow or validation
surfaces until their DEC and closure evidence are attached.

## 6. Acceptance criteria

- §2 individual passes_* columns + `passes_selection`.
- §5 closure passes.
- §3 accidental rate produced for at least the licentiate signal
  sample.

## 7. Dependencies

- **24, 33, 38, 40** — inputs.
- *Consumed by:* plan 35 (kinematic fit), plan 36 (event variables),
  plan 37 (selection), plan 38 (ladder).

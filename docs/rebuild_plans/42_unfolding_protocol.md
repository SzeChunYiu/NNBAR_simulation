---
id: 42_unfolding_protocol
title: Unfolding protocol — particle-level vs detector-level
version: 0.1
status: draft
owner: Analysis WG
depends_on: [00_README, 04_statistical_uncertainty, 36_subsystem_event_variables, 38_truth_substitution_ladder]
outputs:
  - {path: docs/rebuild_plans/42_unfolding_protocol.md, schema: this file}
acceptance:
  - {test: response matrix produced for at least visible invariant mass and π⁰ mass, method: §2 deliverable, pass_when: matrices saved}
  - {test: regularisation choice (IBU vs SVD) named with per-observable iteration / reg parameter, method: §3 review, pass_when: signed in DEC}
  - {test: closure on truth-MC sample passes, method: §4 closure, pass_when: every §4.2 observable row passes its explicit pull/bias/yield tolerance}
risks:
  - {risk: model dependence — unfolded distribution depends on the prior, mitigation: §5 model-variation systematic}
estimated_effort: M
last_updated: 2026-05-10
---

# Unfolding protocol

*Charter.* When quoting a physics distribution (visible invariant
mass, π⁰ mass spectrum), the rebuild reports both detector-level
and particle-level — the latter via unfolding. This plan defines the
protocol; whether unfolded distributions are quoted in the thesis is
a separate user decision.

## 1. Why unfold

Detector-level distributions depend on the simulation; particle-level
distributions depend on physics. For thesis Ch 8/9 plots, the user
chooses which to quote based on whether the goal is to constrain
physics (particle-level) or to characterise the detector (detector-
level).

## 2. Response matrix

**Verified CLI surface (A+ gate, 2026-05-10).** The live L3
worktree exposes `summarize` and `response-matrix` under
`python -m nnbar_reconstruction.cli --help`. `summarize --help`
supports `--run`, `--json`, and `--tables-dir`;
`response-matrix --help` supports `--all-runs`, `--tables-dir`,
`--out-dir`, `--observables`, `--bootstrap`, `--min-truth-count`,
and `--json`. `summarize --help` also supports `--all-runs`,
`--table`, and `--bootstrap` for multi-run table production.
Later unfolding-tuning, closure, and systematic commands remain
L3-owned implementation gates until their `--help` surface exists.

For every observable that may be published at particle level, build an
explicit truth-to-reconstruction response matrix and save the exact
binning contract used by closure and unfolding. Truth inputs are Class B
and are allowed only inside this analysis/unfolding protocol, not inside
production reconstruction decisions.

### 2.1 Runnable procedure

1. Produce reconstruction tables with the verified plan 09 §14 schema
   command and multi-run event-id offsets:

   ```bash
   python -m nnbar_reconstruction.cli summarize \
       NNBAR_Detector/output/sig_foil_v3 --all-runs \
       --tables-dir output/reco/sig_foil_v3/ \
       --table output/reco/sig_foil_v3/runs.csv \
       --json output/reco/sig_foil_v3/summary.json
   ```

2. Assert `output/reco/sig_foil_v3/manifest.json` exists and records
   `event_id_offset = 1000000000`, source hashes, and the same run list
   used by the response-matrix command.
3. Build the response matrices with the verified response-matrix CLI:

   ```bash
   python -m nnbar_reconstruction.cli response-matrix \
       NNBAR_Detector/output/sig_foil_v3 --all-runs \
       --tables-dir output/reco/sig_foil_v3/ \
       --out-dir output/unfolding/response/sig_foil_v3/ \
       --observables visible_mass,pi0_mass,sphericity \
       --bootstrap 200 --min-truth-count 20 \
       --json output/unfolding/response/sig_foil_v3/summary.json
   ```

4. For each observable write `response_<observable>.parquet`,
   `response_<observable>_covariance.npz`, and
   `response_<observable>_metadata.json` containing truth/reco bin
   edges, normalisation convention, bootstrap seed, source file hashes,
   and the plan 38 leaf mapping.
5. Assert every truth-bin column is normalised to
   `sum_i R_ij = 1.0 ± 1e-12` after explicit inefficiency/overflow bins
   are included. Bins with fewer than 20 truth events are merged with a
   neighbour before matrix normalisation and the merge is recorded in
   metadata.

### 2.2 Observable binning and tolerances

| Observable | Truth/reco inputs from plan 09 | Matrix binning / tolerance | Ladder leaf | Subsystem / ledger hook |
|---|---|---|---|---|
| visible invariant mass | truth four-vectors from `Particle_output`; reco `events.csv` visible mass | 25 MeV bins over 0-2500 MeV plus under/overflow; response columns normalise to `1 ± 1e-12`. | E.7 | plan 36; plan 47 §1 mass rows |
| π0 mass | truth photons/π0 ancestry from `Interaction_output`; reco `pi0.csv` mass-window candidates | 5 MeV bins over 0-300 MeV plus no-candidate bin; bins with <20 truth entries are merged. | P.5-P.7 | plans 34-35; plan 47 §1 π0 rows |
| sphericity | truth-derived event variables; reco `events.csv` sphericity | 0.02 bins on [0, 1]; bootstrap covariance must be saved for every populated bin. | E.5 | plan 36; plan 41 ROC/N-1 hooks |

Initial coverage is limited to these three observables because they are
explicit in plan 38's observable budget and have reconstruction-side
tables in plan 09 §14. New particle-level observables require a new row
here before they can be unfolded or quoted in plan 47.

## 3. Regularisation

Regularisation is chosen per observable after the response matrix in §2
is frozen. The choice is a methodology decision: the selected method and
parameter are signed in plan 05 before any unfolded distribution is
quoted in plan 47.

### 3.1 Runnable procedure

1. **Blocked L3 implementation gate:** no verified unfolding-tuning
   CLI exists in the live L3 worktree. Before this section is runnable,
   L3 must expose a help-verified tuning command that scans the frozen
   response artifacts for `visible_mass`, `pi0_mass`, and `sphericity`
   with IBU iterations `{1,2,3,4,5,6,8}` and SVD ranks
   `{2,3,4,5,6,8}`, then writes to `output/unfolding/tuning/`.
2. Save one `tuning_<observable>.parquet` grid with method, parameter,
   bias, variance, bin-to-bin correlation, pull mean/width, and closure
   status. Also save diagnostic PNGs for L-curve / iteration curves.
3. Select the least-flexible parameter that passes the observable's
   tolerance in §3.2 and write `chosen_regularisation.yml` with the DEC
   id that approved the choice.
4. Assert unfolding cannot run in quote mode unless
   `chosen_regularisation.yml` exists, names exactly one method/parameter
   per observable, and the selected grid row has `closure_status=pass`.

### 3.2 Per-observable tuning gates

| Observable | Allowed scan | Selection tolerance | Rationale citation | Cross-reference |
|---|---|---|---|---|
| visible invariant mass | IBU `n_iter ∈ {1,2,3,4,5,6,8}`; SVD `k ∈ {2,3,4,5,6,8}` | choose the smallest parameter with pull mean `|mu| < 0.1`, width in `[0.8, 1.2]`, and median bin correlation `< 0.80`. | plan 40 §2 E.7 | E.7, plan 36, plan 47 §1 |
| π0 mass | IBU `n_iter ∈ {1,2,3,4,5,6}`; SVD `k ∈ {2,3,4,5,6}` | choose the smallest parameter with mass bias `< 1 MeV`, pull width in `[0.9, 1.2]`, and no empty signal-window bin after unfolding. | plan 40 §2 P.5 | P.5-P.7, plans 34-35, plan 47 §1 |
| sphericity | IBU `n_iter ∈ {1,2,3,4,5}`; SVD `k ∈ {2,3,4,5}` | choose the smallest parameter with pull mean `|mu| < 0.1`, width in `[0.9, 1.2]`, and monotonic cumulative distribution preserved. | plan 40 §2 default / plan 38 E.5 | E.5, plan 36, plan 41 |

The default preference is IBU when IBU and SVD both pass with compatible
closure because it exposes a single iteration count and maps directly to
the D'Agostini reference; SVD is selected when it gives the only passing
closure row or materially lower bin correlation under the same tolerance.

## 4. Closure

Closure is mandatory before any unfolded distribution is quoted. The
response matrix is trained on the nominal signal sample, then tested on
a statistically independent or reweighted truth distribution.

### 4.1 Runnable procedure

1. Prepare an alternate closure truth distribution using either a held-out
   run block from `sig_foil_v3` or a plan 13 §4 signal-model reweighting.
2. **Blocked L3 implementation gate:** no verified unfolding-closure
   CLI exists in the live L3 worktree. Before this section is runnable,
   L3 must expose a help-verified closure command that reads the frozen
   response directory, `chosen_regularisation.yml`, `events.csv`,
   `pi0.csv`, `Particle_output_*.parquet`, and
   `Interaction_output_*.parquet`; runs 200 bootstrap replicas; and
   writes to `output/unfolding/closure/sig_foil_v3/`.
3. For each observable write `closure_<observable>.json`,
   `closure_<observable>_pulls.parquet`, and a PNG with truth, folded,
   reconstructed, and unfolded spectra.
4. Assert the closure JSON contains: input hashes, chosen method and
   parameter, truth-bin counts, unfolded covariance, per-bin pulls,
   global pull mean/width, and a pass/fail field evaluated against
   §4.2.

### 4.2 Closure tolerances

| Observable | Closure target | Pass tolerance | Rationale citation | Cross-reference |
|---|---|---|---|---|
| visible invariant mass | unfolded closure spectrum vs truth four-vector mass | global pull mean `|mu| < 0.1`, width in `[0.8, 1.2]`, and no three adjacent bins with same-sign >2σ pulls. | plan 40 §2 E.7 | E.7, plan 36, plan 47 §1 |
| π0 mass | unfolded π0 mass vs truth π0 mass / PDG target | peak bias `< 1 MeV`, pull width in `[0.9, 1.2]`, and signal-window yield within Wilson 68%. | plan 40 §2 P.5; plan 04 §4 | P.5-P.7, plans 34-35 |
| sphericity | unfolded sphericity vs truth event-shape value | global pull mean `|mu| < 0.1`, width in `[0.9, 1.2]`, and cumulative distribution monotonicity preserved. | plan 40 §2 default | E.5, plan 36, plan 41 |

Failed closure blocks quote-mode output. The next action is the plan 40
§3 escalation path: check statistics, bias, systematics, then code bugs
before changing regularisation or binning.

## 5. Model dependence

A response matrix derived from one signal model can bias the unfolded
particle-level spectrum under another branching table. The signal-model
systematic is therefore evaluated by re-deriving the response for the
plan 13 §4 alternatives and propagating the difference into plan 45
nuisance N5.

### 5.1 Runnable procedure

1. For each registered plan 13 §4 variation
   (`branching_amsler1991`, `branching_friedman2007`,
   `eta_omega_enhanced`, `eta_omega_suppressed`), create event weights
   or alternate response inputs with the same plan 09 truth/reco columns
   used by §2.
2. **Blocked L3 implementation gate:** no verified signal-model
   unfolding-systematics CLI exists in the live L3 worktree. Before
   this section is runnable, L3 must expose a help-verified command
   that reads the nominal response, `chosen_regularisation.yml`, plan
   13 signal-model variations, truth parquet, `events.csv`, and
   `pi0.csv`, then writes to
   `output/unfolding/systematics/signal_model/`.
3. Save `signal_model_deltas.parquet`,
   `signal_model_covariance.npz`, and `nuisance_N5.yml` with one row
   per `(observable, bin, variation)`.
4. Assert the nominal and all variations use identical binning and the
   same regularisation choice. If any variation fails §4 closure, mark
   the observable non-quotable rather than dropping the variation.

### 5.2 Systematic tolerances and registry hooks

| Observable | Model-dependence artifact | Acceptance / tolerance | Rationale citation | Registry hook |
|---|---|---|---|---|
| visible invariant mass | per-bin unfolded delta for each plan 13 §4 variation | save full covariance; if any bin shift exceeds `2 × stat σ`, ledger row must quote N5 separately. | plan 45 N5; plan 04 §6 | plan 45 N5 `signal_model` nuisance row |
| π0 mass | peak μ/σ delta and per-bin mass-spectrum delta | peak shift > 1 MeV is a named systematic, not a closure retune. | plan 40 P.5; plan 45 N5 | plan 45 N5 `signal_model` nuisance row |
| sphericity | per-bin unfolded delta and cumulative-shape delta | cumulative-shape shift > bootstrap 68% interval is quoted as N5. | plan 04 §2; plan 45 N5 | plan 45 N5 `signal_model` nuisance row |

The systematic combination rule is the plan 13 §4 quadrature rule
unless plan 45's correlation matrix supersedes it. Plan 47 rows that
quote unfolded values must cite both the closure artifact (§4) and the
N5 systematic artifact from this section.

## 6. Software handoff and blocker contract

The verified software boundary currently stops after §2 response-matrix
production. The response command is real and help-verified; the
regularisation, closure, and signal-model systematic producers in
§§3-5 are deliberately specified as blocked implementation gates until
their own `--help` surfaces exist. Do not replace those gates with
hand-edited notebooks or invented command names.

L3/software handoff requirements:

1. The tuning producer reads frozen response matrices and metadata from
   §2, scans only the method/parameter grids in §3.2, and writes one
   grid table plus diagnostic plots per observable. It fails if any
   selected row lacks a passing closure status or a DEC id.
2. The closure producer reads the frozen response directory,
   `chosen_regularisation.yml`, reconstruction tables, and truth
   parquet inputs. It writes JSON, pulls parquet, covariance, and
   rendered comparison plots for every §4.2 observable and fails if any
   pass/fail field is missing.
3. The signal-model systematic producer reads the same frozen binning,
   chosen regularisation, and plan 13 variation definitions. It writes
   per-bin deltas, covariance, and the plan 45 N5 nuisance handoff
   without dropping a variation whose closure fails.
4. All post-response producers record source hashes, response-matrix
   hashes, bootstrap seed, observable list, ladder leaves, and plan 47
   ledger hooks. A plot without matching machine artifacts is not a
   quotable result.
5. New command lines may be added to this plan only after their CLI
   surfaces are verified under the A+ examiner gate. Until then, the
   blocked sections remain precise software requirements, not runnable
   instructions.

## 7. Acceptance criteria

- §2 response matrices produced for ≥ 3 observables.
- §3 method choice signed.
- §4 closure passes.
- §5 systematic is propagated into plan 45.
- §6 software handoff is complete: each blocked post-response producer
  has explicit inputs, outputs, failure assertions, provenance fields,
  and a no-invented-CLI rule.

## 8. Dependencies

- **04, 36, 38** — inputs.
- *Consumed by:* plan 47 (ledger), plan 50 (defence package), plan
  45 (systematics).

## 9. References

- D'Agostini, *NIM A* 362 (1995) 487 (IBU).
- Höcker & Kartvelishvili, *NIM A* 372 (1996) 469 (SVD).
- RooUnfold documentation.

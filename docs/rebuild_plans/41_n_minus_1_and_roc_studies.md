---
id: 41_n_minus_1_and_roc_studies
title: N-1 plots and ROC studies for selection optimisation
version: 0.1
status: draft
owner: Analysis WG
depends_on: [00_README, 04_statistical_uncertainty, 36_subsystem_event_variables, 37_subsystem_event_selection]
outputs:
  - {path: docs/rebuild_plans/41_n_minus_1_and_roc_studies.md, schema: this file}
  - {path: output/studies/n_minus_1/, schema: per-cut N-1 plots}
  - {path: output/studies/roc/, schema: per-variable ROC plots}
acceptance:
  - {test: N-1 plot produced for every cut in plan 37 §1, method: per-cut review, pass_when: full coverage}
  - {test: ROC produced for every continuous variable in plan 36 §2, method: per-variable review, pass_when: full coverage}
  - {test: optimal-cut suggestion produced with explicit objective, method: §3 deliverable, pass_when: signed in DEC}
risks:
  - {risk: optimisation overfits to the regenerated sample's statistical fluctuation, mitigation: §3 train/validation/test split per plan 04}
estimated_effort: M
last_updated: 2026-05-10
---

# N-1 plots and ROC studies for selection optimisation

*Charter.* For every selection cut and every continuous selection
variable, produce the standard discrimination diagnostics. These
feed plan 37 (selection) reproduction and any future cut-optimisation
proposal.

## 1. N-1 plots

**Verified CLI surface (A+ gate, 2026-05-10).** The live L3
worktree exposes `summarize`, `scan-pid`, `response-matrix`, and
`validate-reco` under `python -m nnbar_reconstruction.cli --help`;
`summarize --help` supports `--all-runs`, `--tables-dir`,
`--table`, `--bootstrap`, and `--json`.
It does not expose N-1, ROC, or cut-search commands yet, so those
steps below are L3/software implementation gates until their `--help`
surface exists.

For every cut C in plan 37 §1, produce one N-1 artifact set with all
other cuts applied and C removed from the AND. This is a closure
procedure, not an optimisation step.

### 1.1 Runnable procedure

1. Build reconstruction tables for each registered sample with the
   verified multi-run plan 09 §14 command:

   ```bash
   python -m nnbar_reconstruction.cli summarize \
       NNBAR_Detector/output/<dataset_id> --all-runs \
       --tables-dir output/reco/<dataset_id>/ \
       --table output/reco/<dataset_id>/runs.csv \
       --json output/reco/<dataset_id>/summary.json
   ```

   Required datasets are `sig_foil_v3` (plan 20),
   `cosmic_cry_essLund_overburdenA_v1` (plan 21), and the beam-neutron
   dataset selected by plan 22. Assert each output directory contains
   `events.csv` and `manifest.json`; the manifest must record the
   plan 09 §15 event-id offset and source hashes before any N-1 or ROC
   producer consumes the table.
2. **Blocked L3/software implementation gate:** no verified N-1 CLI
   exists in the live L3 worktree. Before this section is runnable, a
   help-verified producer must read signal/background `events.csv`,
   the plan 37 cut definitions, run 200 bootstrap replicas, and write
   to `output/studies/n_minus_1/`.
3. For each cut write `<cut>.png`, `<cut>.json`, and a manifest entry
   containing: dataset id, input table hash, applied companion cuts,
   bin edges, weighted counts, signal acceptance, background rejection,
   Wilson interval (plan 04 §4), and ladder leaf.
4. Assert the producer exits non-zero if any plan 37 §1 cut has no JSON
   and PNG artifact. The acceptance gate for this section is artifact
   coverage plus reproducible hashes, not visual inspection alone.

### 1.2 Per-cut fields, tolerances, and cross-references

| Cut | Event-table field(s) from plan 09 §14.6 | N-1 binning / tolerance | Ladder leaf | Ledger hook |
|---|---|---|---|---|
| `pass_scintillator_energy` | total scintillator energy and the boolean cut flag | 20 MeV bins over 0-2000 MeV; acceptance/rejection values must reproduce from JSON within the Wilson 68% interval. | S.1 / E.1-E.2 | LIC-CH10-CUTFLOW using plan 47 §1 schema |
| `pass_tpc_foil_track` | `n_tracks_used`, `n_tracks_skipped`, foil-track boolean | integer bins; zero/nonzero split must match the cut-flow count exactly. | S.1 / V.5 | LIC-CH10-CUTFLOW |
| `pass_pion_count` | charged, photon, and π0 multiplicities | integer bins; cumulative count changes must be ≤ 1 event under deterministic rerun. | S.2 / E.9 | LIC-CH10-CUTFLOW |
| `pass_invariant_mass` | visible invariant mass | 25 MeV bins from 0-2500 MeV; threshold acceptance must match JSON within Wilson 68%. | S.3 / E.7 | LIC-CH10-CUTFLOW |
| `pass_sphericity` | sphericity | 0.02-wide bins on [0, 1]; threshold acceptance must match JSON within Wilson 68%. | S.4 / E.5 | LIC-CH10-CUTFLOW |
| `pass_scintillator_balance` | upper and lower scintillator energies | two 20 MeV marginal histograms plus 2-D pass mask; row/column projections must match JSON within Wilson 68%. | S.5 / E.2 | LIC-CH10-CUTFLOW |

All plotted inputs are reconstruction/event-summary fields derived from
Class A columns in plan 09. Truth labels enter only through dataset-level
sample identity (signal vs named background) and never through per-event
selection decisions.

## 2. ROC curves

For every continuous variable V in plan 36 §2, produce per-background
ROC artifacts using the same frozen `events.csv` inputs as §1. ROC
curves are diagnostics; they do not change the cut tuple until §3 has
a DEC-signed objective.

### 2.1 Runnable procedure

1. Reuse the `output/reco/<dataset_id>/events.csv` tables generated
   by §1.1 and verify their hashes match the N-1 manifest before
   scanning thresholds.
2. **Blocked L3/software implementation gate:** no verified ROC-study
   CLI exists in the live L3 worktree. Before this section is runnable,
   a help-verified producer must read signal/background `events.csv`,
   the plan 36 variable definitions, run 200 bootstrap replicas, and
   write to `output/studies/roc/`.
3. For each `(variable, background)` pair write `<variable>__<background>.png`
   and `.json` with threshold grid, signal efficiency, background
   rejection, AUC, bootstrap 68% interval (plan 04 §2), and the
   licentiate threshold marker when plan 37 §1 defines one.
4. Assert every continuous plan 36 §2 variable has at least one ROC
   JSON per background and a manifest row linking it to plan 38's
   observable budget. Missing variables fail the study even when the
   plotted selection variables are complete.

### 2.2 Variable tolerances and cross-references

| Variable | Event-table field(s) | ROC threshold grid / tolerance | Ladder leaf | Subsystem / ledger hook |
|---|---|---|---|---|
| total calorimeter energy | scintillator plus lead-glass total energy | 20 MeV grid; AUC reproducibility within bootstrap 68% interval. | E.1 / S.1 | plans 36, 37; LIC-CH10-CUTFLOW |
| upper/lower scint energy | upper and lower scintillator energies | 20 MeV grid per hemisphere; reject if both hemisphere markers are not stored. | E.2 / S.5 | plans 36, 37; LIC-CH10-CUTFLOW |
| upper/lower lead-glass energy | upper and lower lead-glass energies | 20 MeV grid; AUC is diagnostic-only unless plan 37 adds a cut. | E.2 | plan 36; plan 47 §1 future row |
| longitudinal energy `EL` | longitudinal event energy | 25 MeV grid; AUC interval from plan 04 bootstrap. | E.3 | plan 36; plan 38 matrix |
| transverse energy `ET` | transverse event energy | 25 MeV grid; AUC interval from plan 04 bootstrap. | E.4 | plan 36; plan 38 matrix |
| sphericity | sphericity | 0.02 grid on [0, 1]; store plan 37 threshold 0.2 as marker. | E.5 / S.4 | plans 36, 37; LIC-CH10-CUTFLOW |
| Fox-Wolfram H0/H2 and thrust | event-shape moments and thrust | 0.02 dimensionless grid; diagnostic-only until plan 37 promotes a cut or MVA feature. | E.6 | plans 36, 57; plan 38 matrix |
| visible invariant mass | visible invariant mass | 25 MeV grid over 0-2500 MeV; store plan 37 threshold 500 MeV as marker. | E.7 / S.3 | plans 36, 37; LIC-CH10-CUTFLOW |
| in-time / out-of-time energy | timing-window energy split | 20 MeV grid; require separate ROC JSON for each timing side. | E.8 | plan 36; plan 38 matrix |

Integer multiplicities in E.9 are excluded from ROC §2 and are covered
by N-1/counting diagnostics in §1; if a future optimiser treats them
as ordered thresholds, that promotion belongs in §3 with an explicit
objective and DEC entry.

## 3. Optimal cut search

A cut tuple `(t_1, …, t_n)` is "optimal" only relative to a
DEC-signed objective. The search may propose new thresholds, but plan
37 remains the thesis baseline until the proposal passes the test split
and the plan 47 ledger row is updated.

### 3.1 Runnable procedure

1. Create deterministic event-level train/validation/test splits from
   the same `events.csv` inputs used by §1-§2. The split manifest must
   store dataset id, run id, event id, split label, input-table hash,
   and seed derived with plan 04 §2 conventions.
2. **Blocked L3/software implementation gate:** no verified cut-search
   CLI exists in the live L3 worktree. Before this section is runnable,
   a help-verified search command must read signal/background
   `events.csv`, the plan 37 baseline tuple, a DEC-approved objective,
   and `output/studies/cut_search/splits.json`, then write to
   `output/studies/cut_search/`.
3. Tune only on the validation split. Write
   `validation_grid.parquet`, `best_tuple.validation.json`, and
   `baseline.validation.json`.
4. Freeze exactly one tuple, then evaluate it once on the test split;
   write `best_tuple.test.json`, `baseline.test.json`, and
   `promotion_decision.json`. The test artifact records whether the
   candidate beats the licentiate baseline by the objective-specific
   tolerance in §3.2.
5. Assert promotion fails unless the output names the DEC entry, the
   unchanged plan 37 baseline tuple, the frozen candidate tuple, all
   S.1-S.6 ladder leaves touched, and the plan 47 ledger row to update.

### 3.2 Objective tolerances and promotion gates

| Objective | Test-set tolerance / promotion gate | Rationale citation | Cross-reference |
|---|---|---|---|
| Significance Z0 | candidate Z0 must exceed baseline by `max(1% relative, bootstrap 68% half-width)`; if background survivors are zero, quote Feldman-Cousins limit instead of `s/sqrt(b)`. | plan 04 §2 and §5 | S.1-S.6, plan 37, plan 47 §1 |
| Balanced F1 | candidate balanced F1 must exceed baseline by `max(0.01 absolute, bootstrap 68% half-width)`. | plan 04 §2 | S.2-S.6, plan 37, plan 47 §1 |
| Punzi figure | candidate Punzi score must exceed baseline by `max(1% relative, bootstrap 68% half-width)` for the DEC-specified target Z. | plan 04 §2 | S.1-S.6, plan 37, plan 46 |
| Fixed signal acceptance | signal acceptance must be within ±0.01 absolute of the DEC target, then background rejection must exceed baseline by its bootstrap 68% half-width. | plan 04 §2 / Wilson intervals in §4 | S.1-S.6, plan 37, plan 47 §1 |

Candidate objectives allowed for DEC approval are: Significance Z0
(`s / sqrt(b)` only when nonzero-background assumptions hold), balanced
F1, Punzi figure, and fixed-acceptance rejection. Any new objective is a
methodology change and must update plan 05 before a cut-search artifact
can be accepted.

## 4. Software handoff and blocker contract

The verified live CLI can build the frozen reconstruction inputs with
`summarize` and can compute the supporting cumulative cut-flow with
`cutflow` (`cli.py:254-263`). The cut-flow support surface is regression
covered by `test_cutflow_counts_are_cumulative_in_plan_37_order`
(`tests/test_selection.py:79-100`) and `test_cutflow_cli_reads_events_csv`
(`tests/test_selection.py:103-119`). It is not a full N-1, ROC, or
cut-search producer: those study producers required by §§1-3 still do
not exist as help-verified surfaces. Until those producers exist, this
plan is intentionally blocked at the software boundary rather than
substituting a hand-made plot.

L3/software handoff requirements:

1. The N-1 producer reads only frozen signal/background `events.csv`
   tables, plan 37 cut definitions, and a manifest of applied companion
   cuts. It writes one JSON plus one PNG per cut and fails if any plan
   37 cut has no artifact.
2. The ROC producer reads the same frozen `events.csv` hashes, plan 36
   variable definitions, and background sample identifiers. It writes
   one JSON plus one PNG per `(variable, background)` pair and fails if
   any continuous plan 36 variable is missing.
3. The cut-search producer reads the §3 split manifest, baseline cut
   tuple, DEC-approved objective, and the frozen ROC/N-1 inputs. It
   writes validation-grid, frozen-candidate, baseline, test, and
   promotion-decision artifacts without mutating plan 37.
4. All three producers record input hashes, bootstrap seed, ladder
   leaves, and plan 47 ledger hooks. A rendered PNG without the matching
   JSON and manifest entry is not accepted.
5. The producer `--help` surfaces must exist before any command line is
   added to this plan. This avoids inventing CLI names and keeps the A+
   examiner gate enforceable.

## 5. Acceptance criteria

- §1 N-1 plots complete for plan 37 cuts.
- §2 ROC curves complete for plan 36 continuous variables.
- §3 objective signed in DEC; optimal tuple reported on test set.
- §4 software handoff is complete: each blocked producer has explicit
  inputs, outputs, failure assertions, provenance fields, the existing
  cut-flow support surface is cited, and a no-invented-CLI rule is in
  force.

## 6. Risks and mitigations

- *Risk:* the licentiate cuts are already near-optimal; the
  optimisation reports a ≤ 1% gain that statistical fluctuation
  obscures.
  *Mitigation:* report bootstrap uncertainty (plan 04 §2) on the
  optimum so improvements within statistical noise are not promoted.

## 7. Dependencies

- **04** — uncertainty machinery.
- **36, 37** — variables and cuts.
- *Consumed by:* plan 37 (cut tuning), plan 47 (ledger), plan 50.

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
last_updated: 2026-05-09
---

# N-1 plots and ROC studies for selection optimisation

*Charter.* For every selection cut and every continuous selection
variable, produce the standard discrimination diagnostics. These
feed plan 37 (selection) reproduction and any future cut-optimisation
proposal.

## 1. N-1 plots

For every cut C in plan 37 §1, produce one N-1 artifact set with all
other cuts applied and C removed from the AND. This is a closure
procedure, not an optimisation step.

### 1.1 Runnable procedure

1. Build the reconstruction tables for each registered sample with the
   canonical event-ID offset (plan 09 §14.6):

   ```bash
   python -m nnbar_reconstruction.cli summarize \
       NNBAR_Detector/output/<dataset_id> --all-runs \
       --table output/reco/<dataset_id>/ --json output/reco/<dataset_id>/summary.json
   ```

   Required datasets are `sig_foil_v3` (plan 20),
   `cosmic_cry_essLund_overburdenA_v1` (plan 21), and the beam-neutron
   dataset selected by plan 22.
2. Run the N-1 producer over the `events.csv` tables only:

   ```bash
   python -m nnbar_reconstruction.cli n-minus-one \
       --signal output/reco/sig_foil_v3/events.csv \
       --background output/reco/cosmic_cry_essLund_overburdenA_v1/events.csv \
       --background output/reco/<beam_neutron_dataset>/events.csv \
       --cuts docs/rebuild_plans/37_subsystem_event_selection.md \
       --bootstrap 200 --out output/studies/n_minus_1/
   ```

3. For each cut write `<cut>.png`, `<cut>.json`, and a manifest entry
   containing: dataset id, input table hash, applied companion cuts,
   bin edges, weighted counts, signal acceptance, background rejection,
   Wilson interval (plan 04 §4), and ladder leaf.
4. Assert the command exits non-zero if any plan 37 §1 cut has no JSON
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

For every continuous variable V in plan 36 §2:

1. Vary V's threshold across its support.
2. Plot signal acceptance vs background rejection (per background
   sample).
3. Compute the AUC.
4. Mark the licentiate cut value on the curve.

ROC curves reveal whether the licentiate's hand-tuned cut sits at the
ROC's knee or could be relaxed/tightened.

## 3. Optimal cut search

A cut tuple `(t_1, …, t_n)` is "optimal" only relative to an
objective. Plan 41 names the objective in a DEC entry:

| Candidate objective | Definition |
|---|---|
| **Significance Z₀** | `s / √b` over the signal box |
| **F1** | balanced precision/recall |
| **Punzi figure** | `s / (a/2 + √b)` for a target Z = a |
| **Fixed acceptance** | maximise rejection at fixed signal acceptance |

Search uses train/validation/test split (plan 04 §2): tune on
validation, freeze, evaluate on test. Reporting the test-set value
is the only valid quote.

## 4. Acceptance criteria

- §1 N-1 plots complete for plan 37 cuts.
- §2 ROC curves complete for plan 36 continuous variables.
- §3 objective signed in DEC; optimal tuple reported on test set.

## 5. Risks and mitigations

- *Risk:* the licentiate cuts are already near-optimal; the
  optimisation reports a ≤ 1% gain that statistical fluctuation
  obscures.
  *Mitigation:* report bootstrap uncertainty (plan 04 §2) on the
  optimum so improvements within statistical noise are not promoted.

## 6. Dependencies

- **04** — uncertainty machinery.
- **36, 37** — variables and cuts.
- *Consumed by:* plan 37 (cut tuning), plan 47 (ledger), plan 50.

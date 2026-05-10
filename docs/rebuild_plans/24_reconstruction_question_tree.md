---
id: 24_reconstruction_question_tree
title: Reconstruction fundamental question tree
version: 0.1
status: draft
owner: Methodology Council
depends_on: [00_README, 01_realism_contract, 07_simulation_atomic_walkthrough, 08_reconstruction_atomic_walkthrough, 09_io_schema_data_dictionary]
inputs:
  - {path: docs/detector_fundamental_question_tree.md, schema: detector-side companion}
  - {path: /Volumes/MyDrive/nnbar/nnbar/NNBAR_Detector-L3/docs/reconstruction.md, schema: implementation reference}
outputs:
  - {path: docs/rebuild_plans/24_reconstruction_question_tree.md, schema: this file}
acceptance:
  - {test: every leaf has the answer-now / deeper-question / next-measurement triplet, method: tree review, pass_when: all leaves complete}
  - {test: every leaf names its inputs (Class A columns), decision rule, allowed truth use, outputs, downstream consumers, method: per-leaf review, pass_when: full coverage}
  - {test: every subsystem plan 25-37 cites the leaf identities defined here, method: cross-reference, pass_when: zero unmatched}
risks:
  - {risk: leaves get renamed during subsystem-plan writing → cascading rework, mitigation: this plan is signed before 25-37 start (00_README §2)}
  - {risk: tree completeness can never be proven, only refuted, mitigation: §11 reviewer challenge inviting new branches}
estimated_effort: L
last_updated: 2026-05-10
---

# Reconstruction fundamental question tree

*Charter.* Mirror `docs/detector_fundamental_question_tree.md` for
the reconstruction side. Decompose the reconstruction recursively
from the root question down to irreducible decisions ("leaves"). Every
subsystem plan 25–37 takes its scope from the leaves named here.

The tree is *prescriptive* about decomposition and *descriptive* about
the current code. Improvements live in the subsystem plans, scored
against the truth-substitution ladder (plan 38).

This plan also establishes the convention that no leaf may consume a
Class B (truth) column in its decision path (plan 01). Migration of
the existing Class B reads (plan 08 §3.7) is tracked as a per-leaf
exit criterion.

## 1. Root question

**Can this reconstruction prove an antineutron annihilation candidate
from detector observables alone, without using simulation truth?**

Answer now: not yet. The current code reads truth in several decision
paths (plan 08 §3.7). The licentiate-grade selection achieves about
70% signal acceptance with finite-sample zero cosmic survival, but
this rests on truth-aware reconstruction in places. Plan 47 ledger
must reproduce the licentiate first (with truth allowed where the
licentiate allowed it) and then re-quote with the truth-leakage
audit (plan 01) green.

Deeper question: which observables are essential rather than
convenient? Tree branches §2–§7 enumerate them.

## 2-6. Branch files

Detailed per-leaf branches are split out to keep plan 24 under the
500-line cap. The split files inherit the truth-leakage gate in §7,
the visual summary in §8, and the acceptance/dependency sections below.

| Branch | Leaves | Split file |
|---|---|---|
| §2 Vertex | V.1-V.5 | `docs/rebuild_plans/24_reconstruction_question_tree/24_2_vertex.md` |
| §3 Charged objects | C.1-C.6 | `docs/rebuild_plans/24_reconstruction_question_tree/24_3_charged.md` |
| §4 Photon / π⁰ | P.1-P.7 | `docs/rebuild_plans/24_reconstruction_question_tree/24_4_photon_pi0.md` |
| §5 Event variables | E.1-E.9 | `docs/rebuild_plans/24_reconstruction_question_tree/24_5_event_variables.md` |
| §6 Selection | S.1-S.6 | `docs/rebuild_plans/24_reconstruction_question_tree/24_6_selection.md` |

## 7. Truth-leakage gate (recursive predicate)

At every leaf in §2–§6, the audit asks:

> *Does this decision depend on a Class B column?*

The acceptable answers are:

- *No.* Production-ready leaf.
- *Yes, only inside a `@validation_only` decorated function.*
  Acceptable for scoring, never for selection.
- *Yes, but only as a sparse-table fallback when Class A inputs
  are unavailable.* Acceptable temporarily; tracked as a migration
  item.
- *Yes, in a production decision path.* **Audit failure.** The leaf
  is not signed off until it migrates.

Plan 01 §4 implements the audit. Plan 08 §3.7 lists the current
violations. Each violation has an exit criterion in the owning
subsystem plan.

## 8. Visualisation

```
Root: Can reconstruction prove n̄ annihilation from observables alone?
  ├── §2 Vertex                 (V.1 hits→tracks → plan 25,
  │                              V.2 direction → plan 26,
  │                              V.3 projection, V.4 aggregation,
  │                              V.5 acceptance → plan 30)
  ├── §3 Charged objects        (C.1 cand, C.2 dE/dx, C.3 range,
  │                              C.4 scint match, C.5 π/p decision,
  │                              C.6 rejection)               → plans 25, 27, 28, 29
  ├── §4 Photon / π⁰            (P.1 cluster, P.2 ch/n test,
  │                              P.3 direction, P.4 energy,
  │                              P.5 pairing, P.6 accidental,
  │                              P.7 kinematic fit)           → plans 31, 32, 33, 34, 35
  ├── §5 Event variables        (E.1-E.9)                     → plan 36
  ├── §6 Selection              (S.1-S.6)                     → plan 37
  └── §7 Truth-leakage gate     (recursive at every leaf)     → plan 01 audit
```

(Per 00_README §4.7 numbering: plan 31 is cluster, 32 shower shape,
33 photon object, 34 π⁰ pairing, 35 kinematic fit, 36 event
variables, 37 event selection.)

## 9. Downstream handoff coverage

The tree is not ready for plan 47 use merely because each leaf is
named. Each leaf family also needs a downstream handoff that says who
produces the observable, who consumes it, and which validation gate
keeps the truth-leakage predicate in §7 enforceable.

Current closure map:

- **Implementation handoffs:** plans 25–30 cover the vertex and
  charged-object leaves already active in the L3 source migration.
- **Study and response handoffs:** plans 41–43 cover the study,
  response-matrix, and efficiency outputs that consume reconstructed
  leaves downstream.
- **Operations handoffs:** plans 60 and 66 cover fiducial-volume and
  data-quality decisions that can veto or stratify reconstructed
  samples.

Stage E.1 leaf-to-artifact handoff map:

| Leaf family | Producer plan | Required frozen artifact | Validation / consumer gate |
|---|---|---|---|
| V.1 / C.1 candidate seeds | plan 25 | V.1 candidate table plus hit-membership sidecar and `plan25_v1_candidates@stage-e1` manifest | plan 26 may consume only rows with `truth_grouping_used=false`; plan 66 consumes candidate quality fractions |
| V.2 track fits | plan 26 | V.2 fit table, residual sidecar, and `plan26_v2_fits@stage-e1` manifest | plans 27, 28, 30, and 40 consume the same `fit_id` and covariance convention |
| C.2 dE/dx | plan 27 | C.2 estimator table, contribution sidecar, and `plan27_c2_dedx@stage-e1` manifest | plan 29 joins by estimator id after truncation and calibration provenance are frozen |
| C.3 range / C.4 association | plan 28 | C.3 range table, associated-hit sidecar, and `plan28_c3_range@stage-e1` manifest | plans 29, 45, 60, and 66 consume explicit association and edge-state provenance |
| C.5 / C.6 charged PID and rejection | plan 29 | charged-PID decision table, rejection table, and `plan29_c5_c6_pid@stage-e1` manifest | plans 38 and 47 consume rule-versioned outputs only after calibration artifacts are frozen |
| V.3 / V.4 / V.5 vertex chain | plan 30 | projection, vertex, foil-acceptance tables, and `plan30_vertex_chain@stage-e1` manifest | plans 43, 47, 60, and 66 consume geometry-versioned vertex/foil rows |

Each artifact row above is an observable-only production boundary.
Truth labels can join only in downstream validation, unfolding, or
ledger artifacts after the production table and manifest hashes are
frozen.

### 9.1 Reviewer verification checklist

Before a plan-47 ledger row consumes any L0 reconstruction leaf, the
reviewer runs these checks against the current worktrees:

1. `grep -rE 'reconstruction\.py:[0-9]' docs/rebuild_plans/{24,25,26,27,28,29,30}*`
   returns no stale monolithic citations.
2. Every Python citation in L0 plans resolves to an existing
   `nnbar_reconstruction/` or `tests/` file, with a `def` or `class`
   inside the cited range.
3. The live CLI help surfaces used by L0 plans exist for
   `summarize`, `response-matrix`, `cutflow`, `validate-reco`, `dqm`,
   and `scan-pid`; missing help output blocks adding a runnable command
   to any plan.
4. Plans 25-30 each contain a Stage E.1 verification command and
   artifact manifest schema; plans 41-43, 60, and 66 each contain a
   software-handoff manifest schema for their downstream study or
   operations artifacts.
5. All L0 writable files remain below the 500-line cap and have no
   unresolved work-marker text or fill-in instructions.

The citation-range check in item 2 is machine-auditable with this
inline command from the simulation worktree while the repo-level helper
is not present:

```bash
python - <<'PY'
import pathlib, re, sys
plan_nums = {24, 25, 26, 27, 28, 29, 30, 41, 42, 43, 60, 66}
base = pathlib.Path("docs/rebuild_plans")
files = [p for p in base.glob("*.md") if p.name[:2].isdigit() and int(p.name[:2]) in plan_nums]
files += sorted((base / "24_reconstruction_question_tree").glob("*.md"))
root = pathlib.Path("/Volumes/MyDrive/nnbar/nnbar/NNBAR_Detector-L3")
pat = re.compile(r"`((?:/Volumes/MyDrive/nnbar/nnbar/NNBAR_Detector-L3/)?(?:nnbar_reconstruction|tests)/[^`:]+):(\d+)(?:-(\d+))?`")
issues = []
for f in files:
    for m in pat.finditer(f.read_text()):
        raw = m.group(1)
        path = pathlib.Path(raw) if raw.startswith("/") else root / raw
        start, end = int(m.group(2)), int(m.group(3) or m.group(2))
        lines = path.read_text().splitlines() if path.exists() else []
        if not lines or not (1 <= start <= end <= len(lines)):
            issues.append((str(f), raw, start, end))
        elif path.suffix == ".py" and not any(re.match(r"\s*(def|class)\s+", line) for line in lines[start-1:end]):
            issues.append((str(f), raw, "no def/class in range"))
sys.exit(1 if issues else 0)
PY
```

The CLI check in item 3 is equally mechanical from the L3 worktree:

```bash
cd /Volumes/MyDrive/nnbar/nnbar/NNBAR_Detector-L3
for cmd in summarize response-matrix cutflow validate-reco dqm scan-pid; do
  python -m nnbar_reconstruction.cli "$cmd" --help >/tmp/nnbar_cli_${cmd//-/_}.help
done
python -m nnbar_reconstruction.cli --help >/tmp/nnbar_cli_root.help
```

The Stage E.1 and software-handoff coverage in item 4 is checked with:

```bash
for p in 25 26 27 28 29 30; do
  f=$(ls docs/rebuild_plans/${p}_*.md)
  grep -q 'Stage E.1 verification command' "$f" || exit 1
  grep -q 'artifact manifest schema' "$f" || exit 1
done
grep -q 'plan41_selection_studies@stage-e1' docs/rebuild_plans/41_n_minus_1_and_roc_studies.md || exit 1
grep -q 'plan42_unfolding@stage-e1' docs/rebuild_plans/42_unfolding_protocol.md || exit 1
grep -q 'plan43_signal_efficiency@stage-e1' docs/rebuild_plans/43_signal_efficiency.md || exit 1
grep -q 'plan60_fiducial_edges@stage-e1' docs/rebuild_plans/60_fiducial_volume_and_edge_effects.md || exit 1
grep -q '66_data_quality_monitoring@stage-e1' docs/rebuild_plans/66_data_quality_monitoring.md || exit 1
```

The current L3 regression slice for the L0-owned reconstruction,
study, fiducial, and DQM handoffs is:

```bash
cd /Volumes/MyDrive/nnbar/nnbar/NNBAR_Detector-L3
pytest -q \
  tests/test_charged_reco.py::test_track_candidates_ignore_forbidden_truth_columns \
  tests/test_charged_reco.py::test_fit_track_candidates_emits_plan_26_direction_schema \
  tests/test_charged_reco.py::test_reconstruct_dedx_table_uses_candidate_hit_membership \
  tests/test_charged_reco.py::test_reconstruct_range_table_projects_scintillator_hits \
  tests/test_charged_reco.py::test_classify_charged_candidates_uses_dedx_and_range_thresholds \
  tests/test_vertex_reco.py::test_project_tracks_to_foil_emits_plan_30_v3_rows \
  tests/test_vertex_reco.py::test_aggregate_and_accept_vertices_use_plan_16_geometry_only \
  tests/test_selection.py::test_cutflow_cli_reads_events_csv \
  tests/test_cli_response_matrix.py::test_response_matrix_help_lists_plan_42_flags \
  tests/test_statistics.py::test_jackknife_efficiency_uses_plan_04_block_size \
  tests/test_dqm.py::test_dqm_cli_writes_run_table_and_manifest
```

The file-existence and 500-line checks in items 4-5 are run with:

```bash
for f in docs/rebuild_plans/{24,25,26,27,28,29,30,41,42,43,60,66}*.md \
         docs/rebuild_plans/24_reconstruction_question_tree/*.md; do
  test -f "$f" || exit 1
  lines=$(wc -l < "$f")
  test "$lines" -le 500 || { echo "$f has $lines lines"; exit 1; }
done
marker_re='TO''DO|FIX''ME|TB''D|stu''b|place''holder|to be fi''lled|open ques''tion|\?\?\?'
grep -nEi "$marker_re" \
  docs/rebuild_plans/{24,25,26,27,28,29,30,41,42,43,60,66}*.md \
  docs/rebuild_plans/24_reconstruction_question_tree/*.md && exit 1 || true
```

Acceptance rule: before any plan-47 ledger row cites a plan-24 leaf,
that leaf's family must have either an implementation handoff
subsystem plan or a software handoff study/operations plan, and the
handoff must name the validation artifact that proves the leaf stayed
observable-only.

## 10. Acceptance criteria

- §2–§7 are populated with the leaf identities listed.
- Subsystem plans 25–37 cite the leaf identities (V.1, C.2, P.5,
  …) verbatim and their per-leaf input/output/decision schemas
  populate the templates here.
- §9 has a downstream handoff entry for every leaf family that plan
  47 is allowed to consume.
- Plan 38 truth-substitution ladder uses the leaf identities as
  rungs.
- Plan 47 reproduction ledger cites leaf identities in its method
  column.

## 11. Reviewer challenge

This tree is signed off only after a reviewer has tried to find a
reconstruction decision that does not fit any leaf above. New leaves
identified by review become signed §2–§6 revision additions.

## 12. Risks and mitigations

- *Risk:* leaf renames after subsystem plans land cascade rework.
  *Mitigation:* this plan is signed before 25–37 start; renames
  require a paired DEC entry and revisions to all citing plans.
- *Risk:* tree drifts from code as reconstruction.py evolves.
  *Mitigation:* plan 53 CI rule: edits to public reconstruction
  functions trigger a check that this tree is updated.
- *Risk:* truth-leakage audit becomes too strict and breaks legacy
  studies.
  *Mitigation:* §7 acceptable-answers ladder; sparse-table
  fallbacks remain allowed during migration.

## 13. Dependencies

- **00_README** — plan space.
- **01_realism_contract** — Class A/B/C scheme; §7 audit gate.
- **07, 08** — simulation/reconstruction baselines.
- **09** — column classifications used in per-leaf input lists.
- *Consumed by:* plans 25–37, 38 (rungs), 47 (ledger method),
  50 (defence package).

## 14. References

- `docs/detector_fundamental_question_tree.md` — direct template.
- `/Volumes/MyDrive/nnbar/nnbar/NNBAR_Detector-L3/docs/reconstruction.md`
  — implementation reference this tree decomposes.

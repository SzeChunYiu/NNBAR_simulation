# DEC backlog — sign-off document

This file lists every `DEC-2026-MM-DD-N stub` currently scattered
across `docs/rebuild_plans/`. Each stub is a methodology decision the
plan body has drafted but the formal `docs/governance/DECISION_LOG.md`
has not yet promoted.

The user reviews this file in **one sitting**. For each stub: approve
the draft answer (→ promote to `DECISION_LOG.md`), amend the answer,
defer with a named owner + due date, or escalate to collaborators.

After review, the relevant plan body cross-references the promoted
`DEC-YYYY-MM-DD-N` ID and the stub paragraph is deleted (the
plan-body decision is now load-bearing on a real decision-log entry,
not a self-reference).

Last refreshed: 2026-05-10.

---

## 1. Already promoted (this round)

| ID | Topic | Plan | Promoted in `DECISION_LOG.md` |
|---|---|---|---|
| DEC-2026-05-10-1 | CRY site/date freeze | 14 §1.1 | ✅ |
| DEC-2026-05-10-3 | FTFP_BERT `_HP` split policy | 12 §2 | ✅ |
| DEC-2026-05-10-5 | TPC W-value production constant | 17 §2 | ✅ |

These three were drafted with concrete decisions in their plan bodies
and the user's stated rules (reproduction baseline preserved,
two-build-tag policy, identity-default for production constants)
imply approval. Promoted to `DECISION_LOG.md` as worked examples
satisfying plan 05 §9 acceptance criterion.

---

## 2. Pending — needs user input or external data

### DEC-2026-05-10-2 stub — beam-neutron source path
**Plan.** 14 §2.1, 22.
**Decision required.** Choose between:
- **(a) MCPL from ESS HIBEAM beam-line simulation** — preferred when
  the ESS team delivers a provenance-sealed file. Preserves
  beam-line correlations (optics, choppers, shielding).
- **(b) Parameterised flux + spectrum** — fallback. Uses HIBEAM
  technical-design spectrum + GPS commands. Reproducible without
  external file but model-limited; correlations become plan-45
  systematics.
- **(c) Dual-run comparison** — run both, quote MCPL as nominal,
  parameterised as systematic.

**Current state.** Plan 22 has parameterised fallback wired up; plan
14 §2 cannot freeze `beam_neutron_hibeam_*_v1` manifests until
this decision lands.

**Draft recommendation.** Adopt **(a)** as soon as ESS team delivers
the MCPL file (status per plan 22: "not yet available"). Until then
use **(b)** as a model-limited fallback and tag every produced row
`beam_neutron_model_only=true`. Promote to a real DEC once the file
arrives.

**Action.** ☐ Approve (a)+(b) sequencing. ☐ Set ESS-team contact and
follow-up date. Owner candidate: beam-line POG lead.

---

### DEC-2026-05-10-4 stub — alignment scenario sigma grid
**Plan.** 16 §2.
**Decision required.** Lock concrete σ values for `nominal_survey`
and `worst_case_construction` alignment scenarios. Currently set to
engineering-prior placeholders (e.g. 5 mm translation σ on shared
shielding, 2 mrad rotation σ).

**Current state.** Plan 16 specifies the scenario grid; plan 30
(vertex), plan 25 (TPC tracks), and plan 45 (alignment systematic)
all consume it. No ESS/HIBEAM survey constants available yet.

**Draft recommendation.** **Defer** to post-survey. In the interim
keep the placeholder values, mark every alignment-systematic row in
plan 45 as "uses placeholder σ — promote with survey data before
quoting in thesis result." Set a follow-up trigger: when the ESS
detector survey is delivered, promote a real DEC entry replacing the
placeholders.

**Action.** ☐ Approve placeholder-with-trigger approach. ☐ Name a
survey contact at ESS. Owner candidate: detector-mechanics POG.

---

### DEC-2026-05-10-6 stub — scintillator yield mode policy
**Plan.** 18 §3.
**Decision required.** The scintillator photon-equivalent count uses
**11136 photons/MeV** in the SD (`reconstruction.md` line 105),
while the optical-mode material-properties table uses
**10000 photons/MeV**. Decide which is canonical and how to compare.

**Current state.** Plan 18 §3 has the procedure: keep 11136 for
fast-mode (existing reconstruction code consumes it) and 10000 for
optical-on samples; apply a `1.1136` scale when comparing optical-on
to fast-mode. Plan 47 ledger rows would need to record the mode tag.

**Draft recommendation.** **Approve** plan 18's policy as-is.
Reasoning: existing reconstruction code is calibrated against 11136;
optical-on samples are model-experimental and should be tagged
separately. Promote to formal DEC after the first paired optical
on/off closure run lands.

**Action.** ☐ Approve plan 18 §3 policy verbatim. ☐ Name first
paired-closure-run owner.

---

## 3. Imported HIBEAM mirror entries — confirm cross-repo policy

These are cross-repository mirrors per plan 05 §6. They reference
HIBEAM-side decisions made in the HIBEAM TPC vertex-reconstruction
repository.

### DEC-2026-04-24-1 (HIBEAM mirror) — vertex truth source = converted CSV
**Plan referenced.** 03 §intro, 05 §6, 09 §schema, 13, 38.
**Status.** Already adopted in plan bodies as the truth-vertex source.
**Decision required.** Confirm cross-repo mirror policy: do we want a
live-mirror pointer (today's behaviour) or a frozen-snapshot copy?

**Draft recommendation.** Approve **live-mirror pointer** — our
DECISION_LOG entry will be a short body that cites the HIBEAM
original; updates upstream propagate via the monthly methodology
council review per plan 05 §6.

**Action.** ☐ Approve live-mirror policy. ☐ Confirm monthly council
cadence is realistic.

---

### DEC-2026-05-08-1 (HIBEAM mirror) — MVA inference-vs-training feature schema
**Plan referenced.** 00 §4.12, 57 §1, §3, §6.
**Status.** Cited by plan 57 as a load-bearing decision.
**Decision required.** Same as above — confirm live-mirror policy.

**Draft recommendation.** Same — live-mirror.

---

## 4. New stub introduced by L3 lane (post-A+ remediation)

### DEC-2026-05-10-L3-reco-split — `reconstruction.py` 500-line refactor split
**Plan referenced.** `docs/rebuild_plans/refactor/reconstruction_py_split.md`.
**Decision required.** Confirm the per-target-module split:
- `charged.py` — `reconstruct_charged_objects` + helpers
- `photon.py` — `reconstruct_photon_objects` + clustering
- `vertex.py` — `reconstruct_event_vertices` + `_track_anchor_*`
- `electron.py` — `reconstruct_electron_pair_objects`
- `reconstruction.py` — re-export shim only (≤ 200 lines)

**Current state.** L3 lane has Wave 2.5 task to land this split.
Refactor plan exists at `docs/rebuild_plans/refactor/reconstruction_py_split.md`.

**Draft recommendation.** **Approve** the four-way split with shim.
Promote to formal DEC when L3 commit lands; the merge commit body
cites the DEC ID.

**Action.** ☐ Approve split layout. ☐ Approve shim retention period
(suggest: 2 weeks then remove).

---

## 5. Sign-off summary

When you finish reviewing, complete:

```
Reviewed by: __________ on __________
Promoted: [DEC-2026-05-10-1, -3, -5]   ← already done
Newly promoted: [_____________________]
Deferred with trigger: [_______________]
Escalated to collaborators: [__________]
```

After sign-off: `git -C /Volumes/MyDrive/nnbar/nnbar/simulation`
commits this updated `DEC_BACKLOG.md` plus any newly promoted
entries appended to `DECISION_LOG.md`. Lanes pick up the changes
on next iteration via the on-complete=redo respawn policy.

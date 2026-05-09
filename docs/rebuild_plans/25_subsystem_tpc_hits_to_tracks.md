---
id: 25_subsystem_tpc_hits_to_tracks
title: Subsystem — TPC hits to track candidates (leaf V.1)
version: 0.1
status: draft
owner: Tracking POG
depends_on: [00_README, 01_realism_contract, 08_reconstruction_atomic_walkthrough, 09_io_schema_data_dictionary, 24_reconstruction_question_tree]
inputs:
  - {path: data/registry/sig_foil_v3, schema: signal sample}
  - {path: data/registry/cal_singlepion*, schema: charged calibration}
outputs:
  - {path: docs/rebuild_plans/25_subsystem_tpc_hits_to_tracks.md, schema: this file}
acceptance:
  - {test: leaf V.1 has Class A inputs only, method: realism audit, pass_when: zero Class B reads in the V.1 production path}
  - {test: track-finding efficiency on cal_singlepion_v1 ≥ 90% within fiducial, method: per-sample efficiency, pass_when: target met or limitation documented}
  - {test: alternative track-finder benchmarked on the ladder (Hough vs Kalman vs current), method: plan 38 IV(V.1), pass_when: matrix entry recorded}
risks:
  - {risk: current "first/last step" sparse representation loses tracking information, mitigation: §3 alternative finders restore intermediate steps when needed}
estimated_effort: M
last_updated: 2026-05-09
---

# Subsystem — TPC hits to track candidates

*Charter.* Owns leaf V.1 (plan 24 §2). The transformation from raw
TPC hits to track candidates is the foundation of vertex and charged-
PID. Improvements at this leaf propagate to V.2, V.3, V.4, C.1, …

## 1. Inputs and outputs

Per plan 24 §2.1 V.1 schema:

| Class A inputs (TPC parquet) | Forbidden Class B |
|---|---|
| `Event_ID`, `x`, `y`, `z`, `t`, `eDep`, `photons` (= electrons), `px`, `py`, `pz`, `xHitID`, `module_ID`, `step_info`, `vol_name` | `Track_ID`, `Parent_ID`, `Name`, `origin_vol_name` |

Output schema (`charged.csv` upstream, vertex.csv downstream):

```
candidate_id          # local id within event
event_id
hit_indices           # indices into TPC table for this event
anchor_xyz            # first hit position
direction_xyz         # unit vector
n_hits
chi2_seed             # quality estimator from fitter
```

## 2. Current implementation (per plan 08 §3.2)

`_track_anchor_and_direction(group)` (`reconstruction.py:165–184`).
Sorts hits by time then input order; takes anchor = first coord,
direction = (last - first). No fit; no covariance; no quality cut
beyond ≥ 2 valid coords.

The grouping into "tracks" is currently driven by `Track_ID` (Class B
violation) — this is the migration item: replace with geometric
clustering on `(x, y, z, t)`.

## 3. Alternative track finders (candidates for plan 49)

Each candidate is benchmarked on the truth-substitution ladder
(plan 38) at leaf V.1.

| Candidate | Source | Pros | Cons |
|---|---|---|---|
| **Geometric clustering** (DBSCAN-like in `(x, y, z, t)`) | new | Class A only | needs hit-density tuning |
| **Hough transform** (helix in cylindrical TPC) | ALICE | well-studied for TPC | no B-field; need straight-line variant |
| **Kalman seeded by Hough** | ACTS | covariance "for free" | implementation cost |
| **Riemann fit** | various | analytic for circles | not directly applicable without B-field |

The current "no B-field" configuration (plan 17) makes tracks
straight; this simplifies finders but eliminates momentum measurement
from curvature — momentum currently comes from kinematics (KE on
hits) plus stopping-range information.

## 4. Acceptance criteria

- §1 inputs match plan 09 (no Class B in production path).
- §2 current implementation noted; migration item logged.
- §3 alternative comparison run on ladder when plan 49 picks an
  improvement target.

## 5. Dependencies

- **08** — current implementation.
- **24** — leaf identity.
- **38** — ladder benchmark.
- *Consumed by:* plans 26 (fit), 30 (vertex), 38 (ladder).

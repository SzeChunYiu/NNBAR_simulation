---
id: 07_6_3_truth_content_per_hit
title: Simulation atomic walkthrough §6.3 — truth content per hit
version: 0.1
status: draft
owner: Sim Production
depends_on: [07_simulation_atomic_walkthrough]
---

### 6.3 Truth content per hit

Every recorded `NNbarHit` from every SD includes the *truth* fields
`name`, `trackID`, `parentID`, `process`, `origin_vol_name`. Per the
realism contract (plan 01), these are Class B columns: the
reconstruction must not consume them in its decision path. Plan 09
freezes their classification per parquet column.

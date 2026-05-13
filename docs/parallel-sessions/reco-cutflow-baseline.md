# Lane: reco-cutflow-baseline

## Goal
Document the current (broken) reconstruction pipeline cutflow for pi0_mono_150mev.
This establishes a quantitative baseline showing where events are lost before the
seed threshold fix (worker-2) is applied.

## Background
`cluster_neutral_hits` uses `min_energy=10.0 MeV` as a SEED threshold.
Max single-step eDep in LG is ~9.99 MeV, so seeds never form → 0 NeutralObjects
→ 0 pi0 candidates in every event.

## Data
`build_lunarc/output/pi0_mono_150mev/`
- `LeadGlass_output_0.parquet` (200 events)
- `Scintillator_output_0.parquet` (200 events)

## Analysis Steps

### Stage 0: Raw event count
n_events = number of unique Event_IDs in Particle_output

### Stage 1: Events with LG hits
n_with_lg = Event_IDs present in LeadGlass_output

### Stage 2: Events where max single-step eDep > seed threshold
For each event: max_eDep = max(LeadGlass_output['eDep']) where Event_ID == eid
n_pass_seed_10mev = events where max_eDep > 10.0
n_pass_seed_01mev = events where max_eDep > 0.1  (proposed new threshold)

### Stage 3: Count NeutralObjects returned by cluster_neutral_hits
Import and call directly:
```python
from nnbar_reconstruction.reconstruction.neutral_reconstruction import cluster_neutral_hits
import numpy as np
```
For each event, call cluster_neutral_hits with default parameters.
Count events returning at least 1 NeutralObject.

### Stage 4: Count pi0 candidates
Call find_pi0_candidates on NeutralObjects.
Count events with ≥ 1 candidate.

### Output
Write `docs/reports/reco_cutflow_baseline.md`:
Table:
| Stage | Cut | n_pass | fraction |
|-------|-----|--------|---------|
| 0 | Total events | 200 | 100% |
| 1 | Has LG hits | N | X% |
| 2a | max eDep > 10 MeV (current) | N | X% |
| 2b | max eDep > 0.1 MeV (proposed) | N | X% |
| 3 | ≥1 NeutralObject (current) | 0 | 0% |
| 4 | ≥1 pi0 candidate (current) | 0 | 0% |

This document will be updated after the seed threshold fix (see reco-cluster-seed-threshold-fix.md).

## Constraints
- Python only, no SLURM
- Do NOT modify neutral_reconstruction.py (worker-2 handles that)
- Read and report; no code changes

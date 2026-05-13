# Lane: reco-cluster-seed-threshold-fix

## Root cause (traced 2026-05-12)

`cluster_neutral_hits` in `neutral_reconstruction.py` uses
`min_energy=10.0` as a **seed-hit** threshold. Do not cite a fixed line
number for this function unless you first re-run the line-reference verifier:

```python
max_energy = available_energies.max()
if max_energy < min_energy:
    break
```

Max single-step eDep in LeadGlass is ~9.8-9.99 MeV across all samples.
This means the loop exits immediately before seeding any cluster → 0 neutral
objects → 0 pi0 candidates in every sample (verified: pi0_mono_150mev, all
vertex scan samples).

`min_energy` was intended as a **cluster-total** minimum (10 MeV), not a seed
threshold. A 75 MeV photon from pi0 decay deposits its energy across hundreds
of steps; no single step reaches 10 MeV.

## Fix — two-part

### Part 1: Lower seed threshold

Change `min_energy: float = 10.0` default to `seed_min_energy: float = 0.1`.
Rename the parameter to make the intent unambiguous.

```python
def cluster_neutral_hits(
    vertex: np.ndarray,
    scint_hits: pd.DataFrame,
    lg_hits: pd.DataFrame,
    assigned_scint_mask: np.ndarray,
    assigned_lg_mask: np.ndarray,
    cone_angle: Optional[float] = None,
    seed_min_energy: float = 0.1,    # changed from min_energy=10.0
    cluster_min_energy: float = 10.0, # new: filter on cluster total
) -> List[NeutralObject]:
```

In the loop:
```python
max_energy = available_energies.max()
if max_energy < seed_min_energy:   # 0.1 MeV: stop when no more seeds
    break
```

### Part 2: Filter on cluster total energy

After computing `total_energy = energies.sum()`, add:
```python
if total_energy < cluster_min_energy:
    # Skip this cluster — mark hits as unavailable and continue
    for idx in cluster_indices:
        available[idx] = False
    continue
```

This ensures only genuine photon/hadronic clusters (> 10 MeV) survive.

### Part 3: Update reconstruct_neutral_objects call site

Update any call to `cluster_neutral_hits` that passes `min_energy=...` as a
keyword argument to use `seed_min_energy=...` instead.

## Expected result after fix

- `reconstruct_neutral_objects` on pi0_mono_150mev (200 events) should return
  ~180+ events with ≥ 1 neutral object
- `find_pi0_candidates` should return non-zero pi0 candidates (expect ~30-50%
  reconstruction efficiency at 150 MeV based on opening angle + LG fraction cuts)

## Verification test

```python
import pandas as pd
from nnbar_reconstruction.reconstruction.neutral_reconstruction import reconstruct_neutral_objects, find_pi0_candidates

lg = pd.read_parquet('build_lunarc/output/pi0_mono_150mev/LeadGlass_output_0.parquet')
sc = pd.read_parquet('build_lunarc/output/pi0_mono_150mev/Scintillator_output_0.parquet')

n_candidates = 0
vertex = (0.0, 0.0, 0.0)
for eid in lg.Event_ID.unique()[:20]:
    objs = reconstruct_neutral_objects(vertex, sc[sc.Event_ID==eid], lg[lg.Event_ID==eid])
    cands = find_pi0_candidates(objs, vertex)
    n_candidates += len(cands)

assert n_candidates > 0, f"FAIL: 0 pi0 candidates after fix"
print(f"PASS: {n_candidates} pi0 candidates in 20 events")
```

## Constraints

- Edit ONLY `nnbar_reconstruction/reconstruction/neutral_reconstruction.py`
- Do NOT change `pi0_cuts.py` thresholds
- Do NOT change macro files, SLURM scripts, or C++ source
- After fix, re-run pi0_reco_driver on pi0_mono_{50,150,250}mev and vertex scan
  samples, update MASTER_PLAN

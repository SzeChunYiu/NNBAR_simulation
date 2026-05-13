# Lane: cosmic-weight-analysis

## Goal

Write a Python script that loads all 26 cosmic Parquet output directories, applies
the w_{i,j} weight from the thesis Eq. 6.1, and produces a combined weighted background
dataset ready for signal vs background discrimination.

## Read first

- `docs/parallel-sessions/MASTER_PLAN.md`
- `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/6_Signal_Bkg_simulation.tex` — Eq. 6.1 and Table 6.1
- `nnbar_reconstruction/data_pipeline/load_simulation_data.py` — existing loader

## Weight formula (thesis Eq. 6.1)

```python
w_ij = (N_ij / S_ij) * (N_ij / sum_i_N_ij)
```
where:
- N_{i,j} = expected events from Table 6.1 (3-year totals)
- S_{i,j} = 1_000_000 (events simulated per bin)
- i = energy bin index (0-5), j = particle index (0-4)

N_{i,j} table (from thesis Table 6.1):
```python
N_IJ = {
    # (ebin, particle): N  — particle order: mu-, gamma, e-, neutron, proton
    (0, 0): 1.69e11, (0, 1): 2.30e12, (0, 2): 4.02e11, (0, 3): 4.33e11, (0, 4): 2.04e10,
    (1, 0): 1.90e11, (1, 1): 1.09e10, (1, 2): 1.05e10, (1, 3): 1.23e10, (1, 4): 4.34e9,
    (2, 0): 7.69e11, (2, 1): 6.21e9,  (2, 2): 5.63e9,  (2, 3): 6.03e9,  (2, 4): 3.24e9,
    (3, 0): 2.68e11, (3, 1): 7.23e8,  (3, 2): 2.24e8,  (3, 3): 1.28e8,  (3, 4): 1.44e8,
    (4, 0): 2.18e11, (4, 1): 2.30e7,  (4, 2): 0,       (4, 3): 5.92e7,  (4, 4): 8.37e7,
    (5, 0): 2.00e11, (5, 1): 0,       (5, 2): 0,       (5, 3): 6.25e6,  (5, 4): 5.00e6,
}
```

## Files to produce

### 1. `nnbar_reconstruction/data_pipeline/cosmic_weights.py` (NEW, <150 lines)

```python
N_IJ = { ... }  # from table above
PARTICLES = ["mu-", "gamma", "e-", "neutron", "proton"]
S = 1_000_000

def get_weight(ebin: int, particle_idx: int) -> float:
    """Compute w_{i,j} from thesis Eq. 6.1."""
    N = N_IJ.get((ebin, particle_idx), 0.0)
    if N == 0:
        return 0.0
    sum_i = sum(N_IJ.get((i, particle_idx), 0.0) for i in range(6))
    if sum_i == 0:
        return 0.0
    return (N / S) * (N / sum_i)
```

### 2. `scripts/combine_cosmic_background.py` (NEW, <200 lines)

CLI:
```bash
python scripts/combine_cosmic_background.py \
    --cosmic-root output/cosmic \
    --output output/combined_cosmic_background.parquet \
    --subsystem TPC               # which subsystem Parquet to combine
```

For each of the 27 nonzero job directories (`cosmic_mu-_bin0/` through `cosmic_proton_bin5/`, skipping only zero-`N_{i,j}` bins):
1. Parse particle name and bin index from directory name
2. Load `TPC_output_0.parquet` (or specified subsystem)
3. Look up w_{i,j} using `get_weight(ebin, particle_idx)`
4. Multiply existing `weight` column by w_{i,j} (or set it if column=1.0)
5. Append to combined DataFrame

Write combined DataFrame to `--output` parquet.
Print summary: N_events per particle type, total weighted events.

### 3. `tests/test_cosmic_weights.py` (NEW, <100 lines)

```python
def test_muon_bin0_weight():
    from nnbar_reconstruction.data_pipeline.cosmic_weights import get_weight
    w = get_weight(ebin=0, particle_idx=0)
    assert w > 0
    # N=1.69e11, S=1e6, sum_i(N_mu)=approx 1.724e12
    expected = (1.69e11/1e6) * (1.69e11/1.724e12)
    assert abs(w - expected) / expected < 0.01

def test_zero_N_returns_zero():
    w = get_weight(ebin=4, particle_idx=2)  # e-, bin4: N=0
    assert w == 0.0

def test_all_weights_positive_for_nonzero_N():
    from nnbar_reconstruction.data_pipeline.cosmic_weights import N_IJ, get_weight
    for (ebin, pidx), N in N_IJ.items():
        if N > 0:
            assert get_weight(ebin, pidx) > 0
```

## Iteration cycle

1. Write the three files
2. Run: `python -m pytest tests/test_cosmic_weights.py -v 2>&1 | tail -10`
3. Fix until pass
4. Commit on `lane/cosmic-weight-analysis`, merge to main

## Stop condition

Tests pass and committed. Write "DONE: cosmic-weight-analysis merged" then re-read
MASTER_PLAN.md and update any task statuses that this work enables.

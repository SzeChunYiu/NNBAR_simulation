# Spec: clustering.py enhancements + clustering_config.yaml

## Files to Touch

- `nnbar_reconstruction/tracking/clustering.py` — enhance in place
- `nnbar_reconstruction/tracking/clustering_config.yaml` — create new

## Do NOT Change

All existing public function signatures must remain identical. This is purely additive.

## Enhancements to clustering.py

### 1. YAML config loader (add near top of file)
```python
def load_clustering_config(config_path=None) -> dict:
```
- Default path: `Path(__file__).parent / 'clustering_config.yaml'`
- Loads with pyyaml, merges over hardcoded defaults section-by-section
- Falls back silently to defaults if file missing or malformed
- Returns dict with keys: `dbscan`, `hdbscan`, `refinement`

### 2. HDBSCAN clustering (add as new function)
```python
def cluster_with_hdbscan(xyz: np.ndarray, min_cluster_size=5, min_samples=3) -> np.ndarray:
```
- Lazy-imports `hdbscan`; raises `ImportError` with pip hint if absent
- Handles edge case: fewer points than min_cluster_size → all noise
- Returns label array matching DBSCAN convention (-1 = noise)

### 3. GPU DBSCAN stub (add as new function)
```python
def cluster_with_gpu_dbscan(xyz: np.ndarray, eps=2.0, min_samples=3) -> np.ndarray:
```
- Only activates if `NNBAR_ENABLE_GPU=1` env var is set
- Tries `cuml.cluster.DBSCAN`; falls back to sklearn on ImportError or any error
- Logs which backend was used

### 4. Logging
- Add `import logging` and `logger = logging.getLogger(__name__)` at module level
- Replace any `print()` calls with `logger.info()` / `logger.debug()`
- Add tqdm progress bars on any loops over events:
  ```python
  try: from tqdm import tqdm
  except ImportError: tqdm = lambda x, **kw: x
  ```

## clustering_config.yaml to create

```yaml
dbscan:
  alpha: 1.5
  min_samples: 3
  k: 6
  phi_weight: 5.0
  z_weight: 1.0
hdbscan:
  min_cluster_size: 5
  min_samples: 3
refinement:
  gap_threshold: 5.0
  d_thresh: 2.0
  angle_thresh_deg: 20.0
```

## Rules

- Keep file under 500 lines if possible; split only if forced
- Python 3.9+; pyyaml and tqdm are available
- No stub functions — write working code

# Lane: rfc-classifier

## Goal

Implement a Random Forest Classifier (RFC) for NNBAR signal vs. cosmic background
discrimination, as described in the licentiate thesis Chapter 10. The RFC is applied
AFTER the sequential cutflow and uses event-level variables as input features.

## Repo

Work in: `/Volumes/MyDrive/nnbar/nnbar/simulation/`
Branch: `lane/rfc-classifier`

## Read first

- `docs/parallel-sessions/MASTER_PLAN.md` — project status
- `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/10_Event_selection.tex` — RFC description
- `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/9_Event_Variables.tex` — input features
- `nnbar_reconstruction/` — existing reconstruction modules to understand what's available
- `scripts/run_reco_pipeline.py` — how the pipeline currently runs end-to-end

## What thesis Chapter 10 says about the RFC

- Trained on: signal (annihilation) events vs. cosmic muon background events
- Input features: the event-level variables from Chapter 9
- Output: probability score P(signal) ∈ [0, 1]
- Validation: ROC curve, AUC, signal efficiency vs. background rejection
- Events weighted by w_{i,j} (cosmic weight from thesis Eq. 6.1) during training
- Hyperparameters: n_estimators=100, max_depth=10 (standard RF settings for HEP)

## Input features (from Chapter 9 event variables)

Use these as RFC features (all float, event-level):
1. `total_energy` — sum of all detected energy (MeV)
2. `scintillator_energy` — energy in scintillator (MeV)
3. `leadglass_energy` — energy in lead glass (MeV)
4. `n_charged_tracks` — number of reconstructed charged tracks
5. `n_pi0` — number of π⁰ candidates
6. `sphericity` — event sphericity S ∈ [0, 1]
7. `invariant_mass` — total event invariant mass W (MeV)
8. `vertex_x`, `vertex_y`, `vertex_z` — reconstructed vertex position (cm)
9. `energy_asymmetry` — (E_top - E_bottom) / (E_top + E_bottom)
10. `n_hits_tpc` — number of TPC hits
11. `leading_track_dedx` — highest dE/dx among charged tracks

## Files to produce

### 1. `nnbar_reconstruction/ml/rfc_classifier.py` (NEW, <400 lines)

```python
class RFCClassifier:
    def __init__(self, n_estimators=100, max_depth=10, random_state=42): ...
    def fit(self, X: pd.DataFrame, y: np.ndarray, sample_weight=None): ...
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray: ...
    def save(self, path: Path): ...          # joblib.dump
    def load(self, path: Path): ...          # joblib.load
    def feature_importance_plot(self, path: Path): ...  # saves PNG
    def roc_curve_plot(self, X_test, y_test, path: Path, weights_test=None): ...
```

Uses: `sklearn.ensemble.RandomForestClassifier`, `sklearn.metrics.roc_auc_score`.

### 2. `nnbar_reconstruction/ml/__init__.py` — export `RFCClassifier`

### 3. `scripts/train_rfc.py` (NEW, <200 lines)

CLI:
```bash
python scripts/train_rfc.py \
    --signal-dir data/signal_test/ \
    --cosmic-dir data/cosmic_test/ \
    --output-dir output/rfc/ \
    --n-events 10000
```

Steps:
1. Load signal Parquet (label=1, weight=1.0)
2. Load cosmic Parquet (label=0, weight from `weight` column if present, else 1.0)
3. Extract feature columns listed above
4. 80/20 train/test split (stratified, weight-aware)
5. Train RFCClassifier
6. Save model to `output/rfc/model.joblib`
7. Save ROC curve to `output/rfc/roc_curve.png`
8. Save feature importance to `output/rfc/feature_importance.png`
9. Print: AUC, signal efficiency at 50% background rejection

### 4. `tests/test_rfc.py` (NEW, <150 lines)

```python
def test_rfc_trains_on_synthetic_data():
    # Create 200 synthetic events: 100 signal (label=1), 100 bkg (label=0)
    # Features: random floats for the 11 feature columns
    # Train RFC, check AUC > 0.5 (better than random)
    # Check predict_proba returns values in [0, 1]

def test_rfc_save_load(tmp_path):
    # Train on 100 synthetic events
    # Save model, load model
    # Check predictions are identical before and after save/load

def test_rfc_feature_importance_plot(tmp_path):
    # Train on 100 synthetic events
    # Call feature_importance_plot(), check PNG is created
```

### 5. `nnbar_reconstruction/ml/feature_extraction.py` (NEW, <150 lines)

```python
def extract_rfc_features(parquet_dir: Path, n_events: int = -1) -> pd.DataFrame:
    """Load Parquet files and extract the 11 RFC feature columns.
    
    Returns DataFrame with columns matching the feature list above.
    If a column is missing from the Parquet files, fills with 0.0.
    """
```

## Iteration cycle

1. Read the thesis chapters and existing code listed above
2. Write the files listed above
3. Run: `python -m pytest tests/test_rfc.py -v 2>&1 | tail -15`
4. Fix until all tests pass
5. Run: `python scripts/train_rfc.py --signal-dir data/signal_test/ --cosmic-dir data/signal_test/ --output-dir /tmp/rfc_test/` (use signal for both as placeholder — real cosmic data not available yet)
6. Commit on `lane/rfc-classifier`
7. Merge to main via: `bash /Volumes/MyDrive/nnbar/nnbar/simulation/scripts/codex-supervisor/merge.sh lane/rfc-classifier`

## Stop condition

Stop when:
- All tests pass
- `train_rfc.py` runs end-to-end on synthetic/signal data
- Committed and merged

Write "DONE: RFC classifier merged to main" then re-read MASTER_PLAN.md and check for
additional NEXT tasks. Think about what else might be missing that isn't on the plan yet —
compare the thesis chapters to what exists in nnbar_reconstruction/ and suggest gaps.

## Constraints

- Use `sklearn` only — no PyTorch, no XGBoost
- Max 500 lines per file
- No hardcoded paths
- Weights are optional (fallback to uniform weights if column missing)

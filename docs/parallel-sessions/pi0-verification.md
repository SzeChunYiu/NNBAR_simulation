# Lane: pi0-verification

## Goal

Verify that π⁰ reconstruction cuts in the codebase match the thesis (Chapter 8-10).
Fix any discrepancies. Add unit tests that pin the cut values to thesis numbers.

## Read first

- `docs/parallel-sessions/MASTER_PLAN.md`
- `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/8_Object_Definition.tex` — π⁰ cuts
- `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/10_Event_selection.tex` — cutflow table
- `nnbar_reconstruction/` — all Python files (grep for pi0, opening_angle, leadglass)

## What the thesis specifies (Chapter 8)

For π⁰ candidate selection:
- Diphoton invariant mass window: **100–180 MeV** (π⁰ mass ± resolution)
- Opening angle between the two photons: local optimum **25°**, final optimized cut **> 30°**
  (cut to remove collinear pairs)
- Lead glass energy fraction: local optimum **60%**, final optimized cut **> 55%** in
  lead glass (not in scintillator — confirms photon didn't convert early)
- Total π⁰ energy: final optimized cut **< 720 MeV**
- Scintillator energy: final optimized cut **< 250 MeV**
- Lead-glass energy: final optimized cut **< 980 MeV**

For event-level selection (extracted Chapter 10 preliminary cutflow table):
- Scintillator energy loss in **[20, 2000] MeV**
- TPC track cut: at least one track traced back to the source foil
- Pion count **≥ 1**
- Invariant mass **W ≥ 0.5 GeV**
- Sphericity **≥ 0.2**
- Filtered scintillator balance: upper **≤ 320 MeV** and lower **≤ 930 MeV**

Note: the extracted Chapter 10 text mentions vertex detection as a future improvement,
not as one of the preliminary cutflow table rows.

## Verification steps

For each cut above:
1. Grep the codebase for the cut value
2. If value matches thesis: write a pytest test that asserts the constant
3. If value is wrong or missing: fix it, then write the test

## Files to produce/modify

### 1. `nnbar_reconstruction/reconstruction/pi0_cuts.py` (NEW or edit existing)

Define all π⁰ cut constants as named module-level variables:
```python
PI0_MASS_WINDOW_MEV = (100.0, 180.0)  # thesis Ch. 8
PI0_MIN_OPENING_ANGLE_DEG = 30.0       # thesis Ch. 8
PI0_MIN_LEADGLASS_FRACTION = 0.55      # thesis Ch. 8 final optimized criteria
PI0_LOCAL_LEADGLASS_FRACTION_OPTIMUM = 0.60  # thesis Ch. 8 local optimum
```

If object_identification.py already has these values, move them here and import.
Do not duplicate constants.

### 2. `tests/test_pi0_cuts.py` (NEW, <150 lines)

```python
def test_pi0_mass_window_matches_thesis():
    from nnbar_reconstruction.reconstruction.pi0_cuts import PI0_MASS_WINDOW_MEV
    assert PI0_MASS_WINDOW_MEV == (100.0, 180.0), "thesis Ch.8: 100-180 MeV window"

def test_opening_angle_threshold_matches_thesis():
    from nnbar_reconstruction.reconstruction.pi0_cuts import PI0_MIN_OPENING_ANGLE_DEG
    assert PI0_MIN_OPENING_ANGLE_DEG == 30.0, "thesis Ch.8: >=30 degrees"

def test_leadglass_fraction_matches_thesis():
    from nnbar_reconstruction.reconstruction.pi0_cuts import PI0_MIN_LEADGLASS_FRACTION
    assert PI0_MIN_LEADGLASS_FRACTION == 0.55, "thesis Ch.8 final optimized cut: >55% lead glass fraction"

def test_pi0_candidate_selection_on_synthetic():
    # Create synthetic diphoton pairs: some pass all cuts, some fail each cut
    # Verify that the selection function returns correct pass/fail for each case
    ...
```

### 3. `tests/test_cutflow.py` (NEW, <150 lines)

Verify the cutflow sequence matches thesis Table 10.1:
- Test that cut order is: scintillator energy → TPC tracks → pion count → invariant mass → sphericity → filtered scintillator balance
- Test signal efficiency > 60% on synthetic signal-like events
- Test background rejection > 80% on synthetic bkg-like events

## Iteration cycle

1. Read thesis chapters 8 and 10 carefully
2. Grep codebase for all pi0-related cuts
3. Write/fix pi0_cuts.py with canonical constants
4. Write tests
5. Run: `python -m pytest tests/test_pi0_cuts.py tests/test_cutflow.py -v 2>&1 | tail -20`
6. Fix until all pass
7. Commit on `lane/pi0-verification`, merge to main

## Stop condition

All tests pass and cuts match thesis. Write "DONE: pi0-verification merged" then re-read
MASTER_PLAN.md. Also: look through nnbar_reconstruction/ for any other missing features
vs the thesis — add them to MASTER_PLAN.md if found.

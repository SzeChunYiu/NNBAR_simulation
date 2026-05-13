# Lane: ch9-event-variables

## Goal

Align the Chapter 9 event-variable formulas used by reconstruction, cutflow, and
RFC feature extraction with the thesis definitions, then pin them with pytest
regressions.

## Scope

Pane 1 / Python only.

Writable files:
- `nnbar_reconstruction/analysis/event_variables.py`
- `nnbar_reconstruction/utils/coordinates.py`
- `tests/test_event_variables.py` (create if needed)
- small `__init__.py` exports only if tests require them

Do not touch C++, CUDA, SLURM, LUNARC jobs, or `NNBAR_Detector/` infrastructure.

## Required reading

- `docs/parallel-sessions/MASTER_PLAN.md`
- Thesis Ch. 9 event-variable definitions (invariant mass, sphericity, energy variables)
- Existing code in `nnbar_reconstruction/analysis/event_variables.py`
- Existing helper `compute_sphericity` in `nnbar_reconstruction/utils/coordinates.py`
- RFC feature extraction in `nnbar_reconstruction/ml/feature_extraction.py` for downstream callers

## Required changes

1. **Sphericity**
   - Implement the thesis momentum-tensor definition using momentum magnitudes:
     \[
     S^{\alpha\beta}=\frac{\sum_i p_i^\alpha p_i^\beta}{\sum_i |\vec p_i|^2}
     \]
   - Sort eigenvalues descending as \(\lambda_1\ge\lambda_2\ge\lambda_3\) and return
     \(S=\frac{3}{2}(\lambda_2+\lambda_3)\).
   - Do not normalize every object to a unit direction before building the tensor.
   - Handle empty, single-object, and zero-momentum inputs deterministically.

2. **Signed longitudinal energy**
   - `compute_longitudinal_energy` must implement
     \(E_L=\sum_i E_i\cos\alpha_i\) with the forward/backward sign preserved.
   - Remove the current `abs(cos_alpha)` behavior.
   - Normalize the beam axis and object directions defensively; clip dot products to [-1, 1].

3. **Regression tests**
   - Add tests that fail under the old implementation:
     - Unequal-momentum sphericity case, e.g. two 10 MeV/c back-to-back x-axis tracks plus one 1 MeV/c y-axis track; expected \(S=1.5/201\), not the direction-only value.
     - Signed longitudinal energy: one 100 MeV forward object plus one 40 MeV backward object gives +60 MeV, not 140 MeV.
   - Pin invariant-mass and transverse-energy smoke cases with explicit expected values and units.
   - Include edge cases for empty/zero momentum inputs.

## Verification

Run:

```bash
python -m pytest tests/test_event_variables.py tests/test_cutflow.py tests/test_rfc.py -q
```

If any unrelated existing tests fail, capture the failing command/output in the handoff and stop.

## Stop condition

Stop when:
- Ch. 9 formula tests pass.
- Existing cutflow/RFC tests still pass.
- `MASTER_PLAN.md` marks this lane `DONE` with a short note about the formulas fixed.
- Changes are committed on the current branch.

Handoff format:

```text
DONE: ch9-event-variables
Files changed: ...
Verification: python -m pytest ... -q -> PASS
Notes/blockers: ...
```

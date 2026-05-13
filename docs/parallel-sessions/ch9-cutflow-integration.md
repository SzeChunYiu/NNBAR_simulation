# Lane: ch9-cutflow-integration

## Goal

Make the default Python event-selection path use the thesis Table 9.1
preliminary cutflow, including the filtered upper/lower scintillator-energy
cuts that depend on the Chapter 7 timing windows.

## Scope

Pane 1 / Python analysis only.

Writable files:
- `nnbar_reconstruction/analysis/event_variables.py`
- `nnbar_reconstruction/analysis/event_selection.py`
- `nnbar_reconstruction/reconstruction/cutflow.py`
- `nnbar_reconstruction/reconstruction/timing_window.py`
- `tests/test_cutflow.py`
- new focused pytest files under `tests/`

Do not touch C++, CUDA, SLURM, LUNARC jobs, or `NNBAR_Detector/` infrastructure.

## Required reading

- `docs/parallel-sessions/MASTER_PLAN.md`
- Thesis Ch. 7 timing-window definitions
- Thesis Ch. 9 preliminary event-selection Table 9.1
- `nnbar_reconstruction/analysis/event_variables.py`
- `nnbar_reconstruction/analysis/event_selection.py`
- `nnbar_reconstruction/reconstruction/cutflow.py`
- `nnbar_reconstruction/reconstruction/timing_window.py`
- `tests/test_cutflow.py`

## Required changes

1. **Use one canonical cutflow**
   - Keep the canonical thresholds in `nnbar_reconstruction/reconstruction/cutflow.py`:
     - scintillator energy: 20--2000 MeV
     - TPC tracks to vertex: at least 1
     - pion count: at least 1
     - invariant mass: at least 500 MeV
     - sphericity: at least 0.2
     - filtered upper scintillator energy: at most 320 MeV
     - filtered lower scintillator energy: at most 930 MeV
   - Make the default `analysis/event_selection.py` path use this same order and
     these constants, not the older top/bottom-asymmetry + vertex-radius defaults.
   - Preserve any legacy cuts only when callers explicitly request them.

2. **Expose filtered scintillator observables**
   - Add filtered upper/lower scintillator-energy fields to `EventVariables`
     with safe default values so existing tests and constructors do not break.
   - Include those fields in `to_dict()`.
   - Add a helper that converts `EventVariables` into `EventCutObservables`
     without duplicating threshold constants.

3. **Tie filtered energies to timing windows**
   - Add or reuse a helper that splits scintillator hits by hemisphere:
     - upper: `y > 0`
     - lower: `y < 0`
   - For each hemisphere, compute out-of-time energy using the Chapter 7
     scintillator timing window
     \([t_{\pi,1000}-2\sigma_{\rm scint}, t_{\pi,100}+2\sigma_{\rm scint}]\).
   - Do not count `y == 0` hits in either hemisphere unless the thesis/code
     convention is documented in the test.

4. **Tests**
   - Add a regression test that fails under the old default selection because
     top/bottom-asymmetry or vertex-radius cuts are applied instead of the
     Table 9.1 filtered-scintillator cut.
   - Add a synthetic-hit timing test with one in-window hit and one out-of-window
     hit in each hemisphere; verify only out-of-window energy contributes to the
     filtered upper/lower observables.
   - Keep the existing threshold/order tests passing.

5. **Sample/survival-fraction handling**
   - If exact thesis sample files are present, add an executable pytest or script
     path that computes the Table 9.1 survival fractions.
   - If exact samples are absent, do not fabricate fractions. Add a short blocker
     note in the handoff naming the missing sample path(s), while still landing
     the code-level integration and synthetic regressions.

## Verification

Run:

```bash
python -m pytest tests/test_event_variables.py tests/test_cutflow.py tests/test_rfc.py -q
python -m pytest tests/ -x -q
```

If unrelated existing tests fail, capture the command and final failure output in
the handoff and stop.

## Stop condition

Stop when:
- The default Python selection uses the Table 9.1 cut order and constants.
- Filtered upper/lower scintillator energies are present on event variables and
  are computed from the timing-window helper.
- Focused pytest regressions pass.
- `MASTER_PLAN.md` marks this lane `DONE` with a short note about the default
  cutflow and filtered-scintillator integration.
- Changes are committed on the current branch.

Handoff format:

```text
DONE: ch9-cutflow-integration
Files changed: ...
Verification: ...
Sample/survival-fraction status: ...
Notes/blockers: ...
```

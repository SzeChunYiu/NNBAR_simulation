# Lane: timing-window-regression

## Goal

Strengthen the Python timing-window and filtered-energy contract against thesis
Chapter 7 timing-window formulas and Chapter 9 out-of-time-window energy/cutflow
usage. This lane should add focused regressions and only make code changes when
the tests expose a real mismatch.

## Writable scope

- `nnbar_reconstruction/reconstruction/timing_window.py`
- `nnbar_reconstruction/reconstruction/cutflow.py` only if the filtered-energy
  cut contract needs a small fix
- Existing or new focused tests under `tests/`, preferably
  `tests/test_timing_window.py` plus targeted additions to
  `tests/test_ch9_cutflow_integration.py`
- `docs/parallel-sessions/MASTER_PLAN.md` only for final lane-status notes

Do not edit C++ simulation, SLURM files, queues, or unrelated reconstruction
modules in this lane.

## Required reading

1. `docs/parallel-sessions.md`
2. `docs/parallel-sessions/MASTER_PLAN.md`
3. `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/7_Reconstruction.tex`
   - Timing Window of Acceptance
4. `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/9_Event_Variables.tex`
   - Out-of-time-window Energy
   - Selection Criteria and Event Cut Flow
5. Existing Python surfaces verified before this spec was written:
   - `nnbar_reconstruction/reconstruction/timing_window.py`
   - functions: `pion_travel_time`, `photon_travel_time`,
     `scintillator_timing_window`, `leadglass_timing_window`,
     `apply_timing_cuts`, `compute_out_of_time_energy`,
     `split_scintillator_hits_by_hemisphere`,
     `compute_filtered_scintillator_hemisphere_energies`
   - `nnbar_reconstruction/reconstruction/cutflow.py`
   - classes/functions: `EventCutObservables`, `CutflowResult`,
     `apply_ch10_cutflow`

Before committing any new file/function/path claim, re-run the verifier rule in
`docs/parallel-sessions.md` rather than trusting this handoff.

## One compact-safe iteration

Pick one small unit and finish it completely. Recommended first unit:

1. Add focused tests for thesis window boundaries:
   - scintillator window is
     \([t_{\pi,1000}-2\sigma_{\rm scint}, t_{\pi,100}+2\sigma_{\rm scint}]\);
   - lead-glass window is
     \([t_\gamma-2\sigma_{\rm lg}, t_\gamma+2\sigma_{\rm lg}]\);
   - hits exactly on both boundaries are accepted and hits just outside are
     rejected;
   - `n_sigma`/`sigma` overrides affect the window as expected.
2. Add or extend filtered-energy regressions:
   - in-window hits do not contribute to out-of-time energy;
   - out-of-window hits do contribute;
   - scintillator y>0/y<0 hemisphere splitting matches the Chapter 9 cutflow
     variables;
   - add analogous lead-glass coverage if not already present.
3. If a mismatch is found, fix the smallest code path in
   `timing_window.py`/`cutflow.py`; otherwise keep the iteration test-only.
4. Do not claim exact signal/cosmic acceptance fractions unless the exact thesis
   samples are available and verified.

## Verification command

Run focused tests first, then full tests if the focused set passes:

```bash
python -m pytest tests/test_timing_window.py tests/test_ch9_cutflow_integration.py tests/test_cutflow.py -q
python -m pytest tests/ -x -q
```

Also verify the 500-line cap:

```bash
wc -l nnbar_reconstruction/reconstruction/timing_window.py nnbar_reconstruction/reconstruction/cutflow.py tests/test_timing_window.py tests/test_ch9_cutflow_integration.py
```

## Stop condition

Stop after one compact, tested unit. Handoff must state which timing/filtered
energy contracts are now covered, any code fixes made, the exact pytest output,
and whether exact acceptance-fraction reproduction remains blocked by missing
samples.

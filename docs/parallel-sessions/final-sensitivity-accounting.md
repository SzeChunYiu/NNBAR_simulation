# Lane: final-sensitivity-accounting

## Goal

Add pure-Python accounting for weighted signal/background yields and zero-survivor
limit inputs so final sensitivity claims can be generated from verified samples
later, without claiming unavailable thesis survival fractions now.

## Writable scope

- `nnbar_reconstruction/analysis/sensitivity.py`
- `tests/test_sensitivity_accounting.py`
- `docs/parallel-sessions/MASTER_PLAN.md` only for final lane-status notes

Do not edit C++ simulation, SLURM files, queues, or unrelated reconstruction
modules in this lane. Avoid adding to existing analysis files that are already
near or above the 500-line cap.

## Required reading

1. `docs/parallel-sessions.md`
2. `docs/parallel-sessions/MASTER_PLAN.md`
3. `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/3_HIBEAM_NNBAR_experiment.tex`
   - sensitivity and quasi-free scaling discussion
4. `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/6_Signal_Bkg_simulation.tex`
   - signal/cosmic-rate setup, if present in this extracted thesis tree
5. `/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/9_Event_Variables.tex`
   - cutflow/RFC survival discussion
6. `nnbar_reconstruction/data_pipeline/cosmic_weights.py`
7. `nnbar_reconstruction/reconstruction/cutflow.py`

Before committing any file/function/path claim, re-run the verifier rule in
`docs/parallel-sessions.md`; do not trust this handoff for line numbers.

## One compact-safe iteration

Implement one deterministic accounting unit:

1. Add small pure functions or dataclasses that compute weighted yields,
   `sum_w2` statistical variance, acceptance from generated/surviving counts,
   and the Poisson mean upper limit for zero observed events as a function of an
   explicit confidence level.
2. Keep confidence level explicit unless the thesis text is verified for a
   canonical default. Do not hard-code a final NNBAR sensitivity number.
3. Add tests using toy arrays/records for weighted-yield sums, uncertainty,
   zero-survivor limits, empty inputs, negative-weight rejection, and acceptance
   edge cases.
4. Add a report helper that can carry blocker text when exact signal/cosmic
   samples are absent, so downstream reports cannot silently imply thesis
   survival fractions were reproduced.
5. Do not run simulations or require thesis sample files in this iteration.

## Verification command

```bash
python -m pytest tests/test_sensitivity_accounting.py -q
python -m pytest tests/ -x -q
wc -l nnbar_reconstruction/analysis/sensitivity.py tests/test_sensitivity_accounting.py
```

## Stop condition

Stop after the accounting unit and tests pass, full tests pass, touched files
remain under 500 lines, and `MASTER_PLAN.md` states that final numeric
sensitivity remains blocked until exact weighted signal/background samples are
verified.

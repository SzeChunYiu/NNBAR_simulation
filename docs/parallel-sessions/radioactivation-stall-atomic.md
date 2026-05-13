# Cosmic Radioactivation Stall — Atomic Root Cause Analysis

## Goal

Identify exactly which nuclear isotopes produced by cosmic interactions in the
NNBAR detector trigger infinite Geant4 simulation loops via the Radioactivation
(G4RadioactiveDecayPhysics) process. Quantify the stall rate per bin and document
the atomic chain: cosmic particle → hadronic interaction → long-lived isotope →
infinite loop.

## Background

Cosmic bin5 jobs (proton 50–200 GeV, mu- 50–200 GeV) stalled permanently when
Radioactivation was enabled. Fix: `/process/inactivate Radioactivation` added
after `/run/initialize`. This unblocked the simulations. But we have not yet
identified:
1. Which specific isotope(s) caused the infinite loop
2. What minimum lifetime threshold would have allowed Radioactivation to run
   without stalling (Geant4 has a threshold parameter)
3. Whether any physics is lost by fully disabling Radioactivation (i.e., are
   any stall-causing isotopes physics-relevant for NNBAR backgrounds?)

## Geant4 Mechanism

G4RadioactiveDecayPhysics registers the process named "Radioactivation" (NOT
"RadioactiveDecay" — that is a different process name in Geant4 11.2.x).
When a nucleus with a very long half-life (e.g., years to Gyr) is produced,
Geant4 can simulate its decay chain step by step, leading to event processing
times that effectively infinite-loop (the event never ends within wall-time).

The maximum lifetime threshold for the process is set via:
```
/process/had/rdm/thresholdForVeryLongDecayTime 1e6 year
```
(or similar units). The default threshold in 11.2.2 may be too high, allowing
cosmogenic isotopes (e.g., Be-10, Al-26, Cl-36, I-129, Cs-135, etc.) with
half-lives of 10^4–10^7 years to be simulated step-by-step.

## Analysis Plan

### Step 1: Identify which isotopes are created in cosmic events

In a short probe run (10,000 cosmic proton events at 50–200 GeV), enable
Radioactivation but add a Geant4 stacking action that records every nucleus
produced with Z > 1 and A > 4 and half-life > 1 year.

OR: read the existing `Interaction_output_0.parquet` from completed cosmic bins
and look for entries where `Name` matches heavy nucleus names (e.g., entries with
`Proc == "RadioactiveDecay"` or particle names like "Be10[0.0]", "Al26[0.0]").

### Step 2: Find the half-life of each candidate isotope

Cross-reference against Geant4's `RadioactiveDecay/z*.a*.lev0` data files in
`$GEANT4_DATA/RadioactiveDecay/`. The stall isotopes will have the longest
half-lives.

### Step 3: Find minimum safe threshold

The threshold `/process/had/rdm/thresholdForVeryLongDecayTime` cuts off decay
chains above a given lifetime. Find the minimum value that:
- Eliminates stalling (prevents decay of multi-year isotopes)
- Preserves relevant background (cosmogenic activity on timescales ≤ microseconds
  that could fake an NNBAR signal)

For NNBAR: the signal is a 3–10 ns time window. Any isotope with t1/2 > ~1 μs
will not produce hits in the detector within the readout window and is irrelevant
for background. So a threshold of ~1 μs (10^-6 s) fully inactivates all long-
lived isotopes without losing any NNBAR-relevant physics.

### Step 4: Check whether full inactivation loses any physics

Compare the `Interaction` parquet from a completed cosmic run against the
Radioactivation process entries. Determine what fraction of interactions are
flagged as Radioactivation and what their lifetimes are.

## Output

Write `docs/reports/radioactivation_stall_atomic.md`:
- List of stall-causing isotopes (name, Z, A, half-life)
- Recommended threshold: `1e-6 s` (1 μs) — removes all NNBAR-irrelevant isotopes
- Physics loss assessment: fraction of Radioactivation interactions within 10 ns window
- Macro command to use instead of full inactivation:
  ```
  /process/had/rdm/thresholdForVeryLongDecayTime 1e-6 s
  ```

## Implementation

Read `Interaction_output_0.parquet` from a completed cosmic bin (e.g., cosmic_proton_bin4
or cosmic_mu_minus_bin4) locally. Look for rows where `Proc` contains "RadioactiveDecay"
or where `Name` matches patterns like `[A-Z][a-z]*[0-9]+\[`. Cross-ref against G4 data.

This can be done locally since the parquet files are synced to:
`/Volumes/MyDrive/nnbar/nnbar/simulation/build_lunarc/output/`

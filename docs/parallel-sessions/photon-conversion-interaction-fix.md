# Photon Conversion Audit Fix Spec

## Problem

`photon_conversion_audit.py::_first_interaction_labels()` looks for a subdetector
column directly in the parquet file, but the simulation writes separate per-subdetector
Parquet files (no single-file subdetector column).

The photon_100MeV_conversion directory contains:
- `Interaction_output_0.parquet` — ALL secondary interactions with columns:
  `Event_ID, Track_ID, Parent_ID, Name, Proc, Current_Vol, Origin, m, KE, t, x, y, z, px, py, pz`
- `Particle_output_0.parquet` — primary particle summary
- Per-subdetector files (Beampipe, TPC, LeadGlass, Silicon, Scintillator)

## Fix

Update `discover_photon_sample` and `run_audit` to:
1. Look for `Interaction_output_0.parquet` inside the photon_100MeV_conversion directory
2. In `_first_interaction_labels`, try the Interaction file approach:
   a. Filter rows where `Proc == "conv"` and `Name in ["e+", "e-"]`
   b. For each `Event_ID`, keep the row with the smallest `t` (earliest conversion)
   c. Extract `Current_Vol` as the conversion subdetector
   d. Map to canonical detector using the existing `_canonical_volume()` function

The existing `_DIRECT_VOLUME_COLUMNS` check can still run first for
forward-compat with simulation schemas that add a direct subdetector column.

## Requirements

- Backward-compatible: if direct subdetector column exists, use it (existing path)
- New fallback: if not, try `Interaction_output_0.parquet` with `Proc=="conv"` approach
- `_looks_like_100mev_photon` should match the Interaction file path too
- `discover_photon_sample` should return `Interaction_output_0.parquet` if found
  under a photon_100MeV_conversion directory (or the Beampipe file as before —
  it's passed to `audit_conversion_fractions` which is then fixed to handle both)

## Test

Add a focused test: synthetic Interaction parquet with 4 events, each having
2 conv tracks (e+/e-) with different `Current_Vol` values and different `t` times.
Verify the fraction counts are correct.

## Files

- `nnbar_reconstruction/analysis/photon_conversion_audit.py` (update)
- `tests/test_photon_conversion_audit.py` (add focused Interaction-file test)

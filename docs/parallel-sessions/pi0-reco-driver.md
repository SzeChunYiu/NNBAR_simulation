# Lane: pi0-reco-driver

## Goal

Implement `nnbar_reconstruction/analysis/pi0_reco_driver.py` — a reconstruction
driver that converts raw mono-energetic π⁰ simulation output (LeadGlass,
Scintillator, Particle Parquets) into per-event reconstructed quantities
(`pi0_mass_mev`, `opening_angle_deg`, `reco_photon_energy_mev`,
`truth_photon_energy_mev`) required by `neutral_pi0_response_audit.py`.

Also update `discover_pi0_sample` in `neutral_pi0_response_audit.py` to prefer
reco files over raw Particle_output when both are present.

## Context

`neutral_pi0_response_audit.audit_pi0_response` reads a Parquet file and looks
for specific column names.  `discover_pi0_sample` currently returns
`pi0_mono_{E}mev/Particle_output_0.parquet` (truth kinematics only), which
triggers all three blockers because it lacks mass/opening-angle/energy columns.

After this lane:
- Driver produces `build_lunarc/output/pi0_reco_response/pi0_reco_{E}mev.parquet`
- Updated discover prefers reco files → audit reads the right file → blockers close

## Raw data layout

```
build_lunarc/output/pi0_mono_{E}mev/
    Particle_output_0.parquet   # columns: Event_ID, KE (truth pi0 KE), u, v, w
    LeadGlass_output_0.parquet  # columns: Event_ID, x, y, z, eDep, ...
    Scintillator_output_0.parquet  # columns: Event_ID, x, y, z, eDep, ...
```

Energies: 50, 150, 250 MeV.  200 events each.  Vertex is always (0, 0, 0)
for all events (confirmed from Particle x/y/z = 0.0 for all rows).

## Files

- Create: `nnbar_reconstruction/analysis/pi0_reco_driver.py` (≤ 400 lines)
- Create: `tests/test_pi0_reco_driver.py` (≤ 250 lines)
- Edit: `nnbar_reconstruction/analysis/neutral_pi0_response_audit.py`
  → update `discover_pi0_sample` only (no other changes)

Do NOT edit C++. Do NOT submit SLURM. Do NOT retune `pi0_cuts.py` constants.

## Implementation steps

### 1. `pi0_reco_driver.py`

```python
PI0_TRUTH_MASS_MEV = 134.9766

def run_pi0_reco(
    sim_output_root: str | Path,
    reco_output_dir: str | Path,
    energies_mev: tuple[int, ...] = (50, 150, 250),
    vertex: np.ndarray = np.zeros(3),
) -> list[Path]:
    """Process raw pi0 sim output into per-event reco Parquet files."""
```

For each energy:
1. Load `pi0_mono_{E}mev/Particle_output_0.parquet` → truth_df (columns: Event_ID, KE)
2. Load `pi0_mono_{E}mev/LeadGlass_output_0.parquet` → lg_df
3. Load `pi0_mono_{E}mev/Scintillator_output_0.parquet` → scint_df
4. Group lg_df and scint_df by Event_ID
5. For each event:
   - Get lg_hits = lg_df[lg_df.Event_ID == eid][['x','y','z','eDep']]
   - Get scint_hits = scint_df[scint_df.Event_ID == eid][['x','y','z','eDep']]
   - Call `reconstruct_neutral_objects(vertex, scint_hits, lg_hits)` →
     returns list of NeutralObject
   - Call `find_pi0_candidates(neutral_objects, vertex)` →
     returns list of (obj1, obj2, invariant_mass) tuples
   - Pick best candidate = highest invariant_mass tuple (if any)
6. Per-event output columns:
   - `Event_ID`: int
   - `truth_ke_mev`: float — truth pi0 kinetic energy from Particle_output
   - `truth_total_energy_mev`: float — truth_ke_mev + 134.9766
   - `n_neutral_objects`: int
   - `n_pi0_candidates`: int
   - `pi0_mass_mev`: float — best candidate invariant_mass, NaN if no candidate
   - `opening_angle_deg`: float — opening angle in DEGREES for best candidate
   - `reco_photon_energy_mev`: float — (E1+E2)/2 for best candidate, NaN if none
   - `truth_photon_energy_mev`: float — truth_total_energy_mev/2 (symmetric proxy)

   Note: opening_angle from `find_pi0_candidates` comes from
   `NeutralPionCandidate.opening_angle` which is in radians (as returned by
   `compute_opening_angle`). Convert to degrees: `np.degrees(opening_angle_rad)`.

7. Write `{reco_output_dir}/pi0_reco_{E}mev.parquet`
8. Return list of written paths

Fail-closed: if any energy directory is missing, emit a warning and skip that
energy (do not raise). If all three are missing, return empty list.

### 2. Update `discover_pi0_sample`

Replace the current `return sorted(...)` line with:

```python
# Prefer reco driver output over raw Particle_output
reco = [p for p in candidates if "reco" in p.as_posix().lower()]
if reco:
    return sorted(reco, key=str)[0]
return sorted(candidates, key=lambda path: ("particle_output" not in path.name.lower(), str(path)))[0]
```

This ensures the audit reads the reco file once it exists, and falls back to
the existing behaviour when only raw Particle_output is available.

### 3. Tests `tests/test_pi0_reco_driver.py`

Three focused tests:

**a) smoke_two_cluster_event**: Construct a minimal synthetic event with two
lead-glass clusters at opposite positions (e.g. cluster1 near (280, 0, 0),
cluster2 near (-280, 0, 0)), each with 10 hits and ~70 MeV total eDep.
Call `run_pi0_reco` with a mock sim root built from these clusters.
Assert: output Parquet has one row, `pi0_mass_mev` is not NaN, and
`opening_angle_deg` > 30.

**b) missing_energy_emits_no_crash**: Call `run_pi0_reco` with an empty
tmp_dir as sim_output_root. Assert: returns empty list, does not raise.

**c) discover_prefers_reco_file**: In a tmp directory with both
`pi0_mono_50mev/Particle_output_0.parquet` (stub) and
`pi0_reco_response/pi0_reco_50mev.parquet` (with a `pi0_mass_mev` column),
call `discover_pi0_sample(50, tmp_dir)`. Assert: returned path contains
"reco".

## Imports needed in driver

```python
from ..reconstruction.neutral_reconstruction import (
    reconstruct_neutral_objects,
    find_pi0_candidates,
)
import numpy as np
import pandas as pd
from pathlib import Path
```

The `find_pi0_candidates` result items are `(NeutralObject, NeutralObject, float)`.
The third element is `pi0_result.invariant_mass` (a float in MeV).  The opening
angle must be taken from the `NeutralPionCandidate` returned by
`identify_neutral_pion` which is called inside `find_pi0_candidates` —
unfortunately that candidate is not exposed.  Use `compute_opening_angle` from
`nnbar_reconstruction.utils.coordinates` directly:

```python
from ..utils.coordinates import compute_opening_angle
import numpy as np
opening_angle_rad = compute_opening_angle(vertex, obj1.position, obj2.position)
opening_angle_deg = float(np.degrees(opening_angle_rad))
```

## Verification

```bash
rtk python -m pytest tests/test_pi0_reco_driver.py -q
rtk zsh -lc 'python -m pytest tests/ -x -q 2>&1 | tail -20'
rtk python -c "
from nnbar_reconstruction.analysis.pi0_reco_driver import run_pi0_reco
import pathlib
paths = run_pi0_reco('build_lunarc/output', '/tmp/pi0_reco_out')
print('Written:', paths)
"
rtk wc -l nnbar_reconstruction/analysis/pi0_reco_driver.py tests/test_pi0_reco_driver.py
```

Expected: focused tests pass; full suite stays green; driver ≤ 400 lines;
test ≤ 250 lines; if run against real data in build_lunarc/output, produces
three Parquet files at /tmp/pi0_reco_out/ with n_events=200 each.

## Stop condition

Implement driver + tests + discover patch, run verification, commit. Do NOT
run the driver against real build_lunarc/output — test data only. Do NOT
update MASTER_PLAN.md rows (planner does that after the next audit run).

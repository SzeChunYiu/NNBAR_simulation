# Lane: pi0-parametric-studies

## Physics motivation

All current pi0 mono simulations fire from vertex (0,0,0), the centre of the
carbon foil.  This is an idealization.  In a real nnbar annihilation, the
vertex is distributed uniformly over the foil surface — a disk of radius
~30 cm at z = 0 (Geant4 geometry constant confirmed from `DetectorConstruction`).

The reconstruction performance metrics — efficiency, mass peak position, mass
resolution, opening-angle bias — are all functions of the vertex transverse
position (r = √(x²+y²)).  Without knowing these functions, we cannot:

1. Compute the true geometric acceptance correction for the signal efficiency.
2. Assign a systematic uncertainty from vertex smearing.
3. Validate that the detector is uniform enough to use a single response function.

This doc maps the full study program and its priority order.

---

## Root cause of current limitation

In `src/core/PrimaryGeneratorAction.cc::GenerateSignalPrimaries` (lines 298–302):

```cpp
// Generate random position (at origin for signal events)
G4double x = 0.0;
G4double y = 0.0;
G4double z = 0.0;
```

These are hardcoded.  No UI command exists to change them.  Fix: add two new
static members and two new macro commands to the existing `/calibration/`
messenger namespace.

---

## C++ change required (spec: pi0-vertex-scan-cpp.md)

Add to `PrimaryGeneratorAction`:

```
/calibration/signal_vertex_x  X cm   — fixed x offset (default 0)
/calibration/signal_vertex_y  Y cm   — fixed y offset (default 0)
/calibration/signal_vertex_z  Z cm   — fixed z offset (default 0)
```

And one distribution command for foil-averaged studies:

```
/calibration/signal_vertex_disk_radius  R cm  — uniform random (x,y) on disk
                                              of radius R at z = signal_vertex_z
                                              (0 = no disk, use fixed vertex)
```

When `signal_vertex_disk_radius > 0`, each event samples a new random (x,y)
uniformly on the disk.  Otherwise the fixed vertex is used.

These values must be written to the Particle_output Parquet (already writes x, y, z
from `rec.x = x / cm`), so every output event carries its truth vertex
position.

---

## Study program

### Study 1: Vertex radial scan (r-dependence) — PRIORITY 1

Fix E = 150 MeV (mid-range), scan r = 0, 5, 10, 15, 20, 25, 30 cm.
For each r, shoot 500 pi0 events isotropically.

Output per radius r:
- Reconstruction efficiency ε(r)  =  (events with pi0 candidate) / 500
- Median reconstructed invariant mass peak(r)
- Mass resolution sigma(r)
- Mean opening angle θ_mean(r)
- Energy bias bias(r) = (E_reco - E_truth) / E_truth

Expected behaviour: efficiency near 1.0 for r < ~20 cm, dropping for outer
radii where one photon cluster exits the lead-glass acceptance.  Any
asymmetry in phi would indicate a geometric bias.

Run as SLURM array: task 0-6 maps to r ∈ {0,5,10,15,20,25,30} cm.
Macro sets `/calibration/signal_vertex_x R 0 0` (on the +x axis, phi=0).
This is conservative; phi-dependence can be checked separately.

### Study 2: Foil-averaged efficiency — PRIORITY 2

5000 events, vertex uniformly distributed on disk r < 30 cm.
Measure: acceptance-averaged efficiency ε_avg and resolution σ_avg.
Compare to r=0 result → geometric acceptance correction factor
A = ε_avg / ε_0.

### Study 3: Full energy response curve — PRIORITY 3

Extend from 3 energies to full ladder at r=0:
50, 100, 150, 200, 250, 300, 350, 400, 450, 500 MeV.
(Already have 50, 150, 250 from current runs.)

Output: ε(E), peak(E), σ(E), bias(E) → calibration curves for thesis Ch. 7.

### Study 4: Pi0 multiplicity dependence — PRIORITY 4

Fix E = 150 MeV, r = 0.  Shoot 1 pi0, 2 pi0s, 3 pi0s from same vertex.
Use existing `/calibration/signal_particles pi0 pi0` mechanism (no new C++).

Output: ε(N), confusion rate, mass peak shift vs N.
Physics: in nnbar signal events, typical pi0 multiplicity is 2-4.

### Study 5: Angular acceptance map — PRIORITY 5

Map detector acceptance vs pi0 direction (theta, phi grid).
Requires new generator command for fixed direction instead of isotropic.
Lower priority — isotropic average is sufficient for thesis sensitivity.

---

## Output schema (studies 1-3)

Each study writes a Parquet with columns:
`Event_ID, truth_vertex_x_cm, truth_vertex_y_cm, truth_vertex_r_cm,
 truth_ke_mev, truth_total_energy_mev,
 n_neutral_objects, n_pi0_candidates,
 pi0_mass_mev, opening_angle_deg,
 reco_photon_energy_mev, truth_photon_energy_mev,
 reco_total_energy_mev, reco_eff_flag`

The `truth_vertex_{x,y,r}_cm` columns come directly from the Particle_output
(already written by the generator via `rec.x = x/cm`).

---

## Implementation plan

1. **C++ spec** (`pi0-vertex-scan-cpp.md`): add vertex commands to
   `PrimaryGeneratorAction` and two new statics.  Queued to codex.

2. **SLURM scan** (`slurm/pi0_vertex_scan.slurm`): SLURM array 0-6,
   each task sets `/calibration/signal_vertex_x R 0 0`, 500 events.

3. **Analysis extension** (`pi0_reco_driver.py` already queued):
   extend to read the `x,y,z` columns from Particle_output for the vertex
   truth information — no new code needed since the driver already reads
   `Particle_output_0.parquet`.

4. **Audit extension** (`neutral_pi0_response_audit.py`): add an optional
   `group_by_vertex_radius` path that segments results by `truth_vertex_r_cm`.

---

## SLURM timing estimate

Study 1 (vertex scan): 7 tasks × 500 events × ~15s/event = ~8750 s ≈ 2.5 h.
Fits in `lu48` 4h walltime per task, 4 threads.

Study 2 (disk avg): 5000 events × ~15s/event = ~20800 s ≈ 5.8 h with 4 threads ≈ 1.5 h.

---

## Dependency chain

```
1. pi0-vertex-scan-cpp.md → C++ implementation (codex) →
2. LUNARC rebuild (sbatch build_nnbar.slurm) →
3. Vertex scan + disk avg SLURM jobs →
4. pi0_reco_driver.py processes outputs →
5. neutral_pi0_response_audit.py compares r=0 vs r>0 →
6. MASTER_PLAN rows for acceptance correction + resolution systematics
```

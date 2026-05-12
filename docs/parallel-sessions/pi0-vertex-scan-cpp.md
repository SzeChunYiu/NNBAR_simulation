# Lane: pi0-vertex-scan-cpp

## Goal

Add vertex-position UI commands to `PrimaryGeneratorAction` so that pi0 mono
studies can fire from any (x,y,z) on the foil instead of the hardcoded origin.
This unblocks Studies 1 and 2 from `docs/parallel-sessions/pi0-parametric-studies.md`.

Do NOT change any physics, cuts, or existing behaviour.  Default values must
reproduce the current origin-vertex behaviour exactly.

## Files

- Edit: `NNBAR_Detector/src/core/PrimaryGeneratorAction.cc`
- Edit: `NNBAR_Detector/include/core/PrimaryGeneratorAction.hh`
- Create: `NNBAR_Detector/macro/studies/pi0_vertex_scan_r0.mac` through
  `NNBAR_Detector/macro/studies/pi0_vertex_scan_r30.mac` (7 macros)

Do NOT edit PhysicsList.cc, DetectorConstruction.cc, or any other file.

## Implementation steps

### 1. Add statics to PrimaryGeneratorAction.hh

In the `// Signal mode static parameters` section, add after `sSignalEnergyMax`:

```cpp
static G4double sSignalVertexX;   // cm, default 0
static G4double sSignalVertexY;   // cm, default 0
static G4double sSignalVertexZ;   // cm, default 0
static G4double sSignalVertexDiskRadius;  // cm, default 0 (= no disk)
```

### 2. Add static member initialization in PrimaryGeneratorAction.cc

After the existing `sSignalEnergyMax` initialization (line ~79), add:

```cpp
G4double PrimaryGeneratorAction::sSignalVertexX = 0.0;
G4double PrimaryGeneratorAction::sSignalVertexY = 0.0;
G4double PrimaryGeneratorAction::sSignalVertexZ = 0.0;
G4double PrimaryGeneratorAction::sSignalVertexDiskRadius = 0.0;
```

### 3. Register new UI commands in the messenger setup

Find the section near line 190 where `fMessenger->DeclareProperty(...)` is called.
After the `signal_energy_max` declaration, add:

```cpp
fMessenger->DeclarePropertyWithUnit("signal_vertex_x", "cm", sSignalVertexX,
    "Fixed signal vertex x (cm); default 0");
fMessenger->DeclarePropertyWithUnit("signal_vertex_y", "cm", sSignalVertexY,
    "Fixed signal vertex y (cm); default 0");
fMessenger->DeclarePropertyWithUnit("signal_vertex_z", "cm", sSignalVertexZ,
    "Fixed signal vertex z (cm); default 0");
fMessenger->DeclarePropertyWithUnit("signal_vertex_disk_radius", "cm",
    sSignalVertexDiskRadius,
    "Uniform disk sampling radius (cm) for signal vertex x/y; 0 = fixed vertex");
```

### 4. Replace hardcoded vertex in GenerateSignalPrimaries

Replace lines 298-302:
```cpp
// Generate random position (at origin for signal events)
G4double x = 0.0;
G4double y = 0.0;
G4double z = 0.0;
```

With:
```cpp
// Signal vertex: fixed or uniform disk on z-plane
G4double x, y;
G4double z = sSignalVertexZ * CLHEP::cm;
if (sSignalVertexDiskRadius > 0.0) {
    G4double R = sSignalVertexDiskRadius * CLHEP::cm;
    G4double r = R * std::sqrt(G4UniformRand());
    G4double phi_v = 2.0 * pi * G4UniformRand();
    x = r * std::cos(phi_v);
    y = r * std::sin(phi_v);
} else {
    x = sSignalVertexX * CLHEP::cm;
    y = sSignalVertexY * CLHEP::cm;
}
```

NOTE: `t` is declared separately on line 302 and is unchanged. The existing
`rec.x = x / CLHEP::cm; rec.y = y / CLHEP::cm; rec.z = z / CLHEP::cm;`
lines (already present around line 355-357) will automatically capture the
new vertex coordinates in the Particle_output Parquet — no extra changes needed.

### 5. Create 7 macro files for the vertex radial scan

`NNBAR_Detector/macro/studies/pi0_vertex_scan_r{N}.mac` for N ∈ {0,5,10,15,20,25,30}:

Pattern:
```mac
# Pi0 vertex scan: fixed vertex at r=N cm, 150 MeV mono-energetic pi0.
# Part of parametric vertex-position study (pi0-parametric-studies.md).

/run/initialize
/tracking/verbose 0

/calibration/signal_particle pi0
/calibration/signal_energy_min 150 MeV
/calibration/signal_energy_max 150 MeV
/calibration/signal_vertex_x N cm
/calibration/signal_vertex_y 0 cm
/calibration/signal_vertex_z 0 cm

/particle_generator/set_folder_name studies/pi0_vertex_scan_r{N}mev
/particle_generator/set_run_number 0
/particle_generator/set_event_number 0

/run/beamOn 500
```

For r0: vertex_x = 0, for r5: vertex_x = 5, etc.

Also create one disk-average macro `pi0_vertex_disk_r30.mac`:
```mac
# Pi0 foil-averaged efficiency: uniform disk r<30cm, 150 MeV.

/run/initialize
/tracking/verbose 0

/calibration/signal_particle pi0
/calibration/signal_energy_min 150 MeV
/calibration/signal_energy_max 150 MeV
/calibration/signal_vertex_disk_radius 30 cm
/calibration/signal_vertex_z 0 cm

/particle_generator/set_folder_name studies/pi0_vertex_disk_r30
/particle_generator/set_run_number 0
/particle_generator/set_event_number 0

/run/beamOn 5000
```

## Verification

```bash
# Compile check (local, not LUNARC)
rtk cmake --build build-codex-native --target nnbar-detector-simulation -j4 2>&1 | tail -10

# Macro syntax check: grep for new commands in macros
rtk grep -l "signal_vertex" NNBAR_Detector/macro/studies/pi0_vertex_scan_r*.mac

# Default-behaviour regression: run 5 events with default (no vertex commands)
# → Particle_output should have x=0,y=0,z=0
# DO NOT run on LUNARC directly — submit via sbatch only
```

## Stop condition

C++ edits + all 8 macro files committed.  Do NOT submit any SLURM job.
Do NOT change PhysicsList.cc or any reconstruction Python.
After commit, notify planner to rebuild on LUNARC and run the vertex scan array.

## After this lane: SLURM scan

`slurm/pi0_vertex_scan.slurm` (separate lane after rebuild):
```
#SBATCH --array=0-7
RADII=(0 5 10 15 20 25 30 disk30)
r=${RADII[$SLURM_ARRAY_TASK_ID]}
./nnbar-detector-simulation.bin -m macro/studies/pi0_vertex_scan_r${r}.mac
```

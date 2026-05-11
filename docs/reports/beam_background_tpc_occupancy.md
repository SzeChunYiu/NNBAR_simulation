# Beam-background and TPC-occupancy evidence audit

Date: 2026-05-11. Lane: `beam-background-tpc-occupancy`.

This is an audit-only compact-safe iteration. It verifies the thesis
Appendix A beam-induced-background inputs and the current local simulation
surfaces that could reproduce them. It does **not** submit SLURM jobs, run
new detector simulations, or promote any Appendix A table as reproduced.

## Verifier transcript

Required evidence paths existed in this worktree:

```text
/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/12_Appendix_1.tex
NNBAR_Detector/slurm/run_cosmic_array.slurm
NNBAR_Detector/src/core/DetectorConstruction.cc
NNBAR_Detector/src/detector/beampipe_geometry.cc
nnbar_reconstruction/config/nnbar_geometry.yaml
```

The required Appendix A grep found the load-bearing phrases and tables:

```text
39: beam stop made of 30 cm of B4C and 3 m thick copper
46: inner surface ... coated ... B4C ... alternatives ... 6LiF ... 1 cm
95: Neutron absorber ... 6LiF ... B4C
105: Beam-stop ... 6LiF ... B4C +Cu
208: no coating, 1 cm B4C, and 1 cm 6LiF configurations
286: 6LiF absorber ... 7.6e8 photons/s ... 0.003 ratio
288: Cd absorber ... 9.9e11 photons/s ... 3.85 ratio
333: intensity per 50 ns
361: drift velocities ... 4 cm/microsecond ... drift times ~25 microseconds
363: N=1200 tracks implies ~1.5 million channels and ~125 time-bins
```

Current beam-neutron source readiness was checked with the plan-22 style
file scan. It found cosmic-neutron paths and generic beampipe outputs, but
no staged beam-line MCPL or beam-neutron macro:

```text
NNBAR_Detector/batch/cosmic_neutron_runs
NNBAR_Detector/macro/cosmic_macro/cosmic_neutron
NNBAR_Detector/output/Beampipe_output_0.parquet
NNBAR_Detector/config/output_layouts/beampipe_output.json
```

`data/registry` is absent in this checkout, so no frozen beam-neutron
manifest is available for Appendix A normalization or table reproduction.

## Thesis Appendix A inputs

### Geometry and material assumptions

Appendix A uses a Geant4 beamline beginning at the last supermirror
reflection point, near `z = 190 m`, and explicitly models the beampipe and
beam stop. The inputs that matter for reproducibility are:

| Quantity | Appendix A value/status | Audit status |
|---|---:|---|
| Beampipe material | aluminum default; beryllium is an option | OPEN: local geometry default checked, but no reproduced material-variation run is registered. |
| Beampipe wall | 2 cm | OPEN: local C++ surface exists; no geometry hash/manifest is frozen. |
| Neutron shield | lead default, at least 2 m thick in prose | OPEN: no Appendix A reproduction manifest or scorer artifact. |
| Neutron absorber coating | B4C default; 6LiF, 6LiH, 6LiC2O3, B4C, none listed; thickness range 1 mm--1 cm with 1 cm default | OPEN: current local beampipe code places B4C coatings, but no runtime material selector for Appendix A alternatives was verified. |
| Beam stop | table lists 6LiF and B4C+Cu options; prose also says 30 cm B4C plus 3 m copper at about 15 m from foil | OPEN: current local code has a B4C+Cu beam-stop surface; no Config. 3/4 beam-stop artifact is frozen. |
| Physics list | FTFP_BERT_HP default in Appendix A table; QGSP_BERT_HP and QGSP_INCLXX_HP listed | OPEN: current local source includes HP headers but the observed registered constructor is non-HP, so Appendix A beam-neutron transport is not yet reproduced. |
| Target foil | 10--150 micrometers, default 100 micrometers | OPEN: no Appendix A beam-source manifest or target-material systematic throw is frozen. |

### Beam-induced background configurations

Appendix A separates absorber studies into configurations:

- Config. 1: no coating.
- Config. 2: default B4C coating.
- Config. 3: 6LiF coating, with the incoming neutron dataset reused with
  varied Geant4 random seeds for 500,000 neutrons.
- Config. 4: cadmium absorber, mentioned as a later/preliminary extension.
- Configs. 5--8: Be target, beam stop at 35 m, endcap at 35 m, and
  QGSP_BERT_HP respectively.

The thesis input normalisation is not just a geometry choice: it depends on
the incoming neutron dataset, 14 pulses separated by 0.071 ms, neutron
weights, and a slow-neutron plateau of roughly 1e13 s^-1 from 300--900 ms.
Those pieces are not frozen in a local `data/registry/<dataset_id>` manifest.

### Appendix A particle-intensity tables

The Appendix A tables contain the target numbers to reproduce, but this
audit treats them as thesis inputs, not as locally reproduced results.
Load-bearing values include:

| Table | Quantity | Thesis value(s) requiring reproduction evidence |
|---|---|---|
| Table 2 | TPC particle intensities for no coating, B4C, 6LiF | photons, neutrons, electrons, and positrons in energy bins; sample-size uncertainty is stated as order 1e7 s^-1. |
| Table 3 | beampipe-near-detector photon rates | default B4C: 2.6e11 s^-1; no coating: 3.0e11 s^-1; 6LiF: 7.6e8 s^-1; Cd: 9.9e11 s^-1; ratios to default recorded. |
| Table 4 | detector interaction intensities per 50 ns for Config. 3 | TPC: 0.60 photons, 2.4 e+/e-, 0.09 neutrons; scintillators and lead-glass rows also listed. |
| Occupancy estimate | TPC drift-time scaling | 4 cm/microsecond drift velocity, ~25 microsecond drift time, ~1200 tracks per frame, ~1.5M channels, ~125 time bins, ~12k pad-row product. |

## Current repo inventory

### C++ geometry and physics surfaces

`NNBAR_Detector/src/detector/beampipe_geometry.cc` contains a current
B4C-centered implementation surface:

```text
43: Beampipe_coating_thickness = 1.0*cm
108: BeamStop_Absorber_thickness = 30.0*cm
109: BeamStop_Metal_thickness = 3.0*m
176: material definition guard for LiF
188: material definition guard for el_Cd
220: B4CMaterial = G4Material::GetMaterial("B4C")
248,272,290,311,335,352,366,387: coating logical volumes use B4CMaterial
411: BeamStop_Absorber_LV uses B4CMaterial
```

That is enough to identify the present nominal coating and beam-stop
surface. It is not enough to reproduce Appendix A Configs. 1, 3, or 4,
because the grep verifier found LiF/Cd definitions but no corresponding
coating-volume or beam-stop-volume use. A runtime or build-time absorber
selector, plus frozen manifests for each configuration, remains open.

`NNBAR_Detector/src/core/PhysicsList.cc` and the duplicate legacy source
show the beam-neutron physics-list blocker:

```text
include G4HadronPhysicsFTFP_BERT_HP.hh
RegisterPhysics(new G4HadronPhysicsFTFP_BERT())
```

Appendix A depends on high-precision neutron transport. The present source
therefore cannot be treated as an HP beam-background reproduction unless a
verified build switch or separate build id actually registers `_HP`.

### SLURM and macro surfaces

`NNBAR_Detector/slurm/run_cosmic_array.slurm` is a CRY cosmic array, not a
beam-induced-background driver. Its verified command surface selects
`/cosmic/mode true`, `/cosmic/particle`, CRY energy bins, and CRY data, then
runs `/run/beamOn ${EVENTS}`. It does not configure Appendix A absorber
variants, incoming beam neutrons, 14 ESS pulses, scorer definitions, or the
per-50-ns occupancy table.

The macro inventory plan requires every thesis-quoted sample to resolve to a
macro, command, output pattern, and registry entry. The current local macro
search found signal/calibration/cosmic surfaces and cosmic-neutron paths, but
no beam-neutron source macro or staged MCPL file. That matches the plan-22
readiness blocker and keeps Appendix A rows non-reproduced.

### Reconstruction/config surfaces

`nnbar_reconstruction/config/nnbar_geometry.yaml` records reconstruction-side
TPC parameters:

```text
drift_length: 85.0 cm
drift_velocity: 0.005 cm/ns  # 5 cm/microsecond
n_layers: 20
n_modules: 8
```

This is useful for a future occupancy checker, but it is not itself an
Appendix A detector-hit occupancy reproduction. Appendix A's rough 4
cm/microsecond and 25 microsecond scaling should be carried as a thesis input
until an executable calculation declares which geometry/config values it uses.

### Governance and systematics surfaces

Plan 03 requires beam-neutron samples to have dataset IDs, command lines,
physics-list/build metadata, geometry hash, RNG seeds, output files, and
SHA-256 hashes before a number can be quoted as reproduced. No such local
registry entry exists.

Plan 10 requires every macro producing a thesis-quoted sample to have an
inventory row and every such sample to have a registry manifest. No Appendix A
beam-background macro row was verified in this iteration.

Plan 45 already names the relevant systematic hooks:

- `N4` physics list affects neutron transport and secondary interactions.
- `N7` beam-neutron flux stays draft until the ESS MCPL or parameterised
  source is frozen.
- `N10` material budget covers geometry/material variation, including photon
  conversion and scattering observables.
- Limitation `L6` says beam-timing background claims carry a bunch-structure
  caveat; `L5` prevents live-rate/DAQ-efficiency claims without a trigger or
  dead-time model.

## Reproducibility blockers

Every item below is intentionally `OPEN:` because this audit did not find a
complete sample/command/output/normalisation chain.

1. `OPEN: incoming-neutron-source` — stage either an ESS/HIBEAM beam-line MCPL
   file or a parameterised neutron-source macro, then record source choice in a
   DEC entry. Target resolution: 2026-06-30.
2. `OPEN: dataset-registry-entry` — create `beam_neutron_hibeam_*_v1`
   manifests with event counts, command, macro hash, geometry hash, physics
   list/build id, RNG seeds, output hashes, and realism class. Target: 2026-06-30.
3. `OPEN: HP-physics-build` — add or select a build id that actually registers
   `G4HadronPhysicsFTFP_BERT_HP` for beam-neutron transport. Target: 2026-06-15.
4. `OPEN: absorber-selector` — expose Configs. 1--4 as checked geometry inputs
   (`none`, B4C, 6LiF, Cd) rather than hard-coded B4C coatings. Target:
   2026-06-20.
5. `OPEN: scorer-definitions` — define the exact scorer volumes and particle
   filters for TPC, scintillator, lead-glass, beampipe-near-detector flux, and
   per-50-ns interaction rates. Target: 2026-06-30.
6. `OPEN: normalization` — encode the 14-pulse timing, 0.071 ms separation,
   neutron weights, plateau window, and per-second/per-50-ns conversion in a
   reproducible script with units. Target: 2026-06-30.
7. `OPEN: random-seed-policy` — record the 500,000-neutron Config. 3 varied-seed
   campaign and any other configuration seed schedule in manifests. Target:
   2026-06-30.
8. `OPEN: occupancy-calculation` — implement a fail-closed checker that derives
   the Table 4 to 25-microsecond drift-frame estimate from declared inputs and
   reports drift velocity, drift length, tracks/frame, time bins, and pad-row
   product. Target: 2026-06-30.
9. `OPEN: Appendix-A-output-artifacts` — freeze the raw scorer tables and any
   plotting inputs used for Tables 2--4 and the flux figures. Target: 2026-07-05.
10. `OPEN: systematics-throws` — connect Configs. 1--8 to plan-45 `N4`, `N7`,
    and `N10` throws before using them in a background-rate sum. Target:
    2026-07-05.

## Next smallest implementation task

Create a read-only fail-closed validator,
`scripts/verify_beam_background_occupancy.py`, with no simulation side effects.
It should:

1. assert that the thesis Appendix A source file, beampipe C++ source,
   physics-list source, macro/slurm tree, and `data/registry` paths are present
   or explicitly report the missing item;
2. parse the Appendix A expected labels and constants for Configs. 1--4,
   Table 3 photon rates, Table 4 per-50-ns detector intensities, and the
   25-microsecond TPC occupancy arithmetic;
3. inspect the local C++ source for hard-coded B4C-only coating use and for an
   actual `_HP` registration line;
4. fail until a `beam_neutron_hibeam_*_v1` registry entry, reproducer command,
   output artifact, and normalization metadata are present.

The validator should be a gate, not a scientific reproduction. It should keep
returning nonzero while the `OPEN:` blockers above remain unresolved.

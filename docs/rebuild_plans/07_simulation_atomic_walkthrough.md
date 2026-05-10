---
id: 07_simulation_atomic_walkthrough
title: Simulation atomic walkthrough — what NNBAR_Detector/ does
version: 0.1
status: draft
owner: Sim Production
depends_on: [00_README, 01_realism_contract]
inputs:
  - {path: NNBAR_Detector/, schema: source tree}
outputs:
  - {path: docs/rebuild_plans/07_simulation_atomic_walkthrough.md, schema: this file}
acceptance:
  - {test: every active source file under NNBAR_Detector/src/ has a section here, method: source ↔ doc cross-reference, pass_when: zero unmatched files}
  - {test: every output parquet column traces to a §-line in this plan, method: link from plan 09 to this plan, pass_when: full coverage}
  - {test: every CMake build option in CMakeLists.txt has a §-entry, method: option ↔ doc cross-reference, pass_when: full coverage}
  - {test: living document — every PR touching NNBAR_Detector/ updates the relevant §, method: CI check, pass_when: blocked PRs cite the §}
risks:
  - {risk: walkthrough rots as code changes, mitigation: plan 53 CI check that PRs touching NNBAR_Detector/src/ also edit this file}
  - {risk: duplicates plan 09 (data dictionary) on output schema, mitigation: 07 names columns; 09 owns their classification and units; both reference the other}
estimated_effort: XL
last_updated: 2026-05-09
---

# Simulation atomic walkthrough — what NNBAR_Detector/ does

*Charter.* This plan is the forensic, file-by-file accounting of the
existing Geant4 simulation. It does not propose changes. It records
what the code does today, where, with what inputs and what outputs,
so that every other plan can cite a known-quoted baseline rather than
rediscover behaviour. Plan 12 (physics-list audit), plan 16
(geometry/alignment), plan 17 (field calibration), and the sample-
regeneration plans (15–18) all consume this document.

## 1. Top-level structure

The simulation lives under `NNBAR_Detector/`. The active source tree is
the structured layout under `src/<topic>/` and `include/<topic>/`. A
*legacy* tree exists under `src/Detector_Module/` and the unprefixed
`src/*.cc` / `include/*.hh` — these are not compiled (verified against
`CMakeLists.txt:505–514`, the `file(GLOB SOURCES …)` glob list).

Active source directories:

| Directory | Contents |
|---|---|
| `src/core/` | `main.cc`-equivalent setup: `DetectorConstruction`, `PhysicsList`, run/event/stepping actions, primary-generator action, action initialisation |
| `src/detector/` | Geometry builders: beampipe, beampipe shielding, TPC, scintillator, lead-glass, silicon, cosmic shielding |
| `src/sensitive/` | Sensitive-detector classes: `CarbonSD`, `SiliconSD`, `TubeSD`, `TPCSD`, `ScintillatorSD`, `Scint_DetSD`, `LeadGlassSD`, `PMTSD`, `ShieldSD`, `DetArea_SD` |
| `src/hits/` | `NNbarHit` (universal hit class) and `NNbarRun` (per-run accumulator) |
| `src/generator/` | `G4MCPLGenerator` (MCPL primary source) and `G4MCPLWriter` (MCPL output writer) |
| `src/output/` | `ParquetOutputManager` (column-oriented writer) |
| `src/physics/` | Optional physics integrations: Garfield++/GarfieldGPU, Celeritas, Opticks, TPC drift/field/pad-readout helpers |
| `src/gpu/` | `TPCDriftGPU`, `OpticalPhotonGPU`, `GPUManager` |
| `src/util/` | `ElectricField`, `GeometryManager`, `GeometryParameters`, `RNGWrapper` |
| `src/gui/` | Qt dashboard (DashboardWindow, EventDisplay, MaterialBudgetPlot, …); only compiled when `WITH_DASHBOARD=ON` |

Active macro directories:

| Directory | Contents |
|---|---|
| `macro/signal/` | foil-origin antineutron annihilation primaries (`run_signal.mac`, `run_signal_100k.mac`) |
| `macro/cosmic_macro/cosmic_<species>/` | per-species cosmic primaries: muon, electron, gamma, neutron, proton; each with `BeamOn.mac` and `run_<n>.mac` partitions |
| `macro/calibration/` | calibration single-particle macros (lead-glass, scintillator, π⁰, gamma) |
| `macro/studies/` | thesis-bound study samples: `pi0_foil_mass.mac`, `pi0_foil_energy_scan.mac`, `charged_pion_proton_foil_stress.mac`, `multiprimary_pion_proton_foil_stress.mac` |
| `macros/` (lower-level legacy) | `signal_*.mac`, `background_compton.mac` — needs status review (plan 10) |

Top-level macro files: `gui.mac`, `init_vis.mac`, `vis.mac`,
`opticks_test.mac`, `quick_test.mac`, `test_signal_quick.mac`.

## 2. Build system (CMakeLists.txt)

Project: `nnbar-detector-simulation` v1.0.0, C++17,
`CMakeLists.txt:5–17`.

### 2.1 Build options

`CMakeLists.txt:74–90`:

| Option | Default | Effect |
|---|---|---|
| `WITH_GEANT4_UIVIS` | ON | Pulls Geant4 with UI/Vis |
| `MCPL_BUILD` | OFF | Default ParticleGun; ON enables MCPL primary source by default |
| `TARGET_BUILD` | ON | Carbon foil placed (`DetectorConstruction.cc:144–148`) |
| `DEBUG_VERBOSE` | OFF | Verbose debug output |
| `WITH_SCINTILLATION` | OFF | Enables `G4OpticalPhysics`; default is "fast mode" without optical photons |
| `WITH_GARFIELD` | OFF | Garfield++ TPC drift |
| `WITH_GARFIELD_GPU` | OFF | Custom CUDA/OpenMP TPC drift |
| `WITH_CELERITAS` | OFF | GPU EM physics offload |
| `WITH_OPTICKS` | OFF | GPU optical-photon propagation |
| `WITH_DASHBOARD` | OFF (auto-on if Qt found) | Qt monitoring GUI |

These options are encoded into `config.h` (generated at
`CMakeLists.txt:417–421`), and the simulation compiles in/out their
code paths via `#if WITH_*` macros.

### 2.2 External dependencies

Pulled by `cmake/FetchDependencies.cmake` (referenced at
`CMakeLists.txt:430`):

- **Arrow / Parquet** for columnar output
  (`CMakeLists.txt:432`).
- **nlohmann_json** (`CMakeLists.txt:433`).
- **spdlog** (`CMakeLists.txt:434`).
- **MCPL** vendored at `external/mcpl/mcpl.c`
  (`CMakeLists.txt:441–450`).
- **parquet-writer** vendored at `external/parquet-writer/src/cpp/`
  (`CMakeLists.txt:455–489`).
- **ACTS** vendored at `acts_tracking/` (top-level, not built by this
  CMake; reserved for future tracking — plan 25).

### 2.3 Wrapper script

The build emits `nnbar-detector-simulation` as a wrapper script and
`nnbar-detector-simulation.bin` as the actual binary
(`CMakeLists.txt:904–919`). The wrapper sets `LD_LIBRARY_PATH` /
`DYLD_LIBRARY_PATH` for Geant4, Arrow, Celeritas, Opticks, CUDA. This
lets a developer invoke the simulation without manual environment
setup. The wrapper-template input is at
`scripts/wrapper_template.sh.in`.

### 2.4 Installed runtime tree

`CMakeLists.txt:681–718` copies into the build dir: `batch/`,
`config/`, `docs/`, `data/`, `macro/`, `profiling_tool/`, `scripts/`,
plus top-level `gui.mac`, `init_vis.mac`, `vis.mac`, `setup.file`.
Output and log directories are created at `CMakeLists.txt:723–724`.

### 2.5 Why several build directories exist

The repo currently contains `build/`, `build-codex/`,
`build-codex-native/`, `build-codex-setup/`, `build-codex-setup2/`.
Plan 11 (build & runtime environment) explains the historical reason
for each; this walkthrough only notes that they coexist and that
`build-codex-setup2/` is the directory cited by `reconstruction.md`
example commands.

## 3. Entry point (src/main.cc, 376 lines)

### 3.1 Command-line interface

`main.cc:99–106` defines:

```
nnbar-detector-simulation [-m macro] [-u UIsession] [-t nThreads] [-g]
  -m macro     : batch mode with macro file
  -u session   : UI session type
  -t nThreads  : number of threads (1 = sequential)
  -g / --gun   : use particle gun instead of MCPL input
```

The `-g` flag flips a global `g_useParticleGun`
(`main.cc:67–68`, defined in `ActionInitialization.cc`). It can also
be flipped from a macro before `/run/initialize` via the pre-init
messenger at `main.cc:71–96` (`/generator/use_particle_gun`).

### 3.2 MCPL preflight

If `MCPL_BUILD=ON` and a macro is provided, `main.cc:117–166`
parses the macro looking for `/particle_generator/set_mcpl_file`. The
file path is resolved relative to the run directory, existence is
verified, and `G4MCPLGenerator::SetInputFile` is set *before*
`/run/initialize`. Failure modes:

- Macro missing the line → exit code 2.
- File path missing on disk → exit code 2.

This is a hard gate that prevents the simulation from starting an
MCPL-mode run without a usable input.

### 3.3 Run-manager construction

`main.cc:222–240`: `G4RunManagerFactory` chooses between the
default (multi-threaded) and serial run managers.
`-t 1` selects `G4RunManagerType::Serial`;
`-t N (N>1)` uses MT with `SetNumberOfThreads(N)`.

### 3.4 Physics list selection and Celeritas wiring

`main.cc:244–302`:

- `PhysicsList` (custom; see §4) is constructed first.
- Production-cut energy range is set to **1 keV–10 TeV**
  (`main.cc:249`). The comment notes the lower edge was raised from
  30 eV to avoid sub-keV particles with no meaningful physics.
- If `WITH_CELERITAS` is enabled at compile-time *and*
  `nnbar::CeleritasInterface::IsEnabled()` at run-time, Celeritas is
  initialised before any other registration:
  - `main.cc:261`: registers `celeritas::TrackingManagerConstructor`
    on the physics list.
  - `main.cc:268–293`: `SetupOptions` with
    `max_num_tracks = 64K`, `initializer_capacity = 1M`,
    `secondary_stack_factor = 3.0`, `auto_flush = 8K`, ignores
    `CoulombScat`, `UniformAlongStepFactory` (no field), SDs disabled
    (Celeritas SD callbacks crash with NNBAR's geometry), output
    file `celeritas.out.json`.
- If Celeritas is not active, the physics list is registered
  unmodified (`main.cc:301`).

### 3.5 Detector + actions registration

`main.cc:304–308`: `DetectorConstruction` and
`ActionInitialization` are registered, then `runManager->Initialize()`
at `main.cc:310`.

### 3.6 Visualisation and UI

`main.cc:313–367`:

- `G4VisExecutive` is initialised.
- If `WITH_DASHBOARD`, the Qt dock widgets are added to the G4UIQt
  main window (`main.cc:319–341`).
- Macro execution is delegated to the UI manager
  (`/control/execute <macro>`).
- Without a macro, the simulation enters interactive mode running
  `init_vis.mac` and (if GUI) `gui.mac`.

### 3.7 Globals

`main.cc:57–65` defines globals consumed elsewhere in the simulation:

- `event_number_global = 1`
- `run_number = 0`
- `theta_bin_index = 0`, `KE_bin_index = 0`, `particle_name_input = 0`
- `extern mcpl_outfile_t f` (MCPL output handle)

These cross-cutting globals are flagged as a future cleanup (plan 49
targeted improvements may revisit) but are unchanged at this baseline.

## 4. Physics list (src/core/PhysicsList.cc, 235 lines)

### 4.1 Constructor

`PhysicsList.cc:61–129`:

- `defaultCutValue = 0.7 mm` (line 63), then immediately
  re-assigned to `1.0 mm` (line 65). The 0.7 mm assignment is
  effectively dead code.
- `fConfig = G4LossTableManager::Instance()->EmConfigurator()`.
- `SetVerboseLevel(0)`.
- `ConstructParticle()` is called explicitly (line 68) before
  registering physics modules.

### 4.2 EM physics

`PhysicsList.cc:71–82`:

- If Celeritas is enabled at runtime, register
  `G4EmStandardPhysics()` (Celeritas-compatible).
- Otherwise register `G4EmStandardPhysics_option4()` (high accuracy).

### 4.3 Decay, hadronic, ions, neutrons, radioactive

`PhysicsList.cc:84–93`:

- `G4DecayPhysics`
- `G4HadronElasticPhysics`
- `G4HadronPhysicsFTFP_BERT` — comment at line 86: `_HP will slow
  down a lot` (so the **High-Precision** neutron physics is *not*
  used). This is a deliberate performance trade-off; plan 12 must
  audit the consequences for low-energy neutron transport in
  cosmic-neutron and beam-neutron samples.
- `G4StoppingPhysics`
- `G4IonPhysics`
- `G4NeutronTrackingCut`
- `G4RadioactiveDecayPhysics`
- `G4StepLimiterPhysics` (enables `G4UserLimits` per logical volume).

### 4.4 Optical physics

`PhysicsList.cc:97–128`:

- When `WITH_CELERITAS` and Celeritas is active, optical physics is
  *not* registered (Celeritas does not handle optical photons).
- Otherwise, gated by `WITH_SCINTILLATION` (compile-time):
  - `G4OpticalPhysics` is registered with parameters
    `WLSTimeProfile=delta`, `CerenkovMaxPhotonsPerStep=2000`,
    `CerenkovMaxBetaChange=100.0`,
    `CerenkovTrackSecondariesFirst=true`,
    `ScintTrackSecondariesFirst=true`.
- In `WITH_SCINTILLATION=OFF` builds (the current default), no
  optical photons are produced — this is the "fast mode" referred to
  in `reconstruction.md`. Plan 18 (intercalibration) audits the
  consequences for lead-glass and scintillator response.

### 4.5 Particles

`PhysicsList.cc:134–171`: constructs all bosons, leptons, mesons,
baryons, ions, short-lived particles. Optical-photon definition is
gated by Celeritas (omitted when active). Calls
`G4VModularPhysicsList::ConstructParticle()` at the end so that
`TrackingManagerConstructor` (Celeritas) can see and register against
all particles.

### 4.6 Cuts

`PhysicsList.cc:175–191`: `defaultCutValue` (1 mm) for gamma, e-,
e+, proton.

### 4.7 PAI model (dead but vendored)

`PhysicsList.cc:196–235`: `AddPAIModel()` and `NewPAIModel()` are
defined but not invoked from the constructor (the call at line 94 is
commented out). PAI for `e±`, `µ±`, `proton`/`π±` would be applied to
the `TPC_region` and `Silicon_region` if turned on. Plan 12 owns the
decision whether to enable PAI or supplement with a different
ionisation model.

## 5. Detector construction (src/core/DetectorConstruction.cc, 384 lines)

### 5.1 Materials

`DetectorConstruction.cc:96–113`:

- *Galactic vacuum* (used as the default world material)
  with refractive index 1 over [2.0, 7.0, 7.14] eV.
- *Carbon target* (custom): density 3.52 g/cm³ — graphite-like — built
  from one element of `C` (NIST). Used at the foil if
  `TARGET_BUILD=1`.

Other materials (gases, scintillator plastic, lead glass, beampipe
steel, silicon) are defined inside the per-subsystem geometry
builders (e.g. `src/detector/TPC_geometry.cc`,
`src/detector/Scintillator_geometry.cc`,
`src/detector/LeadGlass_geometry.cc`). Plan 10 (material budget)
enumerates the full material map; this walkthrough does not duplicate
that.

### 5.2 World volume

`DetectorConstruction.cc:122–125`: a `G4Box` of 20 m × 20 m × 450 m.
The deliberately long Z extent ("makes it longer because I don't want
to shift the coordinates", line 122) means primary positions and
detector elements share the simulation origin without translation.

`DetectorConstruction.cc:127–138`: a `G4LogicalSkinSurface` named
"LeadGlass" (the name is misleading — it is the *world* skin) wraps
the world LV with a non-reflective dielectric-metal optical surface.
Reflectivity and efficiency are zero across [2.0, 3.5] eV. This
absorbs optical photons that escape the world rather than letting
them re-enter sensitive volumes.

### 5.3 Carbon foil

`DetectorConstruction.cc:141–151`: `G4Cons` with inner radius 0,
outer radius 30 cm, half-length 0.01 cm (= 100 µm), full angular
coverage. Placed at the world origin. If `TARGET_BUILD=0`, the foil
is replaced by vacuum (line 146–148).

The foil is the antineutron annihilation target; the licentiate
Chapter 5 reports the foil dimensions, and plan 16 (geometry) verifies
this build matches the thesis specification.

### 5.4 Sub-detector builders

`DetectorConstruction.cc:154–184` constructs each sub-detector via a
dedicated builder class. The file-level forensic details are split so
this index stays below the 500-line cap.

| Builder | Source file | Detail file |
|---|---|---|
| `Beampipe` | `src/detector/beampipe_geometry.cc` | [`07_5_4_beampipe.md`](07_simulation_atomic_walkthrough/07_5_4_beampipe.md) |
| `Beampipe_Shielding` | `src/detector/beampipe_shielding_geometry.cc` | [`07_5_4_beampipe_shielding.md`](07_simulation_atomic_walkthrough/07_5_4_beampipe_shielding.md) |
| `Silicon` | `src/detector/Silicon_geometry.cc` | [`07_5_4_silicon.md`](07_simulation_atomic_walkthrough/07_5_4_silicon.md) |
| `TPC` | `src/detector/TPC_geometry.cc` | [`07_5_4_tpc.md`](07_simulation_atomic_walkthrough/07_5_4_tpc.md) |
| `Scintillator` | `src/detector/Scintillator_geometry.cc` | [`07_5_4_scintillator.md`](07_simulation_atomic_walkthrough/07_5_4_scintillator.md) |
| `LeadGlass` | `src/detector/LeadGlass_geometry.cc` | [`07_5_4_leadglass.md`](07_simulation_atomic_walkthrough/07_5_4_leadglass.md) |
| `CosmicShielding` | `src/detector/Cosmic_Shielding_geometry.cc` | [`07_5_4_cosmicshielding.md`](07_simulation_atomic_walkthrough/07_5_4_cosmicshielding.md) |

### 5.5 Geometry registration

See [`07_5_5_geometry_registration.md`](07_simulation_atomic_walkthrough/07_5_5_geometry_registration.md).

### 5.6 Sensitive detector and field assignment (`ConstructSDandField`)

See [`07_5_6_sd_and_field_assignment.md`](07_simulation_atomic_walkthrough/07_5_6_sd_and_field_assignment.md).

## 6. Sensitive detectors (src/sensitive/*.cc)

All sensitive detectors emit `NNbarHit` objects into per-event hit
collections that the `EventAction` then writes to parquet via
`ParquetOutputManager`. The SD body walkthroughs are split into one
file per active SD.

| Sensitive detector | Source file | Detail file | Status |
|---|---|---|---|
| `TPCSD` | `src/sensitive/TPCSD.cc` | [`07_6_2_tpcsd.md`](07_simulation_atomic_walkthrough/07_6_2_tpcsd.md) | detailed |
| `CarbonSD` | `src/sensitive/CarbonSD.cc` | [`07_6_2_carbonsd.md`](07_simulation_atomic_walkthrough/07_6_2_carbonsd.md) | pending |
| `SiliconSD` | `src/sensitive/SiliconSD.cc` | [`07_6_2_siliconsd.md`](07_simulation_atomic_walkthrough/07_6_2_siliconsd.md) | pending |
| `TubeSD` | `src/sensitive/TubeSD.cc` | [`07_6_2_tubesd.md`](07_simulation_atomic_walkthrough/07_6_2_tubesd.md) | pending |
| `ScintillatorSD` | `src/sensitive/ScintillatorSD.cc` | [`07_6_2_scintillatorsd.md`](07_simulation_atomic_walkthrough/07_6_2_scintillatorsd.md) | pending |
| `LeadGlassSD` | `src/sensitive/LeadGlassSD.cc` | [`07_6_2_leadglasssd.md`](07_simulation_atomic_walkthrough/07_6_2_leadglasssd.md) | pending |
| `PMTSD` | `src/sensitive/PMTSD.cc` | [`07_6_2_pmtsd.md`](07_simulation_atomic_walkthrough/07_6_2_pmtsd.md) | pending |

Present but unattached SD classes are tracked in
[`07_6_2_unattached_sensitive_detectors.md`](07_simulation_atomic_walkthrough/07_6_2_unattached_sensitive_detectors.md).
Truth-field semantics are tracked in
[`07_6_3_truth_content_per_hit.md`](07_simulation_atomic_walkthrough/07_6_3_truth_content_per_hit.md).

## 7. Remaining simulation surfaces

The remaining source-surface walkthroughs are split by section while
preserving the original section numbers.

| Section | Detail file |
|---|---|
| §7 `NNbarHit` class | [`07_7_hit_class.md`](07_simulation_atomic_walkthrough/07_7_hit_class.md) |
| §8 run and event actions | [`07_8_run_event_actions.md`](07_simulation_atomic_walkthrough/07_8_run_event_actions.md) |
| §9 output management | [`07_9_output_management.md`](07_simulation_atomic_walkthrough/07_9_output_management.md) |
| §10 primary generators | [`07_10_primary_generators.md`](07_simulation_atomic_walkthrough/07_10_primary_generators.md) |
| §11 GPU paths | [`07_11_gpu_paths.md`](07_simulation_atomic_walkthrough/07_11_gpu_paths.md) |
| §12 field model | [`07_12_field_model.md`](07_simulation_atomic_walkthrough/07_12_field_model.md) |
| §13 macros overview | [`07_13_macros.md`](07_simulation_atomic_walkthrough/07_13_macros.md) |
| §§14–18 limitations, acceptance, risks, dependencies, references | [`07_14_18_status_acceptance_risks.md`](07_simulation_atomic_walkthrough/07_14_18_status_acceptance_risks.md) |

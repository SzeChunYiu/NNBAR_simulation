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
dedicated builder class. Each `Construct_Volumes(worldLV)` call
returns a vector of `G4LogicalVolume*` that becomes the SD attachment
target later.

| Builder | Source file | Output vector |
|---|---|---|
| `Silicon` | `src/detector/Silicon_geometry.cc` | `Silicon_output` |
| `Beampipe` | `src/detector/beampipe_geometry.cc` | `Beampipe_output` |
| `TPC` | `src/detector/TPC_geometry.cc` | `TPC_output` |
| `Scintillator` | `src/detector/Scintillator_geometry.cc` | `Scintillator_output` |
| `LeadGlass` | `src/detector/LeadGlass_geometry.cc` | `LeadGlass_output` |
| `CosmicShielding` | `src/detector/Cosmic_Shielding_geometry.cc` | `CosmicShielding_output` |
| `Beampipe_Shielding` | `src/detector/beampipe_shielding_geometry.cc` | `Beampipe_Shielding_output` |

These vectors are file-scope globals declared at
`DetectorConstruction.cc:79–85`. Plan 16 documents each builder in
detail; the geometry audit
(`python -m nnbar_reconstruction.cli geometry-audit`) cross-checks
their construction against
`docs/Detector_Geometry_Reference.md`.

### 5.5 Geometry registration

`DetectorConstruction.cc:188–246`:

- `nnbar::GeometryManager::Instance().Initialize()` populates a
  volume-lookup database for visualisation.
- `RegisterTPCGeometry()` (lines 248–303) registers all 12 TPC
  modules with positions, sizes, and drift directions:
  - 6 *front* modules at `z = -TPC_z/2`
  - 6 *back* modules at `z = +TPC_z/2`
  - Each ring of 6 has 2 Type II (top + bottom) and 4 Type I
    (left × 2, right × 2)
  - Drift direction encoded as `(axis, sign)` per module: e.g. Type
    II top drifts `-Y`, Type I left-back drifts `+X`.
- `RegisterGeometryParameters()` (lines 200–246) caches frequently-
  used dimensions (beampipe radii, TPC half-Z, TPC type widths) into
  `nnbar::GeometryParameters`. The values are converted to centimetres
  for downstream consumers.

### 5.6 Sensitive detector and field assignment (`ConstructSDandField`)

`DetectorConstruction.cc:305–384`:

| Volume | Sensitive detector | Class |
|---|---|---|
| `CarbonLV` | `Carbon_Detector` (CarbonSD) | `CarbonSD` |
| `SiliconLV` (×n) | `siliconDetector` (SiliconSD) | `SiliconSD` |
| `BeampipeLV` (×n) | `tubeDetector` (TubeSD) | `TubeSD` |
| `TPCLV` (×12) | `TPCDetector` | `TPCSD` |
| `ScintLV` (×n) | `scintDetector` | `ScintillatorSD` |
| `LeadGlass_output[0]` | `LeadGlassDetector` | `LeadGlassSD` |
| `LeadGlass_output[1]` (PMT face) | `PMTDetector` | `PMTSD` |

Note: `ScintillatorSD` and `Scint_DetSD` both exist in the source
tree; the SD attached to the scintillator volumes is `ScintillatorSD`.
`Scint_DetSD` is reserved or unused — plan 14 (validation suite) flags
this for review. Similarly `ShieldSD` and `DetArea_SD` exist as files
but the active SD attachments here cover only Carbon, Silicon, Tube
(beampipe), TPC, Scintillator, LeadGlass, and PMT.

The TPC field manager (`DetectorConstruction.cc:354–382`) attaches a
`G4UniformElectricField`-like object via `util/ElectricField.cc` to
`TPC_output[0]` and `TPC_output[1]` (the first front-back pair of
front/back TPC mother volumes). Stepper:
`G4DormandPrince745` with 8 variables (E-field). `MinStep = 1 mm`,
`DeltaOneStep = 1 mm`, `LargestAcceptableStep = 1 cm`. Plan 17
audits whether this assignment covers all 12 modules
(it does not — only the first two LVs are field-managed; this is
a known limitation flagged in plan 17).

## 6. Sensitive detectors (src/sensitive/*.cc)

All sensitive detectors emit `NNbarHit` objects (§7) into per-event
hit collections that the `EventAction` then writes to parquet via
`ParquetOutputManager` (§9).

### 6.1 `TPCSD` (src/sensitive/TPCSD.cc, 170 lines)

- `Initialize` creates the `NNbarHitsCollection` for the event
  (`TPCSD.cc:42–43`).
- `ProcessHits` is invoked per Geant4 step.
  - Only `IsFirstStepInVolume()` and `IsLastStepInVolume()` are
    recorded (`TPCSD.cc:52`). All intermediate steps are dropped.
    This is a deliberate sparse representation that matches the
    "track entry/exit" geometry assumed by the offline vertexing
    (`reconstruction.py`).
  - Per recorded step, the hit fields are:
    - `name` = particle PDG name (line 130).
    - `trackID`, `parentID`, `process` (creator-process name; "primary"
      if `parentID == 0`) — lines 60–63.
    - `posX/Y/Z` = midpoint of pre/post-step position
      (lines 71–75; `mm`).
    - `time` = global track time in `ns` (line 79).
    - `kinEnergy` = mean of pre/post-step KE (lines 82–86).
    - `px/py/pz` = pre-step momentum direction (line 88).
    - `vol_name` = current volume; `origin_vol_name` = origin volume
      (lines 89–90).
    - `xHitID` = `replicaNumber(0)` = TPC layer index (line 94).
    - `module_ID` = `replicaNumber(1)` = TPC module index (line 95).
    - `stepInfo` = `1` if first step from outside, `0` otherwise,
      `999` if origin is `TPC_1_layer_PV` or `TPC_2_layer_PV`
      (lines 154–158).
    - `electrons` = Poisson-distributed integer with mean
      `eDep / (23.6 eV)` (lines 98–104). Stored in the `photons` field
      of `NNbarHit` because the field name is reused (line 149–150
      comment: *"too lazy to add one more function"*). Plan 12 must
      reconcile the **TPC W-value** with the broader Ar/CO₂ mixture
      reference value of 26–27.4 eV — the licentiate's
      validation discussion already flags this as a discrepancy
      (cf. `docs/detector_fundamental_question_tree.md` §3).
- Optical photons (`particleName == "opticalphoton"`) are dropped
  early (line 122–124).
- If `WITH_GARFIELD_GPU`, ionisation rows are pushed into
  `nnbar::TPCDriftManager` for later GPU drift simulation
  (lines 106–120).
- `EndOfEvent` adds the hit collection to the event's HC store
  (lines 164–169).

The TPC SD is the only SD that derives a primary observable
(electron count) at hit time. All other SDs record raw eDep and let
the offline pipeline (or the optical-photon tracker) translate.

### 6.2 Other sensitive detectors

The following SDs share the `NNbarHit` schema and the
"first/last step" convention. Each is briefly summarised here; plan 14
validation suite documents per-SD behaviour exhaustively.

- **`CarbonSD`** (`src/sensitive/CarbonSD.cc`): records hits inside
  the carbon foil. Tags annihilation products at production. Per-step
  pattern follows TPCSD without the electron-counting branch.
- **`SiliconSD`** (`src/sensitive/SiliconSD.cc`): records hits in any
  silicon volume (beampipe-5 and silicon module assemblies). No
  ionisation conversion.
- **`TubeSD`** (`src/sensitive/TubeSD.cc`): records hits anywhere in
  the beampipe LVs. Used to study beampipe-origin secondaries.
- **`ScintillatorSD`** (`src/sensitive/ScintillatorSD.cc`): records
  hits in the plastic scintillator. The class also computes a
  "photon-equivalent" count of `11136 photons/MeV` (cited in
  `reconstruction.md`); plan 18 audits this against the optical-table
  yield of `10000 photons/MeV` used when `WITH_SCINTILLATION` is on.
- **`LeadGlassSD`** (`src/sensitive/LeadGlassSD.cc`): records hits in
  the active lead-glass volume.
- **`PMTSD`** (`src/sensitive/PMTSD.cc`): records optical-photon hits
  in the PMT-face volume. Active only when `WITH_SCINTILLATION` (or
  Opticks) feeds it photons.
- **`Scint_DetSD`**, **`ShieldSD`**, **`DetArea_SD`**: present in the
  source tree but not attached in `ConstructSDandField`. Plan 14
  flags as candidates for retirement or revival.

### 6.3 Truth content per hit

Every recorded `NNbarHit` from every SD includes the *truth* fields
`name`, `trackID`, `parentID`, `process`, `origin_vol_name`. Per the
realism contract (plan 01), these are Class B columns: the
reconstruction must not consume them in its decision path. Plan 09
freezes their classification per parquet column.

## 7. Hit class (NNbarHit, include/hits/NNbarHit.hh, 158 lines)

`NNbarHit` is the universal hit object emitted by every SD. The class
exposes 30+ accessor pairs spanning particle identity, kinematics,
geometry indices, and SD-specific fields:

- *Particle identity*: `name`, `trackID`, `parentID`, `process`,
  `localTime`, `time`.
- *Position*: `posX`, `posY`, `posZ` (global midpoint);
  `posX_local`, `posY_local`, `posZ_local` (local frame, set by SDs
  that compute it); `posX_particle`, `posY_particle`, `posZ_particle`
  (particle production point).
- *Momentum direction*: `px`, `py`, `pz` (unit vector from
  pre-step momentum direction).
- *Energy*: `energyDeposit` (per step), `kinEnergy` (mean step KE).
- *Geometry indices*: `xHitID` (= layer / replica 0), `stave_ID_`,
  `group_ID_`, `module_ID_` (= replica 1 in TPC), `origin_rp` (origin
  region/plane).
- *SD-specific*: `photons` (TPC: electrons; scintillator: photons;
  semantic depends on SD; the field name is intentionally retained
  per `TPCSD.cc:149` comment).
- *Track length*: `TrackLength` (set from `aStep->GetStepLength()` in
  TPCSD).
- *Volume names*: `vol_name`, `origin_vol_name`.
- *Step info*: `step_info` (1 / 0 / 999 per TPCSD logic).

The `G4Allocator<NNbarHit>` pool is thread-local (lines 136, 139–155)
to support MT mode.

Plan 09 (data dictionary) maps each of these C++ fields to its
parquet output column name and unit, and assigns each to Class A / B / C.

## 8. Run and event actions

### 8.1 `RunAction` (src/core/RunAction.cc, ~12 KB)

(Read-target at `src/core/RunAction.cc`.) Key responsibilities:

- Open per-run parquet writers via `ParquetOutputManager` (§9) for
  every output stream the SDs feed.
- Set per-run RNG seed (Geant4 random-engine seed; pulled from
  `RNGWrapper` if used).
- Aggregate `NNbarRun` per-run accumulators (`src/hits/NNbarRun.cc`).
- Emit a per-run summary on `EndOfRun`.

The run number `run_number_global` (defined in `main.cc:59`) drives
the output-file naming convention `<TableName>_<run>.parquet`. Plan 47
run orchestration owns the seed-binding rule.

### 8.2 `EventAction` (src/core/EventAction.cc, 13.5 KB)

Key responsibilities:

- On `BeginOfEventAction`: increments `event_number_global`.
- On `EndOfEventAction`: pulls each SD's hit collection out of the
  `G4HCofThisEvent`, converts each `NNbarHit` to a parquet row, and
  appends to the appropriate writer.
- Records primary-particle truth into the `Particle` table.
- Records the Geant4 `Interaction` ancestry table (decay/process tree)
  for the event.

The exact column schema produced by `EventAction` per output file is
codified in plan 09. The event-action source is the *single* code
path that writes a thesis-quoted parquet column; any change to it
requires a paired plan-09 update and a DEC entry (plan 05).

### 8.3 `SteppingAction` (src/core/SteppingAction.cc, 6.9 KB)

Currently a thin wrapper used for diagnostic output and step-length
control. Plan 14 (validation suite) audits whether any step-level
filtering happens here that bypasses SD decisions.

### 8.4 `ActionInitialization` (src/core/ActionInitialization.cc)

Owns:

- `g_useParticleGun` global (`-g` flag toggle).
- Construction of `RunAction`, `EventAction`, `SteppingAction`,
  `PrimaryGeneratorAction`.
- MT-mode worker initialisation.

## 9. Output management (src/output/ParquetOutputManager.cc)

The parquet writer is the surface where Geant4 hits become offline
data. Each SD has a corresponding output stream:

| Output file pattern | Producer | Schema documented in |
|---|---|---|
| `Particle_output_<run>.parquet` | EventAction (truth primaries) | plan 09 |
| `Interaction_output_<run>.parquet` | EventAction (decay/process tree) | plan 09 |
| `Carbon_output_<run>.parquet` | CarbonSD via EventAction | plan 09 |
| `Silicon_output_<run>.parquet` | SiliconSD | plan 09 |
| `Beampipe_output_<run>.parquet` | TubeSD | plan 09 |
| `TPC_output_<run>.parquet` | TPCSD | plan 09 |
| `Scintillator_output_<run>.parquet` | ScintillatorSD | plan 09 |
| `LeadGlass_output_<run>.parquet` | LeadGlassSD | plan 09 |
| `PMT_output_<run>.parquet` | PMTSD | plan 09 |
| `GPUEnergy_output_<run>.parquet` | Celeritas calorimeters (`CeleritasCalorimeter`) | plan 09 |
| `Scintillator_Module_Position.txt` | Scintillator builder (per-module geometry) | plan 09 |

Schema discipline: every writer is configured at the top of
`ParquetOutputManager` against an explicit field list. Plan 09 freezes
the list. The writer wraps the vendored `parquet_writer` library at
`external/parquet-writer/src/cpp/`.

## 10. Primary generators

### 10.1 `PrimaryGeneratorAction` (src/core/PrimaryGeneratorAction.cc, 22 KB)

The largest non-geometry source file in the simulation. It supports
multiple primary-emission modes selected via the messenger
(`PrimaryGeneratorMessenger`, §10.2). Modes documented at
`reconstruction.md` and inferred from messenger commands:

- **Default GPS-style signal mode** (`MCPL_BUILD=OFF`, no `-g`
  override needed if MCPL is off). Emits a single primary per event
  per the kinematic distribution configured by macro commands
  (`/calibration/*`, `/source/*`).
- **Particle-gun mode** (`-g` or `/generator/use_particle_gun true`):
  emits a single primary at a fixed direction/energy.
- **MCPL mode** (`MCPL_BUILD=ON` or `/particle_generator/set_mcpl_file
  <path>`): reads primaries from a vendored MCPL file via
  `G4MCPLGenerator` (§10.3).
- **Calibration list / multi-primary mode**
  (`/calibration/signal_particles ...`): emits multiple named
  primaries from the same vertex, used by the
  `multiprimary_pion_proton_foil_stress.mac` study.

The action records primary truth (PDG name, momentum, position) into
the `Particle_output` table per event.

### 10.2 `PrimaryGeneratorMessenger` (src/core/PrimaryGeneratorMessenger.cc)

Defines the macro-command UI for the generator. Per `reconstruction.md`
and macro inspection, supported directories include:

- `/particle_generator/set_mcpl_file <path>` — set MCPL input.
- `/calibration/*` — calibration single-particle and multi-particle
  configurations (energy ranges, particle lists, vertex constraints).
- `/source/*` — beam-direction and beam-shape commands (when used).

The exact command tree is dumped by Geant4's `/help`; plan 10 (macro
inventory) documents which commands each macro file invokes.

### 10.3 `G4MCPLGenerator` (src/generator/G4MCPLGenerator.cc, 11.8 KB)

Wraps the MCPL C library to expose MCPL primaries to Geant4. Behaviour
is per the standard MCPL contract (one particle per record). Plan 17
(neutron-beam sample) and plan 21 (CRY cosmic sample) consume this
generator if the chosen integration path is "external generator → MCPL
→ Geant4".

### 10.4 `G4MCPLWriter` (src/generator/G4MCPLWriter.cc, 4.5 KB)

Writes primaries out as MCPL. Used when the simulation produces an
intermediate MCPL file (e.g. for cross-check between two physics-list
configurations).

## 11. GPU paths

All three GPU paths are off by default. They exist as opt-in
performance accelerators.

### 11.1 `TPCDriftGPU` (src/gpu/TPCDriftGPU.cc, 13.8 KB)

CUDA / OpenMP / single-threaded fallback for TPC electron drift. Fed
by `TPCSD::ProcessHits` (line 109) when `WITH_GARFIELD_GPU=ON`.
Produces a separate per-event drift output consumed by
`TPCDriftManager`. Plan 17 owns the drift-physics audit.

### 11.2 `OpticalPhotonGPU` (src/gpu/OpticalPhotonGPU.cc, 13.3 KB)

Standalone GPU optical-photon propagator, distinct from the Opticks
integration. Used as a fallback or comparator when Opticks is
unavailable.

### 11.3 `GPUManager` (src/gpu/GPUManager.cc, 10.4 KB)

Coordinates GPU resource ownership across the run. Decides which GPU
path is active per event based on compile-time flags and runtime
conditions (CUDA presence, memory).

### 11.4 Celeritas / Opticks (src/physics/*)

`src/physics/CeleritasInterface.cc`,
`src/physics/CeleritasCalorimeter.cc`,
`src/physics/OpticksInterface.cc` provide the optional GPU EM and
optical-photon offload. Behaviour is documented in the Celeritas /
Opticks upstream projects; plan 12 (physics-list audit) decides
whether to use them in production sample regeneration.

## 12. Field model

The TPC drift field is provided by `util/ElectricField.cc` and
attached only to `TPC_output[0]` and `TPC_output[1]`
(`DetectorConstruction.cc:380–381`). Other TPC modules currently
inherit the world's null field. Plan 17 (field calibration) treats
this as a known incompleteness to address before any quantitative
TPC-drift study.

There is no global magnetic field. The current Geant4 simulation does
not include a B-field for charge-sign determination — this is
limitation L9 in plan 01.

## 13. Macros (overview; full inventory in plan 10)

The macro tree contains:

- **Visualisation**: `gui.mac`, `init_vis.mac`, `vis.mac`,
  `opticks_test.mac`.
- **Quick smoke tests**: `quick_test.mac`, `test.mac`,
  `test_signal_quick.mac`.
- **Signal**: `macro/signal/run_signal.mac`,
  `macro/signal/run_signal_100k.mac`, with a `BeamOn.mac` driver.
- **Cosmics (current set)**: per-species (`cosmic_muon`,
  `cosmic_electron`, `cosmic_gamma`, `cosmic_neutron`, `cosmic_proton`,
  `cosmic_muon_short`), each with a per-run partition. Plan 21
  replaces these with a CRY-driven set.
- **Calibration**: lead-glass and scintillator electron/gamma/pion
  energy scans; π⁰ calibration. Plan 23 promotes these to the
  auxiliary calibration sample registry.
- **Studies (thesis-bound)**:
  `pi0_foil_mass.mac`, `pi0_foil_energy_scan.mac`,
  `charged_pion_proton_foil_stress.mac`,
  `multiprimary_pion_proton_foil_stress.mac`. These produce the
  parquet samples cited by `reconstruction.md` examples.
- **Legacy `macros/` (lower-level)**: `signal_pion_minus.mac`,
  `signal_pion_plus.mac`, `signal_proton.mac`,
  `background_compton.mac`. Plan 10 audits whether any of these are
  still consumed.

Plan 10 freezes the command-by-command inventory.

## 14. Limitations of this walkthrough

This v0.1 of plan 07 is a structural skeleton with cited file paths
and line numbers for the load-bearing components. The following deeper
sections are stubs that codex-supervisor will fill against this
plan's acceptance criteria:

- *§5.4 builder details.* Each of the seven sub-detector builders is
  several hundred lines (e.g. `Scintillator_geometry.cc` ≈ 34 KB,
  `beampipe_geometry.cc` ≈ 35 KB). Per-builder volumes, materials,
  and placements are deferred to plan 16.
- *§6.2 SD details.* Each non-TPC SD's `ProcessHits` body is short
  (≈ 4 KB on average) and follows the TPC pattern with minor variants;
  per-SD walkthroughs are deferred to plan 14.
- *§9 ParquetOutputManager schema.* The exact field list per parquet
  is the authority of plan 09; this plan only names the files.
- *§10.1 PrimaryGeneratorAction modes.* The 22 KB action source
  contains the mode dispatch logic; plan 18 (calibration samples) and
  plan 21 (cosmic) need to walk specific code paths for their work.

These deferrals are intentional: the structural skeleton is enough to
gate the dependent plans, and the deep dives have natural homes in the
plans that consume them.

## 15. Acceptance criteria

- §3, §4, §5, §6.1, §7 are complete (current draft).
- §5.4, §6.2, §10.1 are filled to the same depth as §6.1 by plan 16,
  plan 14, plan 21 respectively.
- A CI rule blocks PRs that touch `NNBAR_Detector/src/{core,detector,
  sensitive,hits,generator,output,physics,gpu,util}/*` without a
  matching edit to this file.
- Every output parquet file in §9 has its column schema in plan 09.
- Every `WITH_*` build option in §2.1 has an entry in plan 14
  validation suite covering the on/off difference.

## 16. Risks and mitigations

- *Risk:* this walkthrough rots silently when code changes land
  outside the CI rule's regex.
  *Mitigation:* the realism audit (plan 01) imports the file list
  this plan covers and emits a warning when a referenced symbol moves.
- *Risk:* duplicate authority with plan 09 (data dictionary) on
  output-parquet schema.
  *Mitigation:* §9 names the files only; column names, dtypes, units,
  and Class A/B/C live in plan 09. Each plan references the other.
- *Risk:* line numbers drift after refactors.
  *Mitigation:* plan 53 CI runs a "stale line number" linter that
  reports doc references to lines that no longer match the cited
  symbol.

## 17. Dependencies

- **00_README** — plan space.
- **01_realism_contract** — defines Class A/B/C; this walkthrough
  cites the contract for hit-field provenance.
- *Consumed by:* plan 09 (column schema), plan 10 (macros), plan 11
  (build env), plan 12 (physics list), plan 14 (validation), plan 16
  (geometry), plan 17 (field), plan 18 (intercalibration), plans 21,
  22, 23 (samples), plan 47 (reproduction ledger entries citing this
  plan as the simulation reference).

## 18. References

- `docs/detector_fundamental_question_tree.md` — the detector-side
  companion that motivated this rebuild.
- `NNBAR_Detector/docs/Detector_Geometry_Reference.md` — geometry
  reference text used by the geometry audit.
- `NNBAR_Detector/docs/reconstruction.md` — companion reference for
  what the reconstruction expects from this simulation.

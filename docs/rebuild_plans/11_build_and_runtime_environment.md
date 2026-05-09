---
id: 11_build_and_runtime_environment
title: Build and runtime environment — CMake, deps, Geant4, OS, libraries
version: 0.1
status: draft
owner: Sim Production
depends_on: [00_README, 07_simulation_atomic_walkthrough]
inputs:
  - {path: NNBAR_Detector/CMakeLists.txt, schema: build configuration}
  - {path: NNBAR_Detector/cmake/FetchDependencies.cmake, schema: external deps}
  - {path: NNBAR_Detector/external/, schema: vendored libraries}
  - {path: NNBAR_Detector/scripts/, schema: build/run scripts}
outputs:
  - {path: docs/rebuild_plans/11_build_and_runtime_environment.md, schema: this file}
acceptance:
  - {test: every WITH_* CMake option in plan 07 §2.1 has a §-entry, method: option ↔ doc cross-reference, pass_when: full coverage}
  - {test: every external dependency has a pinned version, method: lock-file presence, pass_when: zero unpinned deps}
  - {test: build-tree variants (build, build-codex, build-codex-native, build-codex-setup, build-codex-setup2) each have a status, method: dir-by-dir review, pass_when: zero "unknown" status}
risks:
  - {risk: silent Geant4 ABI break on minor-version bump, mitigation: §3 pin policy + plan 53 CI runs the smoke test on every Geant4 update}
  - {risk: CUDA/Opticks build paths rot from disuse, mitigation: §6 explicit disable + smoke build on CI when GPU runner available}
estimated_effort: M
last_updated: 2026-05-09
---

# Build and runtime environment

*Charter.* Forensic accounting of how the simulation builds, what it
links, and which build variants exist. This plan tells codex-supervisor
which build tree to use for which sample, which CMake options to set
for which study, and which environment to provision before running.

Every sample registered in plan 03 carries a `build_id`; this plan is
the reference that maps `build_id` → reproducible build configuration.

## 1. Build entry point

Top-level: `NNBAR_Detector/CMakeLists.txt` (920 lines, walked in plan
07 §2). Project name `nnbar-detector-simulation` v1.0.0; languages C
and C++; C++ standard 17; `CMAKE_EXPORT_COMPILE_COMMANDS=ON` for IDE
support (lines 14–19).

The build is invoked as:

```bash
cd NNBAR_Detector
cmake -S . -B build [-D<option>=<value> ...]
cmake --build build -j<N>
```

Per `CMakeLists.txt:820–823`, the documented next-step sequence is:

```bash
cmake --build . -- -j<N>
./nnbar-detector-simulation -m macro/signal/run_signal.mac
```

The build emits a wrapper script + `.bin` binary so the developer can
run without manually setting `LD_LIBRARY_PATH` or `DYLD_LIBRARY_PATH`
(plan 07 §2.3, `CMakeLists.txt:904–919`).

## 2. Configurable build options

Restated from plan 07 §2.1 with their defaults and impact:

| Option | Default | Effect | Sample-side impact |
|---|---|---|---|
| `WITH_GEANT4_UIVIS` | ON | UI/Vis support | None for batch; required for interactive use |
| `MCPL_BUILD` | OFF | Default ParticleGun. ON enables MCPL primary source by default | Cosmics + neutron beam (plans 21, 22) require MCPL or `-g/--gun` |
| `TARGET_BUILD` | ON | Carbon foil placed | OFF only for empty-detector cross-checks |
| `DEBUG_VERBOSE` | OFF | Verbose output | Never used in production samples |
| `WITH_SCINTILLATION` | OFF | Optical photons | Lead-glass / scintillator yield observables differ between on/off (plan 18) |
| `WITH_GARFIELD` | OFF | Garfield++ TPC | Not consumed by current production samples |
| `WITH_GARFIELD_GPU` | OFF | Custom CUDA/OpenMP TPC drift | Not consumed by current production samples |
| `WITH_CELERITAS` | OFF | GPU EM physics offload | When ON, EM eDep is recorded into `GPUEnergy_output_*.parquet` (plan 09 §12) |
| `WITH_OPTICKS` | OFF | GPU optical photons | When ON, the optical-photon path runs on GPU |
| `WITH_DASHBOARD` | OFF (auto-on if Qt found) | Qt monitoring GUI | Never required for batch samples |

Plan 47 reproduction ledger records the `(option, value)` set used for
each ledger row's sample.

## 3. Geant4 version pin

`CMakeLists.txt:196–202` requires `Geant4` (no minimum version
declared in the CMake itself — implicit minimum from API usage). Plan
07 confirmed Geant4 ≥ 11.0 via the Celeritas branch
(`CMakeLists.txt:312–328`).

Pin policy:

- *Production samples:* freeze the Geant4 version recorded in
  `data/registry/<id>/geant4_environment.txt`. A Geant4 upgrade
  produces a new dataset version (plan 03 §5).
- *Floor:* Geant4 11.0 (Celeritas requirement).
- *Ceiling:* Geant4 12.x is acceptable when Celeritas / Opticks
  catches up; until then the ceiling is the latest 11.x.

Codex-supervisor records `geant4-config --version` plus the
`G4DATADIR` of every data dataset (G4NDL for neutron HP, G4PHOTONEVAP,
G4LEND, G4EMLOW, etc.) at sample-freeze time. Different G4DATA
versions can change cross-sections; this is a real reproducibility
hazard.

## 4. External dependencies (FetchDependencies.cmake)

Pulled or vendored:

| Dependency | How | Version pin | Used by |
|---|---|---|---|
| Arrow / Parquet | FetchContent or system | latest stable matching parquet-writer | output (plan 09) |
| nlohmann_json | FetchContent | header-only, version pinned in CMake | configuration & decision-log mirroring |
| spdlog | FetchContent | header-only or shared lib | parquet-writer logging |
| MCPL | vendored at `external/mcpl/mcpl.c` | upstream snapshot | primary generator (plan 07 §10.3) |
| parquet-writer | vendored at `external/parquet-writer/src/cpp/` | upstream snapshot | output (plan 09) |
| ACTS | vendored at top-level `acts_tracking/` | not built by NNBAR CMake | reserved for plan 25 future tracking |

Plan 03 manifest records the SHA of each vendored snapshot and the
FetchContent commit hash for non-vendored deps. Hash drift forces a
new registered build_id.

## 5. Optional acceleration paths

### 5.1 Garfield++ (CMakeLists.txt:226–240)

Provides realistic TPC drift modelling. Enabled with
`WITH_GARFIELD=ON` plus a discoverable `Garfield_DIR` or
`GARFIELD_HOME`. Currently disabled in production samples.

### 5.2 GarfieldGPU (CMakeLists.txt:248–305)

Custom CUDA implementation (or OpenMP / single-threaded fallback).
Enabled with `WITH_GARFIELD_GPU=ON`. Auto-detects CUDA via
`check_language(CUDA)` and `find_package(CUDAToolkit)`. Hardcoded CUDA
paths preferred: `/usr/local/cuda-12.4` then `/usr/local/cuda`.

CUDA architecture targets default to `60;70;75;80;86`
(`CMakeLists.txt:660`). Plan 47 records the actual runtime GPU model
when this path is exercised.

### 5.3 Celeritas (CMakeLists.txt:310–331)

GPU EM physics. Requires Geant4 ≥ 11.0 and `find_package(Celeritas)`.
Run-time options configured in `main.cc:268–293` (plan 07 §3.4):
`max_num_tracks=64K`, `initializer_capacity=1M`, `auto_flush=8K`,
`ignore_processes={CoulombScat}`, `make_along_step=UniformAlongStep`.
SD callbacks are *disabled* (`opts.sd.enabled=false`,
`main.cc:287`) because they crash with NNBAR's geometry; instead a
parallel `CeleritasCalorimeter` records GPU eDep into
`GPUEnergy_output_*.parquet` (plan 09 §12).

### 5.4 Opticks (CMakeLists.txt:336–370)

GPU optical photon propagation. Requires `find_package(Opticks)` and
`OPTICKS_HOME`. Adds many include directories
(`G4CX`, `U4`, `CSGOptiX`, `CSG`, `SysRap`, `GDXML`, `QUDARap`, `glm`,
`plog`). Defines `NDEBUG` to silence Opticks's strict assertions.

### 5.5 Qt Dashboard (CMakeLists.txt:375–412)

Qt5 or Qt6 (Qt6 preferred). Auto-on when found. Adds
`AUTOMOC/AUTORCC/AUTOUIC` and explicitly MOC-wraps the dashboard
headers under `include/gui/`. Defines `WITH_DASHBOARD=1` to expose
`Q_OBJECT` macros.

## 6. Build-tree variants

The repository contains multiple build trees that have been used at
different points in the rebuild. Each carries a status:

| Build dir | Status | Purpose |
|---|---|---|
| `build/` | active | Default development build; current `nnbar-detector-simulation` binary |
| `build-codex/` | reference | Codex-spawned build, used for cross-comparison |
| `build-codex-native/` | reference | Native-architecture Codex build |
| `build-codex-setup/` | reference | Setup-tested Codex build |
| `build-codex-setup2/` | active (cited by reconstruction.md) | The build whose `output/` directory is the canonical sample location quoted in `reconstruction.md` examples (`build-codex-setup2/output`) |

The proliferation of build trees is a known symptom of rebuilds across
machines. Plan 52 (run orchestration) trims to a single canonical
build tree for production samples (`build-prod/`) once the rebuild
plan-set is signed off. Until then, this plan freezes the *meaning*
of each existing build dir.

## 7. Output and log directories

`CMakeLists.txt:723–724`:

```
${CMAKE_BINARY_DIR}/output/
${CMAKE_BINARY_DIR}/log/
```

Both are created at configure time. Sample parquets land under
`output/`; per-run logs (Geant4 stdout/stderr if redirected) under
`log/`.

For studies, the path becomes
`<build>/output/studies/<study_name>/` per the macros in plan 10
§1.5.

## 8. Wrapper script (scripts/wrapper_template.sh.in)

Generated at build time into `<build>/nnbar-detector-simulation`.
Sets the appropriate `LD_LIBRARY_PATH` (Linux) or `DYLD_LIBRARY_PATH`
(macOS) and execs `nnbar-detector-simulation.bin`.

The library-path list is auto-built at CMake configure
(`CMakeLists.txt:846–895`) from:

- Geant4 install prefix (resolved from `Geant4_DIR`).
- Celeritas install prefix (when found).
- Opticks install prefix (when found).
- Arrow / Parquet / spdlog package install prefixes.
- Vendored Arrow install at `external/arrow-install/lib`.
- Linux-only: `external/arrow-install-linux/lib`,
  `external/spdlog-install-linux/lib`,
  `/usr/local/cuda-12.4/lib64`,
  `/usr/lib/x86_64-linux-gnu`.

Plan 52 (orchestration) freezes the chosen prefix set per cluster.

## 9. Python environment (reconstruction side)

Reconstruction uses Python 3.11+ (per `.cpython-313` cache files
present in source tree). Required packages:

- `pyarrow` (parquet I/O)
- `pandas` (data manipulation)
- `numpy`
- `pytest` (test suite, `pytest.ini`)
- (optional) `pyhf`, `scipy`, `matplotlib`, `sklearn` for analysis-side
  plans (45, 41, 57)

Plan 53 (CI) freezes the exact `requirements.txt` for the
reconstruction side. Codex-supervisor checks the lock file in CI; a
package version bump triggers a full reconstruction-side regression
test.

The Python interpreter that the user reports working is
`/Users/billy/miniforge3/bin/python` (per
`docs/detector_fundamental_question_tree.md` §evidence). On LUNARC,
codex-supervisor uses the cluster module-resolved `python3.11`
(plan 52).

## 10. OS targets

Production targets:

- *Development:* macOS Darwin 25.4.0 (current host), Apple Silicon.
- *Production batch:* LUNARC SLURM cluster (Linux x86_64) — per
  `cluster-status` skill in the user's environment.
- *CI:* GitHub Actions Linux runners or local Docker — owned by plan
  53.

Linux-only RPATH dance at `CMakeLists.txt:67–69`
(`-Wl,--disable-new-dtags`) and the
Linux-specific library-path block at `CMakeLists.txt:875–886`.

macOS compatibility: `DYLD_LIBRARY_PATH` set via wrapper script
(`CMakeLists.txt:889–895`); MCPL and parquet-writer build cleanly on
Apple Silicon.

## 11. Common environment-setup pitfalls

(Forensic — these are the failure modes codex-supervisor must
recognise rather than retry blindly.)

- *Geant4 data env vars unset.* `G4NEUTRONHPDATA`, `G4LEDATA`,
  `G4LEVELGAMMADATA`, `G4PARTICLEXSDATA`, `G4SAIDXSDATA`,
  `G4ENSDFSTATEDATA` must point to the matching G4DATA install.
  Plan 03 manifest records the resolved paths.
- *Celeritas / Geant4 version skew.* `Celeritas` package built against
  one Geant4 minor version, the wrapper linking against another →
  silent ABI breakage. Plan 53 CI explicitly checks
  `geant4-config --version` and `pkg-config --modversion celeritas`
  match the recorded build.
- *macOS AppleDouble files.* Files prefixed `._<name>` exist
  throughout the source tree. The realism audit (plan 01) and the
  parquet reader (plan 08 §2) ignore them; the build's `file(GLOB
  SOURCES …)` filters them with `list(FILTER ... EXCLUDE REGEX
  "/\\._")` (`CMakeLists.txt:515`).
- *MCPL preflight failure.* `MCPL_BUILD=ON` plus a macro lacking
  `/particle_generator/set_mcpl_file` exits with code 2
  (`main.cc:117–166`). Codex-supervisor catches this early.
- *RPATH not picked up on Linux.* Without
  `--disable-new-dtags`, `RUNPATH` is used and `LD_LIBRARY_PATH`
  takes precedence — surprising behaviour during cross-host runs.
  The CMakeLists already sets the correct flag for non-Apple
  builds.

## 12. Reproducible build recipe (provisional)

For a clean reproducible build of the current `main`:

```bash
cd NNBAR_Detector
cmake -S . -B build-prod \
    -DCMAKE_BUILD_TYPE=RelWithDebInfo \
    -DWITH_SCINTILLATION=OFF \
    -DWITH_GARFIELD=OFF \
    -DWITH_GARFIELD_GPU=OFF \
    -DWITH_CELERITAS=OFF \
    -DWITH_OPTICKS=OFF \
    -DWITH_DASHBOARD=OFF \
    -DMCPL_BUILD=OFF \
    -DTARGET_BUILD=ON
cmake --build build-prod -j$(nproc)
```

This produces a CPU-only, fast-mode build (no optical photons) that
matches the licentiate's default sample configuration. Plan 47
records this exact recipe alongside any Geant4 / dependency hashes.

For optical-mode runs (lead-glass calibration, plan 18):

```bash
cmake -S . -B build-optical \
    -DWITH_SCINTILLATION=ON \
    [other flags as above]
```

For Celeritas + Opticks (when GPU available):

```bash
cmake -S . -B build-gpu \
    -DWITH_CELERITAS=ON \
    -DWITH_OPTICKS=ON \
    [other flags as above]
```

## 13. Acceptance criteria

- §6 lists every existing build directory with a status. New build
  directories must be added to §6 before merging.
- §3 records the exact Geant4 version pin used for the next
  thesis-quoted sample regeneration (plan 20–23).
- §4 lists every vendored / fetched dependency with a hash or version
  pin.
- §12 reproducible recipe runs green on a fresh checkout of the
  current `main` (plan 53 CI).
- The Python `requirements.txt` for reconstruction is committed and
  pinned.

## 14. Risks and mitigations

- *Risk:* Geant4 minor-version upgrade (e.g. 11.2 → 11.3) breaks
  Celeritas linkage silently.
  *Mitigation:* §3 pin policy + plan 53 CI runs the smoke build for
  every Celeritas/Geant4 combination registered.
- *Risk:* `build-codex-setup2/output/` is referenced by external
  documentation (`reconstruction.md`) — moving the canonical sample
  path breaks doc links.
  *Mitigation:* §6 retains the directory's status as
  *active (cited)* until plan 47 completes its first ledger pass and
  rewrites the doc-side citations.
- *Risk:* CUDA toolkit version mismatch between development laptop
  and LUNARC cluster.
  *Mitigation:* §10 explicit OS targets; §5.2 records both
  CUDA-12.4 and the cluster-resolved version in the manifest.

## 15. Dependencies

- **00_README** — plan space.
- **07_simulation_atomic_walkthrough** — §2 of plan 07 walks the
  CMake; this plan adds operational detail.
- *Consumed by:* plan 03 manifest fields (`geant4_version`,
  `physics_list`, `build_id`); plan 47 ledger; plan 52 orchestration;
  plan 53 CI.

## 16. References

- `NNBAR_Detector/CMakeLists.txt` — primary source.
- `NNBAR_Detector/cmake/FetchDependencies.cmake` — dependency
  resolution.
- `NNBAR_Detector/scripts/wrapper_template.sh.in` — wrapper template.
- `cluster-status` skill (Claude Code skill) — LUNARC interaction.

---
id: 10_macro_and_sample_inventory
title: Macro and sample inventory — every macro, every command, every output
version: 0.1
status: draft
owner: Sim Production
depends_on: [00_README, 03_dataset_registry, 07_simulation_atomic_walkthrough, 08_reconstruction_atomic_walkthrough]
inputs:
  - {path: NNBAR_Detector/macro/, schema: Geant4 macro tree}
  - {path: NNBAR_Detector/macros/, schema: legacy macro tree}
  - {path: NNBAR_Detector/macro/calibration/, schema: calibration macros}
outputs:
  - {path: docs/rebuild_plans/10_macro_and_sample_inventory.md, schema: this file}
  - {path: data/registry/datasets.yml, schema: registered samples (plan 03)}
acceptance:
  - {test: every .mac in NNBAR_Detector/macro/ and macros/ has a § entry, method: file scan, pass_when: zero unmatched}
  - {test: every CLI invocation in reconstruction.md examples maps to a § entry, method: cross-reference, pass_when: zero unmatched}
  - {test: every macro produces a sample whose registry entry exists, method: ID lookup, pass_when: zero missing}
risks:
  - {risk: macros proliferate during studies and inventory rots, mitigation: plan 53 CI flags new .mac files lacking an entry here}
  - {risk: legacy macros under macros/ are orphaned, mitigation: §8 explicitly status-tags each as active/legacy/retired}
estimated_effort: M
last_updated: 2026-05-09
---

# Macro and sample inventory

*Charter.* Authoritative list of every macro and every CLI command
currently in the simulation and reconstruction. Each entry: purpose,
invocation, output file pattern, sample size, registry status. This
plan is the bridge between the source code (plans 07, 08) and the
samples (plans 20–23) — it tells codex-supervisor exactly which
existing artifact to consume or replace.

## 1. Macro tree under NNBAR_Detector/macro/

### 1.1 Visualisation and quick-test macros

| Macro | Purpose | Status |
|---|---|---|
| `gui.mac` | GUI session boilerplate (top-level) | active |
| `init_vis.mac` | Visualisation initialiser (top-level) | active |
| `vis.mac` | Visualisation default (top-level) | active |
| `macro/quick_test.mac` | Smoke test, ~few events | active |
| `macro/test.mac` | Generic test driver | active |
| `macro/test_signal_quick.mac` | Quick signal smoke test | active |
| `macro/opticks_test.mac` | Opticks GPU optical-photon path test | active when `WITH_OPTICKS=ON` |

### 1.2 Signal macros (macro/signal/)

| Macro | Purpose | Key commands invoked | Output / sample target | Status |
|---|---|---|---|---|
| `macro/signal/run_signal.mac` | HIBEAM-filtered n̄ signal MCPL replay into the full detector | `/run/initialize`; `/physics_engine/neutron/timeLimit 10000 s`; `/particle_generator/set_folder_name signal`; `/particle_generator/set_mcpl_file ./mcpl_files/NNBAR_mfro_signal_GBL_jbar_50k_9001_HIBEAM_filtered.mcpl`; `/particle_generator/set_run_number 0`; `/particle_generator/set_event_number 1`; `/control/loop ./macro/signal/BeamOn.mac a 0 49 1` | `output/signal/*_output_<run>.parquet`; 50 looped `beamOn 1000` batches from the 50k-event signal MCPL | active |
| `macro/signal/BeamOn.mac` | Shared signal batch primitive called by `run_signal.mac` | `/run/beamOn 1000` | Emits the caller-selected output folder/run; not a standalone sample definition | active |

These macros are the source of the antineutron annihilation samples
referenced by the licentiate Chapters 5–10. Plan 20 (signal sample)
replaces them with a registered, hash-sealed regenerator. No
`macro/signal/run_signal_100k.mac` exists in the current macro tree;
if a 100k variant is required it must be restored as a new registered
dataset rather than assumed present.

### 1.3 Cosmic macros (macro/cosmic_macro/)

Per-species, per-run partition. Each `cosmic_<species>/` directory
contains a `BeamOn.mac` and per-run `run_<n>.mac` files.

| Sub-tree | Species | Notes |
|---|---|---|
| `macro/cosmic_macro/cosmic_muon/run_{0..5}.mac` | µ± | 6 partitions |
| `macro/cosmic_macro/cosmic_muon_short/run_muon_{0..5}.mac` | µ± (short version) | 6 partitions + `run_all.mac` |
| `macro/cosmic_macro/cosmic_electron/run_{0..5}.mac` | e± | 6 partitions |
| `macro/cosmic_macro/cosmic_gamma/run_{0..5}.mac` | γ | 6 partitions |
| `macro/cosmic_macro/cosmic_neutron/run_{0..5}.mac` | n | 6 partitions |
| `macro/cosmic_macro/cosmic_proton/run_{0..5}.mac` | p | 6 partitions |
| `macro/cosmic_macro/test_macro/cosmic_simulation.mac` | smoke test | verification driver |

#### 1.3.1 `macro/cosmic_macro/cosmic_electron/`

| Macro | Purpose | Key commands invoked | Output / sample target | Status |
|---|---|---|---|---|
| `macro/cosmic_macro/cosmic_electron/BeamOn.mac` | Shared electron-cosmic batch primitive | `/run/beamOn 1000` | Caller-selected `output/cosmic_electron/cosmic_electron_<i>/*_output_<run>.parquet` | legacy |
| `macro/cosmic_macro/cosmic_electron/run_0.mac` | Electron-cosmic MCPL partition 0 replay | `/run/initialize`; `/physics_engine/neutron/timeLimit 10000 s`; `/particle_generator/set_folder_name cosmic_{name}/cosmic_{name}_{i}`; `/particle_generator/set_mcpl_file ./mcpl_files/cosmic_{name}_{i}.mcpl`; `/particle_generator/set_run_number 0`; `/particle_generator/set_event_number 1`; `/control/loop ./macro/cosmic_macro/cosmic_gamma/BeamOn.mac a 0 999 1` | `output/cosmic_electron/cosmic_electron_0/*_output_<run>.parquet`; target 1000 × `beamOn 1000` from `cosmic_electron_0.mcpl` | legacy |
| `macro/cosmic_macro/cosmic_electron/run_1.mac` | Electron-cosmic MCPL partition 1 replay | same as `run_0.mac` with `i=1` | `output/cosmic_electron/cosmic_electron_1/*_output_<run>.parquet`; target 1M events from `cosmic_electron_1.mcpl` | legacy |
| `macro/cosmic_macro/cosmic_electron/run_2.mac` | Electron-cosmic MCPL partition 2 replay | same as `run_0.mac` with `i=2` | `output/cosmic_electron/cosmic_electron_2/*_output_<run>.parquet`; target 1M events from `cosmic_electron_2.mcpl` | legacy |
| `macro/cosmic_macro/cosmic_electron/run_3.mac` | Electron-cosmic MCPL partition 3 replay | same as `run_0.mac` with `i=3` | `output/cosmic_electron/cosmic_electron_3/*_output_<run>.parquet`; target 1M events from `cosmic_electron_3.mcpl` | legacy |
| `macro/cosmic_macro/cosmic_electron/run_4.mac` | Electron-cosmic MCPL partition 4 replay | same as `run_0.mac` with `i=4` | `output/cosmic_electron/cosmic_electron_4/*_output_<run>.parquet`; target 1M events from `cosmic_electron_4.mcpl` | legacy |
| `macro/cosmic_macro/cosmic_electron/run_5.mac` | Electron-cosmic MCPL partition 5 replay | same as `run_0.mac` with `i=5` | `output/cosmic_electron/cosmic_electron_5/*_output_<run>.parquet`; target 1M events from `cosmic_electron_5.mcpl` | legacy |

The electron partition macros currently call the `cosmic_gamma/BeamOn.mac`
helper; that helper is a one-line `/run/beamOn 1000` wrapper, so the
status remains legacy rather than retired. Plan 21 replaces all per-species
cosmic MCPL replays with a CRY-driven active sample path.

#### 1.3.2 `macro/cosmic_macro/cosmic_gamma/`

| Macro | Purpose | Key commands invoked | Output / sample target | Status |
|---|---|---|---|---|
| `macro/cosmic_macro/cosmic_gamma/BeamOn.mac` | Shared gamma-cosmic batch primitive | `/run/beamOn 1000` | Caller-selected `output/cosmic_gamma/cosmic_gamma_<i>/*_output_<run>.parquet` | legacy |
| `macro/cosmic_macro/cosmic_gamma/run_0.mac` | Gamma-cosmic MCPL partition 0 replay | `/run/initialize`; `/physics_engine/neutron/timeLimit 10000 s`; `/particle_generator/set_folder_name cosmic_{name}/cosmic_{name}_{i}`; `/particle_generator/set_mcpl_file ./mcpl_files/cosmic_{name}_{i}.mcpl`; `/particle_generator/set_run_number 0`; `/particle_generator/set_event_number 1`; `/control/loop ./macro/cosmic_macro/cosmic_gamma/BeamOn.mac a 0 999 1` | `output/cosmic_gamma/cosmic_gamma_0/*_output_<run>.parquet`; target 1000 × `beamOn 1000` from `cosmic_gamma_0.mcpl` | legacy |
| `macro/cosmic_macro/cosmic_gamma/run_1.mac` | Gamma-cosmic MCPL partition 1 replay | same as `run_0.mac` with `i=1` | `output/cosmic_gamma/cosmic_gamma_1/*_output_<run>.parquet`; target 1M events from `cosmic_gamma_1.mcpl` | legacy |
| `macro/cosmic_macro/cosmic_gamma/run_2.mac` | Gamma-cosmic MCPL partition 2 replay | same as `run_0.mac` with `i=2` | `output/cosmic_gamma/cosmic_gamma_2/*_output_<run>.parquet`; target 1M events from `cosmic_gamma_2.mcpl` | legacy |
| `macro/cosmic_macro/cosmic_gamma/run_3.mac` | Gamma-cosmic MCPL partition 3 replay | same as `run_0.mac` with `i=3` | `output/cosmic_gamma/cosmic_gamma_3/*_output_<run>.parquet`; target 1M events from `cosmic_gamma_3.mcpl` | legacy |
| `macro/cosmic_macro/cosmic_gamma/run_4.mac` | Gamma-cosmic MCPL partition 4 replay | same as `run_0.mac` with `i=4` | `output/cosmic_gamma/cosmic_gamma_4/*_output_<run>.parquet`; target 1M events from `cosmic_gamma_4.mcpl` | legacy |
| `macro/cosmic_macro/cosmic_gamma/run_5.mac` | Gamma-cosmic MCPL partition 5 replay | same as `run_0.mac` with `i=5` | `output/cosmic_gamma/cosmic_gamma_5/*_output_<run>.parquet`; target 1M events from `cosmic_gamma_5.mcpl` | legacy |

#### 1.3.3 `macro/cosmic_macro/cosmic_muon/`

| Macro | Purpose | Key commands invoked | Output / sample target | Status |
|---|---|---|---|---|
| `macro/cosmic_macro/cosmic_muon/BeamOn.mac` | Shared muon-cosmic batch primitive | `/run/beamOn 1000` | Caller-selected `output/cosmic_muon/cosmic_muon_<i>/*_output_<run>.parquet` | legacy |
| `macro/cosmic_macro/cosmic_muon/run_0.mac` | Muon-cosmic MCPL partition 0 replay | `/run/initialize`; `/physics_engine/neutron/timeLimit 10000 s`; `/particle_generator/set_folder_name cosmic_{name}/cosmic_{name}_{i}`; `/particle_generator/set_mcpl_file ./mcpl_files/cosmic_{name}_{i}.mcpl`; `/particle_generator/set_run_number 0`; `/particle_generator/set_event_number 1`; `/control/loop ./macro/cosmic_macro/cosmic_muon/BeamOn.mac a 0 999 1` | `output/cosmic_muon/cosmic_muon_0/*_output_<run>.parquet`; target 1000 × `beamOn 1000` from `cosmic_muon_0.mcpl` | legacy |
| `macro/cosmic_macro/cosmic_muon/run_1.mac` | Muon-cosmic MCPL partition 1 replay | same as `run_0.mac` with `i=1` | `output/cosmic_muon/cosmic_muon_1/*_output_<run>.parquet`; target 1M events from `cosmic_muon_1.mcpl` | legacy |
| `macro/cosmic_macro/cosmic_muon/run_2.mac` | Muon-cosmic MCPL partition 2 replay | same as `run_0.mac` with `i=2` | `output/cosmic_muon/cosmic_muon_2/*_output_<run>.parquet`; target 1M events from `cosmic_muon_2.mcpl` | legacy |
| `macro/cosmic_macro/cosmic_muon/run_3.mac` | Muon-cosmic MCPL partition 3 replay | same as `run_0.mac` with `i=3` | `output/cosmic_muon/cosmic_muon_3/*_output_<run>.parquet`; target 1M events from `cosmic_muon_3.mcpl` | legacy |
| `macro/cosmic_macro/cosmic_muon/run_4.mac` | Muon-cosmic MCPL partition 4 replay | same as `run_0.mac` with `i=4` | `output/cosmic_muon/cosmic_muon_4/*_output_<run>.parquet`; target 1M events from `cosmic_muon_4.mcpl` | legacy |
| `macro/cosmic_macro/cosmic_muon/run_5.mac` | Muon-cosmic MCPL partition 5 replay | same as `run_0.mac` with `i=5` | `output/cosmic_muon/cosmic_muon_5/*_output_<run>.parquet`; target 1M events from `cosmic_muon_5.mcpl` | legacy |

#### 1.3.4 `macro/cosmic_macro/cosmic_neutron/`

| Macro | Purpose | Key commands invoked | Output / sample target | Status |
|---|---|---|---|---|
| `macro/cosmic_macro/cosmic_neutron/BeamOn.mac` | Shared neutron-cosmic batch primitive | `/run/beamOn 1000` | Caller-selected `output/cosmic_neutron/cosmic_neutron_<i>/*_output_<run>.parquet` | legacy |
| `macro/cosmic_macro/cosmic_neutron/run_0.mac` | Neutron-cosmic MCPL partition 0 replay | `/run/initialize`; `/physics_engine/neutron/timeLimit 10000 s`; `/particle_generator/set_folder_name cosmic_{name}/cosmic_{name}_{i}`; `/particle_generator/set_mcpl_file ./mcpl_files/cosmic_{name}_{i}.mcpl`; `/particle_generator/set_run_number 0`; `/particle_generator/set_event_number 1`; `/control/loop ./macro/cosmic_macro/cosmic_gamma/BeamOn.mac a 0 999 1` | `output/cosmic_neutron/cosmic_neutron_0/*_output_<run>.parquet`; target 1000 × `beamOn 1000` from `cosmic_neutron_0.mcpl` | legacy |
| `macro/cosmic_macro/cosmic_neutron/run_1.mac` | Neutron-cosmic MCPL partition 1 replay | same as `run_0.mac` with `i=1` | `output/cosmic_neutron/cosmic_neutron_1/*_output_<run>.parquet`; target 1M events from `cosmic_neutron_1.mcpl` | legacy |
| `macro/cosmic_macro/cosmic_neutron/run_2.mac` | Neutron-cosmic MCPL partition 2 replay | same as `run_0.mac` with `i=2` | `output/cosmic_neutron/cosmic_neutron_2/*_output_<run>.parquet`; target 1M events from `cosmic_neutron_2.mcpl` | legacy |
| `macro/cosmic_macro/cosmic_neutron/run_3.mac` | Neutron-cosmic MCPL partition 3 replay | same as `run_0.mac` with `i=3` | `output/cosmic_neutron/cosmic_neutron_3/*_output_<run>.parquet`; target 1M events from `cosmic_neutron_3.mcpl` | legacy |
| `macro/cosmic_macro/cosmic_neutron/run_4.mac` | Neutron-cosmic MCPL partition 4 replay | same as `run_0.mac` with `i=4` | `output/cosmic_neutron/cosmic_neutron_4/*_output_<run>.parquet`; target 1M events from `cosmic_neutron_4.mcpl` | legacy |
| `macro/cosmic_macro/cosmic_neutron/run_5.mac` | Neutron-cosmic MCPL partition 5 replay | same as `run_0.mac` with `i=5` | `output/cosmic_neutron/cosmic_neutron_5/*_output_<run>.parquet`; target 1M events from `cosmic_neutron_5.mcpl` | legacy |

The neutron partition macros call the `cosmic_gamma/BeamOn.mac` helper;
that helper is still only `/run/beamOn 1000`, so the macros are legacy
replay definitions rather than broken/retired macros.

These per-species macros use Geant4 GPS-style cosmic-like primaries
*without* a true atmospheric spectrum source. They are the licentiate
baseline; **plan 21 retires them** and replaces them with a single
CRY-driven generator that samples the actual atmospheric flux. The
six runs in each per-species directory are the partitioning the
licentiate used for batch processing on LUNARC.

Status tag for codex-supervisor: `legacy`. They remain runnable for
back-compatibility with thesis Chapter 6 reproduction (plan 47), but
all *new* cosmic samples come from plan 21.

### 1.4 Calibration macros (macro/calibration/)

| Macro | Purpose | Sample target |
|---|---|---|
| `macro/calibration/calib_quick_leadglass.mac` | quick lead-glass calibration smoke | smoke / fast feedback |
| `macro/calibration/calib_quick_scintillator.mac` | quick scintillator calibration smoke | smoke |
| `macro/calibration/gamma_energy_scan_full.mac` | gamma energy scan full | calibration anchor for lead glass |
| `macro/calibration/leadglass/calib_electron_validation.mac` | electron beam at lead glass | calibration cross-check |
| `macro/calibration/leadglass/calib_gamma_all_surfaces.mac` | gamma at every face | acceptance map |
| `macro/calibration/leadglass/calib_gamma_energy_scan.mac` | per-energy gamma scan | calibration curve |
| `macro/calibration/pi0_calib.mac` | π⁰ calibration | π⁰ peak shape |
| `macro/calibration/run_all_calibrations.mac` | umbrella runner | wraps the others |
| `macro/calibration/scintillator/calib_pion_energy_scan.mac` | pion at scintillator energy scan | scintillator calibration |
| `macro/calibration/scintillator/calib_pion_minus.mac` | π- at scintillator | calibration cross-check |
| `macro/calibration/scintillator/calib_pion_mip.mac` | π MIP response | MIP calibration anchor |

Status: `active`, subject to plan 18 (intercalibration) review. Plan 23
(auxiliary calibration samples) consumes this set as the seed for the
registered single-particle calibration registry.

### 1.5 Studies (macro/studies/) — thesis-bound

| Macro | Purpose | Cited from |
|---|---|---|
| `macro/studies/pi0_foil_mass.mac` | π⁰ at foil, mass scan | reconstruction.md §pi0-study examples |
| `macro/studies/pi0_foil_energy_scan.mac` | π⁰ at foil, energy scan | reconstruction.md §pi0_foil_500mev path |
| `macro/studies/charged_pion_proton_foil_stress.mac` | charged π/p stress at foil | reconstruction.md lines 270–319 |
| `macro/studies/multiprimary_pion_proton_foil_stress.mac` | multi-primary topology | reconstruction.md lines 280–299 |

Status: `active`. These are the macros reconstruction.md lists as
example commands; they are the load-bearing studies for plans 28, 29,
33, 34. Plan 20 elevates each to a registered dataset (plan 03 freeze).

### 1.6 Legacy macros (macros/, lower-level)

| Macro | Purpose | Status |
|---|---|---|
| `macros/background_compton.mac` | Compton background sample | needs status review |
| `macros/signal_pion_minus.mac` | π- single-primary signal | legacy; replaced by `studies/charged_pion_proton_foil_stress.mac` |
| `macros/signal_pion_plus.mac` | π+ single-primary signal | legacy |
| `macros/signal_proton.mac` | p single-primary signal | legacy |

Codex-supervisor reviews the legacy set during plan 23 and either
promotes them into the calibration sample registry or retires them
with a DEC entry (plan 05).

## 2. Recurring macro-command syntax

Per `reconstruction.md` and the source-code messengers (plan 07
§10.2), macros use these directories. Codex-supervisor freezes the
exact command tree by running the simulation in interactive mode and
dumping `/help`; this v0.1 lists the commands actually invoked by
the macros above.

### 2.1 Run control

- `/run/initialize`
- `/run/beamOn <N>` — driver for sample-size selection.

### 2.2 Particle generator selection

- `/generator/use_particle_gun <true|false>` — pre-init only;
  matches `main.cc:71–96`.
- `/particle_generator/set_mcpl_file <path>` — only used in MCPL builds
  (plan 07 §3.2 preflight).

### 2.3 Calibration / signal kinematics

(From `reconstruction.md` and macro inspection — exact list pending
codex-supervisor verification:)

- `/calibration/signal_particles <list>` — multi-primary primary list
  (used by `multiprimary_pion_proton_foil_stress.mac`).
- `/calibration/<species>/...` — per-species kinematic configuration
  (energy range, vertex constraints).
- `/source/...` — beam-direction, beam-shape commands.

### 2.4 Output / diagnostics

- `/run/setRandomSeed <int>` — RNG seed (plan 47 binds this to the
  dataset registry).
- `/output/...` (if defined by ParquetOutputManager messenger) — output
  routing.

## 3. Reconstruction CLI invocations

From `reconstruction.md` lines 167–193, the canonical CLI commands
shipped today. All paths are relative to the repo root unless noted.

```bash
# Summarise a run
python3 -m nnbar_reconstruction.cli summarize build-codex-setup2/output --run 0
python3 -m nnbar_reconstruction.cli summarize build-codex-setup2/output --run 0 \
    --tables-dir reconstruction_out

# Scan PID thresholds
python3 -m nnbar_reconstruction.cli scan-pid build-codex-setup2/output --run 0 --table pid_scan.csv
python3 -m nnbar_reconstruction.cli scan-pid build-codex-setup2/output --runs 0,1,2 --table pid_scan.csv
python3 -m nnbar_reconstruction.cli scan-pid build-codex-setup2/output --all-runs --table pid_scan.csv

# Validate against truth labels
python3 -m nnbar_reconstruction.cli validate-reco build-codex-setup2/output --run 0 \
    --json reco_validation.json
python3 -m nnbar_reconstruction.cli validate-reco build-codex-setup2/output --runs 0,1,2 \
    --json reco_validation.json
python3 -m nnbar_reconstruction.cli validate-reco build-codex-setup2/output --all-runs \
    --json reco_validation.json
python3 -m nnbar_reconstruction.cli validate-reco build-codex-setup2/output --all-runs \
    --min-class-count 100 --min-accuracy 0.95 --min-balanced-f1 0.95 \
    --min-electron-pair-purity 1.0
python3 -m nnbar_reconstruction.cli validate-reco build-codex-setup2/output --all-runs \
    --fail-on-not-ready
python3 -m nnbar_reconstruction.cli validate-reco build-codex-setup2/output --all-runs \
    --pid-proton-dedx-min 0.08 --pid-short-range-cm 40 \
    --pid-short-range-proton-dedx-min 0.03 \
    --json reco_validation_pid_candidate.json

# Geometry audit
python3 -m nnbar_reconstruction.cli geometry-audit . \
    --json output/studies/geometry_audit.json --fail-on-mismatch

# Charged stress study (after running the macro)
./nnbar-detector-simulation -m macro/studies/charged_pion_proton_foil_stress.mac
python3 -m nnbar_reconstruction.cli charged-study \
    output/studies/charged_pion_proton_foil_stress \
    --runs 0,1,2 \
    --json output/studies/charged_pion_proton_foil_stress/charged_study_summary.json \
    --table output/studies/charged_pion_proton_foil_stress/charged_study_rows.csv
python3 -m nnbar_reconstruction.cli validate-reco \
    output/studies/charged_pion_proton_foil_stress --runs 0,1,2 \
    --json output/studies/charged_pion_proton_foil_stress/charged_validation.json
python3 -m nnbar_reconstruction.cli scan-pid \
    output/studies/charged_pion_proton_foil_stress --runs 0,1,2 \
    --table output/studies/charged_pion_proton_foil_stress/pid_scan.csv

# Multi-primary stress study
./nnbar-detector-simulation -m macro/studies/multiprimary_pion_proton_foil_stress.mac
python3 -m nnbar_reconstruction.cli charged-study \
    output/studies/multiprimary_pion_proton_foil_stress --run 0 \
    --json .../charged_study_summary.json --table .../charged_study_rows.csv
python3 -m nnbar_reconstruction.cli validate-reco \
    output/studies/multiprimary_pion_proton_foil_stress --run 0 \
    --pid-proton-dedx-min 0.08 --pid-short-range-cm 40 \
    --pid-short-range-proton-dedx-min 0.03 \
    --json .../charged_validation_pid_candidate.json

# Pi0 fake studies
python3 -m nnbar_reconstruction.cli pi0-fake-study \
    output/studies/charged_pion_proton_foil_stress --runs 0,1,2 \
    --json .../pi0_fake_study_track_isolated.json \
    --table .../pi0_fake_study_track_isolated_rows.csv
python3 -m nnbar_reconstruction.cli pi0-fake-study \
    output/studies/multiprimary_pion_proton_foil_stress --run 0 \
    --json .../pi0_fake_study_track_isolated.json \
    --table .../pi0_fake_study_track_isolated_rows.csv
python3 -m nnbar_reconstruction.cli pi0-fake-study \
    output/studies/charged_pion_proton_foil_stress --runs 0,1,2 \
    --prompt-timing \
    --json .../pi0_fake_study_prompt_timing.json \
    --table .../pi0_fake_study_prompt_timing_rows.csv

# Pi0 mass-ladder study
python3 -m nnbar_reconstruction.cli pi0-study output/studies/pi0_foil_500mev --run 0 \
    --json .../pi0_study_summary.json --table .../pi0_study_rows.csv
build/nnbar-detector-simulation -g -m macro/studies/pi0_foil_energy_scan.mac
```

Each command line above becomes a row in plan 47 (reproduction
ledger) when it produces a thesis-quoted number. Codex-supervisor
links command → registered dataset ID via `data/registry/datasets.yml`.

## 4. Sample-size discipline

Plan 03 dataset registry §3 manifest schema records `events_requested`
and `events_produced` per dataset. Plan 21 (cosmic) and plan 41
(significance) drive *target* sample sizes from upper-limit / Z₀
calculations.

For the existing licentiate samples (`run_signal.mac`,
`run_signal_100k.mac`, cosmic per-species per-run partitions),
codex-supervisor records the `events_produced` count from the
output parquet row counts during the freeze step.

## 5. Acceptance criteria

- §1.1 through §1.6 list every `.mac` in the repo. Diff against
  filesystem must be zero.
- §3 lists every CLI command in `reconstruction.md` and any new
  command added by code in `cli.py`.
- Every macro that produces a thesis-quoted sample has a matching
  `data/registry/<id>/manifest.yml` entry (plan 03).
- The legacy `macros/*.mac` (§1.6) each have a status decision
  (active, retire, promote).
- Plan 53 CI rule: a new `.mac` file under `NNBAR_Detector/macro*/`
  blocks merge until this plan has a row for it.

## 6. Risks and mitigations

- *Risk:* macros are edited in place without changing filename;
  status drifts.
  *Mitigation:* plan 03 manifests record macro-file SHA-256; a hash
  change forces a registry version bump (plan 03 §5).
- *Risk:* CLI invocations cited in `reconstruction.md` go stale as
  the CLI evolves.
  *Mitigation:* §3 is regenerated from `cli.py` parser on every
  `cli.py` change; CI compares generated text to this section.

## 7. Dependencies

- **00_README** — plan space.
- **03_dataset_registry** — every macro produces a registered sample.
- **07** — macros invoke simulation entry point, geometry, primary
  generator.
- **08** — reconstruction CLI entry points are consumed here.
- *Consumed by:* plan 20 (signal sample), plan 21 (cosmic), plan 22
  (beam neutron), plan 23 (calibration aux), plan 47 (ledger).

## 8. Open questions

- Are `macros/` (lower-level) macros still consumed by any thesis
  number? *Default: assumed no; codex-supervisor verifies by running
  each one and checking output coverage against ledger needs.*
- Do we want a `macro/cosmic_macro/cosmic_muon_short/` to survive
  CRY transition for fast-feedback testing? *Default: yes, retain as
  smoke test.*

## 9. References

- `NNBAR_Detector/docs/reconstruction.md` — source of the canonical
  CLI list in §3.

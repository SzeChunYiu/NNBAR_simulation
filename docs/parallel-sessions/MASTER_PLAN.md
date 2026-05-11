# NNBAR Project Master Plan

Last updated: 2026-05-11

This document is the single source of truth for all outstanding work across both
the NNBAR simulation/reconstruction project and the G4GPU side project.
Every codex lane should read this file at start and at finish to check for new tasks.

---

## Status Legend

- `DONE` — committed and merged
- `RUNNING` — currently in a codex pane
- `NEXT` — ready to start, spec exists
- `PLANNED` — scoped but no spec yet
- `BLOCKED` — waiting on dependency

---

## NNBAR Simulation (C++ / LUNARC)

| Task | Status | Lane | Notes |
|------|--------|------|-------|
| Build binary with Geant4 + MCPL | DONE | lunarc-build | job 3039997 |
| Signal run 1000 events | DONE | — | job 3040024, Parquet output verified |
| **CRY cosmic generator C++** | DONE | cry-integration | Built with `-DWITH_CRY=ON` on LUNARC job 3040177 after CRY meter-unit plane fix; 10k muon bin-0 test job 3040178 produced Parquet with `weight` column and 24m×24m x/y span |
| **CRY SLURM array (27/27 nonzero jobs submitted)** | RUNNING | cosmic-slurm-array | 27-bin matrix patch committed in nested `NNBAR_Detector` on `main` and `lane/cosmic-slurm-array` as `a344a47` (`fix(slurm): cover gamma cosmic bin 4`). Jobs 3040180/3040259 account for the original 26-job matrix (3040180_0-11 failed and are retried by 3040259; 3040180_12-23 and 3040259_0,1,2,3,6,7,8,10,11 completed). Gamma bin4 recovery (`particleIdx=1`, `energyBin=4`, 10-50 GeV, `N=2.30e7`) is job 3040275_10. 2026-05-11 12:11 CEST guarded LUNARC check (`ssh -O check` then `squeue -j 3040180,3040259,3040275 --array` and `sacct -X`) still showed six RUNNING blockers: 3040180_24,25; 3040259_4,5,9; 3040275_10. Elapsed times: 3040180_24/25 9:57:08, 3040259_4/5/9 3:39:33, 3040275_10 3:28:12. Fresh log tails reached 3040180_24~948,123, 3040259_4~699,207, 3040259_9~572,227, 3040275_10~124,282; high-energy 3040180_25 and 3040259_5 remained RUNNING with stale/slow stdout (`cosmic-3040180_25.out` mtime 02:20 CEST, visible event 2553; `cosmic-3040259_5.out` mtime 08:34 CEST, visible event 357). Keep open until these finish, fail, or cancel; do not duplicate gamma bin4 while 3040275_10 is RUNNING. |
| Cosmic weight computation script | DONE | cosmic-weight-analysis | `cosmic_weights.py` + `combine_cosmic_background.py` merged; tests/test_cosmic_weights.py passes |
| Worker-0 lane-doc RTK/LUNARC command guard | DONE | worker-0-doc-guard | `docs/parallel-sessions/worker-0.md` now prefixes repo command examples with `rtk`, replaces plain LUNARC SSH wording with the socket check/init guard, and shows guarded `rtk proxy ssh lunarc ...` usage. Verification: `wc -l docs/parallel-sessions/worker-0.md` = 76; `rg -n "ssh lunarc|git commit|sbatch|squeue|rsync|python -m|pytest|cmake|make" docs/parallel-sessions/worker-0.md` only reports `rtk git commit` examples, the explanatory `rsync` keyword, and the guarded `rtk proxy ssh lunarc`/`squeue` example. |

---

## NNBAR Reconstruction (Python)

| Task | Status | Lane | Notes |
|------|--------|------|-------|
| data_pipeline package | DONE | data-pipeline | Merged |
| clustering enhancements | DONE | clustering | Merged |
| End-to-end pipeline runner + tests | DONE | reco-pipeline | Merged, 3 tests pass |
| Random Forest Classifier | DONE | rfc-classifier | RFCClassifier + train_rfc.py merged |
| π⁰ lead-glass fraction cut verification | DONE | pi0-verification | Ch.8 has 60% local optimum and 55% final optimized cut; canonical constants/tests added |
| Opening angle threshold (30°) | DONE | pi0-verification | Ch.8 has 25° local optimum and 30° final optimized cut; canonical constants/tests added |
| Ch.9 event-variable formula regression | DONE | ch9-event-variables | Momentum-tensor sphericity now weights by |p|^2, longitudinal energy preserves sign, and event-variable/cutflow/RFC pytest regressions pass |
| Thesis Table 9.1 default cutflow integration | DONE | ch9-cutflow-integration | Committed in `f757b97`/`330ef29`: default Python selection uses canonical Table 9.1 order/constants and filtered upper/lower scintillator energies from Ch.7 timing windows; focused/full pytest pass (18/18, 34/34). Exact `sig_foil_v3`/`cosmic_cry_essLund_v1` samples remain absent, so survival fractions remain blocked. |
| Config loader portability regression | DONE | config-portability | Hardcoded local config fallbacks removed; default discovery is package/repo-relative and tests/test_config.py covers default discovery, explicit paths, missing paths, and machine-specific fallback regression. Focused/full pytest pass (8/8, 38/38). |
| Rolling trigger TPC-track multiplicity audit | DONE | tpc-trigger-multiplicity | Committed in `c9ca4b6`, `34dde31`, `1f04409`: rolling pre-selection counts unique non-negative `track_id`/`Track_ID` values when present, defaults to the Ch.7 more-than-one TPC-track trigger (`min_tpc_tracks: 2`), preserves documented times-only hit-count fallback, selects a TPC-only active window, and passes focused/full tests (`tests/test_event_preselection.py` 9/9; `tests/` 47/47). |
| Rolling trigger TPC-only active-window selection | DONE | tpc-trigger-t0-fix | Closed by `34dde31`/`1f04409`: regression coverage asserts TPC-only trigger masks retain all triggering tracks, active windows are selected even with zero calorimeter energy, and the calorimeter boundary triggers at 100 MeV but not below. Focused/full tests pass (`tests/test_event_preselection.py` 9/9; `tests/` 47/47). |
| Scintillator range layer-count consistency | DONE | scintillator-layer-count | Committed in `410a279`: Python config now uses the thesis 10-layer scintillator convention; range counting accepts 0-based simulation or 1-based thesis layer labels and ignores invalid out-of-range IDs. Focused/full pytest pass (`tests/test_config.py tests/test_scintillator_range.py` 7/7; `tests/` 50/50). |
| TPC dE/dx electron-count convention | DONE | tpc-dedx-electrons | Committed in `59e0624`: `compute_track_dedx` uses `electrons / layer_path_length` when present, preserves explicit legacy `eDep` fallback, and passes focused/full pytest (`tests/test_tpc_dedx.py` 2/2; `tests/` 52/52). |
| Charged pion/proton \(t(n)\) PID calibration | DONE | charged-pid-tn-calibration | Digitized thesis Ch.8 `charged_OD` t(n) thresholds in e-/cm, wired charged PID to that table instead of legacy MeV/cm YAML coefficients, and added focused regressions; verification passed (`tests/test_charged_pid.py` 8/8, full `tests/` 60/60, touched file caps <=500 lines). |
| Charged PID downstream unit cleanup | DONE | charged-pid-unit-cleanup | Committed in `0f0ac4d`/`b7433bd`: electron-count dE/dx no longer feeds the legacy Bethe-Bloch MeV/cm momentum inversion; focused/full pytest pass (`tests/test_charged_pid.py` 11/11; `tests/` 63/63). Planner follow-up: split `object_identification.py` because it is 497 lines after this unit. |
| Object identification file-cap split | DONE | object-identification-split | Committed in `c51d92b`: `nnbar_reconstruction/reconstruction/object_identification.py` is 379 lines after the neutral-pion helper split into `nnbar_reconstruction/reconstruction/neutral_pid.py` (129 lines), with the historical import surface preserved by re-export. Verification passed: focused pytest (`tests/test_file_caps.py`, `tests/test_pi0_integration.py`, `tests/test_charged_pid.py`) 13/13 and full `tests/` 64/64. |
| Vertex \(\sigma(\theta)\) weighting + smearing validation | DONE | vertex-sigma-smearing | Committed in `4e8e26b`: added explicit 20-degree theta-bin projected-position sigma table support for weighted vertex reconstruction plus regressions for bin boundaries, 1/sigma^2 weights, centimeter single-track uncertainty, and empirical fallback. Extracted Ch.7 text contains the sigma curves only as figures, so no real thesis numeric table was hard-coded; thesis-mode callers must supply a table. Smearing closure is tracked by `vertex-smearing-closure`. Verification passed (`tests/test_vertex_sigma_smearing.py` 4/4; `tests/` 68/68; file caps 438/85 lines). |
| Vertex smearing-closure toy validation | DONE | vertex-smearing-closure | Seeded synthetic projected-smearing closure added in `tests/test_vertex_sigma_smearing.py` with an explicit synthetic sigma(theta) table and pull-width tolerance; no thesis plot values invented. Verification passed: focused test 5/5, full `tests/` 69/69, file caps 438/136 lines. |
| Timing-window acceptance and filtered-energy regression | DONE | timing-window-regression | Committed in worker-1: `tests/test_timing_window.py` covers Ch.7 scintillator/lead-glass boundary inclusivity, `sigma`/`n_sigma` overrides, and lead-glass out-of-window filtered energy; existing Ch.9 scintillator hemisphere regression remains green. Verification passed: focused timing/cutflow tests 13/13, full `tests/` 73/73, touched file caps <=500 lines. Exact signal/cosmic acceptance fractions remain blocked by missing exact thesis samples. |
| Ch.4 detector geometry constants manifest | NEXT | geometry-constants-manifest | See `docs/parallel-sessions/geometry-constants-manifest.md`; add a Python manifest/audit for thesis detector constants versus reconstruction config, with C++ geometry treated read-only. |
| Final sensitivity and zero-survivor limit accounting | NEXT | final-sensitivity-accounting | See `docs/parallel-sessions/final-sensitivity-accounting.md`; add pure-Python weighted-yield and zero-survivor limit accounting without claiming unavailable exact-sample survival fractions. |
| Material budget analysis script | PLANNED | — | Low priority — analysis only |

---

## G4GPU Side Project (geant4-gpu repo)

| Task | Status | Lane | Notes |
|------|--------|------|-------|
| DESIGN_BRIEF + SPEC + VALIDATION docs | DONE | — | Committed in geant4-gpu repo |
| **Phase 0 infrastructure** | DONE | g4gpu-phase0 | libG4GPU.so built on LUNARC, test_stub PASS |
| **Phase 1: Muon physics kernel** | DONE | g4gpu-phase1 | Committed in geant4-gpu `lane/g4gpu-phase1` (`9c3470e`); LUNARC build/test job 3040175 passed `g4gpu_stub`, `g4gpu_muon_range`, and `g4gpu_mcs` with matching local/remote source hashes |
| Phase 2: Voxel geometry (3DDA) | RUNNING | g4gpu-phase2 | Unblocked by Phase 1; see docs/parallel-sessions/g4gpu-phase2.md |
| Phase 3: RTX geometry backend | PLANNED | — | Requires OptiX SDK on LUNARC |
| Phase 4: Optical photon (OptiX) | PLANNED | — | Long-term |

---

## Codex Self-Check Protocol

At the end of every lane goal, the codex agent MUST:
1. Re-read this file (MASTER_PLAN.md)
2. Check: are there tasks marked NEXT that match your expertise? If yes, start one.
3. Check: does your completed work unlock a BLOCKED task? If yes, update this file.
4. If no new work available, write "IDLE: no NEXT tasks match this lane's scope" to stdout.

---

## Key Facts Every Lane Needs

- LUNARC SSH: `ssh lunarc "cmd"` — pre-multiplexed
- SLURM account: `lu2026-2-51` | partition: `lu48` (CPU), `gpua40` (GPU)
- Source on LUNARC: `/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/`
- Geant4 install: `/projects/hep/fs10/shared/nnbar/billy/packages/hibeam_env/`
- Conda env: `hibeam_env` at same path
- geant4-gpu repo: `/Volumes/MyDrive/nnbar/geant4-gpu/`
- Simulation repo: `/Volumes/MyDrive/nnbar/nnbar/simulation/`
- CRY v1.7 download: https://nuclear.llnl.gov/simulation/ (cry_v1.7.tar.gz)
  CRY data dir after install: `$CRY_DIR/data/`
  CRY lib: `$CRY_DIR/lib/libCRY.a`

---

## PROPOSED TASKS (planner, 2026-05-11)

Review scope: extracted thesis front matter/outline/contribution files, chapters 1--11 plus Appendix A (`12_Appendix_1.tex`), extracted thesis `0_main.tex`, current HIBEAM GNN Overleaf article `/Volumes/MyDrive/nnbar/papers/overleaf-696757e2/main.tex`, HIBEAM evidence/governance surfaces needed by those chapters, simulation C++ geometry/sensitive detectors/generators, macros, SLURM scripts, tests and config, both Python reconstruction trees (`nnbar_reconstruction/` and `NNBAR_Detector/nnbar_reconstruction/`), ACTS/Kalman tracking code (`acts_tracking/`), reconstruction/training scripts, thesis reproduction ledger rows, rebuild-plan governance docs, and the G4GPU SPEC/VALIDATION/code surfaces. Chs. 1, 2, and 11 are theory/context/outlook, so no code-facing task was added for them; HIBEAM disappearance/regeneration prose is treated as evidence-boundary material unless it touches detector reconstruction; extracted Ch. 10 is commented placeholder text duplicating the Ch. 9 cutflow/ML discussion; front matter and glossary material are terminology/evidence-map material.

| Task | Reason | Priority | Thesis Ref |
|------|--------|----------|------------|
| GEANT4 physics-list reproducibility audit | Thesis states simulations used GEANT4 4.10.07.p02 with FTFP_BERT_HP plus EM Standard Option4, but `PhysicsList.cc` registers `G4HadronPhysicsFTFP_BERT()` (non-HP) while the repo now builds with Geant4 11.x; document/validate the physics-list/version drift, especially neutron/background and material-budget observables. | High | Ch. 5 GEANT4 model; Appendix A beam backgrounds |
| TPC ionization W-value alignment | Thesis states Ar/CO2 uses \(W=27.4\) eV, but `TPCSD.cc`, `tpc_calibration.py`, and config use 23.6 eV; this changes simulated electron counts and downstream dE/dx. | High | Ch. 5, TPC ionization Eq. \(n_T=\Delta E/W\) |
| TPC response and digitization boundary audit | Thesis describes a first-order TPC response that records Poisson electron counts in 1 cm × 1 cm × 200 cm segments, while the codebase also contains Garfield/GPU drift, pad-readout, gain, diffusion, and electric-field paths; decide which path is thesis-authoritative, validate units and schema, or mark advanced digitization as non-thesis evidence. | High | Ch. 5 Time Projection Chamber; Ch. 7 TPC reconstruction |
| Charged-object cone energy and beampipe deflection validation | Thesis chooses a 25° charged-hit collection cone from a 5°--85° single-track efficiency scan and quantifies pion beampipe multiple-scattering deflection vs kinetic energy; code defaults `cone_angle=25.0` but no task reproduces the efficiency/deflection plots or guards the provenance of that angle. | Medium | Ch. 7, Kinetic Energy Reconstruction; Momentum Direction |
| Lead-glass PMT calibration formula audit | Thesis calibration is \(E_\gamma=0.46N_{\rm PMT}+8.02\) for \(N_{\rm PMT}>0\); Python calibration uses a generic 200 photons/MeV yield, and C++ lead-glass reflectivity is 95% vs thesis 90%. | Medium | Ch. 5, Lead Glass Energy Calibration |
| Scintillator WLS light-collection parameterization | Thesis says WLS SiPM yield parameterization \(f(r)\) and \(f(z)\) was adopted; simulation/reconstruction appear to use simple light yield or attenuation, not the radial/longitudinal WLS functions. | Medium | Ch. 5, Scintillator WLS equations |
| Electron-pair object integration | Thesis identifies \(e^\pm\) pairs when two TPC entry points are within 5 cm; code has `identify_electron_pair` helper but no clear integration into object lists, pion searches, or event variables. | Medium | Ch. 8, Electron and \(e^\pm\) pair |
| Pion multiplicity truth/reconstruction closure | Thesis validates reconstructed charged, neutral, and total pion multiplicities against truth; code counts pions for selection, but no task reproduces the Ch. 9 truth-vs-reco multiplicity heatmaps or checks the `min_pions` cut provenance. | Medium | Ch. 9, Pion Multiplicity |
| RFC feature provenance validation | RFC is merged, but feature extraction currently derives sphericity from TPC hit positions and leading-track “dE/dx” from summed energy, not the Ch. 9 reconstructed object variables; add tests tying RFC inputs to canonical event-variable code and cosmic weights. | Medium | Ch. 9 Machine Learning Method |
| Magnetic-shielding and no-B-field boundary closure | Current tracking/reconstruction plans assume no magnetic field and straight tracks, while thesis Ch. 3 treats nT-scale magnetic shielding and quasi-free phase control as sensitivity requirements; add a boundary note/test plan separating detector no-B-field reconstruction assumptions from beamline magnetic-field systematics and preventing momentum-from-curvature claims. | Medium | Ch. 3 Magnetic Shielding and Sensitivity; rebuild plans 17, 45 |
| Thesis reproduction ledger command/sample closure | `docs/thesis_reproduction_ledger.md` reports only 1/161 rows reproduced, with 43 mismatches and 117 `blocked-no-sample` rows caused by absent exact samples and missing/placeholder command surfaces such as `geometry-audit` and `pi0-fake-study`; add a lane to make row-specific commands and sample paths executable before thesis figures/numbers are cited. | High | Reproducibility ledger Ch. 13; `docs/rebuild_plans/47_reproduction_ledger.md` |
| HIBEAM TPC GNN feature-contract and final-result closure | The HIBEAM GNN Overleaf article and reproducibility ledger say post-2026-05-08 TrackGNN/VertexGNN results must use the current geometry-only feature schema, retrained checkpoints, all five Compton levels, matched \(\sigma_r\) and \(\epsilon\), uncertainties, and deployable/oracle labels; current reconstruction training prep still uses legacy 12-feature placeholders and particle-parquet truth, with no MASTER_PLAN task to regenerate thesis-ready tables. | High | HIBEAM GNN Overleaf article `main.tex`; HIBEAM Reconstruction Ledger Ch. 13 |
| HIBEAM ACTS/Kalman baseline integration closure | The codebase includes an `acts_tracking/` Kalman/CKF/vertex-fitting pipeline with TODOs for full HIBEAM TPC geometry, ambiguity resolution, multi-vertex finding, and real-data integration tests; the HIBEAM GNN Overleaf article requires every method family (including Kalman fits) to report dataset, truth source, split, \(\sigma_r\), \(\epsilon\), and deployable/oracle status before thesis use. | Medium | HIBEAM GNN Overleaf article method families; `acts_tracking/INTEGRATION_GUIDE.md` |
| HIBEAM vertex method-comparison and metric-table closure | The current HIBEAM GNN Overleaf article has incomplete Least-squares, Trackless, GraphNeT, and Clustering+GNN result tables and explicitly asks for validation/no-beampipe samples, 0/1/2/4/8 Compton datasets, train/validation/test split evidence, resolution/efficiency/outlier plots vs pion multiplicity, Compton multiplicity, and foil radius, plus signal-hit/track association efficiency; no single code or ledger surface currently reproduces that whole comparison. | High | HIBEAM GNN Overleaf article Methods, Results, Evaluation Metrics |
| HIBEAM evidence archive and dataset-version pinning | HIBEAM-related evidence rules require final claims to link to dataset registry entries, decision-log entries, validation reports, and a clean pinned commit/tag/archive; dataset registry, decision-log mirror, reproduction-ledger, and glossary/archive plans exist, but no MASTER_PLAN task closes the pinned evidence package before promoting HIBEAM reconstruction numbers. | High | `docs/rebuild_plans/03_dataset_registry.md`; `docs/governance/DECISION_LOG.md`; `docs/thesis_reproduction_ledger.md`; `docs/rebuild_plans/56_glossary.md` |
| Photon conversion map reproduction | Thesis reports 100 MeV photon conversion fractions (4.1% silicon, 23.1% beampipe, 5% TPC, 18.2% scintillator, 49.6% lead glass); no reproduction/validation task is on the plan. | Medium | Ch. 5, Map of photon interaction |
| Signal sample kinematics validation | Thesis uses 50k annihilation events and validates foil vertex distribution, pion/photon/proton KE peaks, and angular biases; current plan only verifies a 1000-event run output, not these physics distributions. | Medium | Ch. 6, Annihilation Event Simulation |
| CRY cosmic kinematics and rate closure | CRY integration and Eq. 6.1 weights exist, but no task verifies generated KE/zenith distributions at the CRY plane and passive shield or reproduces the thesis 3-year expected cosmic particle counts. | Medium | Ch. 6, Cosmic Ray Background Simulation |
| Skyshine and ESS timing-cut disposition | Ch. 3 treats skyshine/groundshine as a minor accelerator-timed neutron component partly suppressed by the 5 ms fast-neutron timing cut and otherwise handled like cosmics; MASTER_PLAN has cosmic and beam-background tasks but no explicit check that skyshine is either modeled, bounded, or documented as covered by those tasks. | Medium | Ch. 3, Skyshine background |
| Neutral-object and single-\(\pi^0\) response validation | Thesis validates photon energy/opening-angle truth-vs-reco distributions and \(\pi^0\) invariant-mass response at 50, 150, and 250 MeV; current \(\pi^0\) tasks mainly lock cut constants, not neutral-object response and mass-resolution reproduction. | Medium | Ch. 7, Neutral Object Reconstruction; Ch. 8 single \(\pi^0\) |
| Carbon foil radius and source-vertex alignment | Thesis and Ch. 3 detector concept use a 1 m-radius carbon target/foil, but `DetectorConstruction.cc` builds a 30 cm carbon radius, Python config uses 50 cm, and particle-gun fallback fixes `x=y=0`; align geometry/config/generator assumptions before trusting vertex and photon-conversion validations. | High | Ch. 3 NNBAR target; Ch. 6 signal vertex distribution |
| Beam-induced background and TPC occupancy validation | Appendix A quantifies absorber choices, photon/neutron fluxes, per-50 ns subsystem intensities, and ~25 µs TPC occupancy; MASTER_PLAN has cosmic weighting but no task to reproduce B4C/\(^{6}\)LiF/Cd beam-background tables or verify TPC rate assumptions. | High | Appendix A, beam-induced backgrounds and TPC full rates |
| G4GPU EM/gamma and neutron physics kernels | `docs/SPEC.md` describes `EMStepKernel.cu` and `NeutronStepKernel.cu` plus EM-shower validation, but MASTER_PLAN only lists muon, geometry, RTX, and optical phases. | Medium | G4GPU SPEC physics kernels |
| G4GPU full-event validation and benchmarks | `docs/VALIDATION.md` requires V7 full NNBAR event validation and B1-B5 throughput/speedup benchmarks; current G4GPU plan only covers phase-local tests. | Medium | G4GPU VALIDATION V7, B1-B5 |

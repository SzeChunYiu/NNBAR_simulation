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
| **CRY SLURM array (27/27 nonzero jobs submitted)** | RUNNING | cosmic-slurm-array | 27-bin matrix patch committed in nested `NNBAR_Detector` on `main` and `lane/cosmic-slurm-array` as `a344a47` (`fix(slurm): cover gamma cosmic bin 4`). Jobs 3040180/3040259 account for the original 26-job matrix; gamma bin4 recovery (`particleIdx=1`, `energyBin=4`, 10-50 GeV, `N=2.30e7`) is job 3040275_10. 2026-05-11 13:31 CEST guarded LUNARC check (`ssh -O check`, then `squeue -j 3040180,3040259,3040275 --array`, `sacct -X`, and stdout tails) still showed five RUNNING external blockers: 3040180_25, 3040259_4, 3040259_5, 3040259_9, and 3040275_10. Elapsed/time-left from `squeue`: 3040180_25 11:17:36/0:42:24; 3040259_4/5/9 05:00:01/6:59:59; 3040275_10 04:48:40/7:11:20. Fresh stdout tails reached 3040259_4 event ~958,773, 3040259_9 event ~777,773, and 3040275_10 event ~171,358; high-energy 3040180_25 and 3040259_5 remained RUNNING with stale/slow stdout (`slurm/cosmic-3040180_25.out` mtime 02:20 CEST, visible event 2553; `slurm/cosmic-3040259_5.out` mtime 08:34 CEST, visible event 357). Keep open until these finish, fail, or cancel; do not duplicate gamma bin4 while 3040275_10 is RUNNING. |
| Cosmic weight computation script | DONE | cosmic-weight-analysis | `cosmic_weights.py` + `combine_cosmic_background.py` merged; tests/test_cosmic_weights.py passes |
| Worker-0 lane-doc RTK/LUNARC command guard | DONE | worker-0-doc-guard | `docs/parallel-sessions/worker-0.md` now prefixes repo command examples with `rtk`, replaces plain LUNARC SSH wording with the socket check/init guard, and shows guarded `rtk proxy ssh lunarc ...` usage. Verification: `wc -l docs/parallel-sessions/worker-0.md` = 76; `rg -n "ssh lunarc|git commit|sbatch|squeue|rsync|python -m|pytest|cmake|make" docs/parallel-sessions/worker-0.md` only reports `rtk git commit` examples, the explanatory `rsync` keyword, and the guarded `rtk proxy ssh lunarc`/`squeue` example. |
| GEANT4 physics-list reproducibility audit | DONE | geant4-physics-list-audit | Committed in worker-0 (`ea1adeb`): created `docs/reports/geant4_physics_list_reproducibility.md` documenting the authoritative `src/core/PhysicsList.cc` source, non-HP `G4HadronPhysicsFTFP_BERT` observation, Celeritas EM branch, Geant4 11.2.2 LUNARC evidence, `nominal_non_hp`/`nominal_hp` validation tags, and N4 downstream risks. Verification passed: report line count is 169 and marker grep found `OPEN:`, `nominal_non_hp`, `nominal_hp`, and `N4`. |
| Beam-induced background and TPC occupancy validation | DONE | beam-background-tpc-occupancy | Audit report created at `docs/reports/beam_background_tpc_occupancy.md` (242 lines). It verifies Appendix A B4C/6LiF/Cd, 50 ns, and 25 µs evidence, inventories current B4C-only beampipe/beam-stop surfaces, confirms no local `data/registry` beam-neutron manifest or beam-neutron macro/MCPL source, and leaves fail-closed `OPEN:` blockers for source staging, HP physics build, absorber selector, scorer definitions, normalization, seeds, occupancy arithmetic, artifacts, and systematics throws. No simulations or SLURM jobs were run. Verification: `wc -l` and required `grep` passed. |
| Carbon foil radius and source-vertex alignment | DONE | carbon-foil-alignment | Audit report created at `docs/reports/carbon_foil_vertex_alignment.md` (251 lines). Verified thesis 1 m target radius and gravity-biased 1 m foil signal vertices, Geant4 30 cm carbon radius at origin, particle-gun origin fallback, MCPL position passthrough, Python `target.radius: 50.0` cm, and no target-radius/source-vertex DEC. Leaves fail-closed `OPEN:` blockers for target-radius DEC, source-vertex sample registry, and later code/config alignment; no simulations or production constants changed. Verification: report `wc -l`, required marker `grep`, and function/source line-reference greps passed. |

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
| Timing-window acceptance and filtered-energy regression | DONE | timing-window-regression | Committed in worker-1: `tests/test_timing_window.py` covers Ch.7 scintillator/lead-glass boundary inclusivity, `sigma`/`n_sigma` overrides, and lead-glass out-of-window filtered energy; existing Ch.9 scintillator hemisphere regression remains green. Fresh planner verification passed: `tests/test_timing_window.py tests/test_cutflow.py tests/test_event_preselection.py` 18/18, full `tests/` 73/73, touched file caps <=500 lines. Exact signal/cosmic acceptance fractions remain blocked by missing exact thesis samples. |
| Ch.4 detector geometry constants manifest | DONE | geometry-constants-manifest | Committed in worker-1 (`c8de07e`): `geometry_constants.py` audits verified thesis Ch.4/5 constants for TPC type dimensions/W-value/container/cell sizes, scintillator layers/staves/stave dimensions/gaps, SF-5 lead-glass block/reflectivity, and cosmic-veto/passive-shield envelope against `nnbar_geometry.yaml`. Current Python config matches/mismatches/missing entries are exposed as data; C++ geometry comparison remains open/read-only. Verification passed: focused 5/5, full `tests/` 78/78, touched file caps 263/78 lines. |
| Geometry manifest path portability fix | DONE | fix-geometry-manifest-paths | Committed in worker-1 (`014d564`): geometry manifest thesis-source resolution now uses the repo-layout default or `NNBAR_THESIS_EXTRACT_DIR`, removing machine-specific absolute paths; regression coverage exercises the environment override. Verification passed: focused geometry manifest tests 6/6, full `tests/` 92/92 with 3 third-party deprecation warnings, touched file caps 283/100 lines. |
| TPC W-value policy audit | DONE | tpc-w-value-policy-audit | Committed in worker-1 (`1c0205b`): `tpc_w_value_policy.py` exposes production 23.6 eV, 26.0/27.4 eV reference scale factors, and config audit helpers without editing over-cap calibration or C++ source. Fresh planner verification passed: focused 4/4, full `tests/` 91/91, touched file caps 187/45 lines. |
| Final sensitivity and zero-survivor limit accounting | DONE | final-sensitivity-accounting | Committed in worker-1 (`ea6f86f`): pure-Python weighted-yield, `sum_w2` variance, acceptance, explicit-CL zero-survivor Poisson-limit, and blocker-aware report helper added. Verification passed (`tests/test_sensitivity_accounting.py` 9/9; full `tests/` 87/87; touched file caps 250/113 lines). Final numeric sensitivity remains blocked until exact weighted signal/background samples are verified. |
| TPC response and digitization boundary audit | DONE | tpc-response-boundary-audit | Committed in worker-1: `tpc_response_boundary.py` defines machine-readable surfaces with first-order Poisson TPC electron-count per segment as `thesis_first_order`; current parquet columns as production schema; drift/gain/diffusion flags as `advanced_non_thesis`; and missing Garfield/GPU drift or absent `electrons` as `missing_or_unverified`. Verification passed: focused 6/6, full `tests/` 98/98 with 3 third-party deprecation warnings, touched file caps 314/84 lines. |
| Thesis reproduction ledger command/sample closure | DONE | thesis-ledger-command-closure | Fail-closed audit module/tests added for ledger markdown parsing, command-shape blockers, CLI verifier blockers, and sample-path checks. Verification passed: focused 8/8, full tests 106/106 with 3 third-party deprecation warnings, file caps 341/126 lines. Current ledger audit remains blocked as intended: 161/161 rows blocked without row-specific sample mappings; blockers include `sample_path_not_checked=161`, `command_placeholder=12`, `python_cli_unverified:scan-pid=24`. Next smallest fix: add a verified per-row sample-path mapping/registry resolver and CLI help allow-list before any reproduction run is promoted. |
| HIBEAM TPC GNN feature-contract and final-result closure | DONE | hibeam-gnn-feature-contract | Fail-closed audit helpers/tests added for geometry-only deployable schemas, TrackGNN/VertexGNN manifest evidence, Compton levels 0/1/2/4/8, split evidence, `sigma_r`, `epsilon`, uncertainty, and oracle-only truth/particle-label sources. Current local article/prep-script audit remains blocked as intended: article blockers 3 (`TODO`, placeholder refs, placeholder metrics); prep-script blockers 6 (truth ancestry, particle parquet, truth vertex/cluster/labels, missing test split). Verification passed: focused 5/5, full `tests/` 111/111 with 3 third-party deprecation warnings, file caps 349/134 lines. |
| HIBEAM GNN test path portability fix | DONE | fix-hibeam-gnn-paths | Committed in worker-2 (`6ce02e6`): `tests/test_hibeam_gnn_feature_contract.py` now uses `NNBAR_HIBEAM_ARTICLE_TEX` plus skip-safe fixtures for optional article/prep evidence, keeps prep-script reads repo-relative, and rejects machine-specific paper/user-home fallbacks in the test source. Verification passed: focused 6 passed/1 skipped; full `tests/` 117 passed/1 skipped; forbidden `/Volumes/MyDrive/nnbar/papers` grep returned no matches; file caps 183/349 lines. HIBEAM article/prep evidence remains fail-closed when supplied; no paper numbers promoted. |
| HIBEAM vertex method-comparison and metric-table closure | DONE | hibeam-vertex-method-closure | Fail-closed audit helpers/tests added for `least_squares`, `trackless`, `graphnet`, and `clustering_gnn` across Compton levels 0/1/2/4/8, requiring pinned dataset/split/artifact evidence, `dx`, `dy`, `d_tot`, `sigma_r` or radial uncertainty, `epsilon`, outlier definition, signal track/hit association efficiency, metric uncertainties, and deployable/oracle status. Current local article audit remains blocked as intended by TODO markers, placeholder references, blank method metrics, and missing pinned dataset ID; no paper numbers promoted. Verification passed: focused 6/6, full `tests/` 123 passed/1 skipped with 3 third-party deprecation warnings, file caps 393/158 lines. |
| HIBEAM evidence archive and dataset-version pinning | DONE | hibeam-evidence-archive | Fail-closed audit helpers/tests/report added for dataset registry IDs, DEC links, validation reports, ledger rows, archive digests, commit/tag pins, and unresolved HIBEAM paper placeholders. Current local package remains blocked as intended until every claim has registry/DEC/ledger/report/archive-pin evidence. Verification passed: focused 5/5, full `tests/` 117 passed/1 skipped with 3 third-party deprecation warnings, file caps 341/128/40 lines. |
| HIBEAM evidence test path portability fix | RUNNING | fix-hibeam-evidence-paths | See `docs/parallel-sessions/fix-hibeam-evidence-paths.md`; replace the hardcoded optional Overleaf path in `tests/test_hibeam_evidence_archive.py` with an environment-variable fixture and add a forbidden machine-specific path regression while preserving fail-closed evidence blockers. |
| Material budget analysis script | PLANNED | — | Low priority — analysis only |

---

## G4GPU Side Project (geant4-gpu repo)

| Task | Status | Lane | Notes |
|------|--------|------|-------|
| DESIGN_BRIEF + SPEC + VALIDATION docs | DONE | — | Committed in geant4-gpu repo |
| **Phase 0 infrastructure** | DONE | g4gpu-phase0 | libG4GPU.so built on LUNARC, test_stub PASS |
| **Phase 1: Muon physics kernel** | DONE | g4gpu-phase1 | Committed in geant4-gpu `lane/g4gpu-phase1` (`9c3470e`); LUNARC build/test job 3040175 passed `g4gpu_stub`, `g4gpu_muon_range`, and `g4gpu_mcs` with matching local/remote source hashes |
| Phase 2: Voxel geometry (3DDA) | DONE | g4gpu-phase2 | Committed and pushed in geant4-gpu `lane/g4gpu-phase2` (`dbb6c54`): `VoxelGeometry.cc` builds a Geant4-sampled material/volume grid, `VoxelGeometry.cu` provides the 3DDA device boundary march, and `MuonStepKernel.cu` uses the active voxel grid for geometry-aware step limits/material transitions. Verification: LUNARC build with `GCC/13.2.0` + `CUDA/12.8.0` succeeded; GPU SLURM job 3040708 ran `ctest --test-dir build --output-on-failure` with 4/4 passing (`g4gpu_stub`, `g4gpu_voxel_geometry`, `g4gpu_muon_range`, `g4gpu_mcs`). |
| Phase 3: RTX geometry backend | BLOCKED | g4gpu-phase3 | Blocked on OptiX SDK install — see `docs/parallel-sessions/g4gpu-optix-unblock.md` |
| Phase 4: Optical photon (Opticks integration) | PLANNED | — | Wrap Simon Blyth's Opticks instead of rebuilding |
| OptiX SDK install on LUNARC | RUNNING | g4gpu-optix-unblock | See `docs/parallel-sessions/g4gpu-optix-unblock.md` |
| **Phase 5: Benchmark suite + L0 microarchitecture wins** | NEXT | g4gpu-phase5 | See `docs/parallel-sessions/g4gpu-phase5.md`; measurement framework + AVX/NEON wins on CPU fallback |
| **Phase 6: L1 algorithmic redesign (SoA tracks)** | PLANNED | — | Depends on Phase 5; see `docs/specs/g4gpu-line-by-line-acceleration.md` |
| **Phase 7: L2 tri-compute integration** | PLANNED | — | Depends on Phase 3 + Phase 6 |
| **Phase 8 algorithm survey (deterministic + ML)** | NEXT | g4gpu-phase8-survey | See `docs/parallel-sessions/g4gpu-phase8-survey.md`; CS/math methods not yet applied to Geant4 — validation-friendly first |
| **Phase 9: Persistent GPU pipeline** | PLANNED | — | Long-term |
| **Phase 10: Differentiable transport** | PLANNED | — | Long-term |

---

## Codex Self-Check Protocol

At the end of every lane goal, the codex agent MUST:
1. Re-read this file (MASTER_PLAN.md)
2. Check: are there tasks marked NEXT that match your expertise? If yes, start one.
3. Check: does your completed work unlock a BLOCKED task? If yes, update this file.
4. If no new work available, write "IDLE: no NEXT tasks match this lane's scope" to stdout.

---

## Key Facts Every Lane Needs

- LUNARC SSH: first run
  `rtk proxy bash -lc 'ssh -O check lunarc 2>/dev/null && echo "Connected" || /Users/billy/lunarc-init.sh'`,
  then use `rtk proxy ssh lunarc "cmd"`.
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
| Charged-object cone energy and beampipe deflection validation | Thesis chooses a 25° charged-hit collection cone from a 5°--85° single-track efficiency scan and quantifies pion beampipe multiple-scattering deflection vs kinetic energy; code defaults `cone_angle=25.0` but no task reproduces the efficiency/deflection plots or guards the provenance of that angle. | Medium | Ch. 7, Kinetic Energy Reconstruction; Momentum Direction |
| Lead-glass PMT calibration formula audit | Thesis calibration is \(E_\gamma=0.46N_{\rm PMT}+8.02\) for \(N_{\rm PMT}>0\); Python calibration uses a generic 200 photons/MeV yield, and C++ lead-glass reflectivity is 95% vs thesis 90%. | Medium | Ch. 5, Lead Glass Energy Calibration |
| Scintillator WLS light-collection parameterization | Thesis says WLS SiPM yield parameterization \(f(r)\) and \(f(z)\) was adopted; simulation/reconstruction appear to use simple light yield or attenuation, not the radial/longitudinal WLS functions. | Medium | Ch. 5, Scintillator WLS equations |
| Electron-pair object integration | Thesis identifies \(e^\pm\) pairs when two TPC entry points are within 5 cm; code has `identify_electron_pair` helper but no clear integration into object lists, pion searches, or event variables. | Medium | Ch. 8, Electron and \(e^\pm\) pair |
| Pion multiplicity truth/reconstruction closure | Thesis validates reconstructed charged, neutral, and total pion multiplicities against truth; code counts pions for selection, but no task reproduces the Ch. 9 truth-vs-reco multiplicity heatmaps or checks the `min_pions` cut provenance. | Medium | Ch. 9, Pion Multiplicity |
| RFC feature provenance validation | RFC is merged, but feature extraction currently derives sphericity from TPC hit positions and leading-track “dE/dx” from summed energy, not the Ch. 9 reconstructed object variables; add tests tying RFC inputs to canonical event-variable code and cosmic weights. | Medium | Ch. 9 Machine Learning Method |
| Magnetic-shielding and no-B-field boundary closure | Current tracking/reconstruction plans assume no magnetic field and straight tracks, while thesis Ch. 3 treats nT-scale magnetic shielding and quasi-free phase control as sensitivity requirements; add a boundary note/test plan separating detector no-B-field reconstruction assumptions from beamline magnetic-field systematics and preventing momentum-from-curvature claims. | Medium | Ch. 3 Magnetic Shielding and Sensitivity; rebuild plans 17, 45 |
| HIBEAM ACTS/Kalman baseline integration closure | The codebase includes an `acts_tracking/` Kalman/CKF/vertex-fitting pipeline with TODOs for full HIBEAM TPC geometry, ambiguity resolution, multi-vertex finding, and real-data integration tests; the HIBEAM GNN Overleaf article requires every method family (including Kalman fits) to report dataset, truth source, split, \(\sigma_r\), \(\epsilon\), and deployable/oracle status before thesis use. | Medium | HIBEAM GNN Overleaf article method families; `acts_tracking/INTEGRATION_GUIDE.md` |
| Photon conversion map reproduction | Thesis reports 100 MeV photon conversion fractions (4.1% silicon, 23.1% beampipe, 5% TPC, 18.2% scintillator, 49.6% lead glass); no reproduction/validation task is on the plan. | Medium | Ch. 5, Map of photon interaction |
| Signal sample kinematics validation | Thesis uses 50k annihilation events and validates foil vertex distribution, pion/photon/proton KE peaks, and angular biases; current plan only verifies a 1000-event run output, not these physics distributions. | Medium | Ch. 6, Annihilation Event Simulation |
| CRY cosmic kinematics and rate closure | CRY integration and Eq. 6.1 weights exist, but no task verifies generated KE/zenith distributions at the CRY plane and passive shield or reproduces the thesis 3-year expected cosmic particle counts. | Medium | Ch. 6, Cosmic Ray Background Simulation |
| Skyshine and ESS timing-cut disposition | Ch. 3 treats skyshine/groundshine as a minor accelerator-timed neutron component partly suppressed by the 5 ms fast-neutron timing cut and otherwise handled like cosmics; MASTER_PLAN has cosmic and beam-background tasks but no explicit check that skyshine is either modeled, bounded, or documented as covered by those tasks. | Medium | Ch. 3, Skyshine background |
| Neutral-object and single-\(\pi^0\) response validation | Thesis validates photon energy/opening-angle truth-vs-reco distributions and \(\pi^0\) invariant-mass response at 50, 150, and 250 MeV; current \(\pi^0\) tasks mainly lock cut constants, not neutral-object response and mass-resolution reproduction. | Medium | Ch. 7, Neutral Object Reconstruction; Ch. 8 single \(\pi^0\) |
| G4GPU EM/gamma and neutron physics kernels | `docs/SPEC.md` describes `EMStepKernel.cu` and `NeutronStepKernel.cu` plus EM-shower validation, but MASTER_PLAN only lists muon, geometry, RTX, and optical phases. | Medium | G4GPU SPEC physics kernels |
| G4GPU full-event validation and benchmarks | `docs/VALIDATION.md` requires V7 full NNBAR event validation and B1-B5 throughput/speedup benchmarks; current G4GPU plan only covers phase-local tests. | Medium | G4GPU VALIDATION V7, B1-B5 |

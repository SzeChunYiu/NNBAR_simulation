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
| **CRY cosmic generator C++** | DONE | cry-integration | Built with `-DWITH_CRY=ON` on LUNARC job 3040120; 10k muon bin-0 test job 3040121 produced Parquet with `weight` column |
| **CRY SLURM array (30 jobs)** | NEXT | — | Unblocked by CRY C++ integration; submit `slurm/run_cosmic.slurm` for full production |
| Cosmic weight computation script | DONE | cosmic-weight-analysis | `cosmic_weights.py` + `combine_cosmic_background.py` merged; tests/test_cosmic_weights.py passes |

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
| Material budget analysis script | PLANNED | — | Low priority — analysis only |

---

## G4GPU Side Project (geant4-gpu repo)

| Task | Status | Lane | Notes |
|------|--------|------|-------|
| DESIGN_BRIEF + SPEC + VALIDATION docs | DONE | — | Committed in geant4-gpu repo |
| **Phase 0 infrastructure** | DONE | g4gpu-phase0 | libG4GPU.so built on LUNARC, test_stub PASS |
| **Phase 1: Muon physics kernel** | NEXT | g4gpu-phase1 | See docs/parallel-sessions/g4gpu-phase1.md |
| Phase 2: Voxel geometry (3DDA) | PLANNED | — | After Phase 1 tests pass |
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

| Task | Reason | Priority | Thesis Ref |
|------|--------|----------|------------|
| TPC ionization W-value alignment | Thesis states Ar/CO2 uses \(W=27.4\) eV, but `TPCSD.cc`, `tpc_calibration.py`, and config use 23.6 eV; this changes simulated electron counts and downstream dE/dx. | High | Ch. 5, TPC ionization Eq. \(n_T=\Delta E/W\) |
| Rolling trigger TPC-track multiplicity audit | Thesis trigger activates on more than one TPC track and/or calorimeter energy \(>100\) MeV; `event_preselection.py` counts TPC hits and defaults `min_tpc_tracks=1`. | High | Ch. 7, Event Pre-selection |
| TPC dE/dx from electron counts per layer | Thesis uses \(N_e/\Delta x\) per TPC layer and lower-60% truncated mean; `compute_track_dedx` currently uses `eDep/path_length`, not the `electrons` column. | High | Ch. 7, TPC dE/dx Eq. |
| Vertex \(\sigma(\theta)\) weighting + smearing validation | Thesis weights projected tracks by \(\sigma(\theta)=\bar d_0(\theta)\) in 20-degree bins and studies Gaussian position/angular smearing; Python vertex code uses empirical/median weighting without thesis-derived sigma tables. | High | Ch. 7, Eq. vertex weighting + Effect of Resolution |
| Scintillator range layer-count consistency | Thesis range counts signal across 10 scintillator layers; C++ geometry builds 10 layers while Python config says `n_layers: 5`, so range/PID may be inconsistent. | High | Ch. 7 Scintillator Range; Ch. 8 Charged pion/proton |
| Charged pion/proton \(t(n)\) PID calibration | Thesis uses optimized TPC dE/dx cut \(t(n)\) vs scintillator range and reports 90.8% pion / 98.0% proton ID; code uses generic linear \(t(n)=2.5+0.1n\) with no thesis-efficiency test. | High | Ch. 8, Fig. charged OD + Table pion/proton efficiency |
| Lead-glass PMT calibration formula audit | Thesis calibration is \(E_\gamma=0.46N_{\rm PMT}+8.02\) for \(N_{\rm PMT}>0\); Python calibration uses a generic 200 photons/MeV yield, and C++ lead-glass reflectivity is 95% vs thesis 90%. | Medium | Ch. 5, Lead Glass Energy Calibration |
| Scintillator WLS light-collection parameterization | Thesis says WLS SiPM yield parameterization \(f(r)\) and \(f(z)\) was adopted; simulation/reconstruction appear to use simple light yield or attenuation, not the radial/longitudinal WLS functions. | Medium | Ch. 5, Scintillator WLS equations |
| Electron-pair object integration | Thesis identifies \(e^\pm\) pairs when two TPC entry points are within 5 cm; code has `identify_electron_pair` helper but no clear integration into object lists, pion searches, or event variables. | Medium | Ch. 8, Electron and \(e^\pm\) pair |
| Longitudinal-energy sign convention check | Thesis \(E_L=\sum E_i\cos\alpha_i\) preserves forward/backward sign; `compute_longitudinal_energy` uses `abs(cos_alpha)`, erasing the asymmetry described in Ch. 9. | Medium | Ch. 9, Longitudinal Energy Eq. |
| Thesis Table 9.1 cutflow integration | Canonical cutflow constants/tests exist, but `analysis/event_selection.py` still defaults to top/bottom asymmetry + vertex radius and `EventVariables` has no filtered-scintillator observables; wire the \(E_{\rm scint}(y>0,\mathrm{filtered})\le320\) MeV and \(E_{\rm scint}(y<0,\mathrm{filtered})\le930\) MeV cuts into the default pipeline and reproduce the thesis survival fractions. | High | Ch. 9, Preliminary Event Selection Table |
| Pion multiplicity truth/reconstruction closure | Thesis validates reconstructed charged, neutral, and total pion multiplicities against truth; code counts pions for selection, but no task reproduces the Ch. 9 truth-vs-reco multiplicity heatmaps or checks the `min_pions` cut provenance. | Medium | Ch. 9, Pion Multiplicity |
| RFC feature provenance validation | RFC is merged, but feature extraction currently derives sphericity from TPC hit positions and leading-track “dE/dx” from summed energy, not the Ch. 9 reconstructed object variables; add tests tying RFC inputs to canonical event-variable code and cosmic weights. | Medium | Ch. 9 Machine Learning Method |
| Photon conversion map reproduction | Thesis reports 100 MeV photon conversion fractions (4.1% silicon, 23.1% beampipe, 5% TPC, 18.2% scintillator, 49.6% lead glass); no reproduction/validation task is on the plan. | Medium | Ch. 5, Map of photon interaction |
| Signal sample kinematics validation | Thesis uses 50k annihilation events and validates foil vertex distribution, pion/photon/proton KE peaks, and angular biases; current plan only verifies a 1000-event run output, not these physics distributions. | Medium | Ch. 6, Annihilation Event Simulation |
| Carbon foil radius and source-vertex alignment | Thesis and Ch. 3 detector concept use a 1 m-radius carbon target/foil, but `DetectorConstruction.cc` builds a 30 cm carbon radius, Python config uses 50 cm, and particle-gun fallback fixes `x=y=0`; align geometry/config/generator assumptions before trusting vertex and photon-conversion validations. | High | Ch. 3 NNBAR target; Ch. 6 signal vertex distribution |
| Beam-induced background and TPC occupancy validation | Appendix A quantifies absorber choices, photon/neutron fluxes, per-50 ns subsystem intensities, and ~25 µs TPC occupancy; MASTER_PLAN has cosmic weighting but no task to reproduce B4C/\(^{6}\)LiF/Cd beam-background tables or verify TPC rate assumptions. | High | Appendix A, beam-induced backgrounds and TPC full rates |
| G4GPU EM/gamma and neutron physics kernels | `docs/SPEC.md` describes `EMStepKernel.cu` and `NeutronStepKernel.cu` plus EM-shower validation, but MASTER_PLAN only lists muon, geometry, RTX, and optical phases. | Medium | G4GPU SPEC physics kernels |
| G4GPU full-event validation and benchmarks | `docs/VALIDATION.md` requires V7 full NNBAR event validation and B1-B5 throughput/speedup benchmarks; current G4GPU plan only covers phase-local tests. | Medium | G4GPU VALIDATION V7, B1-B5 |

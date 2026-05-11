# MCAccel competitor benchmark baseline

Last updated: 2026-05-11

This report is the side-by-side baseline ledger for competitor measurements on
identical LUNARC hardware. Each row is either a captured result with provenance
or an `OPEN:` blocker.

## Current results

| Project | Benchmark | Status | Hardware | Wall time (s) | Throughput | Evidence |
|---|---|---:|---|---:|---:|---|
| Celeritas | compact `celer-sim` simple-cms gamma primary run | QUEUED | LUNARC `gpua40`, 1x A40 | pending | pending | SLURM job 3041282, `PENDING (Resources)`, estimated start 2026-05-12 09:51:19; local script `benchmarks/competitors/celeritas/build.sh`; probe artifact `benchmarks/competitors/celeritas/configure-probe.txt` |
| AdePT | Example1/TestEm3 compact EM workload | OPEN | LUNARC `gpua40`, 1x A40 target | blocked | blocked | `benchmarks/competitors/adept/build.sh`; login configure probe succeeded, but GPU-node jobs 3041291/3041525 could not read the CERN `devAdePT` CVMFS view; see `benchmarks/competitors/adept/setup-blocker-3041525.txt` |
| Opticks | OpNovice2-like optical | OPEN | A100 target | — | — | Not attempted yet. |
| VecGeom | CPU navigation harness | OPEN | Xeon target | — | — | Not attempted yet. |
| GeantV | TaskBench legacy | OPEN | Xeon target | — | — | Not attempted yet. |
| WARP | PWR pin cell | OPEN | GPU target | — | — | Not attempted yet. |
| Serpent-MC GPU | OECD benchmarks | OPEN | A100 target | — | — | Not attempted; likely requires VTT/internal access. |

## Celeritas compact iteration notes

- Upstream source cloned on LUNARC under
  `/projects/hep/fs10/shared/nnbar/billy/mcaccel_competitors/celeritas/source`.
- Configure probe succeeded on LUNARC using `GCC/13.2.0`, `CMake/3.27.6`,
  `Ninja/1.11.1`, `CUDA/12.8.0`, and Geant4 11.2.2 from `hibeam_env`.
- Probe found `CELERITAS_USE_Geant4=ON`, `CELERITAS_USE_HepMC3=OFF`,
  `CELERITAS_USE_VecGeom=OFF`, and `CELERITAS_CORE_GEO=ORANGE`.
- Because HepMC3/VecGeom reference inputs were not available in the compact
  probe, this iteration uses Celeritas' upstream `celer-sim` app with the
  bundled `simple-cms.gdml` geometry and generated 100 MeV gamma primaries.

OPEN: Promote Celeritas to the lane's full reference row only after a follow-up
enables the upstream TestEm3/Hadr04/ZDC-style inputs (or documents a precise
blocker) with HepMC3/VecGeom support and captures the same parquet schema.

Queue blocker: `scontrol show job 3041282` reported `StartTime=2026-05-12T09:51:19` and `Reason=Resources`; no local or non-LUNARC benchmark was run as a substitute.

## AdePT compact iteration notes

- AdePT source exists on LUNARC at
  `/projects/hep/fs10/shared/nnbar/billy/mcaccel-competitors/AdePT` at commit
  `47694da970baebf8a7e5d7454910aac2313f33e3`.
- Configure probe evidence in
  `benchmarks/competitors/adept/logs/adept_config_probe.log` shows CUDA 12.8,
  Geant4 11.4.1, G4HepEm, HepMC3, VecCore, and VecGeom are available through
  the CERN `devAdePT` LCG view from the login/configure environment.
- The corrected worker-3 `adept/build.sh` checks the nightlies `devAdePT` view
  first, falls back to `latest`, builds `example1`, generates a fixed-seed
  TestEm3 macro, and writes the same parquet-summary style as Celeritas.
- GPU-node smoke job 3041525 failed before configure/build/run because neither
  `devAdePT` setup path was readable inside the A40 allocation. Policy
  partition job 3041518 was cancelled after that immediate blocker evidence.

OPEN: Provide a GPU-node-visible AdePT dependency stack (CVMFS `devAdePT` view
on A40 nodes, or a cached project-local Geant4/G4HepEm/VecCore/VecGeom/HepMC3
stack) before rerunning the AdePT baseline on `gpua40`.

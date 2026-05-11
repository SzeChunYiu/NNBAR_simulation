# MCAccel competitor baselines

All competitor builds and runs are performed on LUNARC. GPU baselines use one
A40 on the `gpua40` partition unless an `OPEN:` note says otherwise.

Primary upstream references used for this scaffold:

- Celeritas repository: https://github.com/celeritas-project/celeritas
- Celeritas installation docs: https://celeritas-project.github.io/celeritas/user/usage/installation.html
- Celeritas app docs (`celer-sim`, `celer-g4`): https://celeritas-project.github.io/celeritas/user/usage/execution/applications.html

| Project | Status | LUNARC script | Benchmark target | Notes |
|---|---|---|---|---|
| AdePT | OPEN | `adept/build.sh` | Example1/TestEm3 compact EM workload | Configure probe succeeded from the LUNARC login environment, but GPU-node jobs 3041291 and 3041525 could not read the CERN `devAdePT` CVMFS view. See `adept/setup-blocker-3041525.txt`; rerun after a GPU-visible dependency stack is available. |
| Celeritas | RUNNING | `celeritas/build.sh` | compact `celer-sim` simple-cms gamma workload | SLURM job 3041282 submitted on 2026-05-11 to `gpua40`; scheduler reported `PENDING (Resources)` with estimated start 2026-05-12 09:51:19. Full TestEm3/Hadr04/ZDC is still `OPEN:` until HepMC3/VecGeom/reference inputs are enabled. |
| Opticks | TODO | — | OpNovice2-like optical | Not started in this iteration. |
| VecGeom | TODO | — | CPU navigation harness | Not started in this iteration. |
| GeantV | TODO | — | legacy TaskBench | Not started in this iteration. |
| WARP | TODO | — | PWR pin cell | Not started in this iteration. |
| Serpent-MC GPU | TODO | — | OECD benchmarks | Not started in this iteration; likely external/internal access blocker. |

## Reproduce available jobs

From the simulation repo on the local workstation:

```bash
rtk proxy bash -lc 'ssh -O check lunarc 2>/dev/null && echo "Connected" || /Users/billy/lunarc-init.sh'
rtk proxy ./benchmarks/competitors/run_all.sh
```

AdePT writes remote artifacts under
`/projects/hep/fs10/shared/nnbar/billy/mcaccel-competitors/adept/results/`
once the GPU-node dependency blocker is resolved. Celeritas writes remote
artifacts under
`/projects/hep/fs10/shared/nnbar/billy/mcaccel_competitors/celeritas/results/`.
The local Celeritas configure/queue evidence snapshot is
`celeritas/configure-probe.txt`.

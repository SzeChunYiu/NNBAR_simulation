# OptiX 9 SDK download blocker

## Status — RESOLVED 2026-05-12

Operator transferred `NVIDIA-OptiX-SDK-9.0.0-linux64-x86_64.sh` (55.7 MB) from
local Mac to LUNARC. Installed with `--skip-license --include-subdir --prefix=.`
into `/projects/hep/fs10/shared/nnbar/billy/packages/NVIDIA-OptiX-SDK-9.0.0-linux64-x86_64/`;
symlink `optix-9.0` created. Verification: `OPTIX_READY` confirmed at
`optix-9.0/include/optix.h`. MASTER_PLAN Phase 3 promoted to `NEXT`.

## Required download

- URL: <https://developer.nvidia.com/designworks/optix/download>
- Version: OptiX 9.x, Linux 64-bit installer (`NVIDIA-OptiX-SDK-9.*-linux64.sh`)
- Target LUNARC directory: `/projects/hep/fs10/shared/nnbar/billy/packages/`
- Target install prefix after extraction: `/projects/hep/fs10/shared/nnbar/billy/packages/optix-9.0/`

## Operator commands after browser download

Run from the workstation directory containing the downloaded `.sh` installer.
Replace `NVIDIA-OptiX-SDK-9.0.0-linux64.sh` if NVIDIA provides a newer 9.x file
name.

```bash
rtk proxy bash -lc "ssh -O check lunarc 2>/dev/null && echo Connected || /Users/billy/lunarc-init.sh"
rtk proxy rsync -av NVIDIA-OptiX-SDK-9.0.0-linux64.sh lunarc:/projects/hep/fs10/shared/nnbar/billy/packages/
rtk proxy ssh lunarc 'cd /projects/hep/fs10/shared/nnbar/billy/packages && sh NVIDIA-OptiX-SDK-9.0.0-linux64.sh --skip-license --include-subdir --prefix=.'
```

If the installer creates a differently named subdirectory, normalize it to the
expected prefix:

```bash
rtk proxy ssh lunarc 'cd /projects/hep/fs10/shared/nnbar/billy/packages && test -d optix-9.0 || ln -s NVIDIA-OptiX-SDK-9.0.0-linux64 optix-9.0'
```

## Post-install verification

```bash
rtk proxy ssh lunarc 'test -f /projects/hep/fs10/shared/nnbar/billy/packages/optix-9.0/include/optix.h && echo OPTIX_READY'
```

After `OPTIX_READY` appears, update `docs/parallel-sessions/MASTER_PLAN.md` so
`Phase 3: RTX geometry backend` is `NEXT`, then rerun the worker-0 lane to claim
`g4gpu-phase3`.

## Search evidence from worker-0

Worker-0 checked LUNARC before writing this blocker note:

- `module spider OptiX` / `module avail OptiX optix` returned no usable OptiX module.
- `find` searches for `optix.h` under `/sw`, `/opt`, `/usr/local`, `/projects/hep/fs10/shared/nnbar/billy`, and `/home/scyiu` timed out without returning a header path.
- EasyBuild recipe files exist for OptiX 9.0.0 under `/sw/easybuild_milan/software/EasyBuild/.../easyconfigs/o/OptiX/`, but those are build recipes, not an installed SDK with `include/optix.h`.
- `/projects/hep/fs10/shared/nnbar/billy/packages` did not list an OptiX install or installer.

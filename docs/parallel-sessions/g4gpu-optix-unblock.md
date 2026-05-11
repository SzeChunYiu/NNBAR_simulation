# Lane: g4gpu-optix-unblock (Install OptiX 9 SDK on LUNARC)

## Goal

Unblock G4GPU Phase 3 (RTX geometry) by installing NVIDIA OptiX 9 SDK in user
space on LUNARC. The SDK is header-only + a small runtime library and lives
entirely under our project directory — no admin rights required.

## Blocker

NVIDIA OptiX SDK download requires accepting a click-through license at
https://developer.nvidia.com/designworks/optix/download — this is a manual,
browser-only step. You (the worker) cannot bypass it.

**Two acceptable paths:**

### Path A — Worker delegates to operator

1. Write a clear note in `docs/blockers/optix-sdk-download.md`:
   - URL: https://developer.nvidia.com/designworks/optix/download
   - Required version: OptiX 9.x (latest), Linux 64-bit
   - Target install path: `/projects/hep/fs10/shared/nnbar/billy/packages/optix-9.0/`
   - Required command after download:
     ```bash
     # On the workstation that downloaded the .sh installer:
     rsync -av NVIDIA-OptiX-SDK-9.0.0-linux64.sh lunarc:/projects/hep/fs10/shared/nnbar/billy/packages/
     ssh lunarc 'cd /projects/hep/fs10/shared/nnbar/billy/packages && sh NVIDIA-OptiX-SDK-9.0.0-linux64.sh --skip-license --include-subdir --prefix=.'
     ```
2. Verify the install plan compiles into a real next step (no ambiguity)
3. Commit the blocker note
4. Stop. The operator will execute the download + transfer.

### Path B — OptiX already installed somewhere we missed

Search exhaustively before assuming Path A:

```bash
rtk proxy ssh lunarc 'find /sw /opt /usr/local /projects /home -name "optix.h" -o -name "OptixSDK*" -o -name "NVIDIA-OptiX*" 2>/dev/null | head -30'
rtk proxy ssh lunarc 'module spider optix 2>&1 | grep -i optix'
rtk proxy ssh lunarc 'find /scratch -iname "*optix*" 2>/dev/null | head'
```

If found, write `docs/blockers/optix-sdk-found.md` documenting the location
and update `docs/parallel-sessions/g4gpu-phase3.md` with the include path.
Commit. Mark `g4gpu-phase3` as no longer blocked.

## Iteration cycle

1. Read this spec
2. Mark `g4gpu-optix-unblock` RUNNING in MASTER_PLAN.md
3. Try Path B first (exhaustive search)
4. If not found, execute Path A (write the blocker note)
5. Commit
6. Mark DONE

## Acceptance

Either:
- Path B: OptiX install path documented, Phase 3 spec updated, Phase 3 ready
  to be claimed as NEXT.
- Path A: Blocker note clearly written, operator action items unambiguous,
  status of `g4gpu-phase3` in MASTER_PLAN.md updated to `BLOCKED — see
  docs/blockers/optix-sdk-download.md`.

## Stop condition

After committing the result of Path B or A, stop.

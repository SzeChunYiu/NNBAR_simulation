# Spec: Fix LUNARC Geant4 Build

## Problem

The SLURM build script at:
`/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/slurm/build_nnbar.slurm`

fails because the Geant4 environment path is stale:
```
source /projects/hep/fs12/nnbar/software/geant4-MT/install/bin/geant4.sh
```
That path does not exist. There is no `Geant4` module available via `module avail` either.

## Task

1. Find a working Geant4 installation on LUNARC. Search:
   - `/projects/hep/fs10/shared/nnbar/` — look for `geant4.sh` or `geant4-config`
   - `/projects/hep/fs10/shared/` — shared software
   - `/home/scyiu/nnbar/` — user's own installs (found: `/home/scyiu/nnbar/acts/output/usr/local/bin/geant4.sh` — check if this is a full usable install)
   - Check conda envs at `/projects/hep/fs10/shared/nnbar/billy/packages/` for a geant4 package
   - Ask LUNARC what is available: `ssh lunarc "find /projects/hep -name 'geant4-config' 2>/dev/null | head -20"`

2. Once the correct Geant4 path is found, update `build_nnbar.slurm` (on LUNARC at the path above):
   - Replace the broken `source ...geant4.sh` line with the correct one
   - Also update the `module load` lines to match whatever toolchain that Geant4 was built with
   - The Arrow library is bundled at `external/arrow-install-linux/` — CMake picks it up automatically, no Arrow module needed

3. If no usable Geant4 exists, install via conda:
   ```bash
   /projects/hep/fs10/shared/nnbar/billy/packages/hibeam_env/bin/conda install -c conda-forge geant4 -y
   ```
   Then source it from the conda prefix.

4. After fixing, resubmit: `ssh lunarc "sbatch /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/slurm/build_nnbar.slurm"`

5. Verify the build succeeded: `ssh lunarc "ls -lh /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/build_lunarc/nnbar-detector-simulation*"`

## Key Files

- SLURM script: `/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/slurm/build_nnbar.slurm`
- Source tree: `/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/`
- CMakeLists.txt auto-detects Arrow from `external/arrow-install-linux/` on Linux — no changes needed there
- SLURM account: `lu2026-2-51`, partition: `lu48`

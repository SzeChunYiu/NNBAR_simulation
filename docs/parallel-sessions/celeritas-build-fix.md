# Celeritas Build Fix — geant4.sh conda incompatibility

## Finding

Job 3047497 (mcaccel-celeritas) FAILED after 1:17 at 2026-05-12T20:47:57.

**Root cause (atomic)**:

`build-fixed-20260512.sh` has:
```bash
if [ -f "$HIB/bin/geant4.sh" ]; then
  source "$HIB/bin/geant4.sh"
fi
```

`$HIB/bin/geant4.sh` is a guard script placed by Geant4 in conda installs.
When sourced inside an active conda env it prints:
```
ERROR: geant4.sh and geant4.csh are not needed with conda
Look at using "conda activate ENVIRONMENT_NAME"
```
and exits non-zero. `set -euo pipefail` is active, so the script dies there.
Conda already exports all Geant4 env vars through activate.d hooks;
sourcing geant4.sh is not only unnecessary but actively harmful.

## Fix

In `/projects/hep/fs10/shared/nnbar/billy/mcaccel_competitors/celeritas/build-fixed-20260512.sh`,
remove the geant4.sh block:

```diff
-if [ -f "$HIB/bin/geant4.sh" ]; then
-  # shellcheck disable=SC1091
-  source "$HIB/bin/geant4.sh"
-fi
```

Replace with explicit conda activate.d sourcing (already used in the NNBAR
cosmic sbatch scripts):
```bash
set +u
for f in "$HIB"/etc/conda/activate.d/*.sh; do
  [ -f "$f" ] && source "$f"
done
set -u
```

## File to edit

`/projects/hep/fs10/shared/nnbar/billy/mcaccel_competitors/celeritas/build-fixed-20260512.sh`
(lines ~41–45 in the current version)

## Resubmit

After applying the fix, resubmit:
```bash
cd /projects/hep/fs10/shared/nnbar/billy/mcaccel_competitors/celeritas
sbatch build-fixed-20260512.sh
```

Expected: job runs ~90 min on an A40 GPU node, produces
`results/results.parquet` and `results/provenance.txt`.

## Local copy

Also update the local copy at:
`/Volumes/MyDrive/nnbar/nnbar/simulation/` — check if `build-fixed-20260512.sh`
is tracked in git; if yes, commit the fix.

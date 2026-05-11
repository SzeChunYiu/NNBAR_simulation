#!/usr/bin/env bash
# Launch available MCAccel competitor benchmark jobs on LUNARC.
set -euo pipefail

REMOTE_ROOT=${REMOTE_ROOT:-/projects/hep/fs10/shared/nnbar/billy/mcaccel_competitors}
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

ssh -O check lunarc 2>/dev/null && echo "Connected" || /Users/billy/lunarc-init.sh
ssh lunarc "mkdir -p '$REMOTE_ROOT/celeritas'"
scp "$SCRIPT_DIR/celeritas/build.sh" "lunarc:$REMOTE_ROOT/celeritas/build.sh"
ssh lunarc "chmod +x '$REMOTE_ROOT/celeritas/build.sh' && sbatch '$REMOTE_ROOT/celeritas/build.sh'"

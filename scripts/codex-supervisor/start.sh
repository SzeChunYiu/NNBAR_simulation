#!/usr/bin/env bash
# Wrapper that launches the upstream codex-supervisor with this project's
# prompt file. Resolves the upstream binary via $CODEX_SUPERVISOR or a
# default path under ~/Desktop/projects/codex-supervisor/.

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
SUPERVISOR="${CODEX_SUPERVISOR:-$HOME/Desktop/projects/codex-supervisor/codex-supervisor.sh}"

if [[ ! -x "$SUPERVISOR" ]]; then
    echo "error: codex-supervisor not found at $SUPERVISOR" >&2
    echo "       set CODEX_SUPERVISOR=/path/to/codex-supervisor.sh" >&2
    exit 1
fi

# Use a project-specific tmux session name so we coexist with any other
# codex-supervisor session already running (e.g. "codex-supervisor").
export CODEX_SUPERVISOR_SESSION="${CODEX_SUPERVISOR_SESSION:-nnbar-rebuild}"

# Run from this directory so codex-supervisor finds ./codex-prompts.txt.
cd "$HERE"
exec "$SUPERVISOR" "$@"

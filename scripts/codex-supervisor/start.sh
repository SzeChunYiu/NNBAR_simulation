#!/usr/bin/env bash
# Wrapper that launches the upstream codex-supervisor with this project's
# prompt file and a session name disjoint from any other supervisor
# (notably babbloo's).

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"

# Point at the upstream binary directly. The historical rename to
# `nnbar-supervisor.sh` was a workaround for a stale `reap_stale_daemons`
# implementation that matched on filename; that function is now session-
# aware (matches `--session <SESSION>` explicitly), so the rename is
# unnecessary. Override via CODEX_SUPERVISOR if the upstream lives
# elsewhere.
SUPERVISOR="${CODEX_SUPERVISOR:-$HOME/Desktop/projects/codex-supervisor/codex-supervisor.sh}"

if [[ ! -x "$SUPERVISOR" ]]; then
    echo "error: codex-supervisor not found at $SUPERVISOR" >&2
    echo "       set CODEX_SUPERVISOR=/path/to/codex-supervisor.sh" >&2
    exit 1
fi

# Project-specific tmux session name so we coexist with any other
# codex-supervisor session (babbloo, etc).
export CODEX_SUPERVISOR_SESSION="${CODEX_SUPERVISOR_SESSION:-nnbar-rebuild}"

# After each /goal "Goal achieved", re-send the original prompt so the
# respawned codex reads the (possibly updated) per-lane spec.
export CODEX_SUPERVISOR_ON_COMPLETE="${CODEX_SUPERVISOR_ON_COMPLETE:-redo}"

# Kill+respawn codex on goal completion → fresh context every iteration.
export CODEX_SUPERVISOR_RESPAWN_ON_GOAL="${CODEX_SUPERVISOR_RESPAWN_ON_GOAL:-1}"

# Run from repo root so panes' cwd resolves docs/parallel-sessions/*.md.
REPO_ROOT="$(cd "$HERE/../.." && pwd)"
export CODEX_SUPERVISOR_PROMPTS="$HERE/codex-prompts.txt"

cd "$REPO_ROOT"

# On `start`, pass --session as a CLI flag (in addition to the env var)
# so the upstream reap_stale_daemons matches our daemon by session name
# and only reaps OUR own stale daemons, not babbloo's. Other subcommands
# (stop, status, etc.) read the session from the env var.
if [[ "${1:-start}" == "start" ]]; then
    shift 2>/dev/null || true
    exec "$SUPERVISOR" start --session "$CODEX_SUPERVISOR_SESSION" "$@"
fi
exec "$SUPERVISOR" "$@"

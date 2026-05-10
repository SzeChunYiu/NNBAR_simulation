#!/usr/bin/env bash
# Wrapper that launches the upstream codex-supervisor with this project's
# prompt file. Resolves the upstream binary via $CODEX_SUPERVISOR or a
# default path under ~/Desktop/projects/codex-supervisor/.

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
# Use a renamed local copy of the supervisor so its command line does NOT
# contain "codex-supervisor", which would otherwise be caught by another
# instance's reap_stale_daemons grep and killed.
SUPERVISOR="${CODEX_SUPERVISOR:-$HERE/nnbar-supervisor.sh}"

if [[ ! -x "$SUPERVISOR" ]]; then
    echo "error: codex-supervisor not found at $SUPERVISOR" >&2
    echo "       set CODEX_SUPERVISOR=/path/to/codex-supervisor.sh" >&2
    exit 1
fi

# Use a project-specific tmux session name so we coexist with any other
# codex-supervisor session already running (e.g. "codex-supervisor").
export CODEX_SUPERVISOR_SESSION="${CODEX_SUPERVISOR_SESSION:-nnbar-rebuild}"

# After each /goal "Goal achieved", re-send the original prompt so the
# lane reads the (possibly updated) per-lane spec and starts a fresh
# pursuit. Equivalent to "start a new session after every goal" — codex
# treats /goal as a context reset, and the lane spec re-read picks up
# any wave changes that landed since the last iteration.
export CODEX_SUPERVISOR_ON_COMPLETE="${CODEX_SUPERVISOR_ON_COMPLETE:-redo}"

# When a goal is achieved, kill+respawn the codex CLI process before
# sending the next /goal. This guarantees a fresh codex (no accumulated
# context, no leaked worktree handles, no stale MCP children) per
# iteration — equivalent to "restart codex instead of giving a new /goal
# in the same session". Trade-off: ~10 s of MCP boot per iteration.
export CODEX_SUPERVISOR_RESPAWN_ON_GOAL="${CODEX_SUPERVISOR_RESPAWN_ON_GOAL:-1}"

# Launch from the simulation repo root so codex panes' working directory
# resolves docs/parallel-sessions.md and docs/parallel-sessions/L*.md as
# relative paths. Pass the prompts file explicitly via env var.
REPO_ROOT="$(cd "$HERE/../.." && pwd)"
export CODEX_SUPERVISOR_PROMPTS="$HERE/codex-prompts.txt"

cd "$REPO_ROOT"

# Hard-coded behavior: when we `start` the supervisor we ALWAYS open a
# Terminal window attached to the tmux session. The user wants to see
# the panes; --no-attach is not a thing here. (Other subcommands —
# stop/status/restart/etc — pass through unchanged.)
if [[ "${1:-start}" == "start" ]]; then
    # Strip --no-attach if someone passed it so we can't be silenced.
    args=()
    for a in "$@"; do
        [[ "$a" == "--no-attach" ]] && continue
        args+=("$a")
    done
    # If no subcommand was given, args is empty; inject "start".
    [[ ${#args[@]} -eq 0 ]] && args=("start")
    "$SUPERVISOR" "${args[@]}"
    # Ensure a Terminal.app window opens regardless of the upstream's
    # CODEX_SUPERVISOR_OPEN behavior.
    exec "$SUPERVISOR" attach
fi

exec "$SUPERVISOR" "$@"

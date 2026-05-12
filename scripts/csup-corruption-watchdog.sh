#!/usr/bin/env bash
# csup-corruption-watchdog.sh — periodic watcher that detects and recovers
# from the codex-supervisor /goal -> /model send corruption.
#
# Background: codex-supervisor.sh sends `/` then types the rest of /goal
# character-by-character into codex's slash-command popup. If codex's popup
# happens to highlight a wrong item (e.g. /model) when the first Enter
# arrives, the prompt becomes a malformed /model command. This watchdog
# detects that case and re-injects the original prompt via bracketed paste
# (which bypasses codex's per-char popup interaction).
#
# Usage:
#   bash scripts/csup-corruption-watchdog.sh                 # run forever
#   bash scripts/csup-corruption-watchdog.sh --once          # single pass
#   bash scripts/csup-corruption-watchdog.sh --interval 30   # 30 s loop
#
# Detected corruption signals (any of these in pane content):
#   - "/model goal You are PANE"
#   - "model: String should have at most 256 characters"
#   - "/g[!a-z]" right after Enter where /goal was expected
#
# The watchdog reads the matching session's prompts file to look up the
# CANONICAL prompt for each pane, then re-pastes it.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

INTERVAL=20
ONCE=0
while (( $# > 0 )); do
  case "$1" in
    --once)     ONCE=1; shift ;;
    --interval) INTERVAL="$2"; shift 2 ;;
    *)          echo "unknown arg: $1"; exit 2 ;;
  esac
done

# Map sessions -> prompts file. Keep this Bash-3.2-compatible for local macOS
# validation; associative arrays are unavailable in /bin/bash on macOS.
PROMPTS_FILES=(
  "nnbar-recon-lunarc=codex-prompts-recon.txt"
  "nnbar-sim-lunarc=codex-prompts-sim.txt"
  "nnbar-g4gpu-lunarc=codex-prompts-g4gpu.txt"
  "nnbar-review-lunarc=codex-prompts-review.txt"
  "nnbar-meta-lunarc=codex-prompts-meta.txt"
)

# Patterns that indicate corruption
CORRUPTION_PATTERNS=(
  '/model goal You are PANE'
  'model: String should have at most 256'
  'invalid_request_error.*model'
  '(^|[[:space:]])/g([^[:alpha:]]|$)'
)

LUNARC_SOCKET_READY=0

ensure_lunarc_socket() {
  [[ "$LUNARC_SOCKET_READY" == "1" ]] && return 0
  ssh -O check lunarc >/dev/null 2>&1 || /Users/billy/lunarc-init.sh
  LUNARC_SOCKET_READY=1
}

ssh_lunarc() {
  ensure_lunarc_socket
  ssh lunarc "$@"
}

# Find the LUNARC nnbar-csup jobid (so srun --jobid can land on the node)
get_jobid() {
  ssh_lunarc "squeue -h -u \$USER -n nnbar-csup -t RUNNING -o '%i' 2>/dev/null | head -1"
}

# Re-inject prompt for a single pane via bracketed paste.
reinject() {
  local jobid="$1" session="$2" pane_idx="$3" prompt="$4"
  ssh_lunarc "srun --jobid='$jobid' --overlap bash -lc '
    BUF=\$(mktemp /tmp/csup-reinject.XXXXXX)
    printf %s \"$prompt\" > \"\$BUF\"
    tmux send-keys -t \"$session:.$pane_idx\" Escape 2>/dev/null
    sleep 0.3
    tmux send-keys -t \"$session:.$pane_idx\" C-u 2>/dev/null
    sleep 0.2
    tmux load-buffer -b csup_reinject \"\$BUF\"
    tmux paste-buffer -b csup_reinject -t \"$session:.$pane_idx\"
    sleep 0.6
    tmux send-keys -t \"$session:.$pane_idx\" Enter
    rm -f \"\$BUF\"
  '"
}

run_once() {
  local jobid
  LUNARC_SOCKET_READY=0
  ensure_lunarc_socket
  jobid=$(get_jobid)
  if [[ -z "$jobid" ]]; then
    echo "no RUNNING nnbar-csup holder; skipping"
    return
  fi
  for prompt_mapping in "${PROMPTS_FILES[@]}"; do
    local session="${prompt_mapping%%=*}"
    local prompts_file="${prompt_mapping#*=}"
    [ -f "$prompts_file" ] || continue
    # List of /goal lines, indexed 0..N-1
    LINES=()
    while IFS= read -r prompt_line; do
      LINES+=("$prompt_line")
    done < <(grep -E '^/goal' "$prompts_file")

    # Capture all panes in the session
    local panes_raw
    if ! panes_raw=$(ssh_lunarc "srun --jobid='$jobid' --overlap bash -lc 'tmux list-panes -t $session -F \"#{pane_index}\" 2>/dev/null'"); then
      echo "  [$session] unable to list panes; skipping"
      continue
    fi

    local pane_ordinal=0
    while read -r idx; do
      [[ -z "$idx" ]] && continue
      local prompt_idx=$pane_ordinal
      pane_ordinal=$((pane_ordinal + 1))
      local cap
      if ! cap=$(ssh_lunarc "srun --jobid='$jobid' --overlap bash -lc 'tmux capture-pane -t \"$session:.$idx\" -p -S -80 2>/dev/null'"); then
        echo "  [$session pane $idx] unable to capture pane; skipping"
        continue
      fi
      local corrupt=0
      for pat in "${CORRUPTION_PATTERNS[@]}"; do
        if printf '%s' "$cap" | grep -Eq "$pat"; then
          corrupt=1
          break
        fi
      done
      if (( corrupt )); then
        # tmux pane_index may be one-based on LUNARC; map by list position.
        local prompt="${LINES[$prompt_idx]:-}"
        if [[ -z "$prompt" ]]; then
          echo "  [$session pane $idx] CORRUPT but no prompt at index $prompt_idx; skipping"
          continue
        fi
        echo "  [$session pane $idx] CORRUPT — re-injecting prompt"
        reinject "$jobid" "$session" "$idx" "$prompt"
      fi
    done <<< "$panes_raw"
  done
}

if (( ONCE )); then
  run_once
  exit 0
fi

echo "csup-corruption-watchdog: loop every ${INTERVAL}s; Ctrl-C to stop"
while true; do
  ts=$(date '+%Y-%m-%d %H:%M:%S')
  echo "[$ts] sweep"
  run_once || true
  sleep "$INTERVAL"
done

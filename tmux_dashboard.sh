#!/bin/bash
#
# HIBEAM Pipeline - tmux Live Dashboard
#
# Creates a tmux session "hibeam-dash" with:
#   Top-left:  LUNARC cluster job status (refreshes every 10s)
#   Top-right: Task list (refreshes every 5s)
#   Bottom:    One pane per active agent (refreshes every 3s)
#
# Usage:
#   ./tmux_dashboard.sh          Launch dashboard (or attach if exists)
#   ./tmux_dashboard.sh kill     Kill existing dashboard session
#   ./tmux_dashboard.sh status   Show active agents without tmux
#
# Requirements: tmux, python3, ssh access to lunarc
#

set -euo pipefail

SESSION="hibeam-dash"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TASK_DIR="/tmp/claude-1000/-home-billy-nnbar-simulation/tasks"

# Colors for terminal output (not tmux)
R="\033[0m"
GREEN="\033[1;32m"
YELLOW="\033[0;33m"
RED="\033[1;31m"
CYAN="\033[0;36m"
DIM="\033[0;90m"
BOLD="\033[1m"

# ---------------------------------------------------------------
# Preflight checks
# ---------------------------------------------------------------
check_deps() {
    if ! command -v tmux &>/dev/null; then
        echo -e "${RED}Error: tmux is not installed.${R}"
        echo "  Install with: sudo apt install tmux"
        exit 1
    fi
    if ! command -v python3 &>/dev/null; then
        echo -e "${RED}Error: python3 is not found.${R}"
        exit 1
    fi
}

# ---------------------------------------------------------------
# Discover active agents (modified in last 5 minutes)
# ---------------------------------------------------------------
get_active_agents() {
    python3 "${SCRIPT_DIR}/_dash_agents.py" --list 2>/dev/null
}

# ---------------------------------------------------------------
# Generate the watch command for a pane
# ---------------------------------------------------------------

# Cluster pane: run _dash_cluster.sh in a loop
cluster_cmd() {
    echo "while true; do clear; bash '${SCRIPT_DIR}/_dash_cluster.sh'; sleep 10; done"
}

# Task pane: run _dash_tasks.py in a loop
task_cmd() {
    echo "while true; do clear; python3 '${SCRIPT_DIR}/_dash_tasks.py'; sleep 5; done"
}

# Agent pane: run _dash_agents.py for a specific agent in a loop
agent_cmd() {
    local agent_id="$1"
    echo "while true; do clear; python3 '${SCRIPT_DIR}/_dash_agents.py' '${agent_id}'; sleep 3; done"
}

# All-agents pane: show all agents combined
all_agents_cmd() {
    echo "while true; do clear; python3 '${SCRIPT_DIR}/_dash_agents.py' --all; sleep 3; done"
}

# OpenClaw agents pane: show real-time Claude Code agent monitor
openclaw_agents_cmd() {
    echo "while true; do clear; python3 '${SCRIPT_DIR}/_dash_openclaw_agents.py'; sleep 2; done"
}

# OpenClaw agents compact: one-line-per-agent view
openclaw_compact_cmd() {
    echo "while true; do clear; python3 '${SCRIPT_DIR}/_dash_openclaw_agents.py' --compact; sleep 2; done"
}

# ---------------------------------------------------------------
# Kill existing session
# ---------------------------------------------------------------
kill_session() {
    if tmux has-session -t "$SESSION" 2>/dev/null; then
        tmux kill-session -t "$SESSION"
        echo -e "${YELLOW}Killed session '${SESSION}'${R}"
    else
        echo -e "${DIM}No session '${SESSION}' found${R}"
    fi
}

# ---------------------------------------------------------------
# Build and launch dashboard
# ---------------------------------------------------------------
launch_dashboard() {
    local mode="${1:-hibeam}"  # hibeam or openclaw
    
    # Kill existing session if any
    if tmux has-session -t "$SESSION" 2>/dev/null; then
        echo -e "${YELLOW}Killing existing session '${SESSION}'...${R}"
        tmux kill-session -t "$SESSION"
    fi

    # Discover active agents
    local agents
    agents=$(get_active_agents)
    local agent_count
    agent_count=$(echo "$agents" | grep -c '[a-f0-9]' 2>/dev/null || echo 0)

    echo -e "${CYAN}${BOLD}HIBEAM Pipeline Dashboard${R}"
    echo -e "${DIM}Active agents: ${agent_count}${R}"
    echo -e "${DIM}Mode: ${mode}${R}"

    # Detect terminal size for absolute pane dimensions
    local term_cols=$(tput cols 2>/dev/null || echo 200)
    local term_rows=$(tput lines 2>/dev/null || echo 50)
    local half_cols=$((term_cols / 2))
    local agent_rows=$((term_rows * 7 / 10))  # 70% for agents
    local third_cols=$((term_cols / 3))
    local half_agent=$((agent_rows / 2))

    # Create session with the cluster pane (top-left)
    tmux new-session -d -s "$SESSION" -x "$term_cols" -y "$term_rows" "$(cluster_cmd)"

    # Split top row: task list on the right (50% width)
    tmux split-window -h -t "${SESSION}:0.0" -l "$half_cols" "$(task_cmd)"

    # Now create agent panes below the top row
    if [ "$agent_count" -eq 0 ]; then
        # No active agents - show OpenClaw agent monitor instead
        tmux split-window -v -t "${SESSION}:0.0" -l "$agent_rows" "$(openclaw_agents_cmd)"
    elif [ "$agent_count" -eq 1 ]; then
        # Single agent - one pane below
        local aid
        aid=$(echo "$agents" | head -1)
        tmux split-window -v -t "${SESSION}:0.0" -l "$agent_rows" "$(agent_cmd "$aid")"
    elif [ "$agent_count" -eq 2 ]; then
        # Two agents - split bottom into 2 columns
        local a1 a2
        a1=$(echo "$agents" | sed -n '1p')
        a2=$(echo "$agents" | sed -n '2p')
        tmux split-window -v -t "${SESSION}:0.0" -l "$agent_rows" "$(agent_cmd "$a1")"
        tmux split-window -h -t "${SESSION}:0.2" -l "$half_cols" "$(agent_cmd "$a2")"
    elif [ "$agent_count" -eq 3 ]; then
        # Three agents - bottom split into 3
        local a1 a2 a3
        a1=$(echo "$agents" | sed -n '1p')
        a2=$(echo "$agents" | sed -n '2p')
        a3=$(echo "$agents" | sed -n '3p')
        tmux split-window -v -t "${SESSION}:0.0" -l "$agent_rows" "$(agent_cmd "$a1")"
        tmux split-window -h -t "${SESSION}:0.2" -l $((term_cols * 2 / 3)) "$(agent_cmd "$a2")"
        tmux split-window -h -t "${SESSION}:0.3" -l "$half_cols" "$(agent_cmd "$a3")"
    elif [ "$agent_count" -le 6 ]; then
        # 4-6 agents - 2 rows of agent panes
        local i=0
        local row1=()
        local row2=()
        while IFS= read -r aid; do
            [ -z "$aid" ] && continue
            if [ $i -lt 3 ]; then
                row1+=("$aid")
            else
                row2+=("$aid")
            fi
            i=$((i + 1))
        done <<< "$agents"

        # First row of agents (middle)
        tmux split-window -v -t "${SESSION}:0.0" -l "$agent_rows" "$(agent_cmd "${row1[0]}")"
        local pane_idx=2
        for j in $(seq 1 $((${#row1[@]} - 1))); do
            tmux split-window -h -t "${SESSION}:0.${pane_idx}" "$(agent_cmd "${row1[$j]}")"
            pane_idx=$((pane_idx + 1))
        done

        # Second row of agents (bottom) if any
        if [ ${#row2[@]} -gt 0 ]; then
            tmux split-window -v -t "${SESSION}:0.${pane_idx}" -l "$half_agent" "$(agent_cmd "${row2[0]}")"
            pane_idx=$((pane_idx + 1))
            for j in $(seq 1 $((${#row2[@]} - 1))); do
                tmux split-window -h -t "${SESSION}:0.${pane_idx}" "$(agent_cmd "${row2[$j]}")"
                pane_idx=$((pane_idx + 1))
            done
        fi
    else
        # Many agents - use combined view
        tmux split-window -v -t "${SESSION}:0.0" -l "$agent_rows" "$(all_agents_cmd)"
    fi

    # Set tmux options for nice display
    tmux set-option -t "$SESSION" -g status-style "bg=colour235,fg=colour136"
    tmux set-option -t "$SESSION" -g status-left "#[fg=colour46,bold] HIBEAM Dashboard "
    tmux set-option -t "$SESSION" -g status-right "#[fg=colour245] %Y-%m-%d %H:%M:%S "
    tmux set-option -t "$SESSION" -g status-interval 1
    tmux set-option -t "$SESSION" -g pane-border-style "fg=colour238"
    tmux set-option -t "$SESSION" -g pane-active-border-style "fg=colour46"

    # Enable mouse for easy pane resizing
    tmux set-option -t "$SESSION" -g mouse on 2>/dev/null || true

    echo -e "${GREEN}Dashboard created. Attaching...${R}"
    echo -e "${DIM}  Ctrl+B then D to detach${R}"
    echo -e "${DIM}  Mouse scroll and resize enabled${R}"
    echo ""

    # Attach or switch to session
    if [ -n "${TMUX:-}" ]; then
        tmux switch-client -t "$SESSION"
    else
        tmux attach-session -t "$SESSION"
    fi
}

# ---------------------------------------------------------------
# Status mode - no tmux, just print
# ---------------------------------------------------------------
show_status() {
    echo -e "${CYAN}${BOLD}HIBEAM Pipeline Status${R}  ${DIM}$(date '+%H:%M:%S')${R}"
    echo ""
    bash "${SCRIPT_DIR}/_dash_cluster.sh"
    echo ""
    python3 "${SCRIPT_DIR}/_dash_tasks.py"
    echo ""
    echo -e "${CYAN}${BOLD}  AGENTS:${R}"
    python3 "${SCRIPT_DIR}/_dash_agents.py" --all
}

# ---------------------------------------------------------------
# Main
# ---------------------------------------------------------------
case "${1:-}" in
    kill|stop)
        check_deps
        kill_session
        ;;
    status|--status|-s)
        show_status
        ;;
    agents|openclaw)
        # Launch OpenClaw agent monitor standalone
        check_deps
        python3 "${SCRIPT_DIR}/_dash_openclaw_agents.py" --watch
        ;;
    agents-compact)
        # Launch compact OpenClaw agent view
        check_deps
        python3 "${SCRIPT_DIR}/_dash_openclaw_agents.py" --compact
        ;;
    help|--help|-h)
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  (none)    Launch tmux dashboard (or reattach)"
        echo "  kill      Kill existing dashboard session"
        echo "  status    Show status without tmux (works anywhere)"
        echo "  agents    Launch OpenClaw agent monitor (live refresh)"
        echo "  agents-compact  Show agent status in compact one-line format"
        echo "  help      Show this help"
        echo ""
        echo "Inside the dashboard:"
        echo "  Ctrl+B D       Detach from dashboard"
        echo "  Ctrl+B [       Scroll mode (q to exit)"
        echo "  Mouse scroll   Scroll pane output"
        ;;
    *)
        check_deps
        launch_dashboard
        ;;
esac

#!/bin/bash
#
# OpenClaw Agent Monitor - Standalone launcher
#
# Real-time monitoring of Claude Code agent sessions.
# Shows active agents, tool calls, outputs, and status.
#
# Usage:
#   ./openclaw-monitor.sh           Live refresh (every 2s)
#   ./openclaw-monitor.sh compact   One-line-per-agent view
#   ./openclaw-monitor.sh list      Print session keys (for scripting)
#   ./openclaw-monitor.sh <id>      Show specific session by ID
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
GREEN="\033[1;32m"
CYAN="\033[0;36m"
DIM="\033[0;90m"
R="\033[0m"

case "${1:-}" in
    compact|c)
        echo -e "${CYAN}OpenClaw Agent Monitor (compact)${R}"
        echo -e "${DIM}Press Ctrl+C to exit${R}"
        echo ""
        exec python3 "${SCRIPT_DIR}/_dash_openclaw_agents.py" --watch --compact
        ;;
    list|l)
        exec python3 "${SCRIPT_DIR}/_dash_openclaw_agents.py" --list
        ;;
    once|1)
        exec python3 "${SCRIPT_DIR}/_dash_openclaw_agents.py"
        ;;
    help|--help|-h)
        echo "OpenClaw Agent Monitor"
        echo ""
        echo "Usage: $0 [command|session_id]"
        echo ""
        echo "Commands:"
        echo "  (none)   Live refresh view (Ctrl+C to exit)"
        echo "  compact  One-line-per-agent view"
        echo "  list     Print session keys for scripting"
        echo "  once     Single snapshot (no refresh)"
        echo "  help     Show this help"
        echo ""
        echo "Examples:"
        echo "  $0                    # Live dashboard"
        echo "  $0 compact            # Compact live view"
        echo "  $0 list | head -5     # Get recent sessions"
        echo "  $0 abc123             # Show session matching 'abc123'"
        ;;
    *)
        if [ -n "${1:-}" ]; then
            # Specific session
            exec python3 "${SCRIPT_DIR}/_dash_openclaw_agents.py" "$1"
        else
            # Default: live watch
            echo -e "${CYAN}OpenClaw Agent Monitor${R}"
            echo -e "${DIM}Press Ctrl+C to exit${R}"
            echo ""
            exec python3 "${SCRIPT_DIR}/_dash_openclaw_agents.py" --watch
        fi
        ;;
esac

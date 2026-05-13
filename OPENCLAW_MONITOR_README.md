# 🐼 OpenClaw Agent Monitor

Real-time dashboard for monitoring Claude Code agent sessions, information flow, and task progress.

## Quick Start

```bash
# From the simulation directory
cd ~/nnbar/simulation

# Live monitoring (refreshes every 2s)
./openclaw-monitor.sh

# Or use the main dashboard (includes OpenClaw pane)
./tmux_dashboard.sh
```

## Features

### Agent Status Tracking
- **● LIVE** (green bg) — Activity within last 15 seconds
- **● ACTIVE** (green) — Activity within last 60 seconds  
- **○ IDLE** (yellow) — No activity for 1-5 minutes
- **◌ STALE** (dim) — No activity for 5+ minutes

### Session Types
- `[MAIN]` — Main agent session (direct chat with Billy)
- `[SUB]` — Subagent (spawned for specific tasks)
- `[CRON]` — Scheduled cron job execution
- `[WA]` — WhatsApp channel
- `[TG]` — Telegram channel
- `[WEB]` — Webchat interface

### Information Displayed
- **Task description** — What the agent is working on
- **Tool calls** — `▶ exec(command...)`, `▶ read(path)`, etc.
- **Results** — `↳ Output from tool calls`
- **Text output** — Agent responses and progress
- **Stats** — Tool count, token usage, session size

## Usage Options

### Standalone Monitor
```bash
./openclaw-monitor.sh           # Live refresh (default)
./openclaw-monitor.sh compact   # One line per agent
./openclaw-monitor.sh list      # Print session keys
./openclaw-monitor.sh once      # Single snapshot
./openclaw-monitor.sh <id>      # Show specific session
```

### Via tmux_dashboard.sh
```bash
./tmux_dashboard.sh             # Full dashboard with agents pane
./tmux_dashboard.sh agents      # Just the agent monitor
./tmux_dashboard.sh agents-compact  # Compact view
./tmux_dashboard.sh status      # One-shot status (no tmux)
```

### Direct Python Usage
```bash
python3 _dash_openclaw_agents.py              # All active agents
python3 _dash_openclaw_agents.py --compact    # One line each
python3 _dash_openclaw_agents.py --watch      # Continuous refresh
python3 _dash_openclaw_agents.py --list       # Session keys only
python3 _dash_openclaw_agents.py <session_id> # Specific session
```

## Data Sources

The monitor reads from:
- `~/.openclaw/agents/main/sessions/*.jsonl` — Agent session transcripts
- `~/.openclaw/cron/runs/*.jsonl` — Cron job executions

Each JSONL file contains:
- Session metadata (ID, channel, model)
- User messages (tasks)
- Assistant responses (thinking, tool calls, text)
- Tool results
- Usage statistics (tokens, cost)

## Integration with Existing Dashboard

The OpenClaw agent monitor is integrated into `tmux_dashboard.sh`:

1. **Bottom pane** — When no HIBEAM-specific agents are detected, the dashboard shows the OpenClaw agent monitor instead
2. **Direct access** — Use `./tmux_dashboard.sh agents` for just the monitor
3. **Compact mode** — Use `./tmux_dashboard.sh agents-compact` for minimal display

## Example Output

```
══════════════════════════════════════════════════════════════════
  🐼 OPENCLAW AGENT MONITOR  12:54:48
  ● 2 LIVE   ○ 1 idle  │  Tools: 51  Tokens: 1357k
══════════════════════════════════════════════════════════════════

[SUB] Analyze and enhance...   ● LIVE   opus4.5 │ 13t 12m │ 396k tok
──────────────────────────────────────────────────────────────────
  Task: Analyze and enhance Billy's tmux dashboard...
  11:52:03 ▶ read(~/nnbar/simulation/tmux_dashboard.sh)
  11:52:09 ▶ exec(find /home/billy -name "*.jsonl")
  11:53:23   Creating enhanced agent monitor component...
  11:53:26 ▶ write(/home/billy/nnbar/simulation/_dash_openclaw...)

[SUB] Create automatic t...   ● ACTIVE   opus4.5 │ 18t 15m │ 276k tok
──────────────────────────────────────────────────────────────────
  Task: Create automatic tmux dashboard launcher...
  11:53:12   Now I'll create a wrapper solution...
  11:53:25 ▶ write(/home/billy/.local/bin/claude-with-dashboard)
```

## Compact View Example

```
 ● S Analyze and enhance   │  13t  396k │ ▶ exec(cd ~/nnbar/simulation...)
 ● S Create automatic t    │  18t  276k │ ▶ write(/home/billy/nnbar/sim...)
 ○ S System: [2026-02-0    │  20t  684k │ Done! 🚀 I've spawned a Claude...
```

Legend:
- First column: Status (●/○/◌)
- Second column: Type (M=Main, S=Sub, C=Cron, W=WhatsApp, T=Telegram)
- Session label (truncated)
- Tool count & token usage
- Last activity preview

## Notes

- Sessions older than 1 hour are not shown
- JSONL files with `.deleted` or `compact` in name are skipped
- Only the last ~500KB of each session file is parsed (for efficiency)
- Refresh rate is 2 seconds by default

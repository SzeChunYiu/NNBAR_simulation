# HIBEAM Dashboard Auto-Launcher

Automatically launches the tmux dashboard whenever Claude Code starts.

## Quick Start

```bash
# Enable auto-launch (one time)
claude-dashboard on

# That's it! Dashboard will start with every `claude` command
```

## Commands

### Dashboard Control (`claude-dashboard`)

| Command | Description |
|---------|-------------|
| `claude-dashboard on` | Enable auto-launch with Claude Code |
| `claude-dashboard off` | Disable auto-launch |
| `claude-dashboard status` | Show current status |
| `claude-dashboard bg` | Launch dashboard in background now |
| `claude-dashboard launch` | Launch dashboard (foreground, attach) |
| `claude-dashboard attach` | Attach to running dashboard |
| `claude-dashboard kill` | Kill the dashboard session |

### Setup Management (`claude-dashboard-setup`)

| Command | Description |
|---------|-------------|
| `claude-dashboard-setup status` | Show if wrapper is installed |
| `claude-dashboard-setup install` | Install the wrapper |
| `claude-dashboard-setup restore` | Bypass wrapper (direct Claude) |

## How It Works

```
claude (command)
    ↓
claude-with-dashboard (wrapper)
    ├── Checks ~/.claude-dashboard-enabled
    ├── If enabled: runs `claude-dashboard bg` (background)
    └── Runs real Claude binary
```

The dashboard runs in a **detached tmux session** (`hibeam-dash`) that:
- Doesn't block Claude Code
- Can be closed without affecting Claude
- Persists until manually killed

## Files

| File | Purpose |
|------|---------|
| `~/.local/bin/claude` | Symlink to wrapper |
| `~/.local/bin/claude-with-dashboard` | Wrapper script |
| `~/.local/bin/claude-dashboard` | Dashboard controller |
| `~/.local/bin/claude-dashboard-setup` | Install/restore tool |
| `~/.claude-dashboard-enabled` | Toggle file (presence = enabled) |

## Tmux Session

- **Session name:** `hibeam-dash`
- **Attach:** `tmux attach -t hibeam-dash`
- **Detach:** `Ctrl+B` then `D`
- **Kill:** `claude-dashboard kill`

## Disable Temporarily

```bash
# Option 1: Disable auto-launch
claude-dashboard off

# Option 2: Run Claude directly (bypassing wrapper)
~/.local/share/claude/current "$@"
```

## Uninstall

```bash
# Remove wrapper, restore direct Claude
claude-dashboard-setup restore
claude-dashboard off

# Optionally remove scripts
rm ~/.local/bin/claude-dashboard ~/.local/bin/claude-with-dashboard ~/.local/bin/claude-dashboard-setup
```

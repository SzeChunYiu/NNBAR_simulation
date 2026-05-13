#!/usr/bin/env python3
"""
OpenClaw Agent Monitor - Real-time dashboard for Claude Code agents.

Shows:
- Active agent sessions with status
- Information flow (tool calls, results, messages)
- Task progress and completions
- Real-time updates from JSONL files

Usage:
    python3 _dash_openclaw_agents.py              # Show all active agents
    python3 _dash_openclaw_agents.py --compact    # Compact view (one line each)
    python3 _dash_openclaw_agents.py --list       # List session keys only
    python3 _dash_openclaw_agents.py --watch      # Continuous refresh (2s)
    python3 _dash_openclaw_agents.py <session_id> # Show specific session
"""

import json
import os
import sys
import time
import glob
import re
from datetime import datetime
from collections import defaultdict

# Session paths
OPENCLAW_SESSIONS = os.path.expanduser("~/.openclaw/agents/main/sessions")
CRON_RUNS = os.path.expanduser("~/.openclaw/cron/runs")
CLAWD_DIR = os.path.expanduser("~/clawd")

# Max settings
MAX_AGE_SECONDS = 600  # 10 minutes for "active" status
MAX_READ_BYTES = 500000  # 500KB tail read
MAX_ACTIVITY_LINES = 10
IDLE_THRESHOLD = 60  # seconds

# ANSI colors
R = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[0;90m"
GREEN = "\033[1;32m"
YELLOW = "\033[0;33m"
BYELLOW = "\033[1;33m"
RED = "\033[1;31m"
CYAN = "\033[0;36m"
BLUE = "\033[1;34m"
MAGENTA = "\033[1;35m"
WHITE = "\033[1;37m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"
BG_RED = "\033[41m"


def get_terminal_size():
    """Get terminal dimensions."""
    try:
        cols, rows = os.get_terminal_size()
        return cols, rows
    except Exception:
        return 100, 40


def format_time_ago(ts):
    """Format timestamp as human-readable age."""
    if isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            ts = dt.timestamp()
        except:
            return "?"
    
    age = time.time() - ts
    if age < 0:
        return "future?"
    elif age < 60:
        return f"{int(age)}s"
    elif age < 3600:
        return f"{int(age/60)}m"
    elif age < 86400:
        return f"{int(age/3600)}h"
    else:
        return f"{int(age/86400)}d"


def get_status_indicator(mtime, is_active=False):
    """Get colored status indicator based on recency."""
    age = time.time() - mtime
    if age < 15:
        return f"{BG_GREEN}{BOLD} ● LIVE {R}", "live"
    elif age < IDLE_THRESHOLD:
        return f"{GREEN}● ACTIVE{R}", "active"
    elif age < 300:
        return f"{YELLOW}○ IDLE ({format_time_ago(mtime)}){R}", "idle"
    else:
        return f"{DIM}◌ STALE ({format_time_ago(mtime)}){R}", "stale"


def parse_session_metadata(entries):
    """Extract session metadata from first entries."""
    meta = {
        'session_id': None,
        'session_key': None,
        'label': None,
        'channel': None,
        'model': None,
        'display_name': None,
    }
    
    for entry in entries[:50]:  # Check first 50 entries
        etype = entry.get('type', '')
        
        if etype == 'session':
            meta['session_id'] = entry.get('id')
        
        if etype == 'model_change':
            meta['model'] = entry.get('modelId')
        
        if etype == 'custom':
            ctype = entry.get('customType', '')
            data = entry.get('data', {})
            
            if ctype == 'openclaw.session-meta':
                meta['session_key'] = data.get('sessionKey')
                meta['channel'] = data.get('channel')
                meta['display_name'] = data.get('displayName')
                meta['label'] = data.get('label')
    
    return meta


def extract_agent_label(session_key, entries):
    """Extract a friendly label for the agent."""
    if not session_key:
        # Try to extract from first user message
        for entry in entries[:20]:
            if entry.get('type') == 'message':
                msg = entry.get('message', {})
                if msg.get('role') == 'user':
                    content = msg.get('content', [])
                    if isinstance(content, list) and content:
                        text = content[0].get('text', '')
                        # Check for label patterns like [label:xxx]
                        match = re.search(r'\[(\w+[-\w]*)\]', text)
                        if match:
                            return match.group(1)[:20]
                        # Return first words of task
                        words = text.split()[:4]
                        return ' '.join(words)[:25] + '...' if words else 'unknown'
        return 'unknown'
    
    parts = session_key.split(':')
    
    # agent:main:subagent:uuid -> subagent:uuid[:8]
    if 'subagent' in parts:
        idx = parts.index('subagent')
        if idx + 1 < len(parts):
            return f"sub:{parts[idx+1][:8]}"
    
    # agent:main:cron:uuid -> cron:uuid[:8]
    if 'cron' in parts:
        idx = parts.index('cron')
        if idx + 1 < len(parts):
            return f"cron:{parts[idx+1][:8]}"
    
    # agent:main:main -> MAIN
    if parts[-1] == 'main':
        return 'MAIN'
    
    # Channel-based
    for channel in ['whatsapp', 'telegram', 'discord', 'webchat']:
        if channel in parts:
            return channel.upper()
    
    return parts[-1][:15] if parts else 'unknown'


def parse_session_type(session_key):
    """Parse session key to determine type."""
    if not session_key:
        return "subagent", None
    
    parts = session_key.split(":")
    
    if "subagent" in parts:
        return "subagent", None
    if "cron" in parts:
        return "cron", None
    if parts[-1] == "main":
        return "main", None
    
    for channel in ["whatsapp", "telegram", "discord", "webchat"]:
        if channel in parts:
            return channel, None
    
    return "other", None


def read_jsonl_tail(filepath, max_bytes=MAX_READ_BYTES):
    """Read the last portion of a JSONL file."""
    try:
        size = os.path.getsize(filepath)
        if size == 0:
            return []
        
        with open(filepath, 'rb') as f:
            if size > max_bytes:
                f.seek(size - max_bytes)
                f.readline()  # Skip partial line
            content = f.read().decode('utf-8', errors='ignore')
        
        entries = []
        for line in content.strip().split('\n'):
            if not line.strip():
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return entries
    except Exception as e:
        return []


def extract_session_info(filepath, entries):
    """Extract useful information from session entries."""
    meta = parse_session_metadata(entries)
    
    info = {
        'filepath': filepath,
        'session_id': meta['session_id'],
        'session_key': meta['session_key'],
        'model': meta['model'] or '?',
        'channel': meta['channel'],
        'display_name': meta['display_name'],
        'label': None,
        'total_tokens': 0,
        'tool_count': 0,
        'message_count': 0,
        'activities': [],
        'last_activity': None,
        'task_description': None,
        'errors': [],
    }
    
    # Extract label
    info['label'] = meta['label'] or extract_agent_label(meta['session_key'], entries)
    
    for entry in entries:
        etype = entry.get('type', '')
        ts = entry.get('timestamp', '')
        
        # Messages
        if etype == 'message':
            info['message_count'] += 1
            msg = entry.get('message', {})
            role = msg.get('role', '')
            usage = msg.get('usage', {})
            
            if usage:
                info['total_tokens'] += usage.get('totalTokens', 0)
            
            content_blocks = msg.get('content', [])
            if isinstance(content_blocks, str):
                content_blocks = [{'type': 'text', 'text': content_blocks}]
            
            for block in content_blocks:
                block_type = block.get('type', '')
                
                # User task (first one)
                if role == 'user' and block_type == 'text' and not info['task_description']:
                    text = block.get('text', '')
                    if len(text) > 10:
                        preview = text.replace('\n', ' ').strip()[:200]
                        info['task_description'] = preview
                        info['activities'].append((ts, 'task', preview))
                
                # Tool calls
                if block_type == 'toolCall':
                    info['tool_count'] += 1
                    tool_name = block.get('name', '?')
                    args = block.get('arguments', {})
                    
                    # Extract key arg for display
                    key_arg = ''
                    for key in ['command', 'path', 'file_path', 'query', 'url', 'action', 'pattern', 'message']:
                        if key in args:
                            val = args[key]
                            if isinstance(val, str):
                                key_arg = val.replace('\n', ' ')[:50]
                                break
                    
                    info['activities'].append((ts, 'tool', f"{tool_name}({key_arg})"))
                    info['last_activity'] = ts
                
                # Assistant text output
                if role == 'assistant' and block_type == 'text':
                    text = block.get('text', '').strip()
                    if len(text) > 30:
                        preview = text.replace('\n', ' ')[:80]
                        info['activities'].append((ts, 'output', preview))
                        info['last_activity'] = ts
            
            # Check for errors
            if msg.get('isError'):
                error_text = str(content_blocks)[:100]
                info['errors'].append((ts, error_text))
        
        # Tool results
        if etype == 'message':
            msg = entry.get('message', {})
            if msg.get('role') == 'toolResult':
                for block in msg.get('content', []):
                    if block.get('type') == 'tool_result':
                        result = block.get('content', '')
                        if isinstance(result, str) and len(result) > 20:
                            preview = result.replace('\n', ' ').strip()[:60]
                            info['activities'].append((ts, 'result', preview))
    
    return info


def scan_active_sessions():
    """Scan for active OpenClaw sessions."""
    sessions = []
    now = time.time()
    
    if os.path.isdir(OPENCLAW_SESSIONS):
        for filepath in glob.glob(os.path.join(OPENCLAW_SESSIONS, "*.jsonl")):
            if '.deleted' in filepath or 'compact' in filepath:
                continue
            
            try:
                mtime = os.path.getmtime(filepath)
                size = os.path.getsize(filepath)
                
                # Skip empty or very old
                if size == 0:
                    continue
                if now - mtime > 3600:  # 1 hour limit
                    continue
                
                entries = read_jsonl_tail(filepath)
                if not entries:
                    continue
                
                info = extract_session_info(filepath, entries)
                info['mtime'] = mtime
                info['size'] = size
                
                sessions.append(info)
            except Exception as e:
                continue
    
    # Sort by recency
    sessions.sort(key=lambda s: s.get('mtime', 0), reverse=True)
    
    return sessions


def render_compact_session(session, cols):
    """Render a single session in compact (one-line) format."""
    mtime = session.get('mtime', 0)
    age = time.time() - mtime
    
    # Status indicator
    if age < 15:
        status = f"{GREEN}●{R}"
    elif age < 60:
        status = f"{GREEN}○{R}"
    elif age < 300:
        status = f"{YELLOW}○{R}"
    else:
        status = f"{DIM}◌{R}"
    
    # Type badge
    stype, _ = parse_session_type(session.get('session_key', ''))
    badges = {
        'main': f"{MAGENTA}M{R}",
        'subagent': f"{CYAN}S{R}",
        'cron': f"{BLUE}C{R}",
        'whatsapp': f"{GREEN}W{R}",
        'telegram': f"{BLUE}T{R}",
        'webchat': f"{YELLOW}w{R}",
    }
    badge = badges.get(stype, f"{DIM}?{R}")
    
    label = session.get('label', 'unknown')[:18].ljust(18)
    tools = session.get('tool_count', 0)
    tokens = session.get('total_tokens', 0) // 1000
    
    # Last activity preview
    activities = session.get('activities', [])
    last_act = ''
    if activities:
        _, atype, content = activities[-1]
        if atype == 'tool':
            last_act = f"{YELLOW}{content[:35]}{R}"
        elif atype == 'output':
            last_act = f"{WHITE}{content[:35]}{R}"
        else:
            last_act = f"{DIM}{content[:35]}{R}"
    
    print(f" {status} {badge} {WHITE}{label}{R} {DIM}│{R} {tools:>3}t {tokens:>4}k {DIM}│{R} {last_act}")


def render_session(session, cols, compact=False):
    """Render a single session's information."""
    if compact:
        render_compact_session(session, cols)
        return
    
    mtime = session.get('mtime', 0)
    status_str, status = get_status_indicator(mtime)
    
    # Session type and badge
    stype, _ = parse_session_type(session.get('session_key', ''))
    type_badges = {
        'main': f"{MAGENTA}[MAIN]{R}",
        'subagent': f"{CYAN}[SUB]{R}",
        'cron': f"{BLUE}[CRON]{R}",
        'whatsapp': f"{GREEN}[WA]{R}",
        'telegram': f"{BLUE}[TG]{R}",
        'webchat': f"{YELLOW}[WEB]{R}",
    }
    badge = type_badges.get(stype, f"{DIM}[{stype}]{R}")
    
    # Label and model
    label = session.get('label', 'unknown')
    model = session.get('model', '?').replace('claude-', '').replace('-4-5', '4.5')[:10]
    
    # Stats
    tools = session.get('tool_count', 0)
    tokens = session.get('total_tokens', 0)
    size_kb = session.get('size', 0) // 1024
    msgs = session.get('message_count', 0)
    
    # Header
    sep = '─' * (cols - 2)
    print(f"{badge} {WHITE}{BOLD}{label[:28]}{R}  {status_str}  {DIM}{model} │ {tools}t {msgs}m │ {tokens//1000}k tok{R}")
    print(f"{DIM}{sep}{R}")
    
    # Task description
    task = session.get('task_description', '')
    if task:
        task_preview = task[:cols-10]
        print(f"  {BLUE}Task:{R} {task_preview[:cols-12]}")
    
    # Errors
    if session.get('errors'):
        err_ts, err_text = session['errors'][-1]
        print(f"  {RED}⚠ Error:{R} {err_text[:cols-14]}")
    
    # Recent activities
    activities = session.get('activities', [])[-MAX_ACTIVITY_LINES:]
    max_content = cols - 16
    
    for ts, atype, content in activities:
        tstr = ts[11:19] if isinstance(ts, str) and len(ts) > 19 else "        "
        
        if len(content) > max_content:
            content = content[:max_content - 3] + "..."
        
        if atype == 'task':
            continue  # Already shown above
        elif atype == 'tool':
            print(f"  {DIM}{tstr}{R} {YELLOW}▶ {content}{R}")
        elif atype == 'result':
            print(f"  {DIM}{tstr}{R} {CYAN}  ↳ {content}{R}")
        elif atype == 'output':
            print(f"  {DIM}{tstr}{R} {WHITE}  {content}{R}")
    
    print()


def render_summary(sessions, cols):
    """Render summary header."""
    now = time.time()
    
    live = sum(1 for s in sessions if now - s.get('mtime', 0) < 15)
    active = sum(1 for s in sessions if 15 <= now - s.get('mtime', 0) < 60)
    idle = sum(1 for s in sessions if 60 <= now - s.get('mtime', 0) < 300)
    stale = len(sessions) - live - active - idle
    
    total_tools = sum(s.get('tool_count', 0) for s in sessions)
    total_tokens = sum(s.get('total_tokens', 0) for s in sessions)
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    sep = '═' * (cols - 2)
    print(f"{sep}")
    print(f"{BOLD}{MAGENTA}  🐼 OPENCLAW AGENT MONITOR{R}  {DIM}{timestamp}{R}")
    
    status_parts = []
    if live > 0:
        status_parts.append(f"{BG_GREEN} ● {live} LIVE {R}")
    if active > 0:
        status_parts.append(f"{GREEN}● {active} active{R}")
    if idle > 0:
        status_parts.append(f"{YELLOW}○ {idle} idle{R}")
    if stale > 0:
        status_parts.append(f"{DIM}◌ {stale} stale{R}")
    
    if not status_parts:
        status_parts.append(f"{DIM}No sessions{R}")
    
    print(f"  {'  '.join(status_parts)}  │  {DIM}Tools: {total_tools}  Tokens: {total_tokens//1000}k{R}")
    print(f"{sep}")
    print()


def list_sessions():
    """List session keys only (for scripting)."""
    sessions = scan_active_sessions()
    for s in sessions:
        key = s.get('session_key') or s.get('session_id') or 'unknown'
        label = s.get('label', '')
        mtime = s.get('mtime', 0)
        age = format_time_ago(mtime)
        print(f"{key}\t{label}\t{age}")


def main():
    cols, rows = get_terminal_size()
    compact = '--compact' in sys.argv
    watch_mode = '--watch' in sys.argv
    
    if '--list' in sys.argv:
        list_sessions()
        return
    
    # Check for specific session
    specific_session = None
    for arg in sys.argv[1:]:
        if not arg.startswith('--'):
            specific_session = arg
            break
    
    def render_once():
        sessions = scan_active_sessions()
        
        if specific_session:
            for s in sessions:
                sid = s.get('session_id', '')
                skey = s.get('session_key', '')
                label = s.get('label', '')
                if specific_session in (sid or '') or specific_session in (skey or '') or specific_session in (label or ''):
                    render_session(s, cols, compact=False)
                    return
            print(f"{RED}Session not found: {specific_session}{R}")
            return
        
        render_summary(sessions, cols)
        
        if not sessions:
            print(f"  {DIM}No active sessions found in {OPENCLAW_SESSIONS}{R}")
            return
        
        # Show sessions
        now = time.time()
        recent = [s for s in sessions if now - s.get('mtime', 0) < 300]
        
        if compact:
            for s in recent[:15]:
                render_session(s, cols, compact=True)
            remaining = len(sessions) - len(recent[:15])
        else:
            for s in recent[:6]:
                render_session(s, cols, compact=False)
            remaining = len(sessions) - len(recent[:6])
        
        if remaining > 0:
            print(f"  {DIM}+ {remaining} more sessions{R}")
    
    if watch_mode:
        try:
            while True:
                os.system('clear')
                render_once()
                time.sleep(2)
        except KeyboardInterrupt:
            pass
    else:
        render_once()


if __name__ == '__main__':
    main()

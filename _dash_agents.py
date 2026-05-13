#!/usr/bin/env python3
"""Agent activity pane renderer for tmux dashboard.

Usage: python3 _dash_agents.py [agent_id]
  If agent_id given, show only that agent's activity.
  If not given, show all active agents (for discovery mode).

When called with --list, print one agent_id per line for active agents.
"""

import json, os, sys, time, glob

TASK_DIR = "/tmp/claude-1000/-home-billy-nnbar-simulation/tasks"
SUBAGENT_DIR = os.path.expanduser("~/.claude/projects/-home-billy-nnbar-simulation")
MAX_AGE = 300       # 5 minutes
MAX_READ = 300000   # bytes to read from tail of file
MAX_LINES = 20      # activity lines to show


def _find_all_output_files():
    """Find all agent output files from both task dir and subagent dirs."""
    files = []
    # Standard task output files
    for f in glob.glob(os.path.join(TASK_DIR, "*.output")):
        files.append(f)
    # In-process subagent JSONL files (for teammates)
    for session_dir in glob.glob(os.path.join(SUBAGENT_DIR, "*/subagents")):
        for f in glob.glob(os.path.join(session_dir, "agent-*.jsonl")):
            # Skip compacted files
            if 'compact' in os.path.basename(f):
                continue
            files.append(f)
    return files

# ANSI colors
R  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[1;32m"
YELLOW = "\033[0;33m"
BYELLOW = "\033[1;33m"
CYAN   = "\033[0;36m"
DIM    = "\033[0;90m"
WHITE  = "\033[1;37m"
BLUE   = "\033[1;34m"
RED    = "\033[1;31m"
MAGENTA = "\033[1;35m"


def get_terminal_width():
    try:
        return os.get_terminal_size().columns
    except Exception:
        return 80


def parse_output_file(output_file):
    """Parse an agent output file and return (agent_name, activities, tool_count, mtime)."""
    size = os.path.getsize(output_file)
    if size == 0:
        return None

    mtime = os.path.getmtime(output_file)
    agent_id = os.path.basename(output_file).replace('.output', '')
    name = agent_id[:12]

    read_bytes = min(size, MAX_READ)
    with open(output_file, 'rb') as f:
        if size > read_bytes:
            f.seek(size - read_bytes)
            f.readline()  # skip partial line
        content = f.read().decode('utf-8', errors='ignore')

    activities = []  # (timestamp, type, content)
    tool_count = 0

    for line in content.strip().split('\n'):
        try:
            d = json.loads(line.strip())
        except (json.JSONDecodeError, ValueError):
            continue

        ts = d.get('timestamp', '')

        # Detect agent name from agentId field
        if 'agentId' in d:
            aid = d['agentId']
            name = aid.split('@')[0] if '@' in aid else aid[:16]

        # Also try slug for friendly name
        if 'slug' in d and d['slug']:
            slug = d['slug']
            # Convert slug like "resilient-twirling-dijkstra" to a short form
            parts = slug.split('-')
            if len(parts) >= 2:
                name = parts[-1][:16]

        if d.get('type') == 'user':
            # Initial task message
            msg = d.get('message', {})
            content_val = msg.get('content', '')
            if isinstance(content_val, str) and len(content_val) > 10:
                preview = content_val.replace('\n', ' ').strip()[:200]
                activities.append((ts, 'task', preview))

        elif d.get('type') == 'assistant':
            msg = d.get('message', {})
            for block in msg.get('content', []):
                if block.get('type') == 'tool_use':
                    tool_count += 1
                    tname = block.get('name', '?')
                    inp = block.get('input', {})
                    desc = inp.get('description',
                           inp.get('command',
                           inp.get('prompt',
                           inp.get('pattern',
                           inp.get('query',
                           inp.get('file_path', ''))))))
                    if isinstance(desc, str):
                        desc = desc.replace('\n', ' ').strip()
                    else:
                        desc = str(desc)[:80]
                    activities.append((ts, 'tool', f"{tname}({desc})"))
                elif block.get('type') == 'text':
                    txt = block.get('text', '').strip().replace('\n', ' ')
                    if txt and len(txt) > 5:
                        activities.append((ts, 'text', txt))

        elif d.get('type') == 'tool_result':
            msg = d.get('message', {})
            for block in msg.get('content', []):
                if block.get('type') == 'tool_result':
                    result_content = block.get('content', '')
                    if isinstance(result_content, str) and len(result_content) > 5:
                        preview = result_content.replace('\n', ' ').strip()
                        activities.append((ts, 'result', preview))

    return {
        'agent_id': agent_id,
        'name': name,
        'activities': activities,
        'tool_count': tool_count,
        'mtime': mtime,
        'size': size,
    }


def list_active_agents():
    """Print active agent IDs, one per line."""
    now = time.time()
    agents = []
    seen = set()
    for output_file in _find_all_output_files():
        try:
            # Resolve symlinks to get actual file
            real_path = os.path.realpath(output_file)
            if real_path in seen:
                continue
            seen.add(real_path)
            size = os.path.getsize(output_file)
            if size == 0:
                continue
            mtime = os.path.getmtime(output_file)
            if now - mtime > MAX_AGE:
                continue
            agent_id = os.path.basename(output_file).replace('.output', '').replace('.jsonl', '').replace('agent-', '')
            agents.append((mtime, agent_id, size, output_file))
        except Exception:
            continue

    # Sort by modification time (most recent first)
    agents.sort(key=lambda x: -x[0])
    for _, aid, _, _ in agents:
        print(aid)


def _find_agent_file(agent_id):
    """Find the output file for a given agent ID."""
    # Check task dir
    path = os.path.join(TASK_DIR, f"{agent_id}.output")
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path
    # Check subagent dirs
    for session_dir in glob.glob(os.path.join(SUBAGENT_DIR, "*/subagents")):
        path = os.path.join(session_dir, f"agent-{agent_id}.jsonl")
        if os.path.exists(path):
            return path
    return None


def render_agent(agent_id, cols=None):
    """Render a single agent's activity pane."""
    if cols is None:
        cols = get_terminal_width()
    max_content = cols - 16  # leave room for timestamp prefix

    output_file = _find_agent_file(agent_id)
    if output_file is None:
        print(f"{RED}Agent {agent_id}: output file not found{R}")
        return

    info = parse_output_file(output_file)
    if info is None:
        print(f"{DIM}Agent {agent_id}: empty output{R}")
        return

    now = time.time()
    age = now - info['mtime']
    name = info['name']

    if age < 30:
        status = f"{GREEN}ACTIVE{R}"
    elif age < 120:
        status = f"{YELLOW}IDLE {int(age)}s{R}"
    else:
        status = f"{RED}STALE {int(age)}s{R}"

    # Header
    sep = '-' * (cols - 2)
    print(f"{MAGENTA}{BOLD}[{name}]{R}  {status}  {DIM}({info['tool_count']} tools, {info['size']//1024}KB){R}")
    print(f"{DIM}{sep}{R}")

    activities = info['activities']
    if not activities:
        print(f"{DIM}  (no activity parsed){R}")
        return

    # Show last N activities
    for ts, atype, content in activities[-MAX_LINES:]:
        tstr = ts[11:19] if len(ts) > 19 else "        "

        if atype == 'task':
            line = f"{DIM}{tstr}{R} {BLUE}TASK: {content[:max_content]}{R}"
        elif atype == 'tool':
            if len(content) > max_content:
                content = content[:max_content - 3] + "..."
            line = f"{DIM}{tstr}{R} {YELLOW}> {content}{R}"
        elif atype == 'result':
            if len(content) > max_content:
                content = content[:max_content - 3] + "..."
            line = f"{DIM}{tstr}{R} {CYAN}  => {content}{R}"
        elif atype == 'text':
            if len(content) > max_content:
                content = content[:max_content - 3] + "..."
            line = f"{DIM}{tstr}{R} {WHITE}  {content}{R}"
        else:
            continue
        print(line)


def render_all_agents(cols=None):
    """Render all active agents for a combined view."""
    if cols is None:
        cols = get_terminal_width()

    now = time.time()
    agents = []
    seen = set()

    for output_file in _find_all_output_files():
        try:
            real_path = os.path.realpath(output_file)
            if real_path in seen:
                continue
            seen.add(real_path)
            size = os.path.getsize(output_file)
            if size == 0:
                continue
            mtime = os.path.getmtime(output_file)
            if now - mtime > MAX_AGE:
                continue
            info = parse_output_file(output_file)
            if info:
                agents.append(info)
        except Exception:
            continue

    if not agents:
        print(f"{DIM}  No active agents detected{R}")
        return

    # Sort: active first, then by recency
    agents.sort(key=lambda a: -a['mtime'])

    for info in agents:
        age = now - info['mtime']
        name = info['name']

        if age < 30:
            status = f"{GREEN}ACTIVE{R}"
        elif age < 120:
            status = f"{YELLOW}IDLE {int(age)}s{R}"
        else:
            status = f"{RED}STALE {int(age)}s{R}"

        max_content = cols - 16
        sep = '-' * (cols - 2)

        print(f"\n{MAGENTA}{BOLD}[{name}]{R}  {status}  {DIM}({info['tool_count']} tools){R}")
        print(f"{DIM}{sep}{R}")

        for ts, atype, content in info['activities'][-8:]:
            tstr = ts[11:19] if len(ts) > 19 else "        "
            if atype == 'tool':
                if len(content) > max_content:
                    content = content[:max_content - 3] + "..."
                print(f"{DIM}{tstr}{R} {YELLOW}> {content}{R}")
            elif atype == 'result':
                if len(content) > max_content:
                    content = content[:max_content - 3] + "..."
                print(f"{DIM}{tstr}{R} {CYAN}  => {content}{R}")
            elif atype == 'text':
                if len(content) > max_content:
                    content = content[:max_content - 3] + "..."
                print(f"{DIM}{tstr}{R} {WHITE}  {content}{R}")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--list':
        list_active_agents()
    elif len(sys.argv) > 1 and sys.argv[1] != '--all':
        render_agent(sys.argv[1])
    else:
        render_all_agents()

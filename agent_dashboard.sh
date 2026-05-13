#!/bin/bash
# Live Agent Dashboard - shows active agents' work and thinking
# Usage: bash agent_dashboard.sh          (live refresh every 5s)
#        bash agent_dashboard.sh --once   (single snapshot)

TASK_DIR="/tmp/claude-1000/-home-billy-nnbar-simulation/tasks"
REFRESH=5
[[ "$1" == "--once" ]] && REFRESH=0

show_dashboard() {
    clear
    local cols=$(tput cols 2>/dev/null || echo 100)
    local line=$(printf '%.0s=' $(seq 1 $cols))

    echo -e "\033[1;36m$line\033[0m"
    echo -e "\033[1;36m  HIBEAM Pipeline - Live Agent Dashboard        $(date '+%H:%M:%S')\033[0m"
    echo -e "\033[1;36m$line\033[0m"

    # === CLUSTER JOBS ===
    echo ""
    echo -e "\033[1;33m  CLUSTER JOBS:\033[0m"
    ssh lunarc "squeue -u scyiu --format='    %.10i %.20j %.8T %.10M %.20R' 2>/dev/null" 2>/dev/null | while IFS= read -r jl; do
        if [[ "$jl" == *"RUNNING"* ]]; then echo -e "  \033[1;32m$jl\033[0m"
        elif [[ "$jl" == *"PENDING"* ]]; then echo -e "  \033[0;33m$jl\033[0m"
        else echo "  $jl"; fi
    done

    # === ACTIVE AGENTS - show recent tool calls and outputs ===
    echo ""
    echo -e "\033[1;33m  ACTIVE AGENTS:\033[0m"

    python3 << 'PYEOF' 2>/dev/null
import json, os, time, glob

task_dir = os.environ.get("TASK_DIR", "/tmp/claude-1000/-home-billy-nnbar-simulation/tasks")
cols = int(os.environ.get("COLS", "100")) - 4

r = "\033[0m"
GREEN = "\033[1;32m"
YELLOW = "\033[0;33m"
CYAN = "\033[0;36m"
DIM = "\033[0;90m"
WHITE = "\033[1;37m"
BLUE = "\033[1;34m"

now = time.time()
shown = 0

for output_file in sorted(glob.glob(os.path.join(task_dir, "*.output"))):
    size = os.path.getsize(output_file)
    if size == 0:
        continue
    mtime = os.path.getmtime(output_file)
    age = now - mtime

    # Only show agents active in last 5 minutes
    if age > 300:
        continue

    agent_id = os.path.basename(output_file).replace('.output', '')
    name = agent_id[:12]

    # Parse recent activity
    read_bytes = min(size, 200000)
    with open(output_file, 'rb') as f:
        if size > read_bytes:
            f.seek(size - read_bytes)
            f.readline()
        content = f.read().decode('utf-8', errors='ignore')

    activities = []  # (timestamp, type, content)
    tool_count = 0

    for line in content.strip().split('\n'):
        try:
            d = json.loads(line.strip())
            ts = d.get('timestamp', '')

            if 'agentId' in d:
                aid = d['agentId']
                name = aid.split('@')[0] if '@' in aid else aid[:16]

            if d.get('type') == 'assistant':
                msg = d.get('message', {})
                for block in msg.get('content', []):
                    if block.get('type') == 'tool_use':
                        tool_count += 1
                        tname = block.get('name', '?')
                        inp = block.get('input', {})
                        desc = inp.get('description', inp.get('command', inp.get('prompt', inp.get('pattern', ''))))
                        if isinstance(desc, str):
                            desc = desc.replace('\n', ' ')
                            if len(desc) > cols - 20:
                                desc = desc[:cols-23] + "..."
                        activities.append((ts, 'tool', f"{tname}({desc})"))
                    elif block.get('type') == 'text':
                        txt = block.get('text', '').strip().replace('\n', ' ')
                        if txt and len(txt) > 10:
                            activities.append((ts, 'text', txt[:cols]))

            elif d.get('type') == 'tool_result':
                # Extract short result preview
                msg = d.get('message', {})
                for block in msg.get('content', []):
                    if block.get('type') == 'tool_result':
                        result_content = block.get('content', '')
                        if isinstance(result_content, str) and len(result_content) > 10:
                            preview = result_content.replace('\n', ' ')[:cols]
                            activities.append((ts, 'result', preview))
        except:
            pass

    if not activities:
        continue

    shown += 1
    status = f"{GREEN}ACTIVE{r}" if age < 30 else f"{YELLOW}IDLE ({int(age)}s){r}"

    print(f"\n  {WHITE}[{name}]{r}  {status}  ({tool_count} tool calls)")
    print(f"  {DIM}{'-' * (cols)}{r}")

    # Show last 6 activities
    for ts, atype, content in activities[-6:]:
        tstr = ts[11:19] if len(ts) > 19 else ""
        if atype == 'tool':
            print(f"  {DIM}{tstr}{r} {YELLOW}> {content}{r}")
        elif atype == 'result':
            print(f"  {DIM}{tstr}{r} {CYAN}  => {content[:cols-10]}{r}")
        elif atype == 'text':
            print(f"  {DIM}{tstr}{r} {WHITE}  {content}{r}")

if shown == 0:
    print(f"  {DIM}(no active agents){r}")

# === TASKS (only in-progress) ===
print(f"\n{r}")
print(f"  \033[1;33mACTIVE TASKS:\033[0m")

task_dir2 = os.path.expanduser("~/.claude/tasks/hibeam-pipeline")
tasks = []
for f in glob.glob(os.path.join(task_dir2, "*.json")):
    try:
        with open(f) as fh:
            t = json.load(fh)
            if t.get('status') in ('in_progress', 'pending'):
                tasks.append(t)
    except:
        pass

tasks.sort(key=lambda t: int(t.get('id', 0)))
if not tasks:
    print(f"  {DIM}  (all tasks complete!){r}")
for t in tasks:
    s = t.get('status', '?')
    icon = f"{YELLOW}[~]{r}" if s == 'in_progress' else f"{DIM}[ ]{r}"
    tid = t.get('id', '?')
    subj = t.get('subject', '?')[:55]
    owner = t.get('owner', '')
    blocked = t.get('blockedBy', [])
    extra = ""
    if owner:
        extra += f" ({owner})"
    if blocked:
        extra += f" [blocked]"
    print(f"    {icon} #{tid:>2s} {subj}{extra}")

# Completed count
done = 0
for f in glob.glob(os.path.join(task_dir2, "*.json")):
    try:
        with open(f) as fh:
            if json.load(fh).get('status') == 'completed':
                done += 1
    except:
        pass
if done:
    print(f"    {GREEN}  + {done} tasks completed{r}")

PYEOF

    echo ""
    echo -e "\033[0;90m  Ctrl+C to exit\033[0m"
}

export TASK_DIR COLS
COLS=$(tput cols 2>/dev/null || echo 100)
export COLS

if [[ "$REFRESH" -eq 0 ]]; then
    show_dashboard
else
    trap 'echo ""; echo "Dashboard stopped."; exit 0' INT
    while true; do
        show_dashboard
        sleep "$REFRESH"
    done
fi

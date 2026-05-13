#!/usr/bin/env python3
"""Task list pane renderer for tmux dashboard.

Shows all tasks from ~/.claude/tasks/hibeam-pipeline/*.json
with status coloring and progress summary.
"""

import json, os, sys, glob

TASK_DIR = os.path.expanduser("~/.claude/tasks/hibeam-pipeline")

# ANSI colors
R       = "\033[0m"
BOLD    = "\033[1m"
GREEN   = "\033[1;32m"
YELLOW  = "\033[0;33m"
BYELLOW = "\033[1;33m"
CYAN    = "\033[0;36m"
DIM     = "\033[0;90m"
WHITE   = "\033[1;37m"
BLUE    = "\033[1;34m"
RED     = "\033[1;31m"
MAGENTA = "\033[1;35m"


def get_terminal_width():
    try:
        return os.get_terminal_size().columns
    except Exception:
        return 60


def render_tasks():
    cols = get_terminal_width()
    sep = '=' * (cols - 2)

    print(f"{BYELLOW}{BOLD}  TASK LIST{R}  {DIM}{TASK_DIR}{R}")
    print(f"{DIM}{sep}{R}")

    if not os.path.isdir(TASK_DIR):
        print(f"{RED}  Task directory not found: {TASK_DIR}{R}")
        return

    tasks = []
    for f in glob.glob(os.path.join(TASK_DIR, "*.json")):
        try:
            with open(f) as fh:
                t = json.load(fh)
                tasks.append(t)
        except Exception:
            continue

    if not tasks:
        print(f"{DIM}  No tasks found{R}")
        return

    # Sort by ID
    tasks.sort(key=lambda t: int(t.get('id', 0)))

    # Count statuses
    completed = sum(1 for t in tasks if t.get('status') == 'completed')
    in_progress = sum(1 for t in tasks if t.get('status') == 'in_progress')
    pending = sum(1 for t in tasks if t.get('status') == 'pending')
    total = len(tasks)

    # Progress bar
    bar_width = min(cols - 30, 40)
    filled = int(bar_width * completed / max(total, 1))
    bar = f"{'#' * filled}{'.' * (bar_width - filled)}"
    pct = int(100 * completed / max(total, 1))
    print(f"  {GREEN}[{bar}]{R} {pct}%  {GREEN}{completed}{R}/{total}  "
          f"{YELLOW}{in_progress} running{R}  {DIM}{pending} pending{R}")
    print()

    max_subj = cols - 28

    # Show in-progress first
    for t in tasks:
        if t.get('status') != 'in_progress':
            continue
        tid = t.get('id', '?')
        subj = t.get('subject', '?')[:max_subj]
        owner = t.get('owner', '')
        blocked = t.get('blockedBy', [])
        extra = ""
        if owner:
            extra += f" {DIM}({owner}){R}"
        if blocked:
            extra += f" {RED}[blocked]{R}"
        print(f"  {YELLOW}[~]{R} #{tid:>2s} {WHITE}{subj}{R}{extra}")

    # Show pending
    for t in tasks:
        if t.get('status') != 'pending':
            continue
        tid = t.get('id', '?')
        subj = t.get('subject', '?')[:max_subj]
        owner = t.get('owner', '')
        blocked = t.get('blockedBy', [])
        extra = ""
        if owner:
            extra += f" {DIM}({owner}){R}"
        if blocked:
            extra += f" {RED}[blocked]{R}"
        print(f"  {DIM}[ ]{R} #{tid:>2s} {subj}{extra}")

    # Show completed (collapsed)
    if completed > 0:
        print(f"\n  {GREEN}+ {completed} completed tasks{R}")
        # Show last 3 completed
        completed_tasks = [t for t in tasks if t.get('status') == 'completed']
        for t in completed_tasks[-3:]:
            tid = t.get('id', '?')
            subj = t.get('subject', '?')[:max_subj]
            print(f"  {DIM}  [x] #{tid:>2s} {subj}{R}")


if __name__ == '__main__':
    render_tasks()

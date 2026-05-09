#!/usr/bin/env bash
# merge.sh — merge a lane branch into main with a directory lock.
# Lanes call this after every iteration. The mkdir-lock serialises
# concurrent calls so the main worktree is never raced.
#
# Usage: bash merge.sh <branch>

set -euo pipefail

BRANCH="${1:-}"
if [[ -z "$BRANCH" ]]; then
    echo "usage: $0 <lane-branch>" >&2
    exit 1
fi

REPO_MAIN="/Volumes/MyDrive/nnbar/nnbar/simulation"
LOCKDIR="$REPO_MAIN/scripts/codex-supervisor/.merge.lock.d"
LOG="$REPO_MAIN/scripts/codex-supervisor/log/merge.log"

mkdir -p "$(dirname "$LOG")"

# Acquire lock (mkdir is atomic; portable across macOS / Linux).
attempt=0
while ! mkdir "$LOCKDIR" 2>/dev/null; do
    attempt=$((attempt + 1))
    if [[ $attempt -gt 120 ]]; then
        echo "merge.sh: could not acquire lock after 120s; another merge is stuck" >&2
        exit 2
    fi
    sleep 1
done
trap 'rmdir "$LOCKDIR"' EXIT

ts() { date -u '+%Y-%m-%dT%H:%M:%SZ'; }

echo "$(ts) merge.sh start branch=$BRANCH" >> "$LOG"

cd "$REPO_MAIN"

# The main worktree should already be on main; assert.
current=$(git symbolic-ref --short HEAD 2>/dev/null || true)
if [[ "$current" != "main" ]]; then
    echo "$(ts) merge.sh: main worktree is not on main (current=$current); refusing" >> "$LOG"
    echo "merge.sh: refusing — main worktree is on '$current', not 'main'" >&2
    exit 3
fi

# Verify the branch exists and has new commits.
if ! git show-ref --verify --quiet "refs/heads/$BRANCH"; then
    echo "$(ts) merge.sh: branch $BRANCH does not exist" >> "$LOG"
    echo "merge.sh: branch $BRANCH does not exist" >&2
    exit 4
fi

ahead=$(git rev-list --count "main..$BRANCH" 2>/dev/null || echo 0)
if [[ "$ahead" -eq 0 ]]; then
    echo "$(ts) merge.sh: $BRANCH has no new commits relative to main; nothing to do" >> "$LOG"
    exit 0
fi

# Merge with a non-fast-forward to preserve the lane history.
git merge --no-ff --log "$BRANCH" \
    -m "Merge $BRANCH ($ahead commit(s))" \
    >> "$LOG" 2>&1

if [[ $? -eq 0 ]]; then
    echo "$(ts) merge.sh: merged $ahead commit(s) from $BRANCH into main" >> "$LOG"
    echo "merged $ahead commit(s) from $BRANCH into main"
else
    echo "$(ts) merge.sh: merge FAILED for $BRANCH" >> "$LOG"
    echo "merge.sh: merge failed; check $LOG and resolve in main worktree" >&2
    exit 5
fi

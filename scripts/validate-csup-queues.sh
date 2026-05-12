#!/usr/bin/env bash
# validate-csup-queues.sh — mechanical lint over every codex-supervisor prompts
# and queue file for the nnbar project. Run BEFORE `codex-supervisor.sh start`
# and BEFORE any rolling restart. Exits non-zero on the first failure.
#
# Usage:
#   bash scripts/validate-csup-queues.sh                # check all
#   bash scripts/validate-csup-queues.sh --fix          # auto-prefix #-comment to broken lines
#
# Checks per non-blank non-comment line in:
#   codex-prompts-*.txt
#   codex-tasks/<session>/<lane>.txt
#
# 1. Line MUST start with /goal followed by whitespace or end-of-line.
# 2. Line MUST reference at least one *.md file (the lane spec).
# 3. Line MUST be <= 50 words (codex-supervisor compact prompt contract).
# 4. Line MUST be <= 500 chars (codex TUI safety).
# 5. Line MUST NOT contain stray ASCII control chars (anything < 0x20 except
#    whitespace, anything in 0x7F-0x9F).
# 6. Lane label (extracted from "lane <name>") MUST match [A-Za-z0-9_.-]+ so
#    pop_next_task's filename lookup is well-formed.
#
# Exit codes: 0 = clean, 1 = at least one failure.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

FIX_MODE=0
while (( $# > 0 )); do
  case "$1" in
    --fix) FIX_MODE=1; shift ;;
    *)     echo "unknown arg: $1"; exit 2 ;;
  esac
done

fail_count=0
file_count=0
line_count=0
PROMPT_MAX_WORDS="${PROMPT_MAX_WORDS:-50}"

scan_file() {
  local f="$1"
  [ -f "$f" ] || return 0
  file_count=$((file_count + 1))
  local n=0
  while IFS= read -r line; do
    n=$((n + 1))
    # Skip blank lines and comments
    [[ "$line" =~ ^[[:space:]]*$ ]] && continue
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    line_count=$((line_count + 1))

    local why="" word_count=0
    if ! [[ "$line" =~ ^/goal([[:space:]]|$) ]]; then
      why="must start with /goal"
    elif ! [[ "$line" =~ \.md ]]; then
      why="must reference at least one .md file"
    elif (( PROMPT_MAX_WORDS > 0 )) && {
      read -r -a words <<< "$line"
      word_count="${#words[@]}"
      (( word_count > PROMPT_MAX_WORDS ))
    }; then
      why="has ${word_count} words; word cap is ${PROMPT_MAX_WORDS}"
    elif (( ${#line} > 500 )); then
      why="line is ${#line} chars; cap is 500"
    elif [[ "$line" =~ [[:cntrl:]] ]] && ! [[ "$line" =~ ^[[:print:][:space:]]+$ ]]; then
      why="contains stray control character"
    elif [[ "$line" =~ lane[[:space:]]+([^[:space:]]+) ]]; then
      lane_token="${BASH_REMATCH[1]}"
      # strip trailing period/comma if present (extracted as part of token)
      lane_token="${lane_token%[.,;:]}"
      if ! [[ "$lane_token" =~ ^[A-Za-z0-9_.-]+$ ]]; then
        why="lane label '$lane_token' contains invalid characters"
      fi
    fi

    if [[ -n "$why" ]]; then
      fail_count=$((fail_count + 1))
      printf '  FAIL %s:%d  %s\n    >> %s\n' "$f" "$n" "$why" "${line:0:120}"
      if (( FIX_MODE )); then
        # Comment the line out in place
        sed -i.bak "${n}s|^|# AUTO-COMMENTED (validator: $why): |" "$f"
        printf '    (commented out in --fix mode)\n'
      fi
    fi
  done < "$f"
}

echo "=== validating codex-prompts-*.txt ==="
for f in codex-prompts-*.txt; do
  [ -f "$f" ] || continue
  scan_file "$f"
done

echo "=== validating codex-tasks/<session>/<lane>.txt ==="
if [ -d codex-tasks ]; then
  # Keep the loop in this shell. A pipeline would run the `while` body in a
  # subshell, losing fail_count/file_count updates before the final summary.
  while IFS= read -r f; do
    scan_file "$f"
  done < <(find codex-tasks -mindepth 2 -maxdepth 2 -name '*.txt' ! -name '._*' -print 2>/dev/null | sort)
fi

printf '\n=== summary ===\n'
printf 'files scanned: %d\n' "$file_count"
printf 'prompt lines checked: %d\n' "$line_count"
printf 'failures: %d\n' "$fail_count"

if (( fail_count > 0 )); then
  echo "REJECT: fix the failures above before starting the supervisor."
  exit 1
fi
echo "OK: every prompt line passes all mechanical checks."

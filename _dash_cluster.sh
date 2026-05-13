#!/bin/bash
# Cluster status pane renderer for tmux dashboard.
# Shows LUNARC cluster jobs with color coding.

R="\033[0m"
BOLD="\033[1m"
GREEN="\033[1;32m"
YELLOW="\033[0;33m"
BYELLOW="\033[1;33m"
CYAN="\033[0;36m"
DIM="\033[0;90m"
WHITE="\033[1;37m"
RED="\033[1;31m"

COLS=$(tput cols 2>/dev/null || echo 60)
SEP=$(printf '%.0s=' $(seq 1 $((COLS - 2))))

echo -e "${BYELLOW}${BOLD}  LUNARC CLUSTER${R}  ${DIM}$(date '+%H:%M:%S')${R}"
echo -e "${DIM}${SEP}${R}"

# Try SSH with timeout
OUTPUT=$(timeout 15 ssh lunarc "squeue -u scyiu --format='%.10i %.20j %.8T %.10M %.20R'" 2>/dev/null)
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo -e "  ${RED}SSH connection failed (exit $EXIT_CODE)${R}"
    echo -e "  ${DIM}Retrying next cycle...${R}"
    exit 0
fi

if [ -z "$OUTPUT" ]; then
    echo -e "  ${GREEN}No jobs running${R}"
    exit 0
fi

RUNNING=0
PENDING=0

while IFS= read -r line; do
    if echo "$line" | grep -q "JOBID"; then
        echo -e "  ${DIM}${line}${R}"
    elif echo "$line" | grep -q "RUNNING"; then
        echo -e "  ${GREEN}${line}${R}"
        RUNNING=$((RUNNING + 1))
    elif echo "$line" | grep -q "PENDING"; then
        echo -e "  ${YELLOW}${line}${R}"
        PENDING=$((PENDING + 1))
    elif echo "$line" | grep -q "COMPLETING"; then
        echo -e "  ${CYAN}${line}${R}"
    elif [ -n "$line" ]; then
        echo -e "  ${WHITE}${line}${R}"
    fi
done <<< "$OUTPUT"

echo ""
echo -e "  ${DIM}Total: ${GREEN}${RUNNING} running${R}, ${YELLOW}${PENDING} pending${R}"

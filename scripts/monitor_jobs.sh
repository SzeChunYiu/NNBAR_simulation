#!/usr/bin/env bash
# monitor_jobs.sh — poll SLURM jobs and post-process when complete.
# Usage: ./scripts/monitor_jobs.sh [job_id]  (omit to check all four jobs)
set -euo pipefail

REMOTE="lunarc"
RROOT="/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/build_lunarc/output"
LROOT="/Volumes/MyDrive/nnbar/nnbar/simulation/data/lunarc_output"
REPO="/Volumes/MyDrive/nnbar/nnbar/simulation"
FLAGS="${REPO}/.job_flags"
SCRIPTS="${REPO}/scripts"
mkdir -p "${FLAGS}" "${LROOT}"

# Registry: JOB_ID|TYPE|TASK_COUNT|REMOTE_BASE
REGISTRY=(
  "3053327|pi0_energy|5|"
  "3053328|pi0_mult|3|"
  "3053335|cosmic|4|cosmic_proton_bin5"
  "NEW_MU_BIN5|cosmic|4|cosmic_mu-_bin5"
)

log() { echo "[$(date '+%H:%M:%S')] $*"; }

sacct_states() {
  ssh "${REMOTE}" "sacct -X -j $1 --format=State --noheader 2>/dev/null" \
    | tr -d ' ' | grep -v '^$' || true
}

rsync_shards() {
  local rbase="$1" lbase="$2"
  for s in 0 1 2 3; do
    mkdir -p "${lbase}/shard${s}"
    rsync -av "${REMOTE}:${RROOT}/${rbase}/shard${s}/" "${lbase}/shard${s}/" 2>&1 | tail -2
  done
}

rsync_pi0_dirs() {
  local pattern="$1" lbase="$2"
  eval "for d in ${pattern}; do
    mkdir -p \"${lbase}/\${d}\"
    rsync -av \"${REMOTE}:${RROOT}/\${d}/\" \"${lbase}/\${d}/\" 2>&1 | tail -2
  done"
}

postprocess() {
  local jtype="$1" rbase="$2"
  case "${jtype}" in
    pi0_energy)
      rsync_pi0_dirs "pi0_mono_{100,200,300,400,500}mev" "${LROOT}/pi0_energy_scan"
      log "  running pi0 reco (energy scan)"
      (cd "${REPO}" && python3 "${SCRIPTS}/_pi0_postprocess.py" \
        energy \
        "data/lunarc_output/pi0_energy_scan" \
        "data/lunarc_output/pi0_reco/energy_scan" \
        .)
      ;;
    pi0_mult)
      rsync_pi0_dirs "pi0_multiplicity_{1,2,3}" "${LROOT}/pi0_multiplicity"
      log "  running pi0 reco (multiplicity)"
      (cd "${REPO}" && python3 "${SCRIPTS}/_pi0_postprocess.py" \
        mult \
        "data/lunarc_output/pi0_multiplicity" \
        "data/lunarc_output/pi0_reco/multiplicity" \
        .)
      ;;
    cosmic)
      rsync_shards "${rbase}" "${LROOT}/${rbase}"
      log "  checking row counts for ${rbase}"
      python3 "${SCRIPTS}/_cosmic_rowcheck.py" "${LROOT}/${rbase}"
      ;;
  esac
}

check_job() {
  local entry="$1"
  IFS='|' read -r jobid jtype ntasks rbase <<< "${entry}"

  [[ -f "${FLAGS}/done_${jobid}" ]] && { log "Job ${jobid}: already done — skip"; return; }

  if [[ "${jobid}" == "NEW_MU_BIN5" ]]; then
    log "Job NEW_MU_BIN5: placeholder — update registry with real job ID"; return
  fi

  log "Checking job ${jobid} (${jtype}, ${ntasks} tasks)…"
  local states
  states=$(sacct_states "${jobid}")
  [[ -z "${states}" ]] && { log "  no sacct records — pending?"; return; }

  if echo "${states}" | grep -qE '^(FAILED|CANCELLED|TIMEOUT|NODE_FAIL)$'; then
    log "  WARNING: job ${jobid} has failed tasks:"
    echo "${states}" | sort | uniq -c | sed 's/^/    /'; return
  fi

  local ndone
  ndone=$(echo "${states}" | grep -c '^COMPLETED$' || true)
  if [[ "${ndone}" -ge "${ntasks}" ]]; then
    log "  all ${ntasks} tasks COMPLETED — post-processing"
    postprocess "${jtype}" "${rbase}"
    touch "${FLAGS}/done_${jobid}"
    log "  flagged complete"
  else
    log "  ${ndone}/${ntasks} completed — still running"
    echo "${states}" | sort | uniq -c | sed 's/^/    /'
  fi
}

if [[ $# -eq 1 ]]; then
  matched=0
  for entry in "${REGISTRY[@]}"; do
    IFS='|' read -r jobid _ <<< "${entry}"
    if [[ "${jobid}" == "$1" ]]; then check_job "${entry}"; matched=1; break; fi
  done
  if [[ "${matched}" -eq 0 ]]; then
    log "Job $1 not in registry — state only:"
    sacct_states "$1" | sort | uniq -c | sed 's/^/  /'
  fi
else
  log "Checking all registered jobs…"
  for entry in "${REGISTRY[@]}"; do check_job "${entry}"; done
fi

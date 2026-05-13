#!/bin/bash
#SBATCH --job-name=nnbar-csup
#SBATCH --partition=lu48
#SBATCH --account=lu2026-2-51
#SBATCH --time=5-00:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=40
#SBATCH --mem=200G
#SBATCH --output=/projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim/holder.%j.log
# Holder allocation for the 20-pane NNBAR codex-supervisor layout (4 tmux sessions).
# Hold the allocation, then SSH in to start the four csup sessions:
#   ssh lunarc; ssh <holder-node>; cd /projects/hep/fs10/shared/nnbar/billy/NNBAR_Detector_sim
#   source /projects/hep/fs10/shared/codex-tooling/env-shared.sh
#   csup start --host=recon-lunarc
#   csup start --host=sim-lunarc
#   csup start --host=g4gpu-lunarc
#   csup start --host=review-lunarc

echo "===NODE: $(hostname)==="
echo "===START: $(date)==="
echo "===CPUS: $SLURM_CPUS_ON_NODE==="
echo "===MEM_MB: $SLURM_MEM_PER_NODE==="
echo "===JOBID: $SLURM_JOB_ID==="

# 5 days = 432000 seconds
sleep 432000

#!/bin/bash
# =============================================================================
# Generate P-Signal Training Data
# =============================================================================
# This script generates training data for the P-Signal classifier using:
# - Signal: pi+, pi-, proton from origin (isotropic directions)
# - Background: Compton electrons from TPC inner surface
# =============================================================================

set -e

# Configuration
NNBAR_BUILD="/home/billy/nnbar/simulation/NNBAR_Detector/build"
OUTPUT_BASE="/home/billy/nnbar/simulation/training_data/psignal_raw"
N_THREADS=4

# Number of events per particle type
N_SIGNAL_EACH=5000    # 5000 each for pi+, pi-, proton = 15000 signal
N_BACKGROUND=15000    # 15000 Compton electrons

echo "============================================================"
echo "P-Signal Training Data Generation"
echo "============================================================"
echo "Build directory: ${NNBAR_BUILD}"
echo "Output directory: ${OUTPUT_BASE}"
echo "Signal events per type: ${N_SIGNAL_EACH}"
echo "Background events: ${N_BACKGROUND}"
echo ""

# Create output directory
mkdir -p "${OUTPUT_BASE}"

# Change to build directory
cd "${NNBAR_BUILD}"

# Check if NNBAR executable exists
NNBAR_EXE="./nnbar-detector-simulation"
if [ ! -f "${NNBAR_EXE}" ]; then
    echo "ERROR: nnbar-detector-simulation executable not found in ${NNBAR_BUILD}"
    echo "Please build the simulation first."
    exit 1
fi

# Function to run simulation
run_sim() {
    local name=$1
    local macro=$2
    local n_events=$3
    local folder_name=$4

    echo "------------------------------------------------------------"
    echo "Generating: ${name} (${n_events} events)"
    echo "Output folder: output/${folder_name}/"

    # Create temporary macro with correct event count
    local tmp_macro="/tmp/${name}_run.mac"
    sed "s/beamOn.*/beamOn ${n_events}/" "../macros/${macro}" > "${tmp_macro}"

    # Run simulation in particle gun mode (output goes to ./output/${folder_name}/)
    ${NNBAR_EXE} -g -m "${tmp_macro}" -t ${N_THREADS} 2>&1 | tee "/tmp/${name}_simulation.log"

    # Move output to target location
    if [ -d "./output/${folder_name}" ]; then
        mkdir -p "${OUTPUT_BASE}/${folder_name}"
        cp -r "./output/${folder_name}/"* "${OUTPUT_BASE}/${folder_name}/"
        echo "Copied output to ${OUTPUT_BASE}/${folder_name}/"
    else
        echo "WARNING: Output directory ./output/${folder_name} not found!"
    fi

    # Cleanup
    rm -f "${tmp_macro}"

    echo "Completed: ${name}"
}

# Generate signal data
echo ""
echo "============================================================"
echo "Generating Signal Training Data"
echo "============================================================"

run_sim "signal_pip" "signal_pion_plus.mac" ${N_SIGNAL_EACH} "signal_pip"
run_sim "signal_pim" "signal_pion_minus.mac" ${N_SIGNAL_EACH} "signal_pim"
run_sim "signal_proton" "signal_proton.mac" ${N_SIGNAL_EACH} "signal_proton"

# Generate background data
echo ""
echo "============================================================"
echo "Generating Background Training Data"
echo "============================================================"

run_sim "background_compton" "background_compton.mac" ${N_BACKGROUND} "background_compton"

echo ""
echo "============================================================"
echo "Data Generation Complete!"
echo "============================================================"
echo ""
echo "Generated data locations:"
echo "  Signal (pi+):    ${OUTPUT_BASE}/signal_pip/"
echo "  Signal (pi-):    ${OUTPUT_BASE}/signal_pim/"
echo "  Signal (proton): ${OUTPUT_BASE}/signal_proton/"
echo "  Background:      ${OUTPUT_BASE}/background_compton/"
echo ""
echo "Next step: Run prepare_psignal_from_gun.py to create training dataset"
echo ""
echo "python3 nnbar_reconstruction/training/prepare_psignal_from_gun.py \\"
echo "  --input ${OUTPUT_BASE} \\"
echo "  --output training_data"

"""Post-process pi0 simulation outputs after LUNARC rsync.

Called by monitor_jobs.sh with two positional args:
  argv[1] = mode: "energy" or "mult"
  argv[2] = sim_output_root (local directory already rsynced)
  argv[3] = reco_output_dir
"""
import sys
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, sys.argv[4] if len(sys.argv) > 4 else ".")

mode = sys.argv[1]
sim_root = sys.argv[2]
reco_dir = sys.argv[3]

from nnbar_reconstruction.analysis.pi0_reco_driver import (
    run_pi0_reco,
    run_pi0_vertex_scan_reco,
)

if mode == "energy":
    written = run_pi0_reco(
        sim_output_root=sim_root,
        reco_output_dir=reco_dir,
        energies_mev=(100, 200, 300, 400, 500),
    )
elif mode == "mult":
    samples = (
        ("pi0_multiplicity_1", "pi0_reco_mult1.parquet"),
        ("pi0_multiplicity_2", "pi0_reco_mult2.parquet"),
        ("pi0_multiplicity_3", "pi0_reco_mult3.parquet"),
    )
    written = run_pi0_vertex_scan_reco(
        sim_output_root=sim_root,
        reco_output_dir=reco_dir,
        samples=samples,
    )
else:
    print(f"unknown mode {mode}", file=sys.stderr)
    sys.exit(1)

for p in written:
    print(f"  wrote {p}")

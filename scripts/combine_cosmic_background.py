"""Combine cosmic-ray parquet outputs with thesis Eq. 6.1 weights."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from nnbar_reconstruction.data_pipeline.cosmic_weights import PARTICLES, get_weight


_COSMIC_DIR_RE = re.compile(r"^cosmic_(?P<particle>.+)_(?:bin)?(?P<ebin>[0-5])$")
_PARTICLE_ALIASES = {"muon": "mu-", "electron": "e-"}
_SUBSYSTEM_NAMES = {
    "tpc": "TPC",
    "particle": "Particle",
    "scintillator": "Scintillator",
    "leadglass": "LeadGlass",
}


def parse_cosmic_directory(name: str) -> tuple[str, int] | None:
    """Return ``(particle, ebin)`` for cosmic output directory names."""
    match = _COSMIC_DIR_RE.match(name)
    if not match:
        return None

    particle = _PARTICLE_ALIASES.get(match.group("particle"), match.group("particle"))
    if particle not in PARTICLES:
        return None
    return particle, int(match.group("ebin"))


def combine_cosmic_background(
    cosmic_root: Path,
    output: Path,
    subsystem: str = "TPC",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Load cosmic parquet directories, apply Eq. 6.1 weights, and write parquet."""
    cosmic_root = Path(cosmic_root)
    output = Path(output)
    subsystem_name = _canonical_subsystem_name(subsystem)

    if not cosmic_root.is_dir():
        raise FileNotFoundError(f"Cosmic root directory not found: {cosmic_root}")

    frames: list[pd.DataFrame] = []
    for run_dir in sorted(path for path in cosmic_root.iterdir() if path.is_dir()):
        parsed = parse_cosmic_directory(run_dir.name)
        if parsed is None:
            continue

        particle, ebin = parsed
        particle_idx = PARTICLES.index(particle)
        cosmic_weight = get_weight(ebin, particle_idx)
        frame = _load_subsystem_parquet(run_dir, subsystem_name)
        if frame is None or frame.empty:
            continue

        weighted = frame.copy()
        input_weight = (
            pd.to_numeric(weighted["weight"])
            if "weight" in weighted
            else pd.Series(1.0, index=weighted.index)
        )
        weighted["weight"] = input_weight * cosmic_weight
        weighted["cosmic_weight"] = cosmic_weight
        weighted["cosmic_particle"] = particle
        weighted["cosmic_ebin"] = ebin
        weighted["cosmic_run"] = run_dir.name
        frames.append(weighted)

    if not frames:
        raise FileNotFoundError(
            f"No {subsystem_name}_output_*.parquet files found under {cosmic_root}"
        )

    combined = pd.concat(frames, ignore_index=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    combined.to_parquet(output, index=False)
    return combined, _summarize(combined)


def _canonical_subsystem_name(subsystem: str) -> str:
    return _SUBSYSTEM_NAMES.get(subsystem.lower(), subsystem)


def _load_subsystem_parquet(run_dir: Path, subsystem_name: str) -> pd.DataFrame | None:
    paths = sorted(run_dir.glob(f"{subsystem_name}_output_*.parquet"))
    if not paths:
        return None
    frames = []
    for path in paths:
        frame = pd.read_parquet(path).copy()
        frame["cosmic_source_file"] = path.name
        frames.append(frame)
    if len(frames) == 1:
        return frames[0]
    return pd.concat(frames, ignore_index=True)


def _summarize(combined: pd.DataFrame) -> dict[str, Any]:
    if "Event_ID" in combined:
        event_keys = ["cosmic_run", "Event_ID"]
        if "cosmic_source_file" in combined:
            event_keys.insert(1, "cosmic_source_file")
        unique_events = combined.drop_duplicates(event_keys)
        event_counts = (
            unique_events.groupby("cosmic_particle").size().astype(int).to_dict()
        )
        weighted_events = unique_events.groupby("cosmic_particle")["weight"].sum().to_dict()
    else:
        event_counts = combined.groupby("cosmic_particle").size().astype(int).to_dict()
        weighted_events = combined.groupby("cosmic_particle")["weight"].sum().to_dict()

    return {
        "total_rows": int(len(combined)),
        "n_events_by_particle": event_counts,
        "weighted_events_by_particle": {
            particle: float(weight) for particle, weight in weighted_events.items()
        },
        "total_weighted_events": float(sum(weighted_events.values())),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cosmic-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--subsystem", default="TPC")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    _, summary = combine_cosmic_background(args.cosmic_root, args.output, args.subsystem)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

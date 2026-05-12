"""π⁰ reconstruction driver for mono-energetic calibration samples.

This module converts existing raw simulation Parquets into the compact per-event
schema consumed by :mod:`neutral_pi0_response_audit`. It is intentionally a
local file transformer: it never submits jobs, retunes cuts, or generates new
simulation samples.
"""

from __future__ import annotations

from pathlib import Path
import warnings

import numpy as np
import pandas as pd

from ..reconstruction.neutral_reconstruction import (
    find_pi0_candidates,
    reconstruct_neutral_objects,
)
from ..utils.coordinates import compute_opening_angle

PI0_TRUTH_MASS_MEV = 134.9766
_HIT_COLUMNS = ("x", "y", "z", "eDep")
PI0_VERTEX_SCAN_SAMPLES = (
    ("pi0_vertex_scan_r0mev", "pi0_reco_vertex_r0mev.parquet"),
    ("pi0_vertex_scan_r5mev", "pi0_reco_vertex_r5mev.parquet"),
    ("pi0_vertex_scan_r10mev", "pi0_reco_vertex_r10mev.parquet"),
    ("pi0_vertex_scan_r15mev", "pi0_reco_vertex_r15mev.parquet"),
    ("pi0_vertex_scan_r20mev", "pi0_reco_vertex_r20mev.parquet"),
    ("pi0_vertex_scan_r25mev", "pi0_reco_vertex_r25mev.parquet"),
    ("pi0_vertex_scan_r30mev", "pi0_reco_vertex_r30mev.parquet"),
    ("pi0_vertex_disk_r30", "pi0_reco_vertex_disk_r30.parquet"),
)


def run_pi0_reco(
    sim_output_root: str | Path,
    reco_output_dir: str | Path,
    energies_mev: tuple[int, ...] = (50, 150, 250),
    vertex: np.ndarray = np.zeros(3),
) -> list[Path]:
    """Process raw π⁰ simulation output into per-event reco Parquet files.

    Args:
        sim_output_root: Directory containing ``pi0_mono_{E}mev`` raw outputs.
        reco_output_dir: Destination directory for ``pi0_reco_{E}mev.parquet``.
        energies_mev: Kinetic-energy sample tags to process.
        vertex: Production vertex used by the current mono-π⁰ samples.

    Returns:
        Paths written, in ``energies_mev`` order. Missing sample directories or
        raw Parquet files are warned and skipped; if every energy is absent the
        returned list is empty.
    """

    sim_root = Path(sim_output_root)
    out_dir = Path(reco_output_dir)
    vertex_array = np.asarray(vertex, dtype=float)
    written: list[Path] = []

    for energy_mev in energies_mev:
        raw_dir = sim_root / f"pi0_mono_{energy_mev}mev"
        raw_paths = _raw_paths(raw_dir)
        if not raw_dir.exists() or not all(path.exists() for path in raw_paths.values()):
            warnings.warn(
                f"Skipping {energy_mev} MeV π⁰ sample; raw directory/files missing: {raw_dir}",
                RuntimeWarning,
                stacklevel=2,
            )
            continue

        truth_df = pd.read_parquet(raw_paths["truth"])
        lg_df = pd.read_parquet(raw_paths["leadglass"])
        scint_df = pd.read_parquet(raw_paths["scintillator"])
        reco_rows = _reconstruct_energy_rows(truth_df, lg_df, scint_df, vertex_array)

        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"pi0_reco_{energy_mev}mev.parquet"
        pd.DataFrame(reco_rows).to_parquet(out_path, index=False)
        written.append(out_path)

    return written


def run_pi0_vertex_scan_reco(
    sim_output_root: str | Path,
    reco_output_dir: str | Path,
    samples: tuple[tuple[str, str], ...] = PI0_VERTEX_SCAN_SAMPLES,
) -> list[Path]:
    """Process vertex-scan π⁰ raw samples into per-event reco Parquets.

    Args:
        sim_output_root: Directory containing ``pi0_vertex_*`` raw outputs.
        reco_output_dir: Destination directory for vertex response Parquets.
        samples: ``(raw_dir_name, output_file_name)`` pairs to process.

    Returns:
        Paths written, in ``samples`` order. Missing sample directories or raw
        Parquet files are warned and skipped.
    """

    sim_root = Path(sim_output_root)
    out_dir = Path(reco_output_dir)
    written: list[Path] = []

    for raw_name, output_name in samples:
        raw_dir = sim_root / raw_name
        raw_paths = _raw_paths(raw_dir)
        if not raw_dir.exists() or not all(path.exists() for path in raw_paths.values()):
            warnings.warn(
                f"Skipping π⁰ vertex-scan sample; raw directory/files missing: {raw_dir}",
                RuntimeWarning,
                stacklevel=2,
            )
            continue

        truth_df = pd.read_parquet(raw_paths["truth"])
        lg_df = pd.read_parquet(raw_paths["leadglass"])
        scint_df = pd.read_parquet(raw_paths["scintillator"])
        reco_rows = _reconstruct_vertex_rows(truth_df, lg_df, scint_df)

        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / output_name
        pd.DataFrame(reco_rows).to_parquet(out_path, index=False)
        written.append(out_path)

    return written


def _raw_paths(raw_dir: Path) -> dict[str, Path]:
    return {
        "truth": raw_dir / "Particle_output_0.parquet",
        "leadglass": raw_dir / "LeadGlass_output_0.parquet",
        "scintillator": raw_dir / "Scintillator_output_0.parquet",
    }


def _reconstruct_energy_rows(
    truth_df: pd.DataFrame,
    lg_df: pd.DataFrame,
    scint_df: pd.DataFrame,
    vertex: np.ndarray,
) -> list[dict[str, float | int]]:
    lg_groups = _event_groups(lg_df)
    scint_groups = _event_groups(scint_df)
    empty_hits = pd.DataFrame(columns=_HIT_COLUMNS)
    rows: list[dict[str, float | int]] = []

    for truth_row in truth_df.itertuples(index=False):
        event_id = int(getattr(truth_row, "Event_ID"))
        truth_ke = float(getattr(truth_row, "KE"))
        lg_hits = _hit_view(lg_groups.get(event_id, empty_hits))
        scint_hits = _hit_view(scint_groups.get(event_id, empty_hits))
        neutral_objects = reconstruct_neutral_objects(vertex, scint_hits, lg_hits)
        candidates = find_pi0_candidates(neutral_objects, vertex)
        best = max(candidates, key=lambda item: item[2], default=None)
        rows.append(
            _event_row(
                event_id=event_id,
                truth_ke=truth_ke,
                neutral_count=len(neutral_objects),
                candidate_count=len(candidates),
                best_candidate=best,
                vertex=vertex,
            )
        )

    return rows


def _reconstruct_vertex_rows(
    truth_df: pd.DataFrame,
    lg_df: pd.DataFrame,
    scint_df: pd.DataFrame,
) -> list[dict[str, float | int | bool]]:
    lg_groups = _event_groups(lg_df)
    scint_groups = _event_groups(scint_df)
    empty_hits = pd.DataFrame(columns=_HIT_COLUMNS)
    rows: list[dict[str, float | int | bool]] = []

    for truth_row in truth_df.itertuples(index=False):
        event_id = int(getattr(truth_row, "Event_ID"))
        truth_ke = float(getattr(truth_row, "KE"))
        vertex = _truth_vertex_array(truth_row)
        lg_hits = _hit_view(lg_groups.get(event_id, empty_hits))
        scint_hits = _hit_view(scint_groups.get(event_id, empty_hits))
        neutral_objects = reconstruct_neutral_objects(vertex, scint_hits, lg_hits)
        candidates = find_pi0_candidates(neutral_objects, vertex)
        best = max(candidates, key=lambda item: item[2], default=None)
        rows.append(
            _event_row(
                event_id=event_id,
                truth_ke=truth_ke,
                neutral_count=len(neutral_objects),
                candidate_count=len(candidates),
                best_candidate=best,
                vertex=vertex,
            )
        )

    return rows


def _event_groups(frame: pd.DataFrame) -> dict[int, pd.DataFrame]:
    if frame.empty or "Event_ID" not in frame.columns:
        return {}
    return {int(event_id): group for event_id, group in frame.groupby("Event_ID", sort=False)}


def _hit_view(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=_HIT_COLUMNS)
    return frame.loc[:, list(_HIT_COLUMNS)].copy()


def _event_row(
    *,
    event_id: int,
    truth_ke: float,
    neutral_count: int,
    candidate_count: int,
    best_candidate,
    vertex: np.ndarray,
) -> dict[str, float | int | bool]:
    truth_total_energy = truth_ke + PI0_TRUTH_MASS_MEV
    row: dict[str, float | int | bool] = {
        "Event_ID": event_id,
        "truth_ke_mev": truth_ke,
        "truth_total_energy_mev": truth_total_energy,
        "n_neutral_objects": neutral_count,
        "n_pi0_candidates": candidate_count,
        "pi0_mass_mev": np.nan,
        "opening_angle_deg": np.nan,
        "reco_photon_energy_mev": np.nan,
        "reco_total_energy_mev": np.nan,
        "truth_photon_energy_mev": truth_total_energy / 2.0,
        "truth_vertex_x_cm": float(vertex[0]),
        "truth_vertex_y_cm": float(vertex[1]),
        "truth_vertex_z_cm": float(vertex[2]),
        "truth_vertex_r_cm": float(np.hypot(vertex[0], vertex[1])),
        "reco_eff_flag": False,
    }
    if best_candidate is None:
        return row

    obj1, obj2, invariant_mass = best_candidate
    opening_angle_rad = compute_opening_angle(vertex, obj1.position, obj2.position)
    row.update(
        {
            "pi0_mass_mev": float(invariant_mass),
            "opening_angle_deg": float(np.degrees(opening_angle_rad)),
            "reco_photon_energy_mev": float((obj1.energy + obj2.energy) / 2.0),
            "reco_total_energy_mev": float(obj1.energy + obj2.energy),
            "reco_eff_flag": True,
        }
    )
    return row


def _truth_vertex_array(truth_row) -> np.ndarray:
    return np.array(
        [
            float(getattr(truth_row, "x", 0.0)),
            float(getattr(truth_row, "y", 0.0)),
            float(getattr(truth_row, "z", 0.0)),
        ],
        dtype=float,
    )

"""Electron-pair topology helpers for Ch.8 charged-object integration.

The thesis Ch.8 conversion-pair rule is an observable topology rule: two
charged TPC entry points within the configured 5 cm window are represented as
one e+/e- conversion pair for downstream pion and event-variable counting.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np

from ..utils.config import get_particle_id_params

THESIS_EP_PAIR_DISTANCE_CM = 5.0
ELECTRON_PAIR_LABEL = "ELECTRON_PAIR"
ELECTRON_PAIR_MEMBER_LABEL = "ELECTRON_PAIR_MEMBER"


@dataclass(frozen=True)
class ElectronPairCandidate:
    """Matched e+/e- conversion-pair candidate from TPC entry topology.

    Args:
        primary_index: Index of the row that carries the pair label.
        secondary_index: Index of the paired member row.
        primary_object_id: Stable charged-object id for the pair label row.
        secondary_object_id: Stable charged-object id for the member row.
        distance_cm: TPC entry-point separation in cm.
    """

    primary_index: int
    secondary_index: int
    primary_object_id: int
    secondary_object_id: int
    distance_cm: float

    @property
    def object_ids(self) -> tuple[int, int]:
        """Return stable charged-object ids for the matched pair."""
        return (self.primary_object_id, self.secondary_object_id)


def configured_pair_distance_cm(max_distance_cm: float | None = None) -> float:
    """Return the e+/e- TPC-entry distance threshold in cm.

    Args:
        max_distance_cm: Optional explicit override for tests or scans.

    Returns:
        Positive distance threshold in cm.
    """
    if max_distance_cm is not None:
        return float(max_distance_cm)
    params = get_particle_id_params()
    return float(params.get("epair_distance", THESIS_EP_PAIR_DISTANCE_CM))


def is_electron_pair_distance(
    track1_entry: np.ndarray,
    track2_entry: np.ndarray,
    max_distance_cm: float | None = None,
) -> tuple[bool, float]:
    """Test whether two TPC entries satisfy the Ch.8 pair-distance rule.

    Args:
        track1_entry: TPC entry point of the first charged row.
        track2_entry: TPC entry point of the second charged row.
        max_distance_cm: Optional threshold override in cm.

    Returns:
        Tuple of ``(is_pair, distance_cm)``.  The boundary is inclusive because
        the spec says entry points *within 5 cm* are conversion-pair topology.
    """
    threshold = configured_pair_distance_cm(max_distance_cm)
    distance = float(np.linalg.norm(np.asarray(track1_entry) - np.asarray(track2_entry)))
    return bool(distance <= threshold), distance


def find_electron_pairs(
    charged_objects: Sequence[object],
    max_distance_cm: float | None = None,
) -> list[ElectronPairCandidate]:
    """Find non-overlapping e+/e- pairs among charged-object rows.

    Args:
        charged_objects: Charged rows with ``object_id`` and ``tpc_entry``.
        max_distance_cm: Optional threshold override in cm.

    Returns:
        Greedy list of closest non-overlapping pair candidates.
    """
    candidates: list[tuple[float, int, int]] = []
    for left_index, left in enumerate(charged_objects):
        left_entry = _tpc_entry(left)
        if left_entry is None:
            continue
        for right_index in range(left_index + 1, len(charged_objects)):
            right = charged_objects[right_index]
            right_entry = _tpc_entry(right)
            if right_entry is None:
                continue
            is_pair, distance = is_electron_pair_distance(
                left_entry,
                right_entry,
                max_distance_cm=max_distance_cm,
            )
            if is_pair:
                candidates.append((distance, left_index, right_index))

    pairs: list[ElectronPairCandidate] = []
    used: set[int] = set()
    for distance, left_index, right_index in sorted(candidates):
        if left_index in used or right_index in used:
            continue
        left = charged_objects[left_index]
        right = charged_objects[right_index]
        pairs.append(
            ElectronPairCandidate(
                primary_index=left_index,
                secondary_index=right_index,
                primary_object_id=_object_id(left, left_index),
                secondary_object_id=_object_id(right, right_index),
                distance_cm=distance,
            )
        )
        used.update({left_index, right_index})
    return pairs


def apply_electron_pair_labels(
    charged_objects: Sequence[object],
    max_distance_cm: float | None = None,
) -> list[ElectronPairCandidate]:
    """Label matched e+/e- rows so pion counters cannot consume them.

    Args:
        charged_objects: Mutable charged-object rows with ``particle_type``.
        max_distance_cm: Optional threshold override in cm.

    Returns:
        Pair candidates that were labeled.  The primary row receives
        ``ELECTRON_PAIR`` and the secondary row receives
        ``ELECTRON_PAIR_MEMBER`` so the pair is countable once.
    """
    pairs = find_electron_pairs(charged_objects, max_distance_cm=max_distance_cm)
    for pair in pairs:
        primary = charged_objects[pair.primary_index]
        secondary = charged_objects[pair.secondary_index]
        _label_pair_row(primary, ELECTRON_PAIR_LABEL, pair)
        _label_pair_row(secondary, ELECTRON_PAIR_MEMBER_LABEL, pair)
    return pairs


def electron_pair_event_counts(
    charged_objects: Iterable[object],
    max_distance_cm: float | None = None,
) -> dict[str, int | bool | str]:
    """Expose electron-pair counts for event output rows.

    Args:
        charged_objects: Charged-object rows to audit.
        max_distance_cm: Optional threshold override in cm.

    Returns:
        Dictionary with ``n_electron_pairs`` plus a blocker flag/reason.  Missing
        TPC entries are explicit blockers rather than silently reporting zero.
    """
    objects = list(charged_objects)
    if any(_tpc_entry(obj) is None for obj in objects):
        return {
            "n_electron_pairs": 0,
            "electron_pair_count_blocked": True,
            "electron_pair_blocker_reason": "missing_tpc_entry",
        }

    labeled_count = sum(
        1 for obj in objects if getattr(obj, "particle_type", None) == ELECTRON_PAIR_LABEL
    )
    n_pairs = labeled_count or len(find_electron_pairs(objects, max_distance_cm=max_distance_cm))
    return {
        "n_electron_pairs": int(n_pairs),
        "electron_pair_count_blocked": False,
        "electron_pair_blocker_reason": "",
    }


def _tpc_entry(obj: object) -> np.ndarray | None:
    """Return a finite TPC entry vector or ``None`` when unavailable."""
    entry = getattr(obj, "tpc_entry", None)
    if entry is None:
        return None
    array = np.asarray(entry, dtype=float)
    if array.shape != (3,) or not np.all(np.isfinite(array)):
        return None
    return array


def _object_id(obj: object, fallback: int) -> int:
    """Return stable object id if present, else the row index fallback."""
    return int(getattr(obj, "object_id", fallback))


def _label_pair_row(obj: object, label: str, pair: ElectronPairCandidate) -> None:
    """Attach pair-label metadata to a mutable charged-object row."""
    setattr(obj, "particle_type", label)
    setattr(obj, "pid_confidence", 1.0)
    setattr(obj, "electron_pair_id", pair.primary_object_id)
    setattr(obj, "electron_pair_distance_cm", pair.distance_cm)

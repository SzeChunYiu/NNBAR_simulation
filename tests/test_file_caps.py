"""Regression checks for compact source files touched by worker lanes."""

from pathlib import Path


def test_object_identification_stays_below_pre_addition_guard():
    path = Path("nnbar_reconstruction/reconstruction/object_identification.py")
    line_count = len(path.read_text().splitlines())

    assert line_count <= 450


def test_tracking_clustering_modules_stay_below_file_cap():
    paths = [
        Path("nnbar_reconstruction/tracking/clustering.py"),
        Path("nnbar_reconstruction/tracking/clustering_backends.py"),
        Path("nnbar_reconstruction/tracking/clustering_refinement.py"),
        Path("nnbar_reconstruction/tracking/clustering_variants.py"),
    ]

    for path in paths:
        line_count = len(path.read_text().splitlines())
        assert line_count <= 500, f"{path} has {line_count} lines"

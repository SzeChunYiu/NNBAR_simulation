"""Regression checks for compact source files touched by worker lanes."""

from pathlib import Path


def test_object_identification_stays_below_pre_addition_guard():
    path = Path("nnbar_reconstruction/reconstruction/object_identification.py")
    line_count = len(path.read_text().splitlines())

    assert line_count <= 450

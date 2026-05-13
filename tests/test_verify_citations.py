"""Regression tests for markdown source-citation verification."""

from __future__ import annotations

from pathlib import Path

from scripts.verify_citations import verify_one


def test_verify_one_accepts_cxx_class_declaration_citation(tmp_path: Path) -> None:
    """C++ class declarations are valid cited signatures."""
    source = tmp_path / "Detector.hh"
    source.write_text("class Detector {\n};\n", encoding="utf-8")

    item = verify_one(
        doc=tmp_path / "plan.md",
        doc_line=1,
        citation_path="Detector.hh",
        start=1,
        end=1,
        identifiers=["Detector"],
        source_roots=[tmp_path],
        strict_missing_identifier=True,
    )

    assert item.status == "ok"
    assert item.signature_lines == [1]

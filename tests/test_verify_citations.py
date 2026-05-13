"""Regression tests for markdown source-citation verification."""

from __future__ import annotations

from pathlib import Path

from scripts.verify_citations import expand_doc_inputs, verify_one


def test_expand_doc_inputs_skips_macos_appledouble_markdown_sidecars(
    tmp_path: Path,
) -> None:
    """Directory scans must ignore binary ``._*.md`` AppleDouble sidecars."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    real_doc = docs_dir / "plan.md"
    real_doc.write_text("# Plan\n", encoding="utf-8")
    (docs_dir / "._plan.md").write_bytes(b"\x00\x05bad resource fork")

    assert expand_doc_inputs([docs_dir]) == [real_doc]


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

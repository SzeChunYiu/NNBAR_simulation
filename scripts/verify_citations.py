#!/usr/bin/env python3
"""Verify rebuild-plan source citations against real code signatures.

The verifier is intentionally small and local: it scans markdown files for
source line citations, finds the nearest backticked code identifier, and checks
that a matching Python/C++ signature lands inside the cited line range.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable, NamedTuple

CITATION_RE = re.compile(
    r"(?P<path>[A-Za-z0-9_./-]+\.(?:py|cc|hh)):(?P<start>\d+)"
    r"(?:\s*[-–—]\s*(?P<end>\d+))?"
)
BACKTICK_RE = re.compile(r"`([^`]+)`")
IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
IGNORED_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", "externals"}


class CitationItem(NamedTuple):
    """One citation verification result."""
    doc: str
    doc_line: int
    citation: str
    source_path: str
    start: int
    end: int
    identifier: str | None
    status: str
    message: str
    candidate_files: list[str]
    signature_lines: list[int]


class VerificationReport(NamedTuple):
    """Aggregate verification result returned to tests and CLI callers."""
    summary: dict[str, int]
    items: list[CitationItem]


def normalize_text(text: str) -> str:
    """Normalize punctuation that appears in hand-written plan citations."""
    return text.replace("–", "-").replace("—", "-")


def default_simulation_root() -> Path:
    """Return the orchestration repository root inferred from this script."""
    return Path(__file__).resolve().parents[1]


def default_source_roots(simulation_root: Path) -> list[Path]:
    """Return source roots searched by the parallel-session L3 verifier."""
    roots = []
    env_root = os.environ.get("NNBAR_DETECTOR_L3_ROOT")
    if env_root:
        roots.append(Path(env_root))
    roots.append(Path("/Volumes/MyDrive/nnbar/nnbar/NNBAR_Detector-L3"))
    roots.append(simulation_root)

    unique: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        resolved = root.expanduser().resolve() if root.exists() else root.expanduser()
        if resolved not in seen and root.exists():
            unique.append(resolved)
            seen.add(resolved)
    return unique


def default_doc_paths(simulation_root: Path) -> list[Path]:
    """Return default rebuild-plan and parallel-session markdown inputs."""
    patterns = ["docs/rebuild_plans/**/*.md", "docs/parallel-sessions/*.md"]
    docs: list[Path] = []
    for pattern in patterns:
        docs.extend(sorted(simulation_root.glob(pattern)))
    return docs


def cite_label(path: str, start: int, end: int) -> str:
    """Format a citation label for reports."""
    return f"{path}:{start}" if start == end else f"{path}:{start}-{end}"


def iter_markdown_citations(doc: Path) -> Iterable[tuple[int, str, int, int, str | None]]:
    """Yield source citations and nearby code identifiers from one markdown file."""
    lines = doc.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines, start=1):
        normalized_line = normalize_text(line)
        backticks = list(BACKTICK_RE.finditer(normalized_line))
        for match in CITATION_RE.finditer(normalized_line):
            path = match.group("path")
            start = int(match.group("start"))
            end = int(match.group("end") or start)
            identifier = nearest_identifier(normalized_line, match.start(), match.end(), backticks)
            yield index, path, start, end, identifier


def nearest_identifier(
    line: str,
    cite_start: int,
    cite_end: int,
    backticks: list[re.Match[str]],
) -> str | None:
    """Find the nearest likely code identifier in backticks on the same line."""
    candidates: list[tuple[int, str]] = []
    for tick in backticks:
        content = tick.group(1).strip()
        if CITATION_RE.search(content):
            continue
        identifier = extract_identifier(content)
        if identifier is None:
            continue
        if not looks_like_signature_claim(content, identifier):
            continue
        distance = min(abs(tick.end() - cite_start), abs(tick.start() - cite_end))
        candidates.append((distance, identifier))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0])
    return candidates[0][1]


def extract_identifier(content: str) -> str | None:
    """Extract the function/class name from a backticked markdown code span."""
    if any(marker in content for marker in ("/", "\\", "->")):
        return None
    if ".py" in content or ".cc" in content or ".hh" in content:
        return None
    before_paren = content.split("(", 1)[0].strip()
    if "." in before_paren:
        before_paren = before_paren.rsplit(".", 1)[-1]
    matches = IDENTIFIER_RE.findall(before_paren or content)
    if not matches:
        return None
    return matches[-1] if "." in content else matches[0]


def looks_like_signature_claim(content: str, identifier: str) -> bool:
    """Filter table labels/material names that are not function/class claims."""
    if "(" in content:
        return True
    if identifier.startswith("_"):
        return True
    if identifier and identifier[0].islower():
        return True
    if "class " in content.lower():
        return True
    return False


def resolve_candidates(citation_path: str, source_roots: list[Path]) -> list[Path]:
    """Find source files matching a cited relative path or basename."""
    suffix = Path(citation_path)
    candidates: list[Path] = []
    seen: set[Path] = set()
    for root in source_roots:
        direct = root / suffix
        if direct.exists() and direct.is_file():
            resolved = direct.resolve()
            if resolved not in seen:
                candidates.append(resolved)
                seen.add(resolved)
    if candidates:
        return candidates

    basename = suffix.name
    for root in source_roots:
        for path in walk_source_files(root, basename):
            resolved = path.resolve()
            if resolved not in seen and path.name == basename:
                candidates.append(resolved)
                seen.add(resolved)
    return candidates


def walk_source_files(root: Path, basename: str) -> Iterable[Path]:
    """Walk a source root while avoiding large generated/vendor trees."""
    for current, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        if basename in files:
            yield Path(current) / basename


def signature_regex(identifier: str, suffix: str) -> re.Pattern[str]:
    """Build a Python or C++ signature regex for a cited identifier."""
    name = re.escape(identifier)
    if suffix == ".py":
        return re.compile(rf"^\s*(?:async\s+)?(?:def|class)\s+{name}\b")
    return re.compile(
        rf"^\s*(?:[A-Za-z_][\w:<>,~*&\s]+\s+)+{name}\s*\("
        rf"|^\s*{name}::[A-Za-z_~][\w~]*\s*\("
    )


def signature_lines(path: Path, identifier: str) -> list[int]:
    """Return line numbers whose signatures match the identifier."""
    pattern = signature_regex(identifier, path.suffix)
    lines: list[int] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return lines
    for line_no, line in enumerate(text.splitlines(), start=1):
        if pattern.search(line):
            lines.append(line_no)
    return lines


def verify_one(
    doc: Path,
    doc_line: int,
    citation_path: str,
    start: int,
    end: int,
    identifier: str | None,
    source_roots: list[Path],
    strict_missing_identifier: bool,
) -> CitationItem:
    """Verify one markdown citation against source candidates."""
    label = cite_label(citation_path, start, end)
    if identifier is None:
        status = "missing_identifier" if strict_missing_identifier else "skipped"
        return CitationItem(
            str(doc),
            doc_line,
            label,
            citation_path,
            start,
            end,
            None,
            status,
            "no nearby backticked function/class identifier",
            [],
            [],
        )

    candidates = resolve_candidates(citation_path, source_roots)
    if not candidates:
        return CitationItem(
            str(doc),
            doc_line,
            label,
            citation_path,
            start,
            end,
            identifier,
            "file_not_found",
            "source file not found in configured roots",
            [],
            [],
        )

    all_lines: list[int] = []
    candidate_labels = [str(path) for path in candidates]
    for candidate in candidates:
        lines = signature_lines(candidate, identifier)
        all_lines.extend(lines)
        if any(start <= line <= end for line in lines):
            return CitationItem(
                str(doc),
                doc_line,
                label,
                citation_path,
                start,
                end,
                identifier,
                "ok",
                "signature line falls inside cited range",
                candidate_labels,
                sorted(set(all_lines)),
            )

    status = "symbol_not_found" if not all_lines else "mismatch"
    message = "signature not found" if not all_lines else "signature exists outside cited range"
    return CitationItem(
        str(doc),
        doc_line,
        label,
        citation_path,
        start,
        end,
        identifier,
        status,
        message,
        candidate_labels,
        sorted(set(all_lines)),
    )


def verify_paths(
    doc_paths: list[Path],
    source_roots: list[Path],
    report_json: Path,
    report_md: Path,
    strict_missing_identifier: bool = False,
) -> VerificationReport:
    """Verify citations, write JSON/markdown reports, and return a summary."""
    items: list[CitationItem] = []
    roots = [root.resolve() for root in source_roots]
    for doc in sorted(Path(path) for path in doc_paths):
        if not doc.exists() or not doc.is_file():
            continue
        for doc_line, path, start, end, identifier in iter_markdown_citations(doc):
            items.append(
                verify_one(
                    doc=doc,
                    doc_line=doc_line,
                    citation_path=path,
                    start=start,
                    end=end,
                    identifier=identifier,
                    source_roots=roots,
                    strict_missing_identifier=strict_missing_identifier,
                )
            )

    counts = Counter(item.status for item in items)
    failure_statuses = {"mismatch", "file_not_found", "symbol_not_found"}
    if strict_missing_identifier:
        failure_statuses.add("missing_identifier")
    failures = sum(counts[status] for status in failure_statuses)
    summary = {
        "total": len(items),
        "ok": counts["ok"],
        "skipped": counts["skipped"],
        "missing_identifier": counts["missing_identifier"],
        "mismatch": counts["mismatch"],
        "file_not_found": counts["file_not_found"],
        "symbol_not_found": counts["symbol_not_found"],
        "failures": failures,
    }
    report = VerificationReport(summary=summary, items=items)
    write_json_report(report, report_json)
    write_markdown_report(report, report_md)
    return report


def write_json_report(report: VerificationReport, path: Path) -> None:
    """Write a machine-readable verifier report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "summary": report.summary,
        "items": [item._asdict() for item in report.items],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown_report(report: VerificationReport, path: Path) -> None:
    """Write a human-readable verifier report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Citation verification report",
        "",
        "## Summary",
        "",
    ]
    for key, value in report.summary.items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Findings", ""])
    if not report.items:
        lines.append("No source citations found.")
    for item in report.items:
        marker = "✅" if item.status == "ok" else "⚠️" if item.status == "skipped" else "❌"
        identifier = item.identifier or "<none>"
        signature = ", ".join(str(line) for line in item.signature_lines) or "n/a"
        lines.append(
            f"- {marker} `{item.status}` {item.doc}:{item.doc_line} "
            f"`{identifier}` `{item.citation}` — {item.message}; signature lines: {signature}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse CLI arguments."""
    simulation_root = default_simulation_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Markdown files or directories to scan; defaults to rebuild plans and lane specs.",
    )
    parser.add_argument(
        "--source-root",
        action="append",
        type=Path,
        default=None,
        help="Source root to search; may be repeated.",
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        default=simulation_root / "docs" / "audit" / "citation-report.json",
        help="Path for the JSON report.",
    )
    parser.add_argument(
        "--report-md",
        type=Path,
        default=simulation_root / "docs" / "audit" / "citation-report.md",
        help="Path for the markdown report.",
    )
    parser.add_argument(
        "--strict-missing-identifier",
        action="store_true",
        help="Treat citations with no nearby backticked symbol as failures.",
    )
    return parser.parse_args(argv)


def expand_doc_inputs(paths: list[Path]) -> list[Path]:
    """Expand CLI markdown inputs into files."""
    if not paths:
        return default_doc_paths(default_simulation_root())
    docs: list[Path] = []
    for path in paths:
        if path.is_dir():
            docs.extend(sorted(path.rglob("*.md")))
        else:
            docs.append(path)
    return docs


def main(argv: list[str] | None = None) -> int:
    """Run the citation verifier CLI."""
    args = parse_args(sys.argv[1:] if argv is None else argv)
    simulation_root = default_simulation_root()
    source_roots = args.source_root or default_source_roots(simulation_root)
    report = verify_paths(
        doc_paths=expand_doc_inputs(args.paths),
        source_roots=source_roots,
        report_json=args.report_json,
        report_md=args.report_md,
        strict_missing_identifier=args.strict_missing_identifier,
    )
    print(json.dumps(report.summary, sort_keys=True))
    return 1 if report.summary["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

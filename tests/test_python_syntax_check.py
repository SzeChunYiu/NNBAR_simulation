"""Regression tests for the project Python syntax checker."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "check_python_syntax.py"


def test_syntax_checker_ignores_macos_appledouble_sidecars(tmp_path: Path) -> None:
    """macOS ``._*.py`` sidecars must not make syntax verification fail."""
    source_root = tmp_path / "pkg"
    source_root.mkdir()
    (source_root / "module.py").write_text("ANSWER = 42\n", encoding="utf-8")
    (source_root / "._module.py").write_bytes(b"\x00\x05bad resource fork")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(source_root)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "compiled roots: 1" in result.stdout


def test_syntax_checker_fails_on_real_python_syntax_errors(tmp_path: Path) -> None:
    """The AppleDouble filter must not hide ordinary source syntax errors."""
    source_root = tmp_path / "pkg"
    source_root.mkdir()
    (source_root / "broken.py").write_text("def nope(:\n    pass\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(source_root)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    assert "syntax check failed" in result.stdout

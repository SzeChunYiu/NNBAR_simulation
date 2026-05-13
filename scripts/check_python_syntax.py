#!/usr/bin/env python3
"""Compile project Python sources while skipping macOS AppleDouble sidecars."""

from __future__ import annotations

import argparse
import compileall
import re
import sys
from pathlib import Path


DEFAULT_ROOTS = ("scripts", "nnbar_reconstruction", "tests", "benchmarks")
SKIP_PATTERN = re.compile(r"(^|/)(\._[^/]*|__pycache__)(/|$)")


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Syntax-check Python source roots with compileall while ignoring "
            "macOS AppleDouble resource-fork sidecars such as ._module.py."
        )
    )
    parser.add_argument(
        "roots",
        nargs="*",
        default=list(DEFAULT_ROOTS),
        help="Source roots to compile (default: project Python roots).",
    )
    return parser.parse_args(argv)


def compile_roots(roots: list[str]) -> bool:
    """Compile all existing roots and return True only when every root passes."""
    compiled = 0
    ok = True
    for root_text in roots:
        root = Path(root_text)
        if not root.exists():
            print(f"missing root: {root}", file=sys.stderr)
            ok = False
            continue
        if root.is_dir():
            root_ok = compileall.compile_dir(root, quiet=1, rx=SKIP_PATTERN)
        else:
            root_ok = compileall.compile_file(root, quiet=1, rx=SKIP_PATTERN)
        compiled += 1
        ok = ok and root_ok

    print(f"compiled roots: {compiled}")
    if not ok:
        print("syntax check failed")
    return ok


def main(argv: list[str] | None = None) -> int:
    """Run the syntax checker."""
    args = parse_args(sys.argv[1:] if argv is None else argv)
    return 0 if compile_roots(args.roots) else 1


if __name__ == "__main__":
    raise SystemExit(main())

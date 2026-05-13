#!/usr/bin/env python3
"""CLI entry point for the benchmark harness.

The default mode is a local-safe dry run: render the SLURM script that would be
submitted on LUNARC and print it to stdout.  Passing ``--submit`` writes the
script then invokes ``sbatch`` through :mod:`benchmarks.harness.runner`.
"""

from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path
from typing import Iterable, Sequence

from benchmarks.harness.builder import build_optimized, build_vanilla
from benchmarks.harness.runner import RunRequest, render_sbatch, submit_sbatch, write_sbatch
from benchmarks.harness.schema import RESULT_SCHEMA

DEFAULT_GEANT4_PREFIX = "/projects/hep/fs10/shared/nnbar/billy/packages/hibeam_env"
DEFAULT_SEEDS = 20
DEFAULT_EVENTS = 1000


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for dry-run, submit, and collect modes."""

    parser = argparse.ArgumentParser(
        description="Benchmark harness CLI: render or submit LUNARC sbatch jobs.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--collect", action="store_true", help="collect raw run outputs into the result schema")
    parser.add_argument("--submit", action="store_true", help="submit the generated sbatch script")
    parser.add_argument("--build", action="store_true", help="run builder.py before rendering/submitting")
    parser.add_argument("--generate-reference", action="store_true", help="generate vanilla reference jobs")
    parser.add_argument("--opt-id", help="optimization identifier, e.g. BD-geant4-032")
    parser.add_argument("--opt-branch", default="HEAD", help="optimized build branch or commit")
    parser.add_argument("--opt-cmake-flags", default="", help="extra CMake flags for the optimized build")
    parser.add_argument("--workload", nargs="+", help="one or more workload IDs, e.g. W1 W2")
    parser.add_argument("--physics-list", nargs="+", help="one or more physics-list IDs, e.g. PL1 PL2")
    parser.add_argument("--hw", nargs="+", help="one or more hardware IDs, e.g. H3")
    parser.add_argument("--n-seeds", type=int, default=DEFAULT_SEEDS, help="number of generated seeds")
    parser.add_argument("--seeds", help="comma-separated explicit seed list")
    parser.add_argument("--n-events", type=int, default=DEFAULT_EVENTS, help="events per seed")
    parser.add_argument("--geant4-prefix", default=DEFAULT_GEANT4_PREFIX, help="Geant4 installation prefix")
    parser.add_argument("--source-dir", type=Path, default=Path("."), help="repo root for builds and sbatch cd")
    parser.add_argument("--build-root", type=Path, default=Path("benchmarks/builds"), help="build output root")
    parser.add_argument("--script-dir", type=Path, default=Path("benchmarks/sbatch"), help="sbatch script directory")
    parser.add_argument("--vanilla-binary", type=Path, help="prebuilt vanilla benchmark binary")
    parser.add_argument("--optimized-binary", type=Path, help="prebuilt optimized benchmark binary")
    parser.add_argument("--results-path", type=Path, default=Path("benchmarks/results/results.parquet"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the benchmark-harness CLI."""

    parser = build_parser()
    args = parser.parse_args(argv)
    if args.generate_reference:
        parser.exit(
            2,
            "reference generation is deferred to implementation task 7; "
            "--generate-reference is fail-closed until benchmarks/reference/ "
            "and MANIFEST.sha256 support land\n",
        )
    if args.collect:
        return _collect(args, parser)

    _require(args.opt_id, "--opt-id is required", parser)
    _require(args.workload, "--workload is required", parser)
    _require(args.physics_list, "--physics-list is required", parser)
    _require(args.hw, "--hw is required", parser)
    seeds = _parse_seeds(args.seeds, args.n_seeds, parser)

    scripts_or_submit_outputs: list[str] = []
    for workload, physics_list, hw_id in itertools.product(args.workload, args.physics_list, args.hw):
        request = _request_for(args, workload, physics_list, hw_id, seeds)
        if args.submit:
            script_path = _script_path(args.script_dir, args.opt_id, workload, physics_list, hw_id)
            write_sbatch(request, script_path)
            scripts_or_submit_outputs.append(submit_sbatch(script_path, submit=True))
        else:
            scripts_or_submit_outputs.append(render_sbatch(request))
    sys.stdout.write(_join_outputs(scripts_or_submit_outputs))
    return 0


def _request_for(args: argparse.Namespace, workload: str, physics_list: str, hw_id: str, seeds: list[int]) -> RunRequest:
    vanilla_binary, optimized_binary = _binary_paths(args, workload, hw_id)
    return RunRequest(
        opt_id=args.opt_id,
        workload=workload,
        physics_list=physics_list,
        hw_id=hw_id,
        seeds=seeds,
        vanilla_binary=vanilla_binary,
        optimized_binary=optimized_binary,
        repo_root=args.source_dir,
        n_events=args.n_events,
    )


def _binary_paths(args: argparse.Namespace, workload: str, hw_id: str) -> tuple[Path, Path]:
    if args.build:
        vanilla_build = build_vanilla(
            args.geant4_prefix,
            workload,
            args.build_root,
            source_dir=args.source_dir,
            opt_id="vanilla",
            hw_id=hw_id,
        )
        optimized_build = build_optimized(
            args.geant4_prefix,
            args.opt_branch,
            args.opt_cmake_flags,
            workload,
            args.build_root,
            source_dir=args.source_dir,
            opt_id=args.opt_id,
            hw_id=hw_id,
        )
        return _default_binary(vanilla_build, workload), _default_binary(optimized_build, workload)
    vanilla = args.vanilla_binary or _default_binary(args.build_root / "vanilla" / workload, workload)
    optimized = args.optimized_binary or _default_binary(args.build_root / args.opt_id / workload, workload)
    return Path(vanilla), Path(optimized)


def _collect(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    """Validate collect-mode arguments and fail closed until parsers land."""

    _require(args.opt_id, "--opt-id is required for --collect", parser)
    _require(args.workload and len(args.workload) == 1, "--collect requires exactly one --workload", parser)
    _require(args.physics_list and len(args.physics_list) == 1, "--collect requires exactly one --physics-list", parser)
    _require(args.hw and len(args.hw) == 1, "--collect requires exactly one --hw", parser)
    _parse_seeds(args.seeds, args.n_seeds, parser)
    schema_cols = ", ".join(RESULT_SCHEMA.names)
    parser.exit(2, f"collect mode is fail-closed until raw-output parsing lands; schema={schema_cols}\n")


def _parse_seeds(seed_text: str | None, n_seeds: int, parser: argparse.ArgumentParser) -> list[int]:
    if seed_text:
        try:
            seeds = [int(part) for part in seed_text.split(",") if part]
        except ValueError:
            parser.error("--seeds must be a comma-separated list of integers")
        _require(seeds, "--seeds must not be empty", parser)
        _require(all(seed >= 0 for seed in seeds), "--seeds values must be non-negative", parser)
        return seeds
    _require(n_seeds > 0, "--n-seeds must be positive", parser)
    return list(range(1, n_seeds + 1))


def _default_binary(build_dir: Path, workload: str) -> Path:
    return build_dir / "bin" / workload


def _script_path(script_dir: Path, opt_id: str, workload: str, physics_list: str, hw_id: str) -> Path:
    return script_dir / f"{_slug(opt_id)}_{_slug(workload)}_{_slug(physics_list)}_{_slug(hw_id)}.sbatch"


def _slug(value: str) -> str:
    return "".join(char if char.isalnum() or char in "-_" else "-" for char in value)


def _join_outputs(outputs: Iterable[str]) -> str:
    text = "\n\n# --- next benchmark request ---\n\n".join(output.rstrip() for output in outputs)
    return text + ("\n" if text else "")


def _require(condition: object, message: str, parser: argparse.ArgumentParser) -> None:
    if not condition:
        parser.error(message)


if __name__ == "__main__":
    raise SystemExit(main())

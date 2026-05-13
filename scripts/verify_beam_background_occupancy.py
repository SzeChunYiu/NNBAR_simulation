#!/usr/bin/env python3
"""Fail-closed gate for Appendix A beam-background occupancy readiness.

The verifier is intentionally read-only. It checks that the source, geometry,
physics-list, SLURM/macro, registry, and normalization surfaces needed by
`docs/reports/beam_background_tpc_occupancy.md` exist before Appendix A TPC
occupancy numbers can be treated as reproduced.
"""

from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path


DEFAULT_APPENDIX = Path(
    "/Volumes/MyDrive/nnbar/phd thesis/thesis_extracted/12_Appendix_1.tex"
)


@dataclass(frozen=True)
class ValidationItem:
    name: str
    ok: bool
    detail: str


@dataclass(frozen=True)
class ValidationReport:
    items: tuple[ValidationItem, ...]

    @property
    def blockers(self) -> list[ValidationItem]:
        return [item for item in self.items if not item.ok]

    @property
    def ok(self) -> bool:
        return not self.blockers

    def format(self) -> str:
        lines = []
        for item in self.items:
            status = "PASS" if item.ok else "BLOCK"
            lines.append(f"[{status}] {item.name}: {item.detail}")
        return "\n".join(lines)


def _read(path: Path) -> str:
    return path.read_text(errors="replace")


def _path_item(name: str, path: Path, kind: str = "file") -> ValidationItem:
    exists = path.is_dir() if kind == "dir" else path.is_file()
    detail = str(path) if exists else f"missing: {path}"
    return ValidationItem(name, exists, detail)


def _appendix_constants(appendix_path: Path) -> ValidationItem:
    if not appendix_path.is_file():
        return ValidationItem(
            "appendix_a_constants",
            False,
            "cannot parse constants because Appendix A source is missing",
        )
    text = _read(appendix_path)
    checks = {
        "Config. 1/no-coating label": lambda s: "Configuration 1" in s or "Config. 1" in s,
        "B4C absorber/coating label": lambda s: "B4C" in s or "B$_4$C" in s,
        "6LiF absorber/coating label": lambda s: "6LiF" in s or "LiF" in s,
        "Cd absorber label": lambda s: "Cd" in s or "cadmium" in s,
        "Table 3 default-B4C photon rate": lambda s: bool(
            re.search(r"2\.6\s*(?:e|\s*\\times\s*10\^\{?)11", s)
        ),
        "Table 3 6LiF photon rate": lambda s: bool(
            re.search(r"7\.6\s*(?:e|\s*\\times\s*10\^\{?)8", s)
        ),
        "Table 4 per-50-ns intensity basis": lambda s: "50 ns" in s or "50ns" in s,
        "TPC drift-frame occupancy scale": lambda s: "25 micro" in s
        or ("25" in s and "\\mu" in s),
        "ESS pulse spacing": lambda s: "0.071" in s,
    }
    missing = [label for label, check in checks.items() if not check(text)]
    if missing:
        return ValidationItem("appendix_a_constants", False, ", ".join(missing))
    return ValidationItem("appendix_a_constants", True, "Appendix A labels found")


def _absorber_selector(beampipe_path: Path) -> ValidationItem:
    if not beampipe_path.is_file():
        return ValidationItem(
            "absorber_selector",
            False,
            "cannot inspect absorber selector because beampipe source is missing",
        )
    text = _read(beampipe_path)
    has_alternatives = all(token in text for token in ("B4C", "6LiF", "Cd"))
    has_selector = any(token in text for token in ("SelectAbsorber", "absorber", "Config"))
    hardcoded_b4c = "B4CMaterial" in text and "G4LogicalVolume" in text
    if has_alternatives and has_selector and not hardcoded_b4c:
        return ValidationItem(
            "absorber_selector",
            True,
            "absorber alternatives appear selectable in source",
        )
    reason = "B4C-only coating/beam-stop use remains hard-coded"
    if not has_alternatives:
        reason = "Appendix A absorber alternatives are not all present"
    elif not has_selector:
        reason = "no runtime/build-time absorber selector token found"
    return ValidationItem("absorber_selector", False, reason)


def _hp_physics_registration(physics_path: Path) -> ValidationItem:
    if not physics_path.is_file():
        return ValidationItem(
            "hp_physics_registration",
            False,
            "cannot inspect HP registration because physics-list source is missing",
        )
    text = _read(physics_path)
    hp_registered = "RegisterPhysics(new G4HadronPhysicsFTFP_BERT_HP" in text
    if hp_registered:
        return ValidationItem(
            "hp_physics_registration",
            True,
            "G4HadronPhysicsFTFP_BERT_HP is registered",
        )
    if "G4HadronPhysicsFTFP_BERT_HP" in text:
        detail = "HP header/reference exists, but registered constructor is non-HP"
    else:
        detail = "no FTFP_BERT_HP registration found"
    return ValidationItem("hp_physics_registration", False, detail)


def _beam_neutron_registry(root: Path) -> ValidationItem:
    registry = root / "data/registry"
    manifests = sorted(registry.glob("beam_neutron_hibeam_*_v1/manifest.*"))
    if not manifests:
        return ValidationItem(
            "beam_neutron_registry",
            False,
            f"missing beam_neutron_hibeam_*_v1 manifest under {registry}",
        )
    required = ("command", "output", "normalization", "physics_list")
    for manifest in manifests:
        text = _read(manifest)
        missing = [key for key in required if key not in text]
        if not missing:
            return ValidationItem(
                "beam_neutron_registry",
                True,
                f"manifest has command/output/normalization metadata: {manifest}",
            )
    return ValidationItem(
        "beam_neutron_registry",
        False,
        f"manifest(s) missing required metadata keys: {', '.join(required)}",
    )


def validate(repo_root: Path | str = Path("."), appendix_path: Path | str | None = None) -> ValidationReport:
    root = Path(repo_root)
    appendix = Path(
        appendix_path
        or os.environ.get("NNBAR_APPENDIX_A_TEX", "")
        or DEFAULT_APPENDIX
    )
    beampipe = root / "NNBAR_Detector/src/detector/beampipe_geometry.cc"
    physics = root / "NNBAR_Detector/src/core/PhysicsList.cc"
    slurm = root / "NNBAR_Detector/slurm"
    items = [
        _path_item("appendix_a_source", appendix),
        _path_item("beampipe_geometry_source", beampipe),
        _path_item("physics_list_source", physics),
        _path_item("macro_slurm_tree", slurm, kind="dir"),
        _appendix_constants(appendix),
        _absorber_selector(beampipe),
        _hp_physics_registration(physics),
        _beam_neutron_registry(root),
    ]
    return ValidationReport(tuple(items))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--appendix", type=Path, default=None)
    args = parser.parse_args()
    report = validate(args.repo_root, args.appendix)
    print(report.format())
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

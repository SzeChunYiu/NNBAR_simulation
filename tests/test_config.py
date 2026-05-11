from pathlib import Path

import pytest

from nnbar_reconstruction.utils import config as config_module


@pytest.fixture(autouse=True)
def clear_config_cache():
    config_module._config_cache = None
    config_module._config_path = None
    yield
    config_module._config_cache = None
    config_module._config_path = None


def test_default_config_discovery_finds_packaged_geometry_config():
    expected = (
        Path(config_module.__file__).resolve().parents[1]
        / "config"
        / "nnbar_geometry.yaml"
    )

    default_path = config_module.get_default_config_path()

    assert default_path.resolve() == expected
    assert default_path.exists()

    cfg = config_module.load_config(force_reload=True)
    assert cfg["physics"]["pi0_mass"] == pytest.approx(134.977)
    assert cfg["tpc"]["n_layers"] == 20


def test_load_config_accepts_explicit_config_path(tmp_path):
    custom_config = tmp_path / "custom_geometry.yaml"
    custom_config.write_text(
        "physics:\n"
        "  pi0_mass: 135.0\n"
        "custom_section:\n"
        "  value: 42\n"
    )

    cfg = config_module.load_config(custom_config, force_reload=True)

    assert cfg["physics"]["pi0_mass"] == 135.0
    assert cfg["custom_section"]["value"] == 42


def test_load_config_missing_explicit_path_raises_file_not_found(tmp_path):
    missing_config = tmp_path / "missing.yaml"

    with pytest.raises(FileNotFoundError, match="Configuration file not found"):
        config_module.load_config(missing_config, force_reload=True)


def test_default_config_discovery_ignores_machine_specific_absolute_fallbacks(monkeypatch):
    package_default = (
        Path(config_module.__file__).resolve().parents[1]
        / "config"
        / "nnbar_geometry.yaml"
    )
    machine_specific_fallback = Path(
        "/home/billy/nnbar/simulation/nnbar_reconstruction/config/nnbar_geometry.yaml"
    )

    def fake_exists(path):
        return path == machine_specific_fallback

    monkeypatch.setattr(Path, "exists", fake_exists)

    default_path = config_module.get_default_config_path()

    assert default_path == package_default
    assert "/home/billy/" not in str(default_path)

"""
Configuration loader for NNBAR reconstruction.

Loads the shared YAML configuration file used by both C++ simulation
and Python reconstruction code.

Usage:
    from nnbar_reconstruction.utils import load_config, get_config

    # Load full config
    cfg = load_config()

    # Access parameters
    tpc_layers = cfg['tpc']['n_layers']

    # Or use get_config for nested access
    tpc_layers = get_config('tpc.n_layers')
"""

from pathlib import Path
from typing import Any, Dict, Optional, Union

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    print("[WARNING] PyYAML not installed. Install with: pip install pyyaml")

# Cache for loaded config
_config_cache: Optional[Dict[str, Any]] = None
_config_path: Optional[Path] = None


def _default_config_candidates() -> tuple[Path, ...]:
    """Return repo/package-relative default configuration candidates."""
    # __file__ is utils/config.py, so parent.parent is nnbar_reconstruction/.
    nnbar_recon_dir = Path(__file__).resolve().parent.parent

    return (
        nnbar_recon_dir / "config" / "nnbar_geometry.yaml",
        nnbar_recon_dir.parent / "config" / "nnbar_geometry.yaml",
    )


def get_default_config_path() -> Path:
    """Get the default path to the configuration file.

    Discovery is intentionally limited to paths relative to this package and
    checkout; machine-specific absolute fallbacks make the loader non-portable.
    """
    possible_paths = _default_config_candidates()

    for path in possible_paths:
        if path.exists():
            return path

    # Return the expected packaged path even if it doesn't exist, so callers get
    # a deterministic FileNotFoundError from load_config().
    return possible_paths[0]


def load_config(config_path: Optional[Union[str, Path]] = None, force_reload: bool = False) -> Dict[str, Any]:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config file. If None, uses default location.
        force_reload: If True, reload even if already cached.

    Returns:
        Configuration dictionary.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        ImportError: If PyYAML is not installed.
    """
    global _config_cache, _config_path

    if not HAS_YAML:
        raise ImportError("PyYAML is required. Install with: pip install pyyaml")

    # Use cached config if available
    if _config_cache is not None and not force_reload:
        if config_path is None or Path(config_path) == _config_path:
            return _config_cache

    # Determine config path
    if config_path is None:
        config_path = get_default_config_path()
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    # Load YAML
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Cache the result
    _config_cache = config
    _config_path = config_path

    return config


def get_config(key: str, default: Any = None, config: Optional[Dict] = None) -> Any:
    """
    Get a configuration value using dot notation.

    Args:
        key: Dot-separated key path (e.g., 'tpc.n_layers', 'physics.c_light')
        default: Default value if key not found.
        config: Optional config dict. If None, loads from file.

    Returns:
        Configuration value.

    Examples:
        >>> get_config('tpc.n_layers')
        20
        >>> get_config('physics.pion_mass')
        139.570
        >>> get_config('nonexistent.key', default=0)
        0
    """
    if config is None:
        config = load_config()

    keys = key.split('.')
    value = config

    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default

    return value


def get_physics_constants() -> Dict[str, float]:
    """Get physics constants from config."""
    cfg = load_config()
    return cfg.get('physics', {})


def get_detector_geometry(detector: str) -> Dict[str, Any]:
    """
    Get geometry parameters for a specific detector.

    Args:
        detector: One of 'tpc', 'scintillator', 'calorimeter', 'beampipe', 'target'

    Returns:
        Dictionary of geometry parameters.
    """
    cfg = load_config()
    return cfg.get(detector, {})


def get_reconstruction_params() -> Dict[str, Any]:
    """Get reconstruction parameters."""
    cfg = load_config()
    return cfg.get('reconstruction', {})


def get_clustering_params() -> Dict[str, Any]:
    """Get clustering parameters."""
    cfg = load_config()
    return cfg.get('clustering', {})


def get_tracking_params() -> Dict[str, Any]:
    """Get tracking parameters."""
    cfg = load_config()
    return cfg.get('tracking', {})


def get_particle_id_params() -> Dict[str, Any]:
    """Get particle identification parameters."""
    cfg = load_config()
    return cfg.get('particle_id', {})


def get_event_selection_params() -> Dict[str, Any]:
    """Get event selection parameters."""
    cfg = load_config()
    return cfg.get('event_selection', {})


def get_training_params() -> Dict[str, Any]:
    """Get ML training parameters."""
    cfg = load_config()
    return cfg.get('training', {})


# Convenience functions for common physics calculations
def pion_velocity(kinetic_energy: float) -> float:
    """
    Calculate pion velocity given kinetic energy.

    Args:
        kinetic_energy: Kinetic energy in MeV

    Returns:
        Velocity in cm/ns
    """
    cfg = load_config()
    m = cfg['physics']['pion_mass']
    c = cfg['physics']['c_light']

    total_energy = kinetic_energy + m
    gamma = total_energy / m
    beta = (1 - 1 / gamma**2)**0.5

    return beta * c


def proton_velocity(kinetic_energy: float) -> float:
    """Calculate proton velocity given kinetic energy."""
    cfg = load_config()
    m = cfg['physics']['proton_mass']
    c = cfg['physics']['c_light']

    total_energy = kinetic_energy + m
    gamma = total_energy / m
    beta = (1 - 1 / gamma**2)**0.5

    return beta * c


def photon_travel_time(distance: float) -> float:
    """Calculate photon travel time for a given distance."""
    cfg = load_config()
    c = cfg['physics']['c_light']
    return distance / c


if __name__ == "__main__":
    # Test configuration loading
    try:
        cfg = load_config()
        print("Configuration loaded successfully!")
        print(f"TPC layers: {get_config('tpc.n_layers')}")
        print(f"Pion mass: {get_config('physics.pion_mass')} MeV")
        print(f"Target z: {get_config('target.z_position')} cm")
    except Exception as e:
        print(f"Error: {e}")

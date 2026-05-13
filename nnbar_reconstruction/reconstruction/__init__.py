"""
Event Reconstruction Module

Implements the full reconstruction chain:
- Event preselection (rolling time window)
- Timing windows for calorimeter acceptance
- Charged object reconstruction
- Neutral object reconstruction
- Particle identification
"""

from .event_preselection import (
    rolling_time_window_trigger,
    find_event_time,
)
from .timing_window import (
    scintillator_timing_window,
    leadglass_timing_window,
    apply_timing_cuts,
)
from .charged_reconstruction import (
    reconstruct_charged_objects,
    ChargedObject,
)
from .neutral_reconstruction import (
    reconstruct_neutral_objects,
    NeutralObject,
)
from .object_identification import (
    identify_particle_type,
    identify_pion_proton,
    identify_neutral_pion,
)

__all__ = [
    "rolling_time_window_trigger",
    "find_event_time",
    "scintillator_timing_window",
    "leadglass_timing_window",
    "apply_timing_cuts",
    "reconstruct_charged_objects",
    "ChargedObject",
    "reconstruct_neutral_objects",
    "NeutralObject",
    "identify_particle_type",
    "identify_pion_proton",
    "identify_neutral_pion",
]

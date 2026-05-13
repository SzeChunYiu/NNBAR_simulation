"""Direct tests for event particle-count helpers."""

from __future__ import annotations

from types import SimpleNamespace

from nnbar_reconstruction.analysis.event_particle_counts import count_particles


def _charged(particle_type: str) -> SimpleNamespace:
    return SimpleNamespace(particle_type=particle_type)


def _neutral(is_pi0_candidate: bool) -> SimpleNamespace:
    return SimpleNamespace(is_pi0_candidate=is_pi0_candidate)


def test_count_particles_tallies_charged_and_neutral_species():
    counts = count_particles(
        charged_objects=[
            _charged("PION_PLUS"),
            _charged("PION_MINUS"),
            _charged("PROTON"),
            _charged("ELECTRON_PAIR_MEMBER"),
        ],
        neutral_objects=[
            _neutral(is_pi0_candidate=True),
            _neutral(is_pi0_candidate=False),
            _neutral(is_pi0_candidate=False),
        ],
    )

    assert counts == {
        "charged": 4,
        "neutral": 3,
        "pions": 3,
        "protons": 1,
        "photons": 2,
        "pi0": 1,
    }


def test_count_particles_counts_pi0_candidates_as_pion_multiplicity():
    counts = count_particles(
        charged_objects=[_charged("PION_PLUS")],
        neutral_objects=[_neutral(is_pi0_candidate=True)],
    )

    assert counts["pi0"] == 1
    assert counts["photons"] == 0
    assert counts["pions"] == 2

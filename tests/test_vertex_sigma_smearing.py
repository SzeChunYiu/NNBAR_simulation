import math

import numpy as np

from nnbar_reconstruction.tracking.track_fitting import Track
from nnbar_reconstruction.vertex.classical_vertex import (
    theta_binned_projected_sigma_cm,
    weighted_vertex_reconstruction,
)


def _track(theta_deg, projection=(0.0, 0.0, 0.0), track_id=0):
    theta = math.radians(theta_deg)
    direction = np.array([math.sin(theta), 0.0, math.cos(theta)])
    return Track(
        track_id=track_id,
        center=np.array([50.0, 0.0, 25.0]),
        direction=direction,
        head=np.array([50.0, 0.0, 25.0]),
        tail=np.array([100.0, 0.0, 50.0]),
        length=60.0,
        n_hits=20,
        rms_residual=0.3,
        linearity=0.99,
        hit_indices=np.arange(4),
        vertex_projection=np.array(projection, dtype=float),
        is_signal=True,
    )


def test_theta_binned_sigma_uses_20_degree_boundaries_and_180_endpoint():
    sigma_by_bin = [float(i + 1) for i in range(9)]

    assert theta_binned_projected_sigma_cm(_track(0.0), sigma_by_bin) == 1.0
    assert theta_binned_projected_sigma_cm(_track(19.999), sigma_by_bin) == 1.0
    assert theta_binned_projected_sigma_cm(_track(20.0), sigma_by_bin) == 2.0
    assert theta_binned_projected_sigma_cm(_track(179.999), sigma_by_bin) == 9.0
    assert theta_binned_projected_sigma_cm(_track(180.0), sigma_by_bin) == 9.0


def test_theta_sigma_table_weights_are_inverse_projected_sigma_squared():
    tracks = [
        _track(10.0, projection=(0.0, 0.0, 0.0), track_id=1),
        _track(30.0, projection=(10.0, 0.0, 0.0), track_id=2),
        _track(50.0, projection=(20.0, 0.0, 0.0), track_id=3),
    ]
    sigma_by_bin = [1.0, 2.0, 4.0, 8.0, 16.0, 16.0, 8.0, 4.0, 2.0]

    result = weighted_vertex_reconstruction(
        tracks,
        weight_by_r_head=False,
        theta_sigma_table_cm=sigma_by_bin,
    )

    raw = np.array([1.0 / 1.0**2, 1.0 / 2.0**2, 1.0 / 4.0**2])
    expected_weights = raw / raw.sum()
    np.testing.assert_allclose(result.track_weights, expected_weights)
    np.testing.assert_allclose(result.position, np.sum(result.track_projections * expected_weights[:, None], axis=0))


def test_single_track_table_uncertainty_stays_in_centimeters_not_radians():
    result = weighted_vertex_reconstruction(
        [_track(30.0, projection=(3.0, 4.0, 0.0))],
        weight_by_r_head=False,
        theta_sigma_table_cm=[1.0, 2.5, 4.0, 8.0, 16.0, 16.0, 8.0, 4.0, 2.0],
    )

    assert result.is_valid
    np.testing.assert_allclose(result.position, [3.0, 4.0, 0.0])
    np.testing.assert_allclose(result.uncertainty, [2.5, 2.5, 0.0])


def test_empirical_fallback_still_works_without_theta_sigma_table():
    result = weighted_vertex_reconstruction(
        [
            _track(30.0, projection=(0.0, 0.0, 0.0), track_id=1),
            _track(60.0, projection=(10.0, 0.0, 0.0), track_id=2),
        ],
        weight_by_r_head=False,
    )

    assert result.is_valid
    assert result.n_tracks == 2
    assert np.isclose(result.track_weights.sum(), 1.0)
    assert np.all(result.track_weights > 0.0)


def test_seeded_projected_smearing_closure_matches_injected_sigma_pull():
    """Toy closure for Ch.7 sigma(theta)=d0bar projected-position weights.

    The table is deliberately synthetic: it validates the weighting contract
    without digitizing thesis plot values.  The 0.20 pull-width tolerance covers
    finite-toy fluctuations, not detector-resolution systematics.
    """

    rng = np.random.default_rng(7307)
    true_vertex = np.array([12.0, -7.0, 0.0])
    theta_degs = [10.0, 35.0, 75.0, 115.0, 155.0]
    sigma_by_bin = [1.2, 2.0, 3.0, 4.5, 6.0, 4.5, 3.0, 2.0, 1.2]
    sigmas = np.array([
        theta_binned_projected_sigma_cm(_track(theta), sigma_by_bin)
        for theta in theta_degs
    ])
    expected_estimator_sigma = math.sqrt(1.0 / np.sum(1.0 / sigmas**2))

    residuals = []
    for event_id in range(320):
        tracks = []
        for track_offset, (theta, sigma) in enumerate(zip(theta_degs, sigmas)):
            smear_xy = rng.normal(loc=0.0, scale=sigma, size=2)
            projection = true_vertex + np.array([smear_xy[0], smear_xy[1], 0.0])
            tracks.append(
                _track(
                    theta,
                    projection=projection,
                    track_id=event_id * len(theta_degs) + track_offset,
                )
            )

        result = weighted_vertex_reconstruction(
            tracks,
            weight_by_r_head=False,
            theta_sigma_table_cm=sigma_by_bin,
        )

        assert result.is_valid
        residuals.append(result.position[:2] - true_vertex[:2])

    pulls = np.asarray(residuals) / expected_estimator_sigma

    np.testing.assert_allclose(np.mean(pulls, axis=0), [0.0, 0.0], atol=0.15)
    np.testing.assert_allclose(
        np.sqrt(np.mean(pulls**2, axis=0)),
        [1.0, 1.0],
        atol=0.20,
    )

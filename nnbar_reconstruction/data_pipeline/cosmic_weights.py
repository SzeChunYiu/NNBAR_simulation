"""Cosmic-ray background weights from thesis Eq. 6.1.

The table entries are the expected three-year particle counts at the passive
shielding surface from thesis Table 6.1.  ``get_weight`` applies

    w_ij = (N_ij / S_ij) * (N_ij / sum_i N_ij)

with ``S_ij = 1_000_000`` simulated events per energy-bin/particle sample.
"""

from __future__ import annotations

PARTICLES = ["mu-", "gamma", "e-", "neutron", "proton"]
S = 1_000_000

N_IJ: dict[tuple[int, int], float] = {
    (0, 0): 1.69e11,
    (0, 1): 2.30e12,
    (0, 2): 4.02e11,
    (0, 3): 4.33e11,
    (0, 4): 2.04e10,
    (1, 0): 1.90e11,
    (1, 1): 1.09e10,
    (1, 2): 1.05e10,
    (1, 3): 1.23e10,
    (1, 4): 4.34e9,
    (2, 0): 7.69e11,
    (2, 1): 6.21e9,
    (2, 2): 5.63e9,
    (2, 3): 6.03e9,
    (2, 4): 3.24e9,
    (3, 0): 2.68e11,
    (3, 1): 7.23e8,
    (3, 2): 2.24e8,
    (3, 3): 1.28e8,
    (3, 4): 1.44e8,
    (4, 0): 2.18e11,
    (4, 1): 2.30e7,
    (4, 2): 0.0,
    (4, 3): 5.92e7,
    (4, 4): 8.37e7,
    (5, 0): 2.00e11,
    (5, 1): 0.0,
    (5, 2): 0.0,
    (5, 3): 6.25e6,
    (5, 4): 5.00e6,
}


def get_weight(ebin: int, particle_idx: int) -> float:
    """Compute ``w_{i,j}`` from thesis Eq. 6.1."""
    n_ij = N_IJ.get((ebin, particle_idx), 0.0)
    if n_ij == 0.0:
        return 0.0

    sum_i_n_ij = sum(N_IJ.get((i, particle_idx), 0.0) for i in range(6))
    if sum_i_n_ij == 0.0:
        return 0.0

    return (n_ij / S) * (n_ij / sum_i_n_ij)

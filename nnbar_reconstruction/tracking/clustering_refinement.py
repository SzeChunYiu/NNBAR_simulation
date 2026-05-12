"""Refinement strategies for TPC hit clustering."""

import numpy as np

from .clustering_backends import (
    CuMLKMeans,
    SklearnKMeans,
    get_backend,
    use_gpu_clustering,
)

def split_by_z_gap(
    points: np.ndarray,
    labels: np.ndarray,
    gap_threshold: float = 6.0,
) -> np.ndarray:
    """
    Split clusters that have large gaps in z.

    Args:
        points: Original (x, y, z) points.
        labels: Current cluster labels.
        gap_threshold: Minimum gap in cm to trigger split.

    Returns:
        Updated labels.
    """
    new_labels = labels.copy()
    max_label = labels.max()

    unique_clusters = set(labels) - {-1}

    for cluster_id in unique_clusters:
        mask = labels == cluster_id
        cluster_z = points[mask, 2]

        if len(cluster_z) < 4:
            continue

        # Sort by z and find gaps
        sorted_idx = np.argsort(cluster_z)
        sorted_z = cluster_z[sorted_idx]

        gaps = np.diff(sorted_z)
        large_gaps = np.where(gaps > gap_threshold)[0]

        if len(large_gaps) > 0:
            # Split at largest gap
            split_idx = large_gaps[np.argmax(gaps[large_gaps])]

            # Update labels for second part
            cluster_indices = np.where(mask)[0]
            sorted_cluster_indices = cluster_indices[sorted_idx]

            max_label += 1
            new_labels[sorted_cluster_indices[split_idx + 1:]] = max_label

    return new_labels


def split_by_direction(
    points: np.ndarray,
    labels: np.ndarray,
    angle_threshold: float = 0.7,  # cos(45 deg)
) -> np.ndarray:
    """
    Split clusters with inconsistent track directions.

    Uses PCA to detect multiple directions within a cluster.

    Args:
        points: Original (x, y, z) points.
        labels: Current cluster labels.
        angle_threshold: Cosine of maximum angle between sub-tracks.

    Returns:
        Updated labels.
    """
    from .track_fitting import pca_line_fit

    new_labels = labels.copy()
    max_label = labels.max()

    unique_clusters = set(labels) - {-1}

    for cluster_id in unique_clusters:
        mask = labels == cluster_id
        cluster_points = points[mask]

        if len(cluster_points) < 6:
            continue

        # Split cluster in half by z and compute directions
        sorted_idx = np.argsort(cluster_points[:, 2])
        mid = len(sorted_idx) // 2

        if mid < 3 or (len(sorted_idx) - mid) < 3:
            continue

        first_half = cluster_points[sorted_idx[:mid]]
        second_half = cluster_points[sorted_idx[mid:]]

        try:
            fit1 = pca_line_fit(first_half)
            fit2 = pca_line_fit(second_half)

            # Check angle between directions
            cos_angle = abs(np.dot(fit1['direction'], fit2['direction']))

            if cos_angle < angle_threshold:
                # Directions are too different - split
                cluster_indices = np.where(mask)[0]
                sorted_cluster_indices = cluster_indices[sorted_idx]

                max_label += 1
                new_labels[sorted_cluster_indices[mid:]] = max_label
        except:
            continue

    return new_labels


def split_by_radial_clustering(
    points: np.ndarray,
    labels: np.ndarray,
    r: np.ndarray,
    n_clusters: int = 2,
) -> np.ndarray:
    """
    Split clusters using KMeans on (r, z) residuals from linear fit.

    Helps separate parallel tracks at different radial positions.

    Args:
        points: Original (x, y, z) points.
        labels: Current cluster labels.
        r: Radial coordinates.
        n_clusters: Number of sub-clusters to attempt.

    Returns:
        Updated labels.
    """
    new_labels = labels.copy()
    max_label = labels.max()

    unique_clusters = set(labels) - {-1}

    for cluster_id in unique_clusters:
        mask = labels == cluster_id
        cluster_points = points[mask]
        cluster_r = r[mask]

        if len(cluster_points) < 2 * n_clusters * 3:
            continue

        # Fit linear model in z
        z = cluster_points[:, 2]
        z_mean = z.mean()
        z_std = z.std()
        if z_std < 0.1:
            continue

        # Residuals from linear fit in r vs z
        A = np.column_stack([z, np.ones(len(z))])
        try:
            coeffs, _, _, _ = np.linalg.lstsq(A, cluster_r, rcond=None)
            r_predicted = A @ coeffs
            residuals = cluster_r - r_predicted
        except:
            continue

        # KMeans on (r, residuals)
        features = np.column_stack([cluster_r, residuals])
        try:
            gpu = get_backend()
            if use_gpu_clustering():
                # GPU path using cuML KMeans
                features_gpu = gpu.to_gpu(features.astype(np.float32))
                km = CuMLKMeans(n_clusters=n_clusters, n_init=10, random_state=42)
                sub_labels = km.fit_predict(features_gpu)
                sub_labels = gpu.to_numpy(sub_labels)
            else:
                km = SklearnKMeans(n_clusters=n_clusters, n_init=10, random_state=42)
                sub_labels = km.fit_predict(features)

            # Check if split is meaningful (balanced sizes)
            sizes = [np.sum(sub_labels == i) for i in range(n_clusters)]
            if min(sizes) < 3:
                continue

            # Apply split
            cluster_indices = np.where(mask)[0]
            for i in range(1, n_clusters):
                max_label += 1
                new_labels[cluster_indices[sub_labels == i]] = max_label
        except:
            continue

    return new_labels


def merge_collinear_fragments(
    points: np.ndarray,
    labels: np.ndarray,
    angle_threshold: float = 0.99,
    gap_threshold: float = 5.0,
    min_fragment_size: int = 3,
) -> np.ndarray:
    """
    Merge small collinear cluster fragments.

    Args:
        points: Original (x, y, z) points.
        labels: Current cluster labels.
        angle_threshold: Cosine threshold for collinearity.
        gap_threshold: Maximum gap in cm for merging.
        min_fragment_size: Maximum size of fragment to consider merging.

    Returns:
        Updated labels.
    """
    from .track_fitting import pca_line_fit

    new_labels = labels.copy()
    unique_clusters = list(set(labels) - {-1})

    if len(unique_clusters) < 2:
        return new_labels

    # Compute track parameters for each cluster
    track_params = {}
    for cluster_id in unique_clusters:
        mask = labels == cluster_id
        cluster_points = points[mask]

        if len(cluster_points) < 3:
            continue

        try:
            fit = pca_line_fit(cluster_points)
            track_params[cluster_id] = {
                'center': fit['center'],
                'direction': fit['direction'],
                'head': fit['head'],
                'tail': fit['tail'],
                'size': len(cluster_points),
            }
        except:
            continue

    # Find mergeable pairs
    merged_to = {}  # Maps cluster to its merged parent

    for c1 in track_params:
        if track_params[c1]['size'] > min_fragment_size:
            continue

        best_match = None
        best_gap = float('inf')

        for c2 in track_params:
            if c1 == c2 or c1 in merged_to or c2 in merged_to:
                continue

            p1 = track_params[c1]
            p2 = track_params[c2]

            # Check collinearity
            cos_angle = abs(np.dot(p1['direction'], p2['direction']))
            if cos_angle < angle_threshold:
                continue

            # Check gap (minimum distance between endpoints)
            gaps = [
                np.linalg.norm(p1['head'] - p2['head']),
                np.linalg.norm(p1['head'] - p2['tail']),
                np.linalg.norm(p1['tail'] - p2['head']),
                np.linalg.norm(p1['tail'] - p2['tail']),
            ]
            min_gap = min(gaps)

            if min_gap < gap_threshold and min_gap < best_gap:
                best_match = c2
                best_gap = min_gap

        if best_match is not None:
            merged_to[c1] = best_match

    # Apply merges
    for fragment, parent in merged_to.items():
        new_labels[labels == fragment] = parent

    return new_labels


def split_clusters_by_perp_bimodality(
    points: np.ndarray,
    labels: np.ndarray,
    min_cluster_size: int = 8,
    weight_floor: float = 0.15,
    ashman_threshold: float = 2.0,
) -> np.ndarray:
    """
    Split clusters showing bimodal perpendicular distance (HIBEAM-inspired).

    This separates tracks that are parallel but offset perpendicular to
    the main cluster direction. Uses Ashman's D criterion to assess
    whether a bimodal split is meaningful.

    Args:
        points: Original (x, y, z) points.
        labels: Current cluster labels.
        min_cluster_size: Minimum cluster size to attempt splitting.
        weight_floor: Minimum fraction for sub-cluster (prevents false splits).
        ashman_threshold: Minimum Ashman D value for meaningful separation.

    Returns:
        Updated labels.
    """
    from .track_fitting import pca_line_fit

    new_labels = labels.copy()
    max_label = labels.max()
    unique_clusters = list(set(labels) - {-1})

    for cluster_id in unique_clusters:
        mask = labels == cluster_id
        cluster_points = points[mask]

        if len(cluster_points) < min_cluster_size:
            continue

        try:
            # Fit line to get direction
            fit = pca_line_fit(cluster_points, use_gpu=False)
            center = fit['center']
            direction = fit['direction']

            # Compute perpendicular distances to fitted line
            centered = cluster_points - center
            projections = np.dot(centered, direction)
            parallel_component = np.outer(projections, direction)
            perpendicular = centered - parallel_component
            perp_distances = np.linalg.norm(perpendicular, axis=1)

            # Check for bimodality using 1D K-means
            if use_gpu_clustering():
                gpu = get_backend()
                perp_gpu = gpu.to_gpu(perp_distances.reshape(-1, 1).astype(np.float32))
                km = CuMLKMeans(n_clusters=2, n_init=10, random_state=42)
                sub_labels = km.fit_predict(perp_gpu)
                sub_labels = gpu.to_numpy(sub_labels)
            else:
                km = SklearnKMeans(n_clusters=2, n_init=10, random_state=42)
                sub_labels = km.fit_predict(perp_distances.reshape(-1, 1))

            # Check cluster sizes
            sizes = [np.sum(sub_labels == i) for i in range(2)]
            min_frac = min(sizes) / len(cluster_points)

            if min_frac < weight_floor:
                continue

            # Compute Ashman D criterion for bimodality
            # D = |μ1 - μ2| / sqrt(2 * (σ1² + σ2²))
            perp_0 = perp_distances[sub_labels == 0]
            perp_1 = perp_distances[sub_labels == 1]

            mu_diff = abs(np.mean(perp_0) - np.mean(perp_1))
            var_sum = np.var(perp_0) + np.var(perp_1)

            if var_sum < 1e-10:
                continue

            ashman_d = mu_diff / np.sqrt(2 * var_sum)

            if ashman_d < ashman_threshold:
                continue

            # Apply split
            cluster_indices = np.where(mask)[0]
            max_label += 1
            new_labels[cluster_indices[sub_labels == 1]] = max_label

        except Exception:
            continue

    return new_labels


def refine_clusters(
    points: np.ndarray,
    labels: np.ndarray,
    r: np.ndarray,
    iterations: int = 3,
) -> np.ndarray:
    """
    Apply iterative refinement with multiple splitting strategies.

    Args:
        points: Original (x, y, z) points.
        labels: Initial cluster labels.
        r: Radial coordinates.
        iterations: Number of refinement passes.

    Returns:
        Refined labels.
    """
    current_labels = labels.copy()

    for _ in range(iterations):
        n_before = len(set(current_labels) - {-1})

        # Apply splitting strategies
        current_labels = split_by_z_gap(points, current_labels)
        current_labels = split_by_direction(points, current_labels)
        current_labels = split_by_radial_clustering(points, current_labels, r)

        # Merge fragments
        current_labels = merge_collinear_fragments(points, current_labels)

        n_after = len(set(current_labels) - {-1})

        # Stop if no change
        if n_after == n_before:
            break

    return current_labels

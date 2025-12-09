# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
"""
Module containing utility functions for GIF export such as size estimation and optimal frame
skip calculation to balance file size and angular resolution.
"""
from __future__ import annotations

import numpy as np

GIF_COMPRESSION_RATIO = 0.85  # Derived from LZW compression testing with flower dataset IMAT00010675
BYTES_PER_MB = 1048576


def estimate_gif_size(frame_count: int, image_height: int, image_width: int) -> float:
    """
    Roughly estimate compressed GIF file size in MB.

    Tries to empirically derive compression ratio from GIF LZW compression
    testing with flower imagestack IMAT00010675 (~0.85f).

    Duration is excluded from estimation as it has negligible effect on file size.

    :param frame_count: Number of frames in the GIF
    :param image_height: Height of each frame in pixels
    :param image_width: Width of each frame in pixels
    :return: Estimated file size in MB
    """
    bytes_per_frame = image_height * image_width  # 1 byte per pixel (i.e. grayscale)
    return (frame_count * bytes_per_frame * GIF_COMPRESSION_RATIO) / BYTES_PER_MB


def _calculate_min_skip_for_angular_resolution(angle_count: int) -> int:
    """
    Calculate minimum frame skip to maintain  angular resolution, aiming for around 1 deg per frame.
    This is to help provide an estimate of how many frames are needed for a smooth animation.
    Stack is assumed to cover 360 degrees.

    :param angle_count: Number of unique angles (in degrees, assuming 360° total)
    :return: Minimum frame skip value
    """
    if angle_count <= 0:
        return 1
    degrees_per_frame = 360.0 / angle_count
    return max(1, int(np.ceil(degrees_per_frame)))


def _calculate_max_skip_for_file_size(projection_count: int,
                                      image_height: int,
                                      image_width: int,
                                      max_size_mb: float = 5.0) -> int:
    """
    Calculate maximum frame skip to stay within file size limit.

    :param projection_count: Total number of projections
    :param image_height: Height of each image frame
    :param image_width: Width of each image frame
    :param max_size_mb: Maximum GIF file size in MB (default 5.0)
    :return: Maximum frame skip value
    """
    bytes_per_frame = image_height * image_width
    max_size_bytes = max_size_mb * BYTES_PER_MB

    max_frames_for_size = max(1, int(max_size_bytes / (bytes_per_frame * GIF_COMPRESSION_RATIO)))
    return max(1, int(np.ceil(projection_count / max_frames_for_size)))


def _find_optimal_divisor(projection_count: int, target_skip_interval: int) -> int:
    """
    Find a ideal value for frame skip interval close to recommendation that divides evenly into projection_count.

    The aim of this method is to try and ensure smooth playback by avoiding remainder
    frames that don't evenly fit into projection_count
    e.g. if projection_count=100 and frame_skip=6, the last 4 frames would be skipped.

    :param projection_count: Total number of projections
    :param target_skip_interval: Recommended frame skip value
    :return: Optimal frame skip interval
    """
    for frame_skip_interval in [target_skip_interval, target_skip_interval + 1, target_skip_interval - 1]:
        if frame_skip_interval > 0 and projection_count % frame_skip_interval == 0:
            return frame_skip_interval
    return target_skip_interval


def calculate_optimal_frame_skip(projection_count: int,
                                 image_height: int,
                                 image_width: int,
                                 angle_count: int | None = None,
                                 max_size_mb: float = 5.0) -> int:
    """
    Calculate optimal frame skip (step size) for GIF export.

    Balances the following constraints:
    - Angular resolution (avoid skipping more than 1 frame per degree)
    - File size limit (default 5MB)

    :param projection_count: Total number of projections in the stack
    :param image_height: Height of each image frame (needed for size estimation)
    :param image_width: Width of each image frame (needed for size estimation)
    :param angle_count: Number of unique angles (if None, assumes num_projections = num_angles)
    :param max_size_mb: Maximum GIF file size in MB (default 5.0)
    :return: Recommended frame_skip value (step size)
    """
    if projection_count < 1:
        return 1

    if angle_count is None:
        angle_count = projection_count

    min_skip_for_resolution = _calculate_min_skip_for_angular_resolution(angle_count)
    max_skip_for_filesize = _calculate_max_skip_for_file_size(projection_count, image_height, image_width, max_size_mb)

    recommended_skip = max(min_skip_for_resolution, max_skip_for_filesize)
    return _find_optimal_divisor(projection_count, recommended_skip)

# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import numpy as np

from mantidimaging.core.data import ImageStack
from mantidimaging.core.utility.sensible_roi import SensibleROI


def get_bounding_box(stack: ImageStack) -> SensibleROI:
    edge_clip = 5
    data = stack.data[:, edge_clip:-edge_clip, edge_clip:-edge_clip]  # clip dark edges
    _, height, width = stack.shape
    buffer_pixels = width / 100 * 5
    all_col_mean = np.mean(data, axis=(1, 0))
    all_row_mean = np.mean(data, axis=(2, 0))
    all_col_mean_flipped = np.flip(all_col_mean)
    all_row_mean_flipped = np.flip(all_row_mean)

    def find_bound(data_temp: np.ndarray) -> int:
        data_temp = data_temp[0:round(len(data_temp) / 2)]
        data_diff = np.absolute(np.gradient(data_temp))
        noise_sigma = data_diff[:20].std()
        noise_mean = data_diff[:20].mean()

        for n in np.linspace(10, 2, 10, endpoint=True):
            tol = noise_mean + noise_sigma * n
            above_threshold_ind = np.where(data_diff > tol)[0]
            if not above_threshold_ind.size == 0:
                bound = above_threshold_ind[0]
                return bound - buffer_pixels if bound > buffer_pixels else 0
        return 0

    # add a buffer around the found bounds to make sure all the sample is captured in the bounding box
    top_bound = find_bound(all_row_mean) + edge_clip
    bottom_bound = find_bound(all_row_mean_flipped) + edge_clip
    left_bound = find_bound(all_col_mean) + edge_clip
    right_bound = find_bound(all_col_mean_flipped) + edge_clip

    return SensibleROI(int(left_bound), int(top_bound), int(width - right_bound), int(height - bottom_bound))

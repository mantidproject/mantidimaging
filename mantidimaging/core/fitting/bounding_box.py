# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import numpy as np

from mantidimaging.core.data import ImageStack
from mantidimaging.core.utility.sensible_roi import SensibleROI


def get_bounding_box(stack: ImageStack) -> SensibleROI:
    edge_clip = 5
    # compress to 2d first before running means
    data = stack.data[:, edge_clip:-edge_clip, edge_clip:-edge_clip]  # clip dark edges
    buffer_pixels = round(data.shape[1] / 100) + edge_clip
    all_col_mean = np.mean(data, axis=(1, 0))
    all_row_mean = np.mean(data, axis=(2, 0))
    all_col_mean_flipped = np.flip(all_col_mean)
    all_row_mean_flipped = np.flip(all_row_mean)

    def find_bound(data_temp: np.ndarray, flipped: bool = False, noise_threshold_factor: int = 25) -> int:
        data_temp = data_temp[0:round(len(data_temp) / 2):2]
        data_diff_norm = np.absolute(np.gradient(data_temp) / data_temp)
        noise_sigma = np.std(data_diff_norm[:5])
        noise_threshold = noise_threshold_factor * noise_sigma

        for tol in np.linspace(noise_threshold, 5 * noise_sigma, 20, endpoint=True):
            above_threshold_ind = np.where(data_diff_norm > tol)[0]
            #ignore the first 10% of the data to avoid catching edge effects
            above_threshold_ind = above_threshold_ind[above_threshold_ind > stack.data.shape[1] / 10]
            if not above_threshold_ind.size == 0:
                bound = above_threshold_ind[0] * 2
                if flipped:
                    return stack.data.shape[1] - bound + buffer_pixels if buffer_pixels - bound < 0 \
                        else stack.data.shape[1]
                else:
                    return bound - buffer_pixels if bound > buffer_pixels else 0
        # if no peak can be found above 5 sigma of the noise, then return with full image ROI
        if flipped:
            return stack.data.shape[1]
        else:
            return 0

    # add a buffer around the found bounds to make sure all the sample is captured in the bounding box

    top_bound = find_bound(all_row_mean)
    bottom_bound = find_bound(all_row_mean_flipped, True)
    left_bound = find_bound(all_col_mean)
    right_bound = find_bound(all_col_mean_flipped, True)

    return SensibleROI(left_bound, top_bound, right_bound, bottom_bound)

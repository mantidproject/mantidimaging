# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import matplotlib.pyplot as plt
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
        # find bound by looking where the data first goes outside of the initial noise level (standard deviation of first 5 pixels)
        # could take the abs of the dataset and look for peaks so that it works for inversed datasets
        # take the tol between the noise threshold and 6 * sigma, if no bounds are found, then set the bounds to the full dataset
        data_temp = data_temp[50:round(len(data_temp) / 2)]
        data_diff_norm = np.absolute(np.diff(data_temp) / data_temp[1:])
        noise_sigma = np.std(data_diff_norm[:5])
        noise_threshold = noise_threshold_factor * noise_sigma
        for tol in np.linspace(noise_threshold, 6 * noise_sigma, 10, endpoint=True):
            if not np.where(data_diff_norm > tol)[0].size == 0:
                print(f"{np.where(data_diff_norm > tol)=}")
                bound = int(np.where(data_diff_norm > tol)[0][0])
                if flipped:
                    return stack.data.shape[1] - bound + buffer_pixels if buffer_pixels - bound < 0 else stack.data.shape[1]
                else:
                    return bound - buffer_pixels if bound > buffer_pixels else 0
        # if no peak can be found above 6 sigma of the noise, then return with full image ROI
        if flipped:
            return stack.data.shape[1]
        else:
            return 0
    print(f"{[np.std(np.absolute(np.diff(all_row_mean) / all_row_mean[1:])[:round(depth)]) for depth in [stack.data.shape[1] * 0.01, stack.data.shape[1] * 0.05, stack.data.shape[1] * 0.1]]}")

    # t = np.linspace(np.std(np.absolute(np.diff(all_row_mean) / all_row_mean[1:])[:5]) * 25, 6 * np.std(np.absolute(np.diff(all_row_mean) / all_row_mean[1:])[:5]), 5, endpoint=True)
    # plt.plot(np.absolute(np.diff(all_row_mean) / all_row_mean[1:]), 'b')
    # plt.plot(np.absolute(np.diff(all_col_mean) / all_col_mean[1:]), 'r')
    # for thresh in t:
    #     plt.axhline(y=thresh, color='g', linestyle='-')
    # print(f"STANDARD DEVIATION: {np.std(np.absolute(np.diff(all_row_mean) / all_row_mean[1:])[:5]) * 25}")
    plt.subplot(4, 1, 1)
    plt.plot(all_row_mean, 'b')
    plt.plot(all_col_mean, 'r')
    plt.subplot(4, 1, 2)
    plt.plot(np.gradient(all_row_mean), 'b')
    plt.plot(np.gradient(all_col_mean), 'r')
    plt.subplot(4, 1, 3)
    t = np.linspace(np.std(np.absolute(np.diff(all_row_mean) / all_row_mean[1:])[:5]) * 25,
                    6 * np.std(np.absolute(np.diff(all_row_mean) / all_row_mean[1:])[:5]), 5, endpoint=True)
    plt.plot(np.absolute(np.diff(all_row_mean) / all_row_mean[1:]), 'b')
    plt.plot(np.absolute(np.diff(all_col_mean) / all_col_mean[1:]), 'r')
    for thresh in t:
        plt.axhline(y=thresh, color='g', linestyle='-')
    plt.show()
    plt.subplot(4, 1, 4)
    t = np.linspace(np.std(np.absolute(np.diff(all_col_mean_flipped) / all_col_mean_flipped[1:])[:5]) * 25,
                    6 * np.std(np.absolute(np.diff(all_col_mean_flipped) / all_col_mean_flipped[1:])[:5]), 10, endpoint=True)
    plt.plot(np.absolute(np.diff(all_col_mean_flipped) / all_col_mean_flipped[1:]), 'b')
    for thresh in t:
        plt.axhline(y=thresh, color='g', linestyle='-')
    plt.show()
    # add a buffer around the found bounds to make sure all the sample is captured in the bounding box

    top_bound = find_bound(all_row_mean)
    bottom_bound = find_bound(all_row_mean_flipped, True)
    left_bound = find_bound(all_col_mean)
    right_bound = find_bound(all_col_mean_flipped, True)

    return SensibleROI(left_bound, top_bound, right_bound, bottom_bound)

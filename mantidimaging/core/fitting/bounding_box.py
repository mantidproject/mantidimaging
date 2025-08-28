# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import matplotlib.pyplot as plt
import numpy as np

from mantidimaging.core.data import ImageStack
from mantidimaging.core.utility.sensible_roi import SensibleROI


def get_bounding_box(stack: ImageStack) -> SensibleROI:
    y_tol = 0.02
    x_tol = 0.02
    data = stack.data[:, 5:-5, 5:-5]  # clip dark edges
    all_col_mean = np.mean(data, axis=(1, 0))
    all_row_mean = np.mean(data, axis=(2, 0))
    all_col_mean_flipped = np.flip(all_col_mean)
    all_row_mean_flipped = np.flip(all_row_mean)

    plt.plot(np.diff(all_row_mean) / all_row_mean[1:])
    plt.show()

    def find_bound(data_temp, tol, dim=0):
        data_temp = data_temp[0:round(len(data_temp) / 2)]
        while True:
            if not np.where((np.diff(data_temp) / data_temp[1:]) < -tol)[0].size == 0:
                if dim == 0:
                    return np.where((np.diff(data_temp) / data_temp[1:]) < -tol)[0][0]
                else:
                    return data.shape[dim] - np.where((np.diff(data_temp) / data_temp[1:]) < -tol)[0][0]
            else:
                tol -= 0.001

    # add a buffer around the found bounds to make sure all the sample is captured in the bounding box
    buffer_pixels = round(data.shape[1] / 100)

    top_bound = find_bound(all_row_mean, x_tol, 0) - buffer_pixels
    bottom_bound = find_bound(all_row_mean_flipped, x_tol, 2) + buffer_pixels
    left_bound = find_bound(all_col_mean, y_tol, 0) - buffer_pixels
    right_bound = find_bound(all_col_mean_flipped, y_tol, 1) + buffer_pixels

    return SensibleROI(left_bound, top_bound, right_bound, bottom_bound)

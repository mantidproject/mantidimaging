# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import numpy as np

DEFAULT_NUM_BINS = 2048


def generate_histogram_from_image(image_data, num_bins=DEFAULT_NUM_BINS):
    histogram, bins = np.histogram(image_data.flatten(), num_bins)
    center = (bins[:-1] + bins[1:]) / 2
    return center, histogram, bins

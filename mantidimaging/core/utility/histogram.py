# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import numpy as np

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyqtgraph import HistogramLUTItem

DEFAULT_NUM_BINS = 2048


def set_histogram_log_scale(histogram: HistogramLUTItem) -> None:
    """
    Sets the y-values of a histogram to use a log scale.
    :param histogram: The HistogramLUTItem of an image.
    """
    x_data, y_data = histogram.plot.getData()
    assert isinstance(x_data, np.ndarray) and isinstance(y_data, np.ndarray)
    histogram.plot.setData(x_data, np.log(y_data + 1))


def generate_histogram_from_image(image_data: np.ndarray, num_bins: int = DEFAULT_NUM_BINS) -> tuple:
    histogram, bins = np.histogram(image_data.flatten(), num_bins)
    center = (bins[:-1] + bins[1:]) / 2
    return center, histogram, bins

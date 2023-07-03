# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import numpy as np

from unittest import mock

from mantidimaging.core.utility.histogram import set_histogram_log_scale


def test_set_histogram_log_scale():
    x_data = np.arange(10)
    y_data = x_data.copy()
    histogram = mock.Mock()
    histogram.plot.getData.return_value = (x_data, y_data)
    set_histogram_log_scale(histogram)
    np.testing.assert_array_equal(histogram.plot.setData.call_args_list[0][0][0], x_data)
    np.testing.assert_array_equal(histogram.plot.setData.call_args_list[0][0][1], np.log(y_data + 1))

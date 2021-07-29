# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest

import numpy as np
import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.operations.nan_removal import NaNRemovalFilter


class NaNRemovalFilterTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(NaNRemovalFilterTest, self).__init__(*args, **kwargs)

    def test_replace_nans(self):
        images = th.generate_images()
        images.data[::, 0] = np.nan
        nan_idxs = np.isnan(images.data)

        result = NaNRemovalFilter().filter_func(images, 3.0)
        self.assertFalse(np.any(np.isnan(result.data)))
        npt.assert_allclose(result.data[nan_idxs], 3.0)

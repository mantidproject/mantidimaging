from unittest import TestCase

import numpy as np

from mantidimaging.core.cor_tilt import (
        CorTiltDataModel, auto_find_cors)
from mantidimaging.core.data import Images


class AutoTest(TestCase):

    def test_auto_find_cors(self):
        num_projections = 8
        dim_y = 64
        dim_x = 64

        projections = np.ones((num_projections, dim_y, dim_x))
        images = Images(projections)

        roi = (10, 10, 60, 60)

        model = CorTiltDataModel()
        model.populate_slice_indices(10, 60, 4)

        self.assertFalse(np.any(model.cors))

        auto_find_cors(images.sample, roi, model)

        self.assertTrue(np.any(model.cors))

    def test_auto_find_cors_full_roi(self):
        num_projections = 4
        dim_y = 64
        dim_x = 64

        projections = np.ones((num_projections, dim_y, dim_x))
        images = Images(projections)

        roi = (0, 0, 63, 63)

        model = CorTiltDataModel()
        model.populate_slice_indices(0, 63, 4)

        self.assertFalse(np.any(model.cors))

        auto_find_cors(images.sample, roi, model)

        self.assertTrue(np.any(model.cors))

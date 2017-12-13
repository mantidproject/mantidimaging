from unittest import TestCase

import math

import numpy as np

from mantidimaging.core.data import Images
from mantidimaging.core.reconstruct import cor_tilt


class CorTiltTest(TestCase):

    def test_cors_to_tilt_angle(self):
        theta = cor_tilt.cors_to_tilt_angle(10, 1)
        self.assertAlmostEqual(theta, math.pi / 4)

    def test_tilt_angle_to_cors(self):
        theta = math.pi / 4
        slices = np.linspace(0, 100, 20)
        cors = cor_tilt.tilt_angle_to_cors(theta, 50, slices)
        self.assertAlmostEqual(cors[0], 50.0)
        self.assertAlmostEqual(cors[-1], 150.0)

    def test_calculate_cor_and_tilt(self):
        num_projections = 10
        dim_y = 128
        dim_x = 128

        projections = np.ones((num_projections, dim_y, dim_x))
        images = Images(projections)
        roi = (10, 10, 110, 110)
        indices = np.arange(110 - 1, 10, -10)

        tilt, cor, slices, cors, m = \
            cor_tilt.calculate_cor_and_tilt(images, roi, indices)

        self.assertTrue(isinstance(tilt, float))
        self.assertTrue(isinstance(cor, float))
        self.assertEquals(slices.shape, indices.shape)
        self.assertEquals(cors.shape, indices.shape)
        self.assertTrue(isinstance(m, float))

        auto_cor_tilt = images.properties['auto_cor_tilt']
        self.assertAlmostEqual(auto_cor_tilt['rotation_centre'], cor)
        self.assertAlmostEqual(auto_cor_tilt['tilt_angle_rad'], tilt)
        self.assertAlmostEqual(auto_cor_tilt['fitted_gradient'], m)
        self.assertTrue(isinstance(auto_cor_tilt['slice_indices'], list))
        self.assertTrue(isinstance(auto_cor_tilt['rotation_centres'], list))

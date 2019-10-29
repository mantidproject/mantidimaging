from unittest import TestCase

import numpy as np

from mantidimaging.core.cor_tilt import (
        CorTiltDataModel, run_auto_finding_on_images)
from mantidimaging.core.data import Images


class WorkflowTest(TestCase):

    def test_run_auto_cor_tilt_on_images(self):
        num_projections = 8
        dim_y = 128
        dim_x = 128

        projections = np.ones((num_projections, dim_y, dim_x))
        images = Images(projections)

        roi = (10, 10, 110, 110)

        model = CorTiltDataModel()
        model.populate_slice_indices(10, 110, 5)

        run_auto_finding_on_images(images, model, roi)

        self.assertTrue(model.has_results)

        self.assertTrue(isinstance(model.m, float))
        self.assertTrue(isinstance(model.c, float))
        self.assertTrue(isinstance(model.angle_rad, float))
        self.assertEquals(len(model.slices), 5)
        self.assertEquals(len(model.cors), 5)

        auto_cor_tilt = images.metadata['operation_history'][-1]
        self.assertEquals(auto_cor_tilt['name'], 'cor_tilt_finding')

        auto_cor_tilt_kwargs = auto_cor_tilt['kwargs']
        print(auto_cor_tilt)
        self.assertAlmostEqual(
                auto_cor_tilt_kwargs['rotation_centre'], model.c)
        self.assertAlmostEqual(
                auto_cor_tilt_kwargs['fitted_gradient'], model.m)
        self.assertAlmostEqual(
                auto_cor_tilt_kwargs['tilt_angle_rad'], model.angle_rad)
        self.assertTrue(isinstance(
            auto_cor_tilt_kwargs['slice_indices'], list))
        self.assertTrue(isinstance(
            auto_cor_tilt_kwargs['rotation_centres'], list))

import unittest

import mock
import numpy as np

from mantidimaging.core.cor_tilt.data_model import Point
from mantidimaging.core.data import Images
from mantidimaging.gui.windows.recon import (ReconstructWindowModel, CorTiltPointQtModel)
from mantidimaging.gui.windows.stack_visualiser import (StackVisualiserView, StackVisualiserPresenter)


class CORTiltWindowModelTest(unittest.TestCase):
    def setUp(self):
        self.model = ReconstructWindowModel(CorTiltPointQtModel())

        # Mock stack
        self.stack = mock.create_autospec(StackVisualiserView)
        data = Images(sample=np.ndarray(shape=(10, 128, 128), dtype=np.float32))
        self.stack.presenter = StackVisualiserPresenter(self.stack, data)

        self.model.initial_select_data(self.stack)

    def test_empty_init(self):
        m = ReconstructWindowModel(CorTiltPointQtModel())
        self.assertIsNone(m.stack)
        self.assertIsNone(m.sample)
        self.assertIsNone(m.last_result)

    def test_init(self):
        self.assertEquals(self.model.sample.shape, (10, 128, 128))
        self.assertEquals(self.model.num_projections, 10)

    def test_calculate_slices(self):
        self.assertEquals(self.model.slices, [])
        self.assertEquals(self.model.num_points, 0)
        self.model.roi = (30, 25, 100, 120)
        self.model.calculate_slices(5)
        self.assertEquals(len(self.model.slices), 5)
        self.assertEquals(self.model.num_points, 5)

    def test_calculate_slices_no_roi(self):
        self.assertEquals(self.model.slices, [])
        self.assertEquals(self.model.num_points, 0)
        self.model.roi = None
        self.model.calculate_slices(5)
        self.assertEquals(self.model.slices, [])
        self.assertEquals(self.model.num_points, 0)

    def test_tilt_line_data(self):
        self.model.data_model._points = [Point(50, 1), Point(40, 2), Point(30, 3), Point(20, 4)]
        self.model.data_model._cached_cor = 1
        self.model.data_model._cached_gradient = 2

        data = self.model.preview_tilt_line_data

        self.assertEquals(data, ([1, 4], [50, 20]))

    def test_fit_y_data(self):
        self.model.data_model._points = [Point(1, 0.0), Point(2, 0.0), Point(3, 0.0)]
        self.model.data_model._cached_cor = 1
        self.model.data_model._cached_gradient = 2

        data = self.model.preview_fit_y_data

        self.assertEquals(data, [3, 5, 7])

    def test_set_all_cors(self):
        set_to = 123.0
        data_model = self.model.data_model
        data_model.add_point(slice_idx=0, cor=0.0)
        data_model.add_point(slice_idx=5, cor=10.0)
        data_model.add_point(slice_idx=10, cor=100.0)

        self.model.set_all_cors(set_to)
        for [_, cor] in data_model._points:
            self.assertEquals(cor, set_to)

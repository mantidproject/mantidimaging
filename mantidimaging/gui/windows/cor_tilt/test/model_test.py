from __future__ import (absolute_import, division, print_function)

import unittest

import numpy as np

from mantidimaging.core.data import Images
from mantidimaging.core.utility.special_imports import import_mock

from mantidimaging.gui.windows.cor_tilt import (
        CORTiltWindowModel, CorTiltPointQtModel)
from mantidimaging.gui.windows.stack_visualiser import (
        StackVisualiserView, StackVisualiserPresenter)

mock = import_mock()


class CORTiltWindowModelTest(unittest.TestCase):

    def setUp(self):
        self.model = CORTiltWindowModel(CorTiltPointQtModel(None))

        # Mock stack
        self.stack = mock.create_autospec(StackVisualiserView)
        data = Images(
                sample=np.ndarray(shape=(10, 128, 128), dtype=np.float32))
        self.stack.presenter = StackVisualiserPresenter(self.stack, data, 0)

        self.model.initial_select_data(self.stack)

    def test_empty_init(self):
        m = CORTiltWindowModel(CorTiltPointQtModel(None))
        self.assertIsNone(m.stack)
        self.assertIsNone(m.sample)
        self.assertIsNone(m.last_result)

    def test_init(self):
        self.assertEquals(self.model.sample.shape, (10, 128, 128))
        self.assertEquals(self.model.num_projections, 10)

    def test_calculate_slices(self):
        self.assertEquals(self.model.model.slices, [])
        self.assertEquals(self.model.model.num_points, 0)
        self.model.roi = (30, 25, 100, 120)
        self.model.calculate_slices(5)
        self.assertEquals(len(self.model.model.slices), 5)
        self.assertEquals(self.model.model.num_points, 5)

    def test_calculate_slices_no_roi(self):
        self.assertEquals(self.model.model.slices, [])
        self.assertEquals(self.model.model.num_points, 0)
        self.model.roi = None
        self.model.calculate_slices(5)
        self.assertEquals(self.model.model.slices, [])
        self.assertEquals(self.model.model.num_points, 0)

    def test_tilt_line_data(self):
        self.model.model._points = [
            [50, 1],
            [40, 2],
            [30, 3],
            [20, 4]
        ]
        self.model.model._cached_c = 1
        self.model.model._cached_m = 2

        data = self.model.preview_tilt_line_data

        self.assertEquals(data, ([1, 4], [50, 20]))

    def test_fit_y_data(self):
        self.model.model._points = [
            [1, 0.0],
            [2, 0.0],
            [3, 0.0]
        ]
        self.model.model._cached_c = 1
        self.model.model._cached_m = 2

        data = self.model.preview_fit_y_data

        self.assertEquals(data, [3, 5, 7])

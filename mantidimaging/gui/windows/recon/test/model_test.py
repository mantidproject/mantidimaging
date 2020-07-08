import unittest

import mock
import numpy as np

from mantidimaging.core.cor_tilt.data_model import Point
from mantidimaging.core.data import Images
from mantidimaging.gui.windows.recon import (ReconstructWindowModel, CorTiltPointQtModel)
from mantidimaging.gui.windows.stack_visualiser import (StackVisualiserView, StackVisualiserPresenter)


class ReconWindowModelTest(unittest.TestCase):
    def setUp(self):
        self.model = ReconstructWindowModel(CorTiltPointQtModel())

        # Mock stack
        self.stack = mock.create_autospec(StackVisualiserView)
        data = Images(data=np.ndarray(shape=(10, 128, 128), dtype=np.float32))
        self.stack.presenter = StackVisualiserPresenter(self.stack, data)

        self.model.initial_select_data(self.stack)

    def test_empty_init(self):
        m = ReconstructWindowModel(CorTiltPointQtModel())
        self.assertIsNone(m.stack)
        self.assertIsNone(m.last_result)

    def test_calculate_slices(self):
        self.assertEquals(self.model.slices, [])
        self.assertEquals(self.model.num_points, 0)
        self.model.calculate_slices(5)
        self.assertEquals(len(self.model.slices), 5)
        self.assertEquals(self.model.num_points, 5)

    def test_tilt_line_data(self):
        self.model.data_model._points = [Point(50, 1), Point(40, 2), Point(30, 3), Point(20, 4)]
        self.model.data_model._cached_cor = 1
        self.model.data_model._cached_gradient = 2

        data = self.model.tilt_angle

        self.assertEquals(data, ([1, 4], [50, 20]))

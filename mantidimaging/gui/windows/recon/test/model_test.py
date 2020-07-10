import unittest

import mock
import numpy as np

from mantidimaging.core.cor_tilt.data_model import Point
from mantidimaging.core.data import Images
from mantidimaging.core.utility.data_containers import Degrees, ScalarCoR
from mantidimaging.gui.windows.recon import (ReconstructWindowModel, CorTiltPointQtModel)
from mantidimaging.gui.windows.stack_visualiser import (StackVisualiserView, StackVisualiserPresenter)


class ReconWindowModelTest(unittest.TestCase):
    def setUp(self):
        self.model = ReconstructWindowModel(CorTiltPointQtModel())

        # Mock stack
        self.stack = mock.create_autospec(StackVisualiserView)
        data = Images(data=np.ndarray(shape=(10, 128, 256), dtype=np.float32))
        self.stack.presenter = StackVisualiserPresenter(self.stack, data)

        self.model.initial_select_data(self.stack)

    def test_empty_init(self):
        m = ReconstructWindowModel(CorTiltPointQtModel())
        self.assertIsNone(m.stack)
        self.assertIsNone(m.last_result)

    def test_find_initial_cor(self):
        first_slice, initial_cor = self.model.find_initial_cor()
        self.assertEqual(first_slice, 128 // 2)
        self.assertEqual(initial_cor.value, 256 // 2)

        self.model.initial_select_data(None)
        first_slice, initial_cor = self.model.find_initial_cor()
        self.assertEqual(first_slice, 0)
        self.assertEqual(initial_cor.value, 0)

    def test_tilt_line_data(self):
        self.model.data_model._points = [Point(50, 1), Point(40, 2), Point(30, 3), Point(20, 4)]
        self.model.data_model._cached_cor = 1
        self.model.data_model._cached_gradient = 2

        data = self.model.tilt_angle

        self.assertEqual(data, Degrees(-63.43494882292201))

    def test_set_precalculated(self):
        self.model.data_model._points = [Point(50, 1), Point(40, 2), Point(30, 3), Point(20, 4)]

        # a line with a slope of 'below' gives 4 degree tilt
        expected_slope = -0.06992681194351041
        self.model.set_precalculated(ScalarCoR(1000.0), Degrees(4.0))
        cor, angle, slope = self.model.get_results()
        self.assertEqual(cor.value, 1000.0)
        self.assertEqual(angle.value, 4.0)
        self.assertEqual(slope.value, expected_slope)

        # pre-calculated by hand
        expected_cors_with_this_gradient = [996.5036594028245, 997.2029275222595,
                                            997.9021956416947, 998.6014637611298]
        for i, point in enumerate(self.model.data_model._points):
            self.assertEqual(point.cor, expected_cors_with_this_gradient[i])

        some_cor = self.model.data_model.get_cor_from_regression(1555)

        self.assertEqual(some_cor, 891.2638074278414)

    def test_do_fit(self):
        raise NotImplemented("TODO")

    def test_run_preview_recon(self):
        raise NotImplemented("TODO")

    def test_run_full_recon(self):
        raise NotImplemented("TODO")

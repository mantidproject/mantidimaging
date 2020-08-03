import unittest

import mock
import numpy as np

from mantidimaging.core.data import Images
from mantidimaging.core.operation_history import const
from mantidimaging.core.rotation.data_model import Point
from mantidimaging.core.utility.data_containers import Degrees, ScalarCoR, ReconstructionParameters
from mantidimaging.gui.windows.recon import (ReconstructWindowModel, CorTiltPointQtModel)
from mantidimaging.gui.windows.stack_visualiser import (StackVisualiserView, StackVisualiserPresenter)


def assert_called_once_with(mock: mock.Mock, *args):
    assert 1 == mock.call_count
    for actual, expected in zip(mock.call_args[0], args):
        if isinstance(actual, np.ndarray):
            np.testing.assert_equal(actual, expected)
        else:
            assert actual == expected


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
        # TODO move into data_model test
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

    def test_initial_select_data(self):
        test_cor = ScalarCoR(50)
        test_tilt = Degrees(1.5)
        self.model.preview_projection_idx = 150
        self.model.preview_slice_idx = 150
        self.model.set_precalculated(test_cor, test_tilt)

        self.model.initial_select_data(self.stack)

        self.assertNotEqual(test_cor, self.model.last_cor)
        self.assertNotEqual(test_tilt, self.model.tilt_angle)
        self.assertEqual(0, self.model.preview_projection_idx)
        self.assertEqual(0, self.model.preview_slice_idx)
        self.assertIsNotNone(self.model.proj_angles)
        self.assertEqual(10, len(self.model.proj_angles.value))

    def test_do_fit(self):
        self.model.images.metadata.clear()
        self.model.data_model.add_point(0, 0, 350)
        self.model.data_model.add_point(1, 300, 350)
        self.model.do_fit()
        self.assertTrue(const.OPERATION_HISTORY in self.model.images.metadata)
        self.assertEqual(self.model.last_result, self.model.data_model.stack_properties)

    @mock.patch('mantidimaging.gui.windows.recon.model.get_reconstructor_for')
    def test_run_preview_recon(self, mock_get_reconstructor_for):
        mock_reconstructor = mock.Mock()
        mock_reconstructor.single = mock.Mock()
        mock_get_reconstructor_for.return_value = mock_reconstructor

        expected_idx = 5
        expected_sino = self.model.images.sino(expected_idx)
        expected_cor = ScalarCoR(15)
        expected_recon_params = ReconstructionParameters("FBP_CUDA", "ram-lak")
        self.model.run_preview_recon(expected_idx, expected_cor, expected_recon_params)

        mock_get_reconstructor_for.assert_called_once_with(expected_recon_params.algorithm)
        assert_called_once_with(mock_reconstructor.single, expected_sino, expected_cor, self.model.proj_angles,
                                expected_recon_params)

    def test_run_full_recon(self):
        raise NotImplemented("TODO")

    def test_tilt_angle(self):
        raise NotImplemented("TODO")

# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest

from unittest import mock
import numpy as np

from mantidimaging.core.data import Images
from mantidimaging.core.operation_history import const
from mantidimaging.core.reconstruct.astra_recon import allowed_recon_kwargs as astra_allowed_kwargs
from mantidimaging.core.reconstruct.tomopy_recon import allowed_recon_kwargs as tomopy_allowed_kwargs
from mantidimaging.core.reconstruct.cil_recon import allowed_recon_kwargs as cil_allowed_kwargs
from mantidimaging.core.rotation.data_model import Point
from mantidimaging.core.utility.data_containers import Degrees, ScalarCoR, ReconstructionParameters
from mantidimaging.gui.windows.recon import (ReconstructWindowModel, CorTiltPointQtModel)
from mantidimaging.gui.windows.stack_visualiser import (StackVisualiserView, StackVisualiserPresenter)
from mantidimaging.test_helpers.unit_test_helper import assert_called_once_with, generate_images


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

    def test_find_initial_cor_returns_0_0_without_data(self):
        self.model.initial_select_data(None)
        first_slice, initial_cor = self.model.find_initial_cor()
        self.assertEqual(first_slice, 0)
        self.assertEqual(initial_cor.value, 0)

    def test_find_initial_cor_returns_middle_with_data(self):
        self.model.initial_select_data(self.stack)
        first_slice, initial_cor = self.model.find_initial_cor()
        self.assertEqual(first_slice, 64)
        self.assertEqual(initial_cor.value, 128)

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
        expected_cors_with_this_gradient = [996.5036594028245, 997.2029275222595, 997.9021956416947, 998.6014637611298]
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
        self.assertEqual(64, self.model.preview_slice_idx)

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
        mock_reconstructor.single_sino = mock.Mock()
        mock_reconstructor.single_sino.return_value = np.random.rand(256, 256)
        mock_get_reconstructor_for.return_value = mock_reconstructor

        expected_idx = 5
        expected_sino = self.model.images.sino(expected_idx)
        expected_cor = ScalarCoR(15)
        expected_recon_params = ReconstructionParameters("FBP_CUDA", "ram-lak")
        self.model.run_preview_recon(expected_idx, expected_cor, expected_recon_params)

        mock_get_reconstructor_for.assert_called_once_with(expected_recon_params.algorithm)
        assert_called_once_with(mock_reconstructor.single_sino, expected_sino, expected_cor,
                                self.model.images.projection_angles(), expected_recon_params)

    def test_apply_pixel_size(self):
        images = generate_images()

        initial_value = images.data[0][0, 0]
        test_pixel_size = 100
        recon_params = ReconstructionParameters("FBP", "ram-lak", test_pixel_size, pixel_size=test_pixel_size)
        images = self.model._apply_pixel_size(images, recon_params)

        # converts the number we put for pixel size to microns
        expected_value = initial_value / (test_pixel_size * 1e-4)
        self.assertAlmostEqual(expected_value, images.data[0][0, 0], places=4)
        self.assertEqual(test_pixel_size, images.metadata[const.PIXEL_SIZE])
        self.assertEqual(1, len(images.metadata[const.OPERATION_HISTORY]))

    def test_tilt_angle(self):
        self.assertIsNone(self.model.tilt_angle)
        exp_deg = Degrees(1.5)
        self.model.set_precalculated(ScalarCoR(1), exp_deg)
        self.assertAlmostEqual(self.model.tilt_angle.value, exp_deg.value)

    def test_get_me_a_cor(self):
        self.assertEqual(15, self.model.get_me_a_cor(cor=15))

        self.model.data_model.clear_results()
        self.model.last_cor = ScalarCoR(26)
        self.assertEqual(26, self.model.get_me_a_cor().value)

        self.model.data_model.set_precalculated(ScalarCoR(150), Degrees(1.5))
        self.model.preview_slice_idx = 5
        cor = self.model.get_me_a_cor()

        # expected cor value obtained by running the test
        self.assertAlmostEqual(149.86, cor.value, delta=1e-2)

    def test_proj_180_degree_shape_matches_images_where_they_match(self):
        images = mock.MagicMock()
        images.height = 10
        images.width = 10
        images.proj180deg.height = 10
        images.proj180deg.width = 10
        has_proj180deg = mock.MagicMock(return_value=True)
        images.has_proj180deg = has_proj180deg

        self.assertTrue(self.model.proj_180_degree_shape_matches_images(images))

    def test_proj_180_degree_shape_matches_images_where_they_dont_match(self):
        images = mock.MagicMock()
        images.height = 10
        images.width = 10
        images.proj180deg.height = 20
        images.proj180deg.width = 20
        has_proj180deg = mock.MagicMock(return_value=True)
        images.has_proj180deg = has_proj180deg

        self.assertFalse(self.model.proj_180_degree_shape_matches_images(images))

    def test_proj_180_degree_shape_matches_images_where_no_180_present(self):
        images = mock.MagicMock()
        has_proj180deg = mock.MagicMock(return_value=False)
        images.has_proj180deg = has_proj180deg

        self.assertFalse(self.model.proj_180_degree_shape_matches_images(images))

    def test_load_allowed_recon_args_no_cuda(self):
        with mock.patch("mantidimaging.gui.windows.recon.model.CudaChecker.cuda_is_present", return_value=False):
            assert self.model.load_allowed_recon_kwargs() == tomopy_allowed_kwargs()

    def test_load_allowed_recon_args_with_cuda(self):
        allowed_args = tomopy_allowed_kwargs()
        allowed_args.update(astra_allowed_kwargs())
        allowed_args.update(cil_allowed_kwargs())
        with mock.patch("mantidimaging.gui.windows.recon.model.CudaChecker.cuda_is_present", return_value=True):
            assert self.model.load_allowed_recon_kwargs() == allowed_args

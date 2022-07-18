# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import unittest
from pathlib import Path
from unittest import mock
import io

import numpy as np
import numpy.testing as npt

from mantidimaging.gui.windows.spectrum_viewer import SpectrumViewerWindowPresenter, SpectrumViewerWindowModel
from mantidimaging.test_helpers.unit_test_helper import generate_images
from mantidimaging.core.data import ImageStack
from mantidimaging.core.utility.sensible_roi import SensibleROI


class SpectrumViewerWindowPresenterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.presenter = mock.create_autospec(SpectrumViewerWindowPresenter)
        self.model = SpectrumViewerWindowModel(self.presenter)

    def test_set_stack(self):
        stack = generate_images([10, 11, 12])
        self.model.set_stack(stack)

        self.assertEqual(self.model._stack, stack)
        self.assertEqual(self.model.tof_range, (0, 9))

    def test_set_normalise_stack(self):
        normalise_stack = generate_images([10, 11, 12])
        self.model.set_normalise_stack(normalise_stack)

        self.assertEqual(self.model._normalise_stack, normalise_stack)

    def test_get_image_shape(self):
        stack = generate_images([10, 11, 12])
        self.model.set_stack(stack)

        self.assertEqual(self.model.get_image_shape(), (11, 12))

    def test_get_averaged_image(self):
        stack = ImageStack(np.ones([10, 11, 12]))
        stack.data[:5, :, :] = 2
        self.model.set_stack(stack)

        av_img = self.model.get_averaged_image()
        self.assertEqual(av_img.data.shape, (11, 12))
        self.assertEqual(av_img.data[0, 0], (1.5))

    def test_get_averaged_image_range(self):
        stack = ImageStack(np.ones([10, 11, 12]))
        stack.data[:, :, :] = np.arange(0, 10).reshape((10, 1, 1))
        self.model.set_stack(stack)
        self.model.tof_range = (6, 7)

        av_img = self.model.get_averaged_image()
        self.assertEqual(av_img.data.shape, (11, 12))
        self.assertEqual(av_img.data[0, 0], 6.5)

    def test_get_spectrum(self):
        stack = ImageStack(np.ones([10, 11, 12]))
        spectrum = np.arange(0, 10)
        stack.data[:, :, :] = spectrum.reshape((10, 1, 1))
        self.model.set_stack(stack)

        model_spec = self.model.get_spectrum("roi")
        self.assertEqual(model_spec.shape, (10, ))
        npt.assert_array_equal(model_spec, spectrum)

    def test_get_normalised_spectrum(self):
        stack = ImageStack(np.ones([10, 11, 12]))
        spectrum = np.arange(0, 10)
        stack.data[:, :, :] = spectrum.reshape((10, 1, 1))
        self.model.set_stack(stack)

        normalise_stack = ImageStack(np.ones([10, 11, 12]) * 2)
        self.model.set_normalise_stack(normalise_stack)
        self.model.normalised = True

        model_norm_spec = self.model.get_spectrum("roi")
        self.assertEqual(model_norm_spec.shape, (10, ))
        npt.assert_array_equal(model_norm_spec, spectrum / 2)

    def test_get_normalised_spectrum_zeros(self):
        stack = ImageStack(np.ones([10, 11, 12]))
        spectrum = np.arange(0, 10)
        stack.data[:, :, :] = spectrum.reshape((10, 1, 1))
        self.model.set_stack(stack)

        normalise_stack = ImageStack(np.ones([10, 11, 12]) * 2)
        normalise_stack.data[5] = 0
        self.model.set_normalise_stack(normalise_stack)
        self.model.normalised = True

        model_norm_spec = self.model.get_spectrum("roi")
        expected_spec = spectrum / 2
        expected_spec[5] = 0
        self.assertEqual(model_norm_spec.shape, (10, ))
        npt.assert_array_equal(model_norm_spec, expected_spec)

    def test_set_stack_sets_roi(self):
        stack = ImageStack(np.ones([10, 11, 12]))
        self.model.set_stack(stack)
        self.assertEqual(self.model.get_roi('all'), self.model.get_roi('roi'))
        npt.assert_array_equal(self.model.get_roi('all').top, 0)
        npt.assert_array_equal(self.model.get_roi('all').left, 0)
        npt.assert_array_equal(self.model.get_roi('all').right, 12)
        npt.assert_array_equal(self.model.get_roi('all').bottom, 11)

    def test_get_spectrum_roi(self):
        stack = ImageStack(np.ones([10, 11, 12]))
        spectrum = np.arange(0, 10)
        stack.data[:, :, :] = spectrum.reshape((10, 1, 1))
        stack.data[:, :, 6:] *= 2
        self.model.set_stack(stack)

        self.model.set_roi('roi', SensibleROI.from_list([0, 0, 3, 3]))
        model_spec = self.model.get_spectrum("roi")
        npt.assert_array_equal(model_spec, spectrum)

        self.model.set_roi('roi', SensibleROI.from_list([6, 0, 6 + 3, 3]))
        model_spec = self.model.get_spectrum("roi")
        npt.assert_array_equal(model_spec, spectrum * 2)

    def test_save_csv(self):
        stack = ImageStack(np.ones([10, 11, 12]))
        spectrum = np.arange(0, 10) * 2
        stack.data[:, :, :] = spectrum.reshape((10, 1, 1))
        self.model.set_stack(stack)

        class CloseCheckStream(io.StringIO):
            self.is_closed: bool = False

            def close(self) -> None:
                # don't call real close as it clears buffer
                self.is_closed = True

        mock_stream = CloseCheckStream()
        mock_path = mock.create_autospec(Path)
        mock_path.open.return_value = mock_stream

        self.model.save_csv(mock_path)
        mock_path.open.assert_called_once_with("w")
        self.assertIn("# tof_index,all,roi", mock_stream.getvalue())
        self.assertIn("0.0,0.0,0.0", mock_stream.getvalue())
        self.assertIn("1.0,2.0,2.0", mock_stream.getvalue())
        self.assertTrue(mock_stream.is_closed)

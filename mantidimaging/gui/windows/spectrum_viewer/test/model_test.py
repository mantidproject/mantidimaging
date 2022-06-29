# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import unittest
from unittest import mock

import numpy as np
import numpy.testing as npt

from mantidimaging.gui.windows.spectrum_viewer import SpectrumViewerWindowPresenter, SpectrumViewerWindowModel
from mantidimaging.test_helpers.unit_test_helper import generate_images
from mantidimaging.core.data import ImageStack


class SpectrumViewerWindowPresenterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.presenter = mock.create_autospec(SpectrumViewerWindowPresenter)
        self.model = SpectrumViewerWindowModel(self.presenter)

    def test_set_stacks(self):
        stack = generate_images([10, 11, 12])
        open_stack = generate_images([10, 11, 12])
        self.model.set_stack(stack)
        self.model.set_open_stack(open_stack)

        self.assertEqual(self.model._stack, stack)
        self.assertEqual(self.model._open_stack, open_stack)
        self.assertEqual(self.model.tof_range, (0, 9))

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

        model_spec = self.model.get_spectrum()
        self.assertEqual(model_spec.shape, (10, ))
        npt.assert_array_equal(model_spec, spectrum)

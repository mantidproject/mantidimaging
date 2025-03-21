# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import os
from unittest.mock import patch

import numpy as np
import unittest

from PyQt5.QtWidgets import QFileDialog
from tifffile import tifffile

from mantidimaging.test_helpers.unit_test_helper import generate_images
from mantidimaging.gui.widgets.mi_mini_image_view.view import MIMiniImageView
from mantidimaging.test_helpers import start_qapplication


@start_qapplication
class MIMiniImageViewTest(unittest.TestCase):

    def __init__(self, methodName: str = "runTest"):
        super().__init__(methodName)

    def setUp(self):
        self.view = MIMiniImageView()
        self.test_file = "test_output.tif"

    def tearDown(self):
        self.view.cleanup()
        del self.view
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_set_image_uses_brightness_percentile(self):
        image = generate_images(seed=2023, shape=(20, 10, 10))
        self.view.set_brightness_percentiles(1, 99)
        self.view.setImage(image.data)
        np.testing.assert_array_equal(self.view.im.getLevels().round(5),
                                      np.array(self.view.levels).round(5), 'Brightness levels not set correctly')

    @patch.object(QFileDialog, 'getSaveFileName', return_value=("test_output.tif", ""))
    def test_save_raw_image_saves_correct_data(self, mock_get):
        image = generate_images(seed=2023, shape=(10, 10))
        self.view.setImage(image.data)
        self.view.save_raw_image()

        self.assertTrue(os.path.exists(self.test_file), "File was not saved.")
        saved_image = tifffile.imread(self.test_file)
        np.testing.assert_array_equal(saved_image, image.data, "Saved raw image does not match original.")

    @patch.object(QFileDialog, 'getSaveFileName', return_value=("test_output.tif", ""))
    def test_save_displayed_image_correct_data(self, mock_get):
        image = generate_images(seed=2023, shape=(10, 10))
        self.view.setImage(image.data)
        self.view.save_displayed_image()

        self.assertTrue(os.path.exists(self.test_file), "File was not saved.")
        saved_image = tifffile.imread(self.test_file)
        self.assertEqual(saved_image.dtype, np.uint8, "Saved displayed image should be 8-bit.")
        self.assertEqual(saved_image.shape, image.data.shape, "Saved displayed image does not match original.")

# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from unittest.mock import patch
import numpy as np
from PyQt5.QtWidgets import QFileDialog

from mantidimaging.test_helpers.unit_test_helper import generate_images
from mantidimaging.gui.widgets.mi_mini_image_view.view import MIMiniImageView
from mantidimaging.test_helpers import start_qapplication


@start_qapplication
class MIMiniImageViewTest(unittest.TestCase):

    def setUp(self):
        self.view = MIMiniImageView()
        self.test_file = "/tmp/test_output.tif"
        self.test_png = "/tmp/test_output.png"

    def tearDown(self):
        self.view.cleanup()
        del self.view

    def test_set_image_uses_brightness_percentile(self):
        image = generate_images(seed=2023, shape=(20, 10, 10))
        self.view.set_brightness_percentiles(1, 99)
        self.view.setImage(image.data)
        np.testing.assert_array_equal(self.view.im.getLevels().round(5),
                                      np.array(self.view.levels).round(5), 'Brightness levels not set correctly')

    def test_save_raw_image_saves_correct_data(self):
        image = generate_images(seed=2023, shape=(10, 10))
        self.view.setImage(image.data)

        with patch("mantidimaging.gui.widgets.mi_mini_image_view.view.tifffile.imwrite") as mock_write:
            with patch.object(QFileDialog, 'getSaveFileName', return_value=(self.test_file, "")):
                self.view.save_raw_image()
        mock_write.assert_called_once()
        saved_path, saved_data = mock_write.call_args[0]
        self.assertEqual(saved_path, self.test_file)
        np.testing.assert_array_equal(saved_data, image.data)

    def test_save_displayed_image_saves_correct_data(self):
        image = generate_images(seed=2023, shape=(10, 10))
        self.view.setImage(image.data)
        with patch.object(QFileDialog, 'getSaveFileName', return_value=(self.test_png, "")), \
             patch('PyQt5.QtGui.QImage.save', return_value=True) as mock_save:
            self.view.save_displayed_image()
            mock_save.assert_called_once()

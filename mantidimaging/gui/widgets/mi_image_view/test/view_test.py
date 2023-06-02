# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from unittest import mock

import numpy as np
import unittest

from mantidimaging.gui.widgets.mi_image_view.view import MIImageView
from mantidimaging.test_helpers import start_qapplication


@start_qapplication
class MIImageViewTest(unittest.TestCase):

    def setUp(self) -> None:
        self.view = MIImageView()

    def test_set_image_creates_tVals_for_small_image_size(self):
        image = np.zeros((1, 1, 1))

        self.view.setImage(image)
        self.assertTrue(hasattr(self.view, 'tVals'), 'tVals attribute missing for small image size')

    def test_set_image_calls_set_roi_for_new_image(self):
        self.view.set_roi = mock.Mock()
        image = np.zeros((1, 1, 1))

        self.view.setImage(image)
        self.view.set_roi.assert_called_once()

    def test_set_image_calls_set_roi_for_changed_image_dimensions(self):
        image = np.zeros((1, 1, 1))
        self.view.setImage(image)
        self.view.set_roi = mock.Mock()
        new_image = np.zeros((1, 10, 10))

        self.view.setImage(new_image)
        self.view.set_roi.assert_called_once()

    def test_set_image_does_not_call_set_roi_for_same_image_dimensions(self):
        image = np.zeros((1, 1, 1))
        self.view.setImage(image)
        self.view.set_roi = mock.Mock()

        self.view.setImage(image)
        self.view.set_roi.assert_not_called()

    def test_set_roi(self):
        image = np.zeros((1, 10, 5))
        self.view.setImage(image)
        self.view.roi.setPos = mock.Mock()
        self.view.roi.setSize = mock.Mock()
        self.view._update_roi_region_avg = mock.Mock()
        self.view._update_message = mock.Mock()
        self.view.roi_changed_callback = mock.Mock()

        left = top = 0
        right = 10
        bottom = 5
        self.view.set_roi([left, top, right, bottom])

        self.view.roi.setPos.assert_called_once_with(left, top, update=False)
        self.view.roi.setSize.assert_called_once_with([right - left, bottom - top])
        self.view._update_roi_region_avg.assert_called_once()
        self.view.roi_changed_callback.assert_called_once()
        self.view._update_message.assert_called_once()

    def test_default_roi(self):
        image = np.zeros((1, 50, 50))
        self.view.setImage(image)
        expected_roi = [0, 0, 25, 25]

        self.assertListEqual(expected_roi, self.view.default_roi())

    def test_default_roi_uses_min_value_for_small_images(self):
        image = np.zeros((1, 5, 5))
        self.view.setImage(image)
        expected_roi = [0, 0, 20, 20]

        self.assertListEqual(expected_roi, self.view.default_roi())

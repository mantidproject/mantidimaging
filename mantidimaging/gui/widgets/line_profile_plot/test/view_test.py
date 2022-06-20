# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import unittest
from unittest import mock

import numpy as np
from PyQt5.QtCore import QRect
from parameterized import parameterized

from mantidimaging.gui.widgets.line_profile_plot.view import LineProfilePlot, ImageViewLineROI
from mantidimaging.gui.widgets.mi_mini_image_view.view import MIMiniImageView
from mantidimaging.test_helpers import start_qapplication

IMAGE_WIDTH = 10
IMAGE_HEIGHT = 15
IMAGE = np.zeros((IMAGE_HEIGHT, IMAGE_WIDTH))
INITIAL_POS_Y = IMAGE_HEIGHT // 2
INITIAL_POS = [(0, INITIAL_POS_Y), (IMAGE_WIDTH, INITIAL_POS_Y)]
BOUNDS = QRect(0, 0 - INITIAL_POS_Y, IMAGE_WIDTH, IMAGE_HEIGHT)


def check_state_and_bounds(roi_line: ImageViewLineROI, initial_pos=INITIAL_POS, bounds=BOUNDS):
    assert roi_line.maxBounds is not None
    assert roi_line._initial_state['points'] == initial_pos
    assert roi_line.saveState()['points'] == initial_pos
    assert roi_line.maxBounds == bounds


@start_qapplication
class ImageViewLineROITest(unittest.TestCase):
    def setUp(self):
        self.image_view = MIMiniImageView()
        self.roi_line = ImageViewLineROI(self.image_view)

    def test_reset_is_needed_no_image_data(self):
        self.assertFalse(self.roi_line.reset_is_needed())

    def test_reset_is_needed_roi_not_visible(self):
        self._set_image()

        self.assertFalse(self.roi_line.reset_is_needed())

    @parameterized.expand([("Diff width", IMAGE_WIDTH + 5, IMAGE_HEIGHT, True),
                           ("Diff height", IMAGE_WIDTH, IMAGE_HEIGHT + 5, True),
                           ("Same dimensions", IMAGE_WIDTH, IMAGE_HEIGHT, False)])
    def test_reset_is_needed(self, _, width, height, expected_result):
        self._set_image(np.zeros((height, width)))
        self.roi_line._roi_line_is_visible = True
        self.roi_line.maxBounds = BOUNDS

        self.assertEqual(self.roi_line.reset_is_needed(), expected_result)

    def test_add_reset_menu_option(self):
        self.roi_line._add_reset_menu_option()

        self.assertIsNotNone(self.roi_line._reset_option)
        self.assertTrue(self.roi_line._reset_option in self.image_view.viewbox.menu.actions())

    def test_add_roi_to_image(self):
        self._set_image()
        self.assertFalse(self.roi_line._roi_line_is_visible)
        self.roi_line._add_roi_to_image()

        check_state_and_bounds(self.roi_line)
        self.assertTrue(self.roi_line in self.image_view.viewbox.addedItems)
        self.assertTrue(self.roi_line._roi_line_is_visible)

    def test_reset_no_image_data(self):
        self.roi_line._set_initial_state = mock.Mock()
        self.roi_line.reset()

        self.roi_line._set_initial_state.assert_not_called()

    def test_reset_roi_not_visible(self):
        self._set_image()
        self.roi_line._set_initial_state = mock.Mock()
        self.roi_line.reset()

        self.roi_line._set_initial_state.assert_not_called()

    def test_reset(self):
        self._set_image()
        self.roi_line._roi_line_is_visible = True
        self.roi_line._image_view.viewbox.autoRange = mock.Mock()
        self.roi_line.reset()

        check_state_and_bounds(self.roi_line)
        self.roi_line._image_view.viewbox.autoRange.assert_called_once()

    def test_get_image_region_no_image_data(self):
        self.assertIsNone(self.roi_line.get_image_region())

    def test_get_image_region_no_visible_roi(self):
        self._set_image()
        self.assertIsNotNone(self.roi_line.get_image_region())

    def test_get_image_region_visible_roi(self):
        self._set_image()
        self.roi_line._add_roi_to_image()
        self.assertIsNotNone(self.roi_line.get_image_region())

    def _set_image(self, image=IMAGE):
        self.image_view.setImage(image)


@start_qapplication
class LineProfilePlotTest(unittest.TestCase):
    def setUp(self) -> None:
        self.image_view = MIMiniImageView()
        self.line_profile = LineProfilePlot(self.image_view)

    def test_update_no_image_data(self):
        self.line_profile._line_profile.setData = mock.Mock()
        self.line_profile.clear_plot = mock.Mock()
        self.line_profile.update()

        self.line_profile._line_profile.setData.assert_not_called()
        self.line_profile.clear_plot.assert_called_once()

    def test_update(self):
        self.line_profile._line_profile.setData = mock.Mock()
        self._set_image()
        self.line_profile.update()

        self.line_profile._line_profile.setData.assert_called_once()

    def test_reset_with_roi_reset(self):
        self.line_profile._line_profile.setData = mock.Mock()
        self._set_image()
        self.line_profile._roi_line._add_roi_to_image()

        # Update the image data so that an ROI reset would be needed
        new_width = IMAGE_WIDTH + 5
        self._set_image(np.zeros((IMAGE_HEIGHT, new_width)))
        self.line_profile._roi_line.reset_is_needed = mock.Mock()
        self.line_profile._roi_line.reset_is_needed.return_value = True

        self.line_profile.reset()

        new_y_pos = IMAGE_HEIGHT // 2
        new_position = [(0, new_y_pos), (new_width, new_y_pos)]
        new_bounds = QRect(0, 0 - new_y_pos, new_width, IMAGE_HEIGHT)
        check_state_and_bounds(self.line_profile._roi_line, new_position, new_bounds)
        self.line_profile._line_profile.setData.assert_called_once()

    def test_reset_without_roi_reset(self):
        self.line_profile._line_profile.setData = mock.Mock()
        self._set_image()
        self.line_profile._roi_line._add_roi_to_image()
        self.line_profile._roi_line.reset_is_needed = mock.Mock()
        self.line_profile._roi_line.reset_is_needed.return_value = False
        self.line_profile.reset()

        self.line_profile._line_profile.setData.assert_called_once()

    def _set_image(self, image=IMAGE):
        self.image_view.setImage(image)

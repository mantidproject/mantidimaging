# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import unittest
from unittest import mock

import numpy as np
from PyQt5.QtCore import QRect
from parameterized import parameterized

from mantidimaging.gui.widgets.line_profile_plot.view import LineProfilePlot, MILineSegmentROI
from mantidimaging.gui.widgets.mi_mini_image_view.view import MIMiniImageView
from mantidimaging.test_helpers import start_qapplication


@start_qapplication
class LineProfilePlotTest(unittest.TestCase):
    IMAGE_WIDTH = 10
    IMAGE_HEIGHT = 15
    IMAGE = np.zeros((IMAGE_HEIGHT, IMAGE_WIDTH))
    INITIAL_POS = [(0, 0), (IMAGE_WIDTH, 0)]
    BOUNDS = QRect(0, 0, IMAGE_WIDTH, IMAGE_HEIGHT)

    def setUp(self) -> None:
        self.image_view = MIMiniImageView()
        self.line_profile = LineProfilePlot(self.image_view)

    def test_roi_bounds(self):
        self._set_image()
        bounds = self.line_profile._roi_bounds()
        self.assertIsInstance(bounds, QRect)
        self.assertEqual(bounds.x(), 0)
        self.assertEqual(bounds.y(), 0)
        self.assertEqual(bounds.height(), self.IMAGE_HEIGHT)
        self.assertEqual(bounds.width(), self.IMAGE_WIDTH)

    def test_roi_initial_pos_no_image(self):
        self.assertIsNone(self.line_profile._roi_initial_pos())

    def test_roi_initial_pos_with_image(self):
        self._set_image()
        initial_pos = self.line_profile._roi_initial_pos()
        self.assertIsNotNone(initial_pos)
        self.assertEqual(initial_pos, self.INITIAL_POS)

    def test_roi_line_needs_resetting_no_image(self):
        self.assertFalse(self.line_profile._roi_line_needs_resetting())

    def test_roi_line_needs_resetting_no_roi_line(self):
        self._set_image()
        self.assertFalse(self.line_profile._roi_line_needs_resetting())

    @parameterized.expand([("Diff width", IMAGE_WIDTH + 5, IMAGE_HEIGHT, True),
                           ("Diff height", IMAGE_WIDTH, IMAGE_HEIGHT + 5, True),
                           ("Same dimensions", IMAGE_WIDTH, IMAGE_HEIGHT, False)])
    def test_roi_line_needs_resetting(self, _, width, height, expected_result):
        self._set_image()
        self.line_profile._roi_line = mock.Mock()
        self.line_profile._roi_line.maxBounds.width.return_value = width
        self.line_profile._roi_line.maxBounds.height.return_value = height

        self.assertEqual(self.line_profile._roi_line_needs_resetting(), expected_result)

    def test_try_add_roi_to_image_view_no_image(self):
        self.assertFalse(self.line_profile._try_add_roi_to_image_view())

    def test_try_add_roi_to_image_view(self):
        self._set_image()
        result = self.line_profile._try_add_roi_to_image_view()
        self.assertTrue(result)
        self.assertIsInstance(self.line_profile._roi_line, MILineSegmentROI)
        self._check_state_and_bounds()
        self.assertTrue(self.line_profile._roi_line in self.image_view.viewbox.addedItems)

    def test_add_roi_reset_menu_option(self):
        self.line_profile._add_roi_reset_menu_option()
        self.assertIsNotNone(self.line_profile._reset_roi)
        self.assertTrue(self.line_profile._reset_roi in self.image_view.viewbox.menu.actions())

    def test_reset_roi_line_no_initial_state(self):
        self.assertIsNone(self.line_profile._roi_initial_state)
        self.line_profile._roi_initial_pos = mock.Mock()
        self.line_profile.reset_roi_line(force_reset=True)
        self.line_profile._roi_initial_pos.assert_not_called()

    def test_reset_roi_line_no_need_for_reset(self):
        self.line_profile._roi_initial_state = mock.Mock()
        self.line_profile._roi_line_needs_resetting = mock.Mock()
        self.line_profile._roi_line_needs_resetting.return_value = False
        self.line_profile._roi_initial_pos = mock.Mock()
        self.line_profile.reset_roi_line(force_reset=False)
        self.line_profile._roi_initial_pos.assert_not_called()

    def test_reset_roi_line(self):
        self._set_image()
        self.line_profile._try_add_roi_to_image_view()
        self._check_state_and_bounds()

        new_height = self.IMAGE_HEIGHT + 5
        new_width = self.IMAGE_WIDTH + 5
        reset_position = [(0, 0), (new_width, 0)]
        reset_bounds = QRect(0, 0, new_width, new_height)
        self.line_profile._roi_initial_pos = mock.Mock()
        self.line_profile._roi_initial_pos.return_value = reset_position
        self.line_profile._roi_bounds = mock.Mock()
        self.line_profile._roi_bounds.return_value = reset_bounds
        self.line_profile.reset_roi_line(force_reset=True)
        self._check_state_and_bounds(reset_position, reset_bounds)

    def test_update_plot_with_roi(self):
        self.line_profile._roi_line = mock.Mock()
        self.line_profile._roi_line.getArrayRegion = mock.Mock()
        self.line_profile._line_profile.setData = mock.Mock()

        self.line_profile.update_plot()
        self.line_profile._roi_line.getArrayRegion.assert_called_once()
        self.line_profile._line_profile.setData.assert_called_once()

    def test_update_plot_no_roi_and_cannot_add(self):
        self.assertIsNone(self.line_profile._roi_line)
        self.line_profile._try_add_roi_to_image_view = mock.Mock()
        self.line_profile._try_add_roi_to_image_view.return_value = False
        self.line_profile._line_profile.setData = mock.Mock()

        self.line_profile.update_plot()
        self.line_profile._line_profile.setData.assert_not_called()

    def test_update_plot_no_roi_and_can_add(self):
        self.assertIsNone(self.line_profile._roi_line)
        self.line_profile._line_profile.setData = mock.Mock()

        self._set_image()
        self.line_profile.update_plot()
        self.line_profile._line_profile.setData.assert_called_once()

    def _set_image(self, image=IMAGE):
        self.image_view.setImage(image)

    def _check_state_and_bounds(self, expected_points=INITIAL_POS, expected_bounds=BOUNDS):
        self.assertIsNotNone(self.line_profile._roi_initial_state)
        self.assertIsNotNone(self.line_profile._roi_line.maxBounds)
        self.assertEqual(self.line_profile._roi_initial_state['points'], expected_points)
        self.assertEqual(self.line_profile._roi_line.saveState()['points'], expected_points)
        self.assertEqual(self.line_profile._roi_line.maxBounds, expected_bounds)

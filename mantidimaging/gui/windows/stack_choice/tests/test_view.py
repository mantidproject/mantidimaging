# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import unittest
from unittest import mock
from unittest.mock import DEFAULT, Mock, patch
from uuid import uuid4

from PyQt5 import sip
from PyQt5.QtWidgets import QMessageBox
from pyqtgraph import ViewBox

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.gui.windows.stack_choice.view import Notification, StackChoiceView
from mantidimaging.test_helpers import start_qapplication


@start_qapplication
class StackChoiceViewTest(unittest.TestCase):
    def setUp(self):
        self.original_stack = th.generate_images()
        self.new_stack = th.generate_images()
        self.p = mock.MagicMock()
        self.v = StackChoiceView(self.original_stack, self.new_stack, self.p, None)

    def tearDown(self):
        sip.delete(self.v)
        self.v = None

    def test_toggle_roi_show_true(self):
        self.v.roi_shown = True
        self.v.original_stack.roiClicked = mock.MagicMock()
        self.v.new_stack.roiClicked = mock.MagicMock()

        self.v._toggle_roi()

        self.assertFalse(self.v.original_stack.ui.roiBtn.isChecked())
        self.assertFalse(self.v.new_stack.ui.roiBtn.isChecked())
        self.v.original_stack.roiClicked.assert_called_once()
        self.v.new_stack.roiClicked.assert_called_once()

    def test_toggle_roi_show_false(self):
        self.v.roi_shown = False
        self.v.original_stack.roiClicked = mock.MagicMock()
        self.v.new_stack.roiClicked = mock.MagicMock()

        self.v._toggle_roi()

        self.assertTrue(self.v.original_stack.ui.roiBtn.isChecked())
        self.assertTrue(self.v.new_stack.ui.roiBtn.isChecked())
        self.v.original_stack.roiClicked.assert_called_once()
        self.v.new_stack.roiClicked.assert_called_once()

    def test_setup_stack_for_view(self):
        stack = mock.MagicMock()
        data = uuid4()
        self.v.roiButton = mock.MagicMock()
        roi_clicked = uuid4()
        stack.roiClicked = roi_clicked

        self.v._setup_stack_for_view(stack, data)

        stack.setContentsMargins.assert_called_once_with(4, 4, 4, 4)
        stack.setImage.assert_called_once_with(data)
        stack.ui.menuBtn.hide.assert_called_once()
        stack.ui.roiBtn.hide.assert_called_once()
        stack.button_stack_right.hide.assert_called_once()
        stack.button_stack_left.hide.assert_called_once()
        stack.details.setSizePolicy.assert_called_once()
        self.v.roiButton.clicked.connect.assert_called_once_with(roi_clicked)

    def test_sync_roi_plot_for_new_stack_with_old_stack(self):
        new_stack = mock.MagicMock()
        self.v.new_stack = new_stack
        uuid = uuid4()
        self.v._sync_roi_plot_for_old_stack_with_new_stack = uuid

        self.v._sync_roi_plot_for_new_stack_with_old_stack()

        new_stack.roi.sigRegionChanged.disconnect.assert_called_once_with(uuid)
        new_stack.roi.setPos.assert_called_once()
        new_stack.roi.setSize.assert_called_once()
        new_stack.roi.sigRegionChanged.connect.assert_called_once_with(uuid)

    def test_sync_roi_plot_for_old_stack_with_new_stack(self):
        original_stack = mock.MagicMock()
        self.v.original_stack = original_stack
        uuid = uuid4()
        self.v._sync_roi_plot_for_new_stack_with_old_stack = uuid

        self.v._sync_roi_plot_for_old_stack_with_new_stack()

        original_stack.roi.sigRegionChanged.disconnect.assert_called_once_with(uuid)
        original_stack.roi.setPos.assert_called_once()
        original_stack.roi.setSize.assert_called_once()
        original_stack.roi.sigRegionChanged.connect.assert_called_once_with(uuid)

    def test_sync_timelines_for_new_stack_with_old_stack(self):
        new_stack = mock.MagicMock()
        self.v.new_stack = new_stack
        index = uuid4()
        function = uuid4()
        self.v._sync_timelines_for_old_stack_with_new_stack = function

        self.v._sync_timelines_for_new_stack_with_old_stack(index, None)

        new_stack.sigTimeChanged.disconnect.assert_called_once_with(function)
        new_stack.setCurrentIndex.assert_called_once_with(index)
        new_stack.sigTimeChanged.connect.assert_called_once_with(function)

    def test_sync_timelines_for_old_stack_with_new_stack(self):
        original_stack = mock.MagicMock()
        self.v.original_stack = original_stack
        index = uuid4()
        function = uuid4()
        self.v._sync_timelines_for_new_stack_with_old_stack = function

        self.v._sync_timelines_for_old_stack_with_new_stack(index, None)

        original_stack.sigTimeChanged.disconnect.assert_called_once_with(function)
        original_stack.setCurrentIndex.assert_called_once_with(index)
        original_stack.sigTimeChanged.connect.assert_called_once_with(function)

    def test_closeEvent(self):
        self.v.choice_made = True
        self.v.original_stack = mock.MagicMock()
        self.v.new_stack = mock.MagicMock()

        self.v.closeEvent(None)

        self.v.original_stack.close.assert_called_once()
        self.v.new_stack.close.assert_called_once()

    @mock.patch("mantidimaging.gui.windows.stack_choice.view.QMessageBox")
    def test_closeEvent_message_pop_up_if_choice_not_made_and_notifies_presenter_on_ok(self, message_box):
        self.v.choice_made = False
        self.v.original_stack = mock.MagicMock()
        self.v.new_stack = mock.MagicMock()
        message_box.warning.return_value = QMessageBox.Ok
        message_box.Ok = QMessageBox.Ok
        mock_event = mock.MagicMock()

        self.v.closeEvent(mock_event)

        message_box.warning.assert_called_once()
        self.p.notify.assert_called_once_with(Notification.CHOOSE_NEW_DATA)
        self.v.original_stack.close.assert_called_once()
        self.v.new_stack.close.assert_called_once()
        mock_event.ignore.assert_not_called()

    @mock.patch("mantidimaging.gui.windows.stack_choice.view.QMessageBox")
    def test_closeEvent_message_pop_up_if_choice_not_made_and_doesnt_notify_presenter_on_cancel(self, message_box):
        self.v.choice_made = False
        self.v.original_stack = mock.MagicMock()
        self.v.new_stack = mock.MagicMock()
        message_box.warning.return_value = QMessageBox.Cancel
        mock_event = mock.MagicMock()

        self.v.closeEvent(mock_event)

        message_box.warning.assert_called_once()
        self.p.notify.assert_not_called()
        self.v.original_stack.close.assert_not_called()
        self.v.new_stack.close.assert_not_called()
        mock_event.ignore.assert_called_once()

    def test_images_are_synced(self):
        self.v.original_stack = mock.MagicMock()
        self.v.new_stack = mock.MagicMock()
        self.v.new_stack.view = "view"

        self.v._sync_both_image_axis()

        self.assertIn(mock.call(ViewBox.XAxis, "view"), self.v.original_stack.view.linkView.call_args_list)
        self.assertIn(mock.call(ViewBox.YAxis, "view"), self.v.original_stack.view.linkView.call_args_list)
        self.assertEqual(2, self.v.original_stack.view.linkView.call_count)

    def test_ensure_range_is_the_same_new_stack_min_original_stack_max(self):
        self.v.new_stack.ui.histogram.vb = mock.MagicMock()
        self.v.original_stack.ui.histogram.vb = mock.MagicMock()
        self.v.new_stack.ui.histogram.getLevels = mock.MagicMock(return_value=[0, 100])
        self.v.original_stack.ui.histogram.getLevels = mock.MagicMock(return_value=[0, 200])

        self.v._ensure_range_is_the_same()

        self.v.new_stack.ui.histogram.vb.setRange.assert_called_once_with(yRange=(0, 200))
        self.v.original_stack.ui.histogram.vb.setRange.assert_called_once_with(yRange=(0, 200))

    def test_ensure_range_is_the_same_new_stack_max_original_stack_min(self):
        self.v.new_stack.ui.histogram.vb = mock.MagicMock()
        self.v.original_stack.ui.histogram.vb = mock.MagicMock()
        self.v.new_stack.ui.histogram.getLevels = mock.MagicMock(return_value=[0, 200])
        self.v.original_stack.ui.histogram.getLevels = mock.MagicMock(return_value=[0, 100])

        self.v._ensure_range_is_the_same()

        self.v.new_stack.ui.histogram.vb.setRange.assert_called_once_with(yRange=(0, 200))
        self.v.original_stack.ui.histogram.vb.setRange.assert_called_once_with(yRange=(0, 200))

    @patch.multiple('mantidimaging.gui.windows.stack_choice.view.StackChoiceView',
                    _set_from_old_to_new=DEFAULT,
                    _set_from_new_to_old=DEFAULT)
    def test_connect_histogram_changes(self, _set_from_old_to_new: Mock = Mock(), _set_from_new_to_old: Mock = Mock()):
        self.v.connect_histogram_changes()

        # check this is called once to set the same range on the new histogram as is currently selected on the new one
        _set_from_old_to_new.assert_called_once()

        expected_emit = (0, 99)
        _set_from_old_to_new.reset_mock()

        self.v.original_stack.ui.histogram.sigLevelsChanged.emit(expected_emit)
        _set_from_old_to_new.assert_called_once_with(expected_emit)

        self.v.new_stack.ui.histogram.sigLevelsChanged.emit(expected_emit)
        _set_from_new_to_old.assert_called_once_with(expected_emit)

        # reset mocks and disconnect signals
        _set_from_old_to_new.reset_mock()
        _set_from_new_to_old.reset_mock()
        self.v.disconnect_histogram_changes()

        self.v.original_stack.ui.histogram.sigLevelsChanged.emit(expected_emit)
        _set_from_old_to_new.assert_not_called()

        self.v.new_stack.ui.histogram.sigLevelsChanged.emit(expected_emit)
        _set_from_new_to_old.assert_not_called()

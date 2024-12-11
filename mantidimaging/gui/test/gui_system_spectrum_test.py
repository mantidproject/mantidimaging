# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from unittest import mock

from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtGui import QColor

from mantidimaging.gui.test.gui_system_base import GuiSystemBase, SHOW_DELAY, SHORT_DELAY
from mantidimaging.gui.windows.spectrum_viewer.model import SpecType, SensibleROI
from mantidimaging.test_helpers.qt_test_helpers import wait_until


class TestGuiSpectrumViewer(GuiSystemBase):

    def setUp(self) -> None:
        patcher_show_error_dialog = mock.patch(
            "mantidimaging.gui.windows.spectrum_viewer.view.SpectrumViewerWindowView.show_error_dialog")
        self.mock_show_error_dialog = patcher_show_error_dialog.start()
        self.addCleanup(patcher_show_error_dialog.stop)
        super().setUp()
        self._close_welcome()
        self._load_data_set()

        self._open_spectrum_viewer()
        assert self.main_window.spectrum_viewer is not None
        self.spectrum_window = self.main_window.spectrum_viewer

        self.assertTrue(self.spectrum_window.isVisible())

        wait_until(lambda: self.spectrum_window.presenter.model._stack is not None, max_retry=600)

    def tearDown(self) -> None:
        self._close_image_stacks()
        super().tearDown()
        self.assertFalse(self.main_window.isVisible())

    def test_spectrum_window_opens_with_data_in_default_state(self) -> None:
        self.assertFalse(self.spectrum_window.normaliseCheckBox.isChecked())
        self.assertFalse(self.spectrum_window.normalise_ShutterCount_CheckBox.isEnabled())
        self.assertEqual(self.spectrum_window.roi_table_model.rowCount(), 1)
        self.assertEqual(self.spectrum_window.roi_table_model.columnCount(), 3)
        self.assertTrue(self.spectrum_window.addBtn.isEnabled())
        self.assertTrue(self.spectrum_window.removeBtn.isEnabled())
        self.assertTrue(self.spectrum_window.exportButton.isEnabled())
        self.assertIn('roi', self.spectrum_window.roi_table_model.roi_names())
        self.assertIn('roi', self.spectrum_window.spectrum_widget.roi_dict)
        QTest.qWait(SHOW_DELAY)

    def test_add_roi(self) -> None:
        for i in range(1, 4):
            initial_roi_count = self.spectrum_window.roi_table_model.rowCount()
            QTest.mouseClick(self.spectrum_window.addBtn, Qt.MouseButton.LeftButton)
            QTest.qWait(SHORT_DELAY)
            final_roi_count = self.spectrum_window.roi_table_model.rowCount()
            self.assertEqual(final_roi_count, initial_roi_count + 1)
            self.assertIn(f'roi_{i}', self.spectrum_window.roi_table_model.roi_names())
            self.assertIn(f'roi_{i}', self.spectrum_window.spectrum_widget.roi_dict)

    def test_remove_roi(self) -> None:
        QTest.mouseClick(self.spectrum_window.addBtn, Qt.MouseButton.LeftButton)
        QTest.qWait(SHORT_DELAY)
        initial_roi_count = self.spectrum_window.roi_table_model.rowCount()

        QTest.mouseClick(self.spectrum_window.removeBtn, Qt.MouseButton.LeftButton)
        QTest.qWait(SHORT_DELAY)
        final_roi_count = self.spectrum_window.roi_table_model.rowCount()

        self.assertEqual(final_roi_count, initial_roi_count - 1)
        self.assertNotIn(f'roi_{initial_roi_count - 1}', self.spectrum_window.roi_table_model.roi_names())
        self.assertNotIn(f'roi_{initial_roi_count - 1}', self.spectrum_window.spectrum_widget.roi_dict)

    def test_change_roi_color(self):
        QTest.mouseClick(self.spectrum_window.addBtn, Qt.MouseButton.LeftButton)
        QTest.qWait(SHORT_DELAY)

        roi_name = 'roi_1'
        new_color = (255, 0, 0, 255)

        sensible_roi = SensibleROI(left=0, top=0, right=10, bottom=10)
        self.spectrum_window.spectrum_widget.add_roi(sensible_roi, roi_name)

        spec_roi = self.spectrum_window.spectrum_widget.roi_dict[roi_name]

        with mock.patch.object(spec_roi, 'openColorDialog', return_value=QColor(*new_color)):
            spec_roi.onChangeColor()

        self.assertEqual(self.spectrum_window.spectrum_widget.roi_dict[roi_name].colour, new_color)

    def test_rename_roi(self):
        QTest.mouseClick(self.spectrum_window.addBtn, Qt.MouseButton.LeftButton)
        QTest.qWait(SHORT_DELAY)

        old_name = 'roi_1'
        new_name = 'roi_renamed'

        table_model = self.spectrum_window.roi_table_model
        row = table_model.roi_names().index(old_name)

        table_model.set_element(row, 0, new_name)
        table_model.dataChanged.emit(table_model.index(row, 0), table_model.index(row, 0))

        self.assertNotIn(old_name, self.spectrum_window.spectrum_widget.roi_dict)
        self.assertIn(new_name, self.spectrum_window.spectrum_widget.roi_dict)

    def test_adjust_roi(self):
        QTest.mouseClick(self.spectrum_window.addBtn, Qt.MouseButton.LeftButton)
        QTest.qWait(SHORT_DELAY)

        roi_names = self.spectrum_window.presenter.get_roi_names()
        roi_name = next(name for name in roi_names if name != 'all')
        roi_widget = self.spectrum_window.spectrum_widget.roi_dict[roi_name]
        handle_index = 0
        new_position = (10, 20)

        roi_widget.movePoint(handle_index, new_position)
        QTest.qWait(SHORT_DELAY)

        updated_roi = self.spectrum_window.spectrum_widget.get_roi(roi_name)
        self.assertEqual(updated_roi.right, new_position[0])
        self.assertEqual(updated_roi.bottom, new_position[1])
        self.assertEqual(updated_roi.top, 0)
        self.assertEqual(updated_roi.left, 0)

    def test_normalisation_toggle(self):
        self.spectrum_window.normaliseCheckBox.setCheckState(Qt.CheckState.Checked)
        QTest.qWait(SHORT_DELAY)
        assert self.spectrum_window.presenter.spectrum_mode == SpecType.SAMPLE_NORMED

        self.spectrum_window.normaliseCheckBox.setCheckState(Qt.CheckState.Unchecked)
        QTest.qWait(SHORT_DELAY)
        assert self.spectrum_window.presenter.spectrum_mode == SpecType.SAMPLE

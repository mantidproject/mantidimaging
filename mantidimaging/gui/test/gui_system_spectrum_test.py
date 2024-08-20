# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from unittest import mock

from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest

from mantidimaging.gui.test.gui_system_base import GuiSystemBase, SHOW_DELAY, SHORT_DELAY
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

    def test_change_roi_color(self) -> None:
        QTest.mouseClick(self.spectrum_window.addBtn, Qt.MouseButton.LeftButton)
        QTest.qWait(SHORT_DELAY)

        new_color = (255, 0, 0, 255)
        self.spectrum_window.spectrum_widget.change_roi_colour('roi_1', new_color)

        self.assertEqual(self.spectrum_window.spectrum_widget.roi_dict['roi_1'].colour, new_color)

    def test_rename_roi(self) -> None:
        QTest.mouseClick(self.spectrum_window.addBtn, Qt.MouseButton.LeftButton)
        QTest.qWait(SHORT_DELAY)

        old_name = 'roi_1'
        new_name = 'roi_renamed'
        self.spectrum_window.presenter.rename_roi(old_name, new_name)

        self.assertNotIn(old_name, self.spectrum_window.spectrum_widget.roi_dict)
        self.assertIn(new_name, self.spectrum_window.spectrum_widget.roi_dict)

    def test_adjust_roi(self):
        QTest.mouseClick(self.spectrum_window.addBtn, Qt.MouseButton.LeftButton)
        QTest.qWait(SHORT_DELAY)
        roi_name = self.spectrum_window.presenter.get_roi_names()[0]
        roi = self.spectrum_window.presenter.model.get_roi(roi_name)
        new_roi = roi.copy()
        new_roi.left += 10
        new_roi.top += 10
        self.spectrum_window.presenter.model.set_roi(roi_name, new_roi)
        self.spectrum_window.presenter.handle_roi_moved()
        updated_roi = self.spectrum_window.presenter.model.get_roi(roi_name)
        assert updated_roi.left == new_roi.left
        assert updated_roi.top == new_roi.top

    def test_reset_units_menu(self) -> None:
        self.assertFalse(self.spectrum_window.tof_mode_select_group.isEnabled())

        self.spectrum_window.presenter.handle_sample_change("sample_uuid")
        self.assertTrue(self.spectrum_window.tof_mode_select_group.isEnabled())

    def test_normalisation_toggle(self):
        self.spectrum_window.normaliseCheckBox.setCheckState(Qt.CheckState.Checked)
        QTest.qWait(SHORT_DELAY)
        assert self.spectrum_window.presenter.spectrum_mode == SpecType.SAMPLE_NORMED

        self.spectrum_window.normaliseCheckBox.setCheckState(Qt.CheckState.Unchecked)
        QTest.qWait(SHORT_DELAY)
        assert self.spectrum_window.presenter.spectrum_mode == SpecType.SAMPLE

    def test_export_csv(self) -> None:
        with mock.patch("mantidimaging.gui.windows.spectrum_viewer.view.QFileDialog.getSaveFileName",
                        return_value=("test_output.csv", "CSV Files (*.csv)")):
            self.spectrum_window.presenter.handle_export_csv()

            with open("test_output.csv", "r") as file:
                lines = file.readlines()
                self.assertGreater(len(lines), 1)

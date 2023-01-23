# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from itertools import product
from unittest import mock
from typing import TYPE_CHECKING

from parameterized import parameterized
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QFormLayout, QLabel, QWidget, QPushButton

from mantidimaging.gui.widgets.roi_selector.view import ROISelectorView
from mantidimaging.gui.windows.stack_choice.presenter import StackChoicePresenter
from mantidimaging.core.data import ImageStack
from mantidimaging.gui.test.gui_system_base import GuiSystemBase, SHOW_DELAY, SHORT_DELAY
from mantidimaging.gui.windows.operations.view import FiltersWindowView
from mantidimaging.test_helpers.qt_test_helpers import wait_until
from mantidimaging.test_helpers.start_qapplication import start_multiprocessing_pool

if TYPE_CHECKING:
    from uuid import UUID

OP_LIST = [
    ("Arithmetic", [["Multiply", "2"]]),
    ("Circular Mask", []),
    ("Clip Values", [["Clip Max", "10000"]]),
    ("Crop Coordinates", [["ROI", "10,10,100,100"]]),
    ("Divide", []),
    ("Flat-fielding", []),
    ("Gaussian", []),
    ("Median", []),
    # ("Monitor Normalisation", []),
    ("NaN Removal", []),
    ("Remove Outliers", []),
    ("Rebin", []),
    # ("Remove all stripes", []),
    # ("Remove dead stripes", []),
    # ("Remove large stripes", []),
    # ("Remove stripes with filtering", []),
    # ("Remove stripes with sorting and fitting", []),
    ("Rescale", [["Max input", "10000"]]),
    ("Ring Removal", []),
    ("ROI Normalisation", []),
    ("Rotate Stack", []),
]


@start_multiprocessing_pool
class TestGuiSystemOperations(GuiSystemBase):
    def setUp(self) -> None:
        super().setUp()
        self._close_welcome()
        self._load_data_set()

        self._open_operations()
        self.assertIsNotNone(self.main_window.filters)
        assert isinstance(self.main_window.filters, FiltersWindowView)  # for yapf
        self.assertTrue(self.main_window.filters.isVisible())
        self.op_window = self.main_window.filters

    def tearDown(self) -> None:
        if self.main_window.filters:
            self.main_window.filters.close()
        QTest.qWait(SHOW_DELAY)
        self._close_image_stacks()
        super().tearDown()
        self.assertFalse(self.main_window.isVisible())

    @staticmethod
    def _get_operation_parameter_widget(form: QFormLayout, param_name: str) -> QWidget:
        for i in range(form.rowCount()):
            label_item = form.itemAt(i * 2)
            widget_item = form.itemAt(i * 2 + 1)

            if label_item is not None and widget_item is not None:
                label = label_item.widget()
                assert isinstance(label, QLabel)
                if label.text() == param_name:
                    return widget_item.widget()

        raise ValueError(f"Could not find '{param_name}' in form")

    @staticmethod
    def _get_operation_button_widget(form: QFormLayout, button_name: str) -> QWidget:
        for i in range(form.rowCount()):
            widget_item = form.itemAt(i * 2)

            if widget_item is not None:
                button = widget_item.widget()
                if isinstance(button, QPushButton) and button.text() == button_name:
                    return button

        raise ValueError(f"Could not find '{button_name}' in form")

    @parameterized.expand(OP_LIST)
    def test_run_operation_stack(self, op_name, params):
        QTest.qWait(SHOW_DELAY)
        index = self.op_window.filterSelector.findText(op_name)
        self.assertGreaterEqual(index, 0, f'Operation "{op_name}" not found in filterSelector')
        self.op_window.filterSelector.setCurrentIndex(index)
        QTest.qWait(SHOW_DELAY)

        for param_name, param_value in params:
            widget = self._get_operation_parameter_widget(self.op_window.filterPropertiesLayout, param_name)
            widget.selectAll()
            QTest.keyClicks(widget, param_value)
            QTest.keyClick(widget, Qt.Key_Return)
            QTest.qWait(SHOW_DELAY)

        self.op_window.safeApply.setChecked(False)
        QTest.mouseClick(self.op_window.applyButton, Qt.MouseButton.LeftButton)
        QTest.qWait(SHORT_DELAY)
        wait_until(lambda: self.op_window.presenter.filter_is_running is False, max_retry=600)

    @parameterized.expand(product(OP_LIST[:3], ["new", "original"]))
    def test_run_operation_stack_safe(self, op_info, keep_stack):
        op_name, params = op_info
        print(f"test_run_operation_stack_safe {op_name=} {params=} {keep_stack=}")
        QTest.qWait(SHOW_DELAY)
        index = self.op_window.filterSelector.findText(op_name)
        self.assertGreaterEqual(index, 0, f'Operation "{op_name}" not found in filterSelector')
        self.op_window.filterSelector.setCurrentIndex(index)
        QTest.qWait(SHOW_DELAY)

        for param_name, param_value in params:
            widget = self._get_operation_parameter_widget(self.op_window.filterPropertiesLayout, param_name)
            widget.selectAll()
            QTest.keyClicks(widget, param_value)
            QTest.keyClick(widget, Qt.Key_Return)
            QTest.qWait(SHOW_DELAY)

        self.op_window.safeApply.setChecked(True)
        QTest.qWait(SHOW_DELAY)

        def mock_wait_for_stack_choice(self, new_stack: ImageStack, stack_uuid: UUID):
            print("mock_wait_for_stack_choice")
            stack_choice = StackChoicePresenter(self.original_images_stack[stack_uuid], new_stack, self)
            stack_choice.show()
            QTest.qWait(SHOW_DELAY)
            if keep_stack == "new":
                QTest.mouseClick(stack_choice.view.newDataButton, Qt.MouseButton.LeftButton)
            else:
                QTest.mouseClick(stack_choice.view.originalDataButton, Qt.MouseButton.LeftButton)

            return stack_choice.use_new_data

        with mock.patch("mantidimaging.gui.windows.operations.presenter.FiltersWindowPresenter._wait_for_stack_choice",
                        mock_wait_for_stack_choice):

            QTimer.singleShot(SHORT_DELAY, lambda: self._click_messageBox("OK"))
            QTest.mouseClick(self.op_window.applyButton, Qt.MouseButton.LeftButton)

            QTest.qWait(SHORT_DELAY)
            wait_until(lambda: self.op_window.presenter.filter_is_running is False)

    @mock.patch("mantidimaging.gui.windows.operations.presenter.FiltersWindowPresenter.do_update_previews")
    def test_selecting_auto_update_triggers_preview(self, mock_do_update_previews):
        self.op_window.previewAutoUpdate.setCheckState(Qt.CheckState.Unchecked)

        QTest.mouseClick(self.op_window.previewAutoUpdate, Qt.MouseButton.LeftButton)
        wait_until(lambda: mock_do_update_previews.call_count == 1)

    @mock.patch("mantidimaging.gui.windows.operations.presenter.FiltersWindowPresenter.do_update_previews")
    def test_clicking_update_now_btn_triggers_preview(self, mock_do_update_previews):
        self.op_window.previewAutoUpdate.setCheckState(Qt.CheckState.Unchecked)

        QTest.mouseClick(self.op_window.updatePreviewButton, Qt.MouseButton.LeftButton)
        wait_until(lambda: mock_do_update_previews.call_count == 1)

    def test_run_operation_after_deletes(self):
        self._close_image_stacks()
        QTest.qWait(SHOW_DELAY)
        self._load_data_set()
        QTest.qWait(SHOW_DELAY)
        index = self.op_window.filterSelector.findText("Crop Coordinates")
        self.op_window.filterSelector.setCurrentIndex(index)
        QTest.qWait(SHOW_DELAY)

        widget = self._get_operation_parameter_widget(self.op_window.filterPropertiesLayout, "ROI")
        widget.selectAll()
        QTest.keyClicks(widget, "0,0,20,20")
        QTest.keyClick(widget, Qt.Key_Return)
        QTest.qWait(SHOW_DELAY)

        self.op_window.safeApply.setChecked(False)
        QTest.mouseClick(self.op_window.applyButton, Qt.MouseButton.LeftButton)
        QTest.qWait(SHORT_DELAY)
        wait_until(lambda: self.op_window.presenter.filter_is_running is False, max_retry=600)

    @parameterized.expand([(OP_LIST[3][0], "Select ROI", "ROI"), (OP_LIST[13][0], "Select Air Region", "Air Region")])
    def test_opening_roi_selector_window_toggles_controls_correctly(self, op_name, button_name, field_name):
        QTest.qWait(SHOW_DELAY)
        index = self.op_window.filterSelector.findText(op_name)
        self.op_window.filterSelector.setCurrentIndex(index)
        QTest.qWait(SHOW_DELAY)

        # Check the relevant controls are disabled when the window is opened
        roi_button = self._get_operation_button_widget(self.op_window.filterPropertiesLayout, button_name)
        roi_field = self._get_operation_parameter_widget(self.op_window.filterPropertiesLayout, field_name)
        self.assertTrue(roi_button.isEnabled())
        self.assertTrue(roi_field.isEnabled())
        QTest.mouseClick(roi_button, Qt.MouseButton.LeftButton)
        QTest.qWait(SHOW_DELAY)
        self.assertFalse(roi_button.isEnabled())
        self.assertFalse(roi_field.isEnabled())

        # Check the relevant controls are enabled again when the window is closed
        self._close_window(ROISelectorView)
        self.assertTrue(roi_button.isEnabled())
        self.assertTrue(roi_field.isEnabled())

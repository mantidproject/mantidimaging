# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
from unittest import mock

from mantidimaging.eyes_tests.base_eyes import BaseEyesTest
from mantidimaging.gui.widgets.roi_selector.view import ROISelectorView


class OperationsWindowTest(BaseEyesTest):

    def setUp(self):
        super().setUp()

    def tearDown(self):
        self.imaging.filters.close()
        super().tearDown()

    def test_operation_window_opens(self):
        self.imaging.show_filters_window()
        self.check_target(widget=self.imaging.filters)

    def test_operation_window_opens_with_data(self):
        self._load_strict_data_set()

        self.imaging.show_filters_window()
        self.check_target(widget=self.imaging.filters)

    def test_operation_window_after_data_was_processed(self):
        self._load_strict_data_set(set_180=True)

        self.imaging.show_filters_window()
        QApplication.processEvents()
        self.imaging.show_question_dialog = mock.MagicMock()
        self.imaging.filters.safeApply.setChecked(False)
        self.imaging.filters.applyButton.click()
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)
        self.imaging.show_question_dialog.assert_not_called()

    def test_operations_crop_coordinates_parameters(self):
        self._load_strict_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Crop Coordinates")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_flat_fielding_parameters(self):
        self._load_strict_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Flat-fielding")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_remove_outliers_parameters(self):
        self._load_strict_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Remove Outliers")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_ROI_normalisation_parameters(self):
        self._load_strict_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("ROI Normalisation")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_arithmetic_parameters(self):
        self._load_strict_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Arithmetic")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_circular_mask_parameters(self):
        self._load_strict_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Circular Mask")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_clip_values_parameters(self):
        self._load_strict_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Clip Values")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_divide_parameters(self):
        self._load_strict_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Divide")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_gaussian_parameters(self):
        self._load_strict_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Gaussian")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_median_parameters(self):
        self._load_strict_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Median")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_monitor_normalisation_parameters(self):
        self._load_strict_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Monitor Normalisation")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_nan_removal_parameters(self):
        self._load_strict_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("NaN Removal")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_rebin_parameters(self):
        self._load_strict_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Rebin")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_rescale_parameters(self):
        self._load_strict_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Rescale")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_ring_removal_parameters(self):
        self._load_strict_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Ring Removal")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_rotate_stack_parameters(self):
        self._load_strict_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Rotate Stack")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_remove_all_stripes_parameters(self):
        self._load_strict_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Remove all stripes")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_remove_dead_stripes_parameters(self):
        self._load_strict_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Remove dead stripes")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_remove_large_stripes_parameters(self):
        self._load_strict_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Remove large stripes")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_remove_stripes_with_filtering_parameters(self):
        self._load_strict_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Remove stripes with filtering")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_remove_stripes_with_sorting_and_fitting_parameters(self):
        self._load_strict_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Remove stripes with sorting and fitting")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_roi_visualiser_window(self):
        self._load_strict_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Crop Coordinates")
        QApplication.processEvents()

        roi_button = self._get_operation_button_widget("Select ROI")
        roi_button.click()
        QApplication.processEvents()

        roi_window = self._get_top_level_widget(ROISelectorView)
        self.check_target(widget=roi_window)

        roi_window.close()

    def _get_operation_button_widget(self, button_name: str) -> QWidget:
        form = self.imaging.filters.filterPropertiesLayout
        for i in range(form.rowCount()):
            widget_item = form.itemAt(i * 2)

            if widget_item is not None:
                button = widget_item.widget()
                if isinstance(button, QPushButton) and button.text() == button_name:
                    return button

        raise ValueError(f"Could not find '{button_name}' in form")

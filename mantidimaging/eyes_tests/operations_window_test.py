# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from PyQt5.QtWidgets import QApplication
from unittest import mock
import pytest

from mantidimaging.eyes_tests.base_eyes import BaseEyesTest


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
        self._load_data_set()

        self.imaging.show_filters_window()
        self.check_target(widget=self.imaging.filters)

    @pytest.mark.xfail
    def test_operation_window_after_data_was_processed(self):
        self._load_data_set(set_180=True)

        self.imaging.show_filters_window()
        QApplication.processEvents()
        self.imaging.filters.ask_confirmation = mock.MagicMock(return_value=True)
        self.imaging.filters.safeApply.setChecked(False)
        self.imaging.filters.applyButton.click()
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)
        self.imaging.filters.ask_confirmation.assert_called_once()

    def test_operations_crop_coordinates_parameters(self):
        self._load_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Crop Coordinates")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_flat_fielding_parameters(self):
        self._load_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Flat-fielding")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_remove_outliers_parameters(self):
        self._load_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Remove Outliers")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_ROI_normalisation_parameters(self):
        self._load_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("ROI Normalisation")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_arithmetic_parameters(self):
        self._load_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Arithmetic")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_circular_mask_parameters(self):
        self._load_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Circular Mask")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_clip_values_parameters(self):
        self._load_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Clip Values")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_divide_parameters(self):
        self._load_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Divide")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_gaussian_parameters(self):
        self._load_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Gaussian")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_median_parameters(self):
        self._load_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Median")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_monitor_normalisation_parameters(self):
        self._load_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Monitor Normalisation")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_nan_removal_parameters(self):
        self._load_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("NaN Removal")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_rebin_parameters(self):
        self._load_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Rebin")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_rescale_parameters(self):
        self._load_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Rescale")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_ring_removal_parameters(self):
        self._load_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Ring Removal")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_rotate_stack_parameters(self):
        self._load_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Rotate Stack")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_remove_all_stripes_parameters(self):
        self._load_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Remove all stripes")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_remove_dead_stripes_parameters(self):
        self._load_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Remove dead stripes")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_remove_large_stripes_parameters(self):
        self._load_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Remove large stripes")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_stripe_removal_parameters(self):
        self._load_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Stripe Removal")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_remove_stripes_with_filtering_parameters(self):
        self._load_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Remove stripes with filtering")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

    def test_operations_remove_stripes_with_sorting_and_fitting_parameters(self):
        self._load_data_set()

        self.imaging.show_filters_window()
        self.imaging.filters.filterSelector.setCurrentText("Remove stripes with sorting and fitting")
        QApplication.processEvents()

        self.check_target(widget=self.imaging.filters)

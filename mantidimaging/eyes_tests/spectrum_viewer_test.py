# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import numpy as np
from PyQt5.QtWidgets import QApplication
from mantidimaging.core.data.dataset import Dataset
from mantidimaging.test_helpers.qt_test_helpers import wait_until
from mantidimaging.test_helpers.unit_test_helper import generate_images

from mantidimaging.eyes_tests.base_eyes import BaseEyesTest


class SpectrumViewerWindowTest(BaseEyesTest):

    def _generate_spectrum_dataset(self):
        sample_stack = generate_images(seed=2023, shape=(20, 10, 10))
        sample_stack.name = "Sample Stack"
        open_stack = generate_images(seed=666, shape=(20, 10, 10))
        open_stack.name = "Open Beam Stack"
        dataset = Dataset(sample=sample_stack, flat_before=open_stack)
        self.imaging.presenter.model.add_dataset_to_model(dataset)
        QApplication.sendPostedEvents()

    def test_spectrum_viewer_opens_with_data(self):
        self._generate_spectrum_dataset()
        self.imaging.show_spectrum_viewer_window()
        wait_until(lambda: not np.isnan(self.imaging.spectrum_viewer.spectrum_widget.spectrum_data_dict["roi"]).any(),
                   max_retry=600)
        self.check_target(widget=self.imaging.spectrum_viewer)

    def test_spectrum_viewer_opens_with_data_and_normalisation(self):
        self._generate_spectrum_dataset()
        self.imaging.show_spectrum_viewer_window()
        self.imaging.spectrum_viewer.normaliseCheckBox.setChecked(True)
        self.imaging.spectrum_viewer.normaliseStackSelector.try_to_select_relevant_stack("Open Beam Stack")
        wait_until(lambda: not np.isnan(self.imaging.spectrum_viewer.spectrum_widget.spectrum_data_dict["roi"]).any(),
                   max_retry=600)
        self.check_target(widget=self.imaging.spectrum_viewer)

    def test_spectrum_viewer_add_new_roi(self):
        self._generate_spectrum_dataset()
        self.imaging.show_spectrum_viewer_window()
        self.imaging.spectrum_viewer.normaliseCheckBox.setChecked(True)
        self.imaging.spectrum_viewer.normaliseStackSelector.try_to_select_relevant_stack("Open Beam Stack")
        self.imaging.spectrum_viewer.set_new_roi()
        self.imaging.spectrum_viewer.spectrum_widget.roi_dict["roi_1"].setSize((2, 2))
        self.imaging.spectrum_viewer.spectrum_widget.roi_dict["roi_1"].setPos(5, 5)
        wait_until(lambda: not np.isnan(self.imaging.spectrum_viewer.spectrum_widget.spectrum_data_dict["roi_1"]).any(),
                   max_retry=600)
        self.check_target(widget=self.imaging.spectrum_viewer)

    def test_spectrum_viewer_scatter_plot(self):
        self._generate_spectrum_dataset()
        self.imaging.show_spectrum_viewer_window()
        for action in self.imaging.spectrum_viewer.spectrum.spectrum.join_choice_group.actions():
            if action.text() == 'Points':
                action.trigger()
        self.check_target(widget=self.imaging.spectrum_viewer)

    def test_spectrum_viewer_fitting_tab(self):
        self._generate_spectrum_dataset()
        self.imaging.show_spectrum_viewer_window()
        self.imaging.spectrum_viewer.formTabs.setCurrentIndex(1)
        self.check_target(widget=self.imaging.spectrum_viewer)

    def test_spectrum_viewer_export_tab(self):
        self._generate_spectrum_dataset()
        self.imaging.show_spectrum_viewer_window()
        self.imaging.spectrum_viewer.formTabs.setCurrentIndex(2)
        self.check_target(widget=self.imaging.spectrum_viewer)

    def test_spectrum_viewer_initial_fit_from_roi(self):
        self._generate_spectrum_dataset()
        self.imaging.show_spectrum_viewer_window()
        self.imaging.spectrum_viewer.formTabs.setCurrentIndex(1)
        self.imaging.spectrum_viewer.scalable_roi_widget.from_roi_button.click()
        self.check_target(widget=self.imaging.spectrum_viewer)

    def test_spectrum_viewer_run_fit(self):
        self._generate_spectrum_dataset()
        self.imaging.show_spectrum_viewer_window()
        self.imaging.spectrum_viewer.formTabs.setCurrentIndex(1)
        self.imaging.spectrum_viewer.scalable_roi_widget.from_roi_button.click()
        self.imaging.spectrum_viewer.scalable_roi_widget.run_fit_button.click()
        self.check_target(widget=self.imaging.spectrum_viewer)

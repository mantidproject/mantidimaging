# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import numpy as np
from PyQt5.QtWidgets import QApplication

from mantidimaging.eyes_tests.base_eyes import BaseEyesTest
from mantidimaging.test_helpers.unit_test_helper import generate_images
from mantidimaging.core.data.dataset import MixedDataset


class ReconstructionWindowTest(BaseEyesTest):
    def setUp(self):
        super().setUp()

    def tearDown(self):
        self.imaging.recon.close()
        super().tearDown()

    def test_reconstruction_window_opens(self):
        self.imaging.show_recon_window()

        self.check_target(widget=self.imaging.recon)

    def test_reconstruction_window_opens_with_data(self):
        self._load_data_set()

        self.imaging.show_recon_window()

        self.check_target(widget=self.imaging.recon)

    def test_reconstruction_window_cor_and_tilt_tab(self):
        self.imaging.show_recon_window()

        self.imaging.recon.tabWidget.setCurrentWidget(self.imaging.recon.resultsTab)

        self.check_target(widget=self.imaging.recon)

    def test_reconstruction_window_reconstruct_tab(self):
        self.imaging.show_recon_window()

        self.imaging.recon.tabWidget.setCurrentWidget(self.imaging.recon.reconTab)

        self.check_target(widget=self.imaging.recon)

    def test_negative_nan_overlay(self):
        images = generate_images(seed=10)
        images.name = "bad_data"
        ds = MixedDataset([images])
        self.imaging.presenter.model.add_dataset_to_model(ds)
        self.imaging.presenter.create_single_tabbed_images_stack(images)
        QApplication.sendPostedEvents()

        images.data[0:, 7:] = 0
        images.data[0:, 3:4] = -1
        images.data[0:, 0:1] = np.nan

        self.imaging.show_recon_window()
        self.check_target(widget=self.imaging.recon)

    def test_reconstruction_window_colour_palette_dialog(self):
        self._load_data_set()

        self.imaging.show_recon_window()
        self.imaging.recon.image_view.imageview_recon.setImage(np.zeros((512, 512)))
        self.imaging.recon.changeColourPaletteButton.click()

        self.check_target(widget=self.imaging.recon.change_colour_palette_dialog)

# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from unittest import mock

from mantidimaging.eyes_tests.base_eyes import BaseEyesTest


class WelcomeWindowTest(BaseEyesTest):
    def setUp(self):
        super().setUp()

    @mock.patch("mantidimaging.gui.windows.welcome_screen.presenter.versions")
    @mock.patch("mantidimaging.gui.windows.welcome_screen.presenter.cuda_check")
    def test_about_window_good_cuda(self, cuda_check, versions):
        cuda_check.CudaChecker.return_value.cuda_is_present.return_value = True
        versions.get_version.return_value = "version_number"
        versions.get_conda_installed_version.return_value = None
        versions.needs_update.return_value = False

        self.imaging.show_about()

        self.check_target(widget=self.imaging.welcome_window.view)
        cuda_check.CudaChecker.return_value.cuda_is_present.assert_called_once()
        versions.needs_update.assert_called_once()

    @mock.patch("mantidimaging.gui.windows.welcome_screen.presenter.versions")
    @mock.patch("mantidimaging.gui.windows.welcome_screen.presenter.cuda_check")
    def test_about_window_bad_cuda(self, cuda_check, versions):
        cuda_check.CudaChecker.return_value.cuda_is_present.return_value = False
        cuda_check.not_found_message.return_value = ("Bad Cuda", "detailed")
        versions.get_version.return_value = "version_number"
        versions.get_conda_installed_version.return_value = None
        versions.needs_update.return_value = False

        self.imaging.actionAbout.trigger()

        self.check_target(widget=self.imaging.welcome_window.view)
        cuda_check.CudaChecker.return_value.cuda_is_present.assert_called_once()
        versions.needs_update.assert_called_once()

    @mock.patch("mantidimaging.gui.windows.welcome_screen.presenter.versions")
    @mock.patch("mantidimaging.gui.windows.welcome_screen.presenter.cuda_check")
    def test_about_window_good_conda(self, cuda_check, versions):
        versions.needs_update.return_value = False
        versions.get_version.return_value = "version_number"
        versions.get_conda_installed_version.return_value = None

        self.imaging.actionAbout.trigger()

        self.check_target(widget=self.imaging.welcome_window.view)
        cuda_check.CudaChecker.return_value.cuda_is_present.assert_called_once()
        versions.needs_update.assert_called_once()

    @mock.patch("mantidimaging.gui.windows.welcome_screen.presenter.versions")
    @mock.patch("mantidimaging.gui.windows.welcome_screen.presenter.cuda_check")
    def test_about_window_bad_conda(self, cuda_check, versions):
        versions.needs_update.return_value = True
        versions.conda_update_message.return_value = ("Bad Conda", "detailed")
        versions.get_version.return_value = "version_number"
        versions.get_conda_installed_version.return_value = None

        self.imaging.actionAbout.trigger()

        self.check_target(widget=self.imaging.welcome_window.view)
        cuda_check.CudaChecker.return_value.cuda_is_present.assert_called_once()
        versions.needs_update.assert_called_once()

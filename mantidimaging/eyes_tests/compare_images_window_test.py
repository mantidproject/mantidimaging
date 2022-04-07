# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from unittest import mock

from PyQt5.QtWidgets import QDialog
from mantidimaging.test_helpers.unit_test_helper import generate_images

from mantidimaging.eyes_tests.base_eyes import BaseEyesTest


class CompareImagesWindowTest(BaseEyesTest):
    @mock.patch("mantidimaging.gui.windows.main.view.MultipleStackSelect")
    def test_compare_images_window_opens(self, multi_stack_select):
        multi_stack_select.return_value.exec.return_value = QDialog.DialogCode.Accepted
        test_stack = generate_images(seed=2021)
        self.imaging.presenter.get_stack = mock.MagicMock()
        self.imaging.presenter.get_stack.return_value = test_stack

        stack_compare = self.imaging.show_stack_select_dialog()

        self.check_target(widget=stack_compare.view)

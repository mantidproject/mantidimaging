# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from PyQt5.QtWidgets import QApplication

from eyes_tests.base_eyes import BaseEyesTest


class OperationsWindowTest(BaseEyesTest):
    def test_operation_window_opens(self):
        self.imaging.show_filters_window()
        self.check_target(widget=self.imaging.filters)

    def test_operation_window_opens_with_data(self):
        self._load_data_set()

        self.imaging.show_filters_window()
        self.check_target(widget=self.imaging.filters)

    def test_operation_window_after_data_was_processed(self):
        pass

    def test_all_operations_parameters(self):
        pass

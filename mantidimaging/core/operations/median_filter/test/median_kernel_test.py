# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest
from unittest import mock

from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest

from mantidimaging.core.operations.median_filter.median_filter import KernelSpinBox
from mantidimaging.test_helpers import start_qapplication


@start_qapplication
class MedianKernelTest(unittest.TestCase):

    def setUp(self) -> None:
        self.size_kernel = KernelSpinBox(on_change=mock.Mock())

    def test_default_kernel_size(self):
        self.assertEqual(self.size_kernel.value(), 3)

    def test_step_up_increases_size_by_two(self):
        self.size_kernel.stepUp()
        self.assertEqual(self.size_kernel.value(), 5)

    def test_minimum_value_of_three(self):
        self.size_kernel.stepDown()
        self.assertEqual(self.size_kernel.value(), 3)

    def test_maximum_value_of_nine_nine_nine(self):
        self.size_kernel.setValue(999)
        self.size_kernel.stepUp()
        self.assertEqual(self.size_kernel.value(), 999)

    def test_even_numbers_rejected(self):
        for even_num_str in [str(i) for i in range(2, 10, 2)]:
            self.size_kernel.lineEdit().setText(even_num_str)
            self.assertEqual(self.size_kernel.value(), 3)

    def test_odd_kernel_size_with_even_first_digit_is_accepted(self):
        QTest.keyClick(self.size_kernel.lineEdit(), Qt.Key.Key_Delete)  # Clear the line edit
        QTest.keyClicks(self.size_kernel.lineEdit(), "21")
        QTest.keyClick(self.size_kernel.lineEdit(), Qt.Key.Key_Enter)
        self.assertEqual(self.size_kernel.value(), 21)

# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest

from parameterized import parameterized

from mantidimaging.core.utility.sensible_roi import SensibleROI, ROIBinner


class CloseEnoughPoint:

    def __init__(self, x, y):
        self.x = x
        self.y = y


class SensibleROITestCase(unittest.TestCase):

    def test_initialization_default(self):
        roi = SensibleROI()
        self.assertEqual(roi.left, 0)
        self.assertEqual(roi.top, 0)
        self.assertEqual(roi.right, 0)
        self.assertEqual(roi.bottom, 0)

    def test_initialization_custom(self):
        roi = SensibleROI(1, 2, 3, 4)
        self.assertEqual(roi.left, 1)
        self.assertEqual(roi.top, 2)
        self.assertEqual(roi.right, 3)
        self.assertEqual(roi.bottom, 4)

    def test_from_points(self):
        position = CloseEnoughPoint(10, 20)
        size = CloseEnoughPoint(30, 40)
        roi = SensibleROI.from_points(position, size)
        self.assertEqual(roi.left, 10)
        self.assertEqual(roi.top, 20)
        self.assertEqual(roi.right, 40)
        self.assertEqual(roi.bottom, 60)

    def test_from_list(self):
        roi = SensibleROI.from_list([5, 10, 15, 20])
        self.assertEqual(roi.left, 5)
        self.assertEqual(roi.top, 10)
        self.assertEqual(roi.right, 15)
        self.assertEqual(roi.bottom, 20)

    def test_iterable(self):
        roi = SensibleROI(1, 2, 3, 4)
        expected = [1, 2, 3, 4]
        self.assertEqual(list(roi), expected)

    def test_str(self):
        roi = SensibleROI(1, 2, 3, 4)
        self.assertEqual(str(roi), "Left: 1, Top: 2, Right: 3, Bottom: 4")

    def test_to_list_string(self):
        roi = SensibleROI(1, 2, 3, 4)
        self.assertEqual(roi.to_list_string(), "1, 2, 3, 4")

    def test_width(self):
        roi = SensibleROI(1, 2, 4, 6)
        self.assertEqual(roi.width, 3)

    def test_height(self):
        roi = SensibleROI(1, 2, 4, 6)
        self.assertEqual(roi.height, 4)


class ROIBinnerTest(unittest.TestCase):

    def test_get_length(self):
        roi = SensibleROI(1, 10, 15, 20)
        step_size = 1
        bin_size = 1
        binner = ROIBinner(roi, step_size, bin_size)
        self.assertEqual(binner.lengths(), (14, 10))

    @parameterized.expand([
        (4, 1, 4),
        (4, 2, 2),
        (4, 4, 1),
        (5, 2, 3),
        (6, 2, 3),
    ])
    def test_length_step(self, width, step_size, expected_len):
        for start in [0, 1, 10]:
            roi = SensibleROI(start, start, start + width, start + width)
            bin_size = 1
            binner = ROIBinner(roi, step_size, bin_size)
            self.assertEqual(binner.lengths(), (expected_len, expected_len))

    @parameterized.expand([
        (1, 1, 10),
        (2, 2, 5),
        (1, 2, 9),
        (3, 3, 3),
        (3, 4, 3),
    ])
    def test_length_width(self, step_size, bin_size, expected_len):
        width = 10
        for start in [0, 1, 10]:
            roi = SensibleROI(start, start, start + width, start + width)
            binner = ROIBinner(roi, step_size, bin_size)
            self.assertEqual(binner.lengths(), (expected_len, expected_len))

    @parameterized.expand([(0, 0, SensibleROI(1, 2, 4, 5)), (0, 1, SensibleROI(1, 4, 4, 7)),
                           (1, 0, SensibleROI(3, 2, 6, 5))])
    def test_get_sub_roi(self, i, j, sub_roi):
        roi = SensibleROI(1, 2, 15, 20)
        binner = ROIBinner(roi, 2, 3)

        self.assertEqual(binner.get_sub_roi(i, j), sub_roi)

    def test_all_rois(self):
        roi = SensibleROI(100, 200, 120, 225)
        binner = ROIBinner(roi, 4, 5)
        sub_w, sub_h = binner.lengths()
        self.assertEqual((sub_w, sub_h), (4, 6))
        for i in range(sub_w):
            for j in range(sub_h):
                sub_roi = binner.get_sub_roi(i, j)
                self.assertTrue(roi.left <= sub_roi.left <= roi.right)
                self.assertTrue(roi.left <= sub_roi.right <= roi.right)
                self.assertTrue(roi.top <= sub_roi.top <= roi.bottom)
                self.assertTrue(roi.top <= sub_roi.bottom <= roi.bottom)

    def test_WHEN_index_out_of_range_THEN_exception_raised(self):
        binner = ROIBinner(SensibleROI(10, 10, 15, 20), 2, 2)
        self.assertEqual(binner.lengths(), (2, 5))
        self.assertIsInstance(binner.get_sub_roi(0, 0), SensibleROI)
        self.assertIsInstance(binner.get_sub_roi(1, 4), SensibleROI)
        self.assertRaises(IndexError, binner.get_sub_roi, 2, 1)
        self.assertRaises(IndexError, binner.get_sub_roi, 1, 5)

    def test_dont_allow_modification(self):
        binner = ROIBinner(SensibleROI(10, 10, 15, 20), 2, 2)
        with self.assertRaises(AttributeError):
            binner.roi = SensibleROI(1, 1, 2, 2)
        with self.assertRaises(AttributeError):
            binner.step_size = 3
        with self.assertRaises(AttributeError):
            binner.bin_size = 4

    def test_dont_allow_zero_step_size(self):
        with self.assertRaisesRegex(ValueError, "step_size"):
            ROIBinner(SensibleROI(0, 0, 5, 5), 0, 1)

    @parameterized.expand([
        ("larger_than_1", 0, 1, False),  # bin_size < 1
        ("bin_less_than_or_equal_to_step", 1, 2, False),  # bin_size <= step_size
        ("less_than_roi", 9, 10, False),  # bin_size and step_size > min(roi.width, roi.height)
        ("less_than_roi", 10, 9, False),  # bin_size and step_size > min(roi.width, roi.height)
        ("valid", 2, 1, True),  # valid case
    ])
    def test_binner_is_valid(self, _, bin_size, step_size, expect_is_valid):
        binner = ROIBinner(SensibleROI(0, 0, 5, 5), step_size, bin_size)
        is_valid, reason = binner.is_valid()
        self.assertEqual(is_valid, expect_is_valid)


if __name__ == '__main__':
    unittest.main()

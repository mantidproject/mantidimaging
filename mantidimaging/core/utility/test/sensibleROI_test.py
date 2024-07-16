# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest

from mantidimaging.core.utility.sensible_roi import SensibleROI


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


if __name__ == '__main__':
    unittest.main()

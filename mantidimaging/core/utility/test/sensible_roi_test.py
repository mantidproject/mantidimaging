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

    def test_area(self):
        roi = SensibleROI(1, 2, 4, 6)
        self.assertEqual(roi.area, 12)

    def test_overlap(self):
        roi1 = SensibleROI(0, 0, 5, 5)
        roi2 = SensibleROI(3, 3, 7, 7)
        self.assertEqual(roi1.overlap(roi2), 4)
        self.assertEqual(roi2.overlap(roi1), 4)

    def test_no_overlap(self):
        roi1 = SensibleROI(0, 0, 2, 2)
        roi2 = SensibleROI(3, 3, 5, 5)
        self.assertEqual(roi1.overlap(roi2), 0)
        self.assertEqual(roi2.overlap(roi1), 0)

    def test_has_significant_overlap(self):
        roi1 = SensibleROI(0, 0, 10, 10)
        roi2 = SensibleROI(5, 5, 15, 15)
        self.assertTrue(roi1.has_significant_overlap(roi2, threshold=0.2))
        self.assertFalse(roi1.has_significant_overlap(roi2, threshold=0.5))

    def test_intersection(self):
        roi1 = SensibleROI(0, 0, 5, 5)
        roi2 = SensibleROI(3, 3, 7, 7)
        intersection = roi1.intersection(roi2)
        self.assertEqual(intersection.left, 3)
        self.assertEqual(intersection.top, 3)
        self.assertEqual(intersection.right, 5)
        self.assertEqual(intersection.bottom, 5)
        self.assertEqual(intersection.area, 4)

    def test_no_intersection(self):
        roi1 = SensibleROI(0, 0, 2, 2)
        roi2 = SensibleROI(3, 3, 5, 5)
        intersection = roi1.intersection(roi2)
        self.assertEqual(intersection.left, 0)
        self.assertEqual(intersection.top, 0)
        self.assertEqual(intersection.right, 0)
        self.assertEqual(intersection.bottom, 0)
        self.assertEqual(intersection.area, 0)
if __name__ == '__main__':
    unittest.main()

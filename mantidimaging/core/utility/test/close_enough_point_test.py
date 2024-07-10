import unittest

from mantidimaging.core.utility.close_enough_point import CloseEnoughPoint


class TestCloseEnoughPoint(unittest.TestCase):

    def test_with_integers(self):
        point = CloseEnoughPoint([10, 20])
        self.assertEqual(point.x, 10)
        self.assertEqual(point.y, 20)
        self.assertEqual(str(point), "(10, 20)")

    def test_with_floats(self):
        point = CloseEnoughPoint([10.9, 20.1])
        self.assertEqual(point.x, 10)
        self.assertEqual(point.y, 20)
        self.assertEqual(str(point), "(10, 20)")

    def test_with_mixed_types(self):
        point = CloseEnoughPoint([10.5, 20])
        self.assertEqual(point.x, 10)
        self.assertEqual(point.y, 20)
        self.assertEqual(str(point), "(10, 20)")

    def test_with_negative_values(self):
        point = CloseEnoughPoint([-10.5, -20.7])
        self.assertEqual(point.x, -10)
        self.assertEqual(point.y, -20)
        self.assertEqual(str(point), "(-10, -20)")

    def test_with_single_value(self):
        with self.assertRaises(IndexError):
            CloseEnoughPoint([10])

    def test_with_empty_sequence(self):
        with self.assertRaises(IndexError):
            CloseEnoughPoint([])


if __name__ == '__main__':
    unittest.main()

from unittest import TestCase

import numpy as np

from mantidimaging.core.cor_tilt import (
        CorTiltDataModel, Field, FIELD_NAMES)


class CorTiltDataModelTest(TestCase):

    def test_field_defs_sanity(self):
        self.assertEquals(len(Field), len(FIELD_NAMES))

    def test_init(self):
        m = CorTiltDataModel()

        self.assertTrue(m.empty)
        self.assertEquals(m.num_points, 0)
        self.assertEquals(m.slices, [])
        self.assertEquals(m.cors, [])
        self.assertFalse(m.has_results)

    def test_add_points(self):
        m = CorTiltDataModel()
        m.add_point(0)
        m.add_point(0, 20, 5.0)
        m.add_point(1, 60, 7.8)

        self.assertFalse(m.empty)
        self.assertEquals(m.num_points, 3)
        self.assertEquals(m.slices, [20, 60, 0])
        self.assertEquals(m.cors, [5.0, 7.8, 0.0])

    def test_add_points_no_index(self):
        m = CorTiltDataModel()
        m.add_point(None)
        m.add_point(None, 20, 5.0)
        m.add_point(None, 60, 7.8)

        self.assertFalse(m.empty)
        self.assertEquals(m.num_points, 3)
        self.assertEquals(m.slices, [0, 20, 60])
        self.assertEquals(m.cors, [0.0, 5.0, 7.8])

    def test_clear_points(self):
        m = CorTiltDataModel()
        m.add_point(0)
        m.add_point(0, 20, 5.0)
        m.add_point(1, 60, 7.8)
        m.clear_points()

        self.assertTrue(m.empty)
        self.assertEquals(m.num_points, 0)
        self.assertEquals(m.slices, [])
        self.assertEquals(m.cors, [])

    def test_set_point(self):
        m = CorTiltDataModel()
        m.add_point(0)
        m.add_point(0, 20, 5.0)
        m.add_point(1, 60, 7.8)
        m.set_point(0, cor=55.0)
        m.set_point(1, slice_idx=25)

        self.assertEquals(m.slices, [20, 25, 0])
        self.assertEquals(m.cors, [55.0, 7.8, 0.0])

    def test_populate_slice_indices_no_cor(self):
        m = CorTiltDataModel()
        m.populate_slice_indices(300, 400, 20)

        self.assertEquals(m.num_points, 20)
        self.assertEquals(m.point(0)[0], 300)
        self.assertEquals(m.point(19)[0], 400)

        for i in range(20):
            self.assertEquals(m.point(i)[1], 0.0)

    def test_populate_slice_indices_with_cor(self):
        m = CorTiltDataModel()
        m.populate_slice_indices(300, 400, 20, 56.7)

        self.assertEquals(m.num_points, 20)
        self.assertEquals(m.point(0)[0], 300)
        self.assertEquals(m.point(19)[0], 400)

        for i in range(20):
            self.assertEquals(m.point(i)[1], 56.7)

    def test_linear_regression_no_data(self):
        m = CorTiltDataModel()

        with self.assertRaises(ValueError):
            m.linear_regression()

        self.assertFalse(m.has_results)

    def test_linear_regression(self):
        m = CorTiltDataModel()
        m.add_point(None, 0, 5.0)
        m.add_point(None, 10, 6.0)
        m.add_point(None, 20, 7.0)
        m.add_point(None, 30, 8.0)
        m.linear_regression()

        self.assertTrue(m.has_results)
        self.assertAlmostEqual(m.m, 0.1)
        self.assertAlmostEqual(m.c, 5.0)

    def test_linear_regression_data(self):
        m = CorTiltDataModel()
        m._points = [
            [1409, 1401],
            [1386, 1400],
            [1363, 1400],
            [1340, 1401],
            [1317, 1400],
            [1294, 1399],
            [1271, 1398],
            [1248, 1400],
            [1225, 1398],
            [1202, 1400],
            [1179, 1399],
            [1156, 1399],
            [1133, 1400],
            [1110, 1402],
            [1087, 1398],
            [1064, 1398],
            [1041, 1397],
            [1018, 1399],
            [995, 1398],
            [972, 1401],
            [949, 1397],
            [926, 1398],
            [903, 1398],
            [880, 1398],
            [857, 1396],
            [834, 1397]
        ]
        m.linear_regression()

        self.assertAlmostEqual(m.m, 0.005292, places=6)
        self.assertAlmostEqual(m.c, 1392.99, places=2)

    def test_stack_properties(self):
        m = CorTiltDataModel()
        m.add_point(None, 0, 5.0)
        m.add_point(None, 10, 6.0)
        m.add_point(None, 20, 7.0)
        m.add_point(None, 30, 8.0)
        m.linear_regression()

        d = m.stack_properties
        self.assertTrue('auto_cor_tilt' in d)

        d = d['auto_cor_tilt']
        self.assertEqual(len(d), 5)

        self.assertEqual(d['fitted_gradient'], m.m)
        self.assertEqual(d['rotation_centre'], m.c)
        self.assertEqual(d['slice_indices'], m.slices)
        self.assertEqual(d['rotation_centres'], m.cors)
        self.assertTrue(isinstance(d['tilt_angle_rad'], float))

    def test_clear_results(self):
        m = CorTiltDataModel()
        m.add_point(None, 0, 5.0)
        m.add_point(None, 10, 6.0)
        m.add_point(None, 20, 7.0)
        m.add_point(None, 30, 8.0)
        m.linear_regression()

        m.clear_results()

        self.assertFalse(m.has_results)

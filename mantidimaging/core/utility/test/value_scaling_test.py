import unittest

import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.utility import value_scaling


class ValueScalingTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(ValueScalingTest, self).__init__(*args, **kwargs)

        self.alg = value_scaling

    def test_create_factors_no_roi(self):
        data = th.generate_images().data
        expected_factors = [3, 3, 3, 3, 3, 3, 3, 3, 3, 3]

        # make then with increasing values
        for z in range(data.shape[0]):
            for y in range(data.shape[1]):
                data[z, y] = y

        # roi = [4, 4, 8, 8]
        result = self.alg.create_factors(data, cores=1)
        # unittest assert for len which is ints
        self.assertEqual(len(result), data.shape[0])
        # numpy assert for arrays
        npt.assert_equal(expected_factors, result)

    def test_create_factors(self):
        data = th.generate_images().data
        expected_factors = [5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5, 5.5]
        # make then with increasing values
        for z in range(data.shape[0]):
            for y in range(data.shape[1]):
                data[z, y] = y

        roi = [4, 4, 8, 8]
        result = self.alg.create_factors(data, roi, cores=1)
        # unittest assert for len which is ints
        self.assertEqual(len(result), data.shape[0])
        # numpy assert for arrays
        npt.assert_equal(expected_factors, result)

    def test_apply_factors(self):
        data = th.generate_images().data
        data[:] = 2
        roi = [4, 4, 8, 8]
        result = self.alg.create_factors(data, roi, cores=1)
        result = self.alg.apply_factor(data, result, 1)
        npt.assert_equal(data, result)


if __name__ == '__main__':
    unittest.main()

import unittest
from unittest import mock

import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.filters.rotate_stack import RotateFilter
from mantidimaging.core.utility.memory_usage import get_memory_usage_linux


class RotateStackTest(unittest.TestCase):
    """
    Test rotate stack filter.

    Tests return value and in-place modified data.
    """
    def __init__(self, *args, **kwargs):
        super(RotateStackTest, self).__init__(*args, **kwargs)

    def test_executed_par(self):
        self.do_execute()

    def test_executed_seq(self):
        self.do_execute(cores=1)

    def do_execute(self, cores=None):
        # only works on square images
        images = th.generate_images((10, 10, 10))

        rotation = -90
        images.data[:, 0, :] = 42

        result = RotateFilter.filter_func(images, rotation, cores=cores)

        npt.assert_equal(result.data[:, :, -1], 42)

    def test_memory_change_acceptable(self):
        """
        Expected behaviour for the filter is to be done in place
        without using more memory.

        In reality the memory is increased by about 40MB (4 April 2017),
        but this could change in the future.

        The reason why a 10% window is given on the expected size is
        to account for any library imports that may happen.

        This will still capture if the data is doubled, which is the main goal.
        """
        # only works on square images
        images = th.generate_images((10, 10, 10))
        rotation = 1  # once clockwise
        images.data[:, 0, 0] = 42  # set all images at 0,0 to 42

        cached_memory = get_memory_usage_linux(kb=True)[0]

        RotateFilter.filter_func(images, rotation)

        self.assertLess(get_memory_usage_linux(kb=True)[0], cached_memory * 1.1)

    def test_execute_wrapper_return_is_runnable(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        rotation_count = mock.Mock()
        rotation_count.value = mock.Mock(return_value=0)
        execute_func = RotateFilter.execute_wrapper(rotation_count)

        images = th.generate_images()
        execute_func(images)

        self.assertEqual(rotation_count.value.call_count, 1)


if __name__ == '__main__':
    unittest.main()

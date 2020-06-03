import unittest

import numpy as np
import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.filters.ring_removal import RingRemovalFilter
from mantidimaging.core.utility.memory_usage import get_memory_usage_linux


class RingRemovalTest(unittest.TestCase):
    """
    Test ring removal filter.

    Tests return value and in-place modified data.
    """

    def __init__(self, *args, **kwargs):
        super(RingRemovalTest, self).__init__(*args, **kwargs)

    def test_not_executed(self):
        images = th.generate_images_class_random_shared_array()

        # invalid threshold
        run_ring_removal = False

        original = np.copy(images.sample[0])
        result = RingRemovalFilter.filter_func(images, run_ring_removal, cores=1)
        npt.assert_equal(result.sample[0], original)

    def test_memory_change_acceptable(self):
        images, control = th.gen_img_shared_array_and_copy()
        # invalid threshold
        run_ring_removal = False

        cached_memory = get_memory_usage_linux(kb=True)[0]

        result = RingRemovalFilter.filter_func(images, run_ring_removal, cores=1)

        self.assertLess(get_memory_usage_linux(kb=True)[0], cached_memory * 1.1)

        npt.assert_equal(result, control)
        npt.assert_equal(images, control)

        npt.assert_equal(result, images)

    def test_execute_wrapper_return_is_runnable(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        images = th.generate_images_class_random_shared_array()
        RingRemovalFilter.execute_wrapper()(images)


if __name__ == '__main__':
    unittest.main()

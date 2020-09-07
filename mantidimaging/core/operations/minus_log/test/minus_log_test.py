import unittest

import numpy as np
import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.operations.minus_log import MinusLogFilter
from mantidimaging.core.utility.memory_usage import get_memory_usage_linux


class MinusLogTest(unittest.TestCase):
    """
    Test minus log filter.

    Tests return value and in-place modified data.
    """
    def __init__(self, *args, **kwargs):
        super(MinusLogTest, self).__init__(*args, **kwargs)

    def test_no_execute(self):
        images = th.generate_images()

        sample = np.copy(images.data)
        result = MinusLogFilter.filter_func(images, minus_log=False)

        npt.assert_equal(result.data, sample)

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
        images = th.generate_images()

        cached_memory = get_memory_usage_linux(kb=True)[0]
        original = np.copy(images.data)

        result = MinusLogFilter.filter_func(images, minus_log=True)

        self.assertLess(get_memory_usage_linux(kb=True)[0], cached_memory * 1.1)
        th.assert_not_equals(result.data, original)

    def test_execute_wrapper_return_is_runnable(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        images = th.generate_images()
        MinusLogFilter.execute_wrapper()(images)


if __name__ == '__main__':
    unittest.main()

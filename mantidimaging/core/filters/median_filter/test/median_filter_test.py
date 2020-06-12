import unittest
from unittest import mock

import numpy as np

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.filters.median_filter import MedianFilter
from mantidimaging.core.gpu import utility as gpu
from mantidimaging.core.utility.memory_usage import get_memory_usage_linux

GPU_UTIL_LOC = "mantidimaging.core.gpu.utility.gpu_available"


class MedianTest(unittest.TestCase):
    """
    Test median filter.

    Tests return value and in-place modified data.
    """
    def __init__(self, *args, **kwargs):
        super(MedianTest, self).__init__(*args, **kwargs)

    def test_not_executed(self):
        images = th.generate_images_class_random_shared_array()

        size = None
        mode = None

        original = np.copy(images.sample[0])
        result = MedianFilter.filter_func(images, size, mode)

        th.assert_not_equals(result.sample, original)

    def test_executed_no_helper_parallel(self):
        images = th.generate_images_class_random_shared_array()

        size = 3
        mode = 'reflect'

        original = np.copy(images.sample[0])
        result = MedianFilter.filter_func(images, size, mode)

        th.assert_not_equals(result.sample, original)

    @unittest.skipIf(not gpu.gpu_available(), reason="Skip GPU tests if cupy isn't installed")
    def test_executed_no_helper_gpu(self):
        images = th.generate_images_class_random_shared_array()

        size = 3
        mode = 'reflect'

        original = np.copy(images.sample[0])
        result = MedianFilter.filter_func(images, size, mode, force_cpu=False)

        th.assert_not_equals(result.sample, original)

    def test_executed_no_helper_seq(self):
        images = th.generate_images_class_random_shared_array()

        size = 3
        mode = 'reflect'

        original = np.copy(images.sample[0])
        th.switch_mp_off()
        result = MedianFilter.filter_func(images, size, mode)
        th.switch_mp_on()

        th.assert_not_equals(result.sample, original)

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
        images = th.generate_images_class_random_shared_array()
        size = 3
        mode = 'reflect'

        cached_memory = get_memory_usage_linux(kb=True)[0]

        MedianFilter.filter_func(images, size, mode)

        self.assertLess(get_memory_usage_linux(kb=True)[0], cached_memory * 1.1)

    def test_execute_wrapper_return_is_runnable(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        size_field = mock.Mock()
        size_field.value = mock.Mock(return_value=0)
        mode_field = mock.Mock()
        mode_field.currentText = mock.Mock(return_value=0)
        use_gpu_field = mock.Mock()
        use_gpu_field.isChecked = mock.Mock(return_value=False)
        execute_func = MedianFilter.execute_wrapper(size_field, mode_field, use_gpu_field)

        images = th.generate_images_class_random_shared_array()
        execute_func(images)

        self.assertEqual(size_field.value.call_count, 1)
        self.assertEqual(mode_field.currentText.call_count, 1)
        self.assertEqual(use_gpu_field.isChecked.call_count, 1)


if __name__ == '__main__':
    unittest.main()

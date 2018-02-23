import unittest

import numpy.testing as npt

import mantidimaging.core.testing.unit_test_helper as th

from mantidimaging.core.utility.memory_usage import get_memory_usage_linux

from mantidimaging.core.filters import clip_values


class ClipValuesTest(unittest.TestCase):
    """
    Test clip values filter.

    Tests return value and in-place modified data.
    """

    def __init__(self, *args, **kwargs):
        super(ClipValuesTest, self).__init__(*args, **kwargs)

    def test_no_execute(self):
        images, control = th.gen_img_shared_array_and_copy()

        result = clip_values.execute(images)

        npt.assert_equal(result, control)
        npt.assert_equal(images, control)

    def test_execute_min_only(self):
        images, control = th.gen_img_shared_array_and_copy()

        result = clip_values.execute(images,
                                     clip_min=0.2,
                                     clip_max=None,
                                     clip_min_new_value=0.1,
                                     clip_max_new_value=None)

        th.assert_not_equals(result, control)
        th.assert_not_equals(images, control)

        npt.assert_equal(result, images)

        npt.assert_approx_equal(result.min(), 0.1)

    def test_execute_max_only(self):
        images, control = th.gen_img_shared_array_and_copy()

        result = clip_values.execute(images,
                                     clip_min=None,
                                     clip_max=0.8,
                                     clip_min_new_value=None,
                                     clip_max_new_value=0.9)

        th.assert_not_equals(result, control)
        th.assert_not_equals(images, control)

        npt.assert_equal(result, images)

        npt.assert_approx_equal(result.max(), 0.9)

    def test_execute_min_max(self):
        images, control = th.gen_img_shared_array_and_copy()

        result = clip_values.execute(images,
                                     clip_min=0.2,
                                     clip_max=0.8,
                                     clip_min_new_value=0.1,
                                     clip_max_new_value=0.9)

        th.assert_not_equals(result, control)
        th.assert_not_equals(images, control)

        npt.assert_equal(result, images)

        npt.assert_approx_equal(result.min(), 0.1)
        npt.assert_approx_equal(result.max(), 0.9)

    def test_execute_min_max_no_new_values(self):
        images, control = th.gen_img_shared_array_and_copy()

        result = clip_values.execute(images,
                                     clip_min=0.2,
                                     clip_max=0.8,
                                     clip_min_new_value=None,
                                     clip_max_new_value=None)

        th.assert_not_equals(result, control)
        th.assert_not_equals(images, control)

        npt.assert_equal(result, images)

        npt.assert_approx_equal(result.min(), 0.2)
        npt.assert_approx_equal(result.max(), 0.8)

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
        images, control = th.gen_img_shared_array_and_copy()

        cached_memory = get_memory_usage_linux(kb=True)[0]

        result = clip_values.execute(images,
                                     clip_min=0.2,
                                     clip_max=0.8,
                                     clip_min_new_value=0.1,
                                     clip_max_new_value=0.9)

        self.assertLess(
            get_memory_usage_linux(kb=True)[0], cached_memory * 1.1)

        th.assert_not_equals(result, control)
        th.assert_not_equals(images, control)

        npt.assert_equal(result, images)


if __name__ == '__main__':
    unittest.main()

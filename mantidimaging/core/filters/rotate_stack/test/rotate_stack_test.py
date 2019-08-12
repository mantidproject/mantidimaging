import unittest

import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th

from mantidimaging.core.utility.memory_usage import get_memory_usage_linux

from mantidimaging.core.filters import rotate_stack


class RotateStackTest(unittest.TestCase):
    """
    Test rotate stack filter.

    Tests return value and in-place modified data.
    """

    def __init__(self, *args, **kwargs):
        super(RotateStackTest, self).__init__(*args, **kwargs)

    def test_not_executed(self):
        # only works on square images
        images, control = th.gen_img_shared_array_and_copy((10, 10, 10))

        # empty params
        result = rotate_stack.execute(images, None)

        npt.assert_equal(result, control)
        npt.assert_equal(images, control)

    def test_executed_par(self):
        self.do_execute()

    def test_executed_seq(self):
        th.switch_mp_off()
        self.do_execute()
        th.switch_mp_on()

    def do_execute(self):
        # only works on square images
        images, control = th.gen_img_shared_array_and_copy((10, 10, 10))

        rotation = 1  # once clockwise
        images[:, 0, 0] = 42  # set all images at 0,0 to 42

        result = rotate_stack.execute(images, rotation)

        w = result.shape[2]
        npt.assert_equal(result[:, 0, w - 1], 42.0)
        npt.assert_equal(images[:, 0, w - 1], 42.0)

        npt.assert_equal(result, images)

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
        images, control = th.gen_img_shared_array_and_copy((10, 10, 10))
        rotation = 1  # once clockwise
        images[:, 0, 0] = 42  # set all images at 0,0 to 42

        cached_memory = get_memory_usage_linux(kb=True)[0]

        result = rotate_stack.execute(images, rotation)

        w = result.shape[2]

        self.assertLess(
            get_memory_usage_linux(kb=True)[0], cached_memory * 1.1)

        npt.assert_equal(result[:, 0, w - 1], 42.0)
        npt.assert_equal(images[:, 0, w - 1], 42.0)

        npt.assert_equal(result, images)


if __name__ == '__main__':
    unittest.main()

import unittest

import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.filters.crop_coords import CropCoordinatesFilter
from mantidimaging.core.utility.memory_usage import get_memory_usage_linux
from mantidimaging.core.utility.sensible_roi import SensibleROI


class CropCoordsTest(unittest.TestCase):
    """
    Test crop by coordinates filter.

    Tests return value only.
    """

    def __init__(self, *args, **kwargs):
        super(CropCoordsTest, self).__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls) -> None:
        import SharedArray as sa
        for arr in sa.list():
            sa.delete(arr.name.decode("utf-8"))

    def tearDown(self):
        import SharedArray as sa
        assert len(sa.list()) == 0

    def test_executed_only_volume(self):
        # Check that the filter is  executed when:
        #   - valid Region of Interest is provided
        #   - no flat or dark images are provided

        roi = SensibleROI.from_list([1, 1, 5, 5])
        images = th.generate_images(automatic_free=False)
        # store a reference here so it doesn't get freed inside the filter execute
        sample = images.data
        result = CropCoordinatesFilter.filter_func(images, roi)
        expected_shape = (10, 4, 4)

        npt.assert_equal(result.data.shape, expected_shape)
        # check that the data has been modified
        th.assert_not_equals(result.data, sample)
        images.free_memory()

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
        images = th.generate_images(automatic_free=False)
        roi = SensibleROI.from_list([1, 1, 5, 5])

        cached_memory = get_memory_usage_linux(mb=True)[0]

        result = CropCoordinatesFilter.filter_func(images, roi)

        self.assertLess(get_memory_usage_linux(mb=True)[0], cached_memory * 1.1)

        expected_shape = (10, 4, 4)

        npt.assert_equal(result.data.shape, expected_shape)
        result.free_memory()

    def test_execute_wrapper_return_is_runnable(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        images = th.generate_images(automatic_free=False)
        CropCoordinatesFilter.execute_wrapper()(images, [1, 1, 5, 5])
        images.free_memory()


if __name__ == '__main__':
    unittest.main()

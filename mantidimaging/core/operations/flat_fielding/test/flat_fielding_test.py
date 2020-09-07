import unittest
from typing import Tuple
from unittest import mock

import numpy as np
import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.data import Images
from mantidimaging.core.operations.flat_fielding import FlatFieldFilter


class FlatFieldingTest(unittest.TestCase):
    """
    Test background correction filter.

    Tests return value and in-place modified data.
    """
    def __init__(self, *args, **kwargs):
        super(FlatFieldingTest, self).__init__(*args, **kwargs)

    def _make_images(self) -> Tuple[Images, Images, Images]:
        images = th.generate_images()

        flat = th.generate_images()
        dark = th.generate_images()
        return images, flat, dark

    def test_real_result(self):
        # the calculation here was designed on purpose to have a value
        # below the np.clip in flat_fielding
        # the operation is (sample - dark) / (flat - dark)
        images, flat, dark = self._make_images()
        images.data[:] = 26.
        flat.data[:] = 7.
        dark.data[:] = 6.

        expected = np.full(images.data.shape, 20.)

        # we dont want anything to be cropped out
        result = FlatFieldFilter.filter_func(images, flat, dark)

        npt.assert_almost_equal(result.data, expected, 7)

    def test_execute_wrapper_return_is_runnable(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        fake_presenter = mock.MagicMock()
        fake_presenter.presenter.images = th.generate_images()
        flat_widget = mock.Mock()
        flat_widget.main_window.get_stack_visualiser = mock.Mock()
        flat_widget.main_window.get_stack_visualiser.return_value = fake_presenter
        dark_widget = mock.Mock()
        dark_widget.main_window.get_stack_visualiser = mock.Mock()
        dark_widget.main_window.get_stack_visualiser.return_value = fake_presenter
        execute_func = FlatFieldFilter.execute_wrapper(flat_widget, dark_widget)
        images = th.generate_images()
        execute_func(images)


if __name__ == '__main__':
    unittest.main()

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

    def _make_images(self) -> Tuple[Images, Images, Images, Images, Images]:
        images = th.generate_images()
        flat_before = th.generate_images()
        dark_before = th.generate_images()
        flat_after = th.generate_images()
        dark_after = th.generate_images()
        return images, flat_before, dark_before, flat_after, dark_after

    def test_real_result_before_only(self):
        # the calculation here was designed on purpose to have a value
        # below the np.clip in flat_fielding
        # the operation is (sample - dark) / (flat - dark)
        images, flat_before, dark_before, flat_after, dark_after = self._make_images()
        images.data[:] = 26.
        flat_before.data[:] = 7.
        dark_before.data[:] = 6.

        expected = np.full(images.data.shape, 20.)

        # we dont want anything to be cropped out
        result = FlatFieldFilter.filter_func(images, flat_before=flat_before, dark_before=dark_before,
                                             selected_flat_fielding="Only Before")

        npt.assert_almost_equal(result.data, expected, 7)

    def test_real_result_after_only(self):
        images, flat_before, dark_before, flat_after, dark_after = self._make_images()
        images.data[:] = 26.
        flat_after.data[:] = 7.
        dark_after.data[:] = 6.

        expected = np.full(images.data.shape, 20.)

        # we dont want anything to be cropped out
        result = FlatFieldFilter.filter_func(images, flat_after=flat_after, dark_after=dark_after,
                                             selected_flat_fielding="Only After")

        npt.assert_almost_equal(result.data, expected, 7)

    def test_real_result_both_concat(self):
        images, flat_before, dark_before, flat_after, dark_after = self._make_images()
        images.data[:] = 26.

        flat_after.data[:] = 6.
        flat_before.data[:] = 8.
        dark_after.data[:] = 7.
        dark_before.data[:] = 5.

        expected = np.full(images.data.shape, 20.)

        # we dont want anything to be cropped out
        result = FlatFieldFilter.filter_func(images, flat_before=flat_before, dark_before=dark_before,
                                             flat_after=flat_after, dark_after=dark_after,
                                             selected_flat_fielding="Both, concatenated")

        npt.assert_almost_equal(result.data, expected, 7)

    def test_execute_wrapper_return_is_runnable(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        fake_presenter = mock.MagicMock()
        fake_presenter.presenter.images = th.generate_images()
        flat_before_widget = mock.Mock()
        flat_before_widget.main_window.get_stack_visualiser = mock.Mock()
        flat_before_widget.main_window.get_stack_visualiser.return_value = fake_presenter
        flat_after_widget = mock.Mock()
        flat_after_widget.main_window.get_stack_visualiser = mock.Mock()
        flat_after_widget.main_window.get_stack_visualiser.return_value = fake_presenter
        dark_before_widget = mock.Mock()
        dark_before_widget.main_window.get_stack_visualiser = mock.Mock()
        dark_before_widget.main_window.get_stack_visualiser.return_value = fake_presenter
        dark_after_widget = mock.Mock()
        dark_after_widget.main_window.get_stack_visualiser = mock.Mock()
        dark_after_widget.main_window.get_stack_visualiser.return_value = fake_presenter
        selected_flat_fielding_widget = mock.Mock()

        execute_func = FlatFieldFilter.execute_wrapper(flat_before_widget=flat_before_widget,
                                                       flat_after_widget=flat_before_widget,
                                                       dark_before_widget=dark_before_widget,
                                                       dark_after_widget=dark_after_widget,
                                                       selected_flat_fielding_widget=selected_flat_fielding_widget)
        images = th.generate_images()
        execute_func(images)


if __name__ == '__main__':
    unittest.main()

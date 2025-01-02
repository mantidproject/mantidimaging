# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from parameterized import parameterized
import unittest
from typing import TYPE_CHECKING
from unittest import mock

import numpy as np
import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.operations.flat_fielding.flat_fielding import enable_correct_fields_only
from mantidimaging.core.operations.flat_fielding import FlatFieldFilter

if TYPE_CHECKING:
    from mantidimaging.core.data import ImageStack


class FlatFieldingTest(unittest.TestCase):
    """
    Test background correction filter.

    Tests return value and in-place modified data.
    """

    def _make_images(self) -> tuple[ImageStack, ImageStack, ImageStack, ImageStack, ImageStack]:
        images = th.generate_images()
        flat_before = th.generate_images()
        dark_before = th.generate_images()
        flat_after = th.generate_images()
        dark_after = th.generate_images()
        return images, flat_before, dark_before, flat_after, dark_after

    @parameterized.expand([("None", None), ("Invalid", "invalid")])
    def test_raises_exception_for_invalid_method(self, _, method):
        images = th.generate_images()

        self.assertRaises(ValueError, FlatFieldFilter.filter_func, images, selected_flat_fielding=method)

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
        result = FlatFieldFilter.filter_func(images,
                                             flat_before=flat_before,
                                             flat_after=None,
                                             dark_before=dark_before,
                                             dark_after=None,
                                             selected_flat_fielding="Only Before")

        npt.assert_almost_equal(result.data, expected, 7)

    def test_real_result_after_only(self):
        images, flat_before, dark_before, flat_after, dark_after = self._make_images()
        images.data[:] = 26.
        flat_after.data[:] = 7.
        dark_after.data[:] = 6.

        expected = np.full(images.data.shape, 20.)

        # we dont want anything to be cropped out
        result = FlatFieldFilter.filter_func(images,
                                             None,
                                             flat_after=flat_after,
                                             dark_before=None,
                                             dark_after=dark_after,
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
        result = FlatFieldFilter.filter_func(images,
                                             flat_before=flat_before,
                                             flat_after=flat_after,
                                             dark_before=dark_before,
                                             dark_after=dark_after,
                                             selected_flat_fielding="Both, concatenated")

        npt.assert_almost_equal(result.data, expected, 7)

    def test_execute_wrapper_return_is_runnable(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        fake_images = th.generate_images()
        flat_before_widget = mock.Mock()
        flat_before_widget.main_window.get_stack = mock.Mock(return_value=fake_images)
        flat_after_widget = mock.Mock()
        flat_after_widget.main_window.get_stack = mock.Mock(return_value=fake_images)
        dark_before_widget = mock.Mock()
        dark_before_widget.main_window.get_stack = mock.Mock(return_value=fake_images)
        dark_after_widget = mock.Mock()
        dark_after_widget.main_window.get_stack = mock.Mock(return_value=fake_images)
        selected_flat_fielding_widget = mock.Mock()
        selected_flat_fielding_widget.currentText = mock.Mock(return_value="Only Before")
        use_dark_widget = mock.Mock()

        execute_func = FlatFieldFilter.execute_wrapper(flat_before_widget=flat_before_widget,
                                                       flat_after_widget=flat_before_widget,
                                                       dark_before_widget=dark_before_widget,
                                                       dark_after_widget=dark_after_widget,
                                                       selected_flat_fielding_widget=selected_flat_fielding_widget,
                                                       use_dark_widget=use_dark_widget)
        images = th.generate_images()
        execute_func(images)

    def test_enable_correct_fields_only_before(self):
        text = "Only Before"
        flat_before_widget = mock.MagicMock()
        flat_after_widget = mock.MagicMock()
        dark_before_widget = mock.MagicMock()
        dark_after_widget = mock.MagicMock()
        use_dark_frame = mock.MagicMock(isChecked=lambda: True)

        enable_correct_fields_only(mock.Mock(currentText=lambda: text), flat_before_widget, flat_after_widget,
                                   dark_before_widget, dark_after_widget, use_dark_frame)

        flat_before_widget.setEnabled.assert_called_once_with(True)
        flat_after_widget.setEnabled.assert_called_once_with(False)
        dark_before_widget.setEnabled.assert_called_once_with(True)
        dark_after_widget.setEnabled.assert_called_once_with(False)

    def test_enable_correct_fields_only_after(self):
        text = "Only After"
        flat_before_widget = mock.MagicMock()
        flat_after_widget = mock.MagicMock()
        dark_before_widget = mock.MagicMock()
        dark_after_widget = mock.MagicMock()
        use_dark_frame = mock.MagicMock(isChecked=lambda: True)

        enable_correct_fields_only(mock.Mock(currentText=lambda: text), flat_before_widget, flat_after_widget,
                                   dark_before_widget, dark_after_widget, use_dark_frame)

        flat_before_widget.setEnabled.assert_called_once_with(False)
        flat_after_widget.setEnabled.assert_called_once_with(True)
        dark_before_widget.setEnabled.assert_called_once_with(False)
        dark_after_widget.setEnabled.assert_called_once_with(True)

    def test_enable_correct_fields_both(self):
        text = "Both, concatenated"
        flat_before_widget = mock.MagicMock()
        flat_after_widget = mock.MagicMock()
        dark_before_widget = mock.MagicMock()
        dark_after_widget = mock.MagicMock()
        use_dark_frame = mock.MagicMock(isChecked=lambda: True)

        enable_correct_fields_only(mock.Mock(currentText=lambda: text), flat_before_widget, flat_after_widget,
                                   dark_before_widget, dark_after_widget, use_dark_frame)

        flat_before_widget.setEnabled.assert_called_once_with(True)
        flat_after_widget.setEnabled.assert_called_once_with(True)
        dark_before_widget.setEnabled.assert_called_once_with(True)
        dark_after_widget.setEnabled.assert_called_once_with(True)

    def test_enable_correct_fields_runtime_error(self):
        text = "BANANA"
        flat_before_widget = mock.MagicMock()
        flat_after_widget = mock.MagicMock()
        dark_before_widget = mock.MagicMock()
        dark_after_widget = mock.MagicMock()
        use_dark_frame = mock.MagicMock(isChecked=lambda: True)

        with self.assertRaises(RuntimeError):
            enable_correct_fields_only(mock.Mock(currentText=lambda: text), flat_before_widget, flat_after_widget,
                                       dark_before_widget, dark_after_widget, use_dark_frame)

        flat_before_widget.setEnabled.assert_not_called()
        flat_after_widget.setEnabled.assert_not_called()
        dark_before_widget.setEnabled.assert_not_called()
        dark_after_widget.setEnabled.assert_not_called()

    def test_enable_correct_fields_runtime_no_dark(self):
        text = "Both, concatenated"
        flat_before_widget = mock.MagicMock()
        flat_after_widget = mock.MagicMock()
        dark_before_widget = mock.MagicMock()
        dark_after_widget = mock.MagicMock()
        use_dark_frame = mock.MagicMock(isChecked=lambda: False)

        enable_correct_fields_only(mock.Mock(currentText=lambda: text), flat_before_widget, flat_after_widget,
                                   dark_before_widget, dark_after_widget, use_dark_frame)

        flat_before_widget.setEnabled.assert_called_once_with(True)
        flat_after_widget.setEnabled.assert_called_once_with(True)
        dark_before_widget.setEnabled.assert_called_once_with(False)
        dark_after_widget.setEnabled.assert_called_once_with(False)


if __name__ == '__main__':
    unittest.main()

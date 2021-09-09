# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest
from unittest import mock

import numpy as np
from PyQt5.QtWidgets import QSpinBox, QComboBox, QDoubleSpinBox
from mantidimaging.test_helpers import start_qapplication

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.operations.outliers import OutliersFilter
from mantidimaging.core.operations.outliers.outliers import OUTLIERS_BRIGHT


@start_qapplication
class OutliersTest(unittest.TestCase):
    """
    Test outliers filter.

    Tests return value only.
    """
    def __init__(self, *args, **kwargs):
        super(OutliersTest, self).__init__(*args, **kwargs)

    def test_executed(self):
        images = th.generate_images()

        radius = 8
        threshold = 0.1

        sample = np.copy(images.data)
        result = OutliersFilter.filter_func(images, threshold, radius, cores=1)

        th.assert_not_equals(result.data, sample)

    def test_execute_wrapper_return_is_runnable(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        diff_field = mock.Mock()
        diff_field.value = mock.Mock(return_value=0)
        size_field = mock.Mock()
        size_field.value = mock.Mock(return_value=0)
        mode_field = mock.Mock()
        mode_field.currentText = mock.Mock(return_value=OUTLIERS_BRIGHT)
        execute_func = OutliersFilter.execute_wrapper(diff_field, size_field, mode_field)

        images = th.generate_images()
        execute_func(images)

        self.assertEqual(diff_field.value.call_count, 1)
        self.assertEqual(size_field.value.call_count, 1)
        self.assertEqual(mode_field.currentText.call_count, 1)

    def test_register_gui_returns_correct_types(self):
        gui_dict = OutliersFilter.register_gui(mock.MagicMock(), mock.MagicMock(), mock.MagicMock())

        assert (isinstance(gui_dict["diff_field"], QDoubleSpinBox))
        assert (isinstance(gui_dict["size_field"], QSpinBox))
        assert (isinstance(gui_dict["mode_field"], QComboBox))
        # use sets because dictionary order isn't guaranteed in Python 3
        self.assertEqual({'diff_field', 'size_field', 'mode_field'}, set(gui_dict.keys()))

    def test_gui_diff_spin_box_min_is_0(self):
        gui_dict = OutliersFilter.register_gui(mock.MagicMock(), mock.MagicMock(), mock.MagicMock())

        self.assertEqual(0, gui_dict["diff_field"].minimum())

    def test_nan_removal(self):
        images = th.generate_images()
        images.data[::2, 0, 0] = np.nan

        radius = 8
        threshold = 0.1

        result = OutliersFilter.filter_func(images, threshold, radius, cores=1)

        assert not np.any(np.isnan(result.data))


if __name__ == '__main__':
    unittest.main()

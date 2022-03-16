# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from parameterized import parameterized
import unittest
from unittest import mock

import numpy as np
import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.test_helpers.start_qapplication import setup_shared_memory_manager
from mantidimaging.core.operations.rebin import RebinFilter


@setup_shared_memory_manager
class RebinTest(unittest.TestCase):
    """
    Test rebin filter.

    Tests return value only.
    """
    @parameterized.expand([("Zero", 0), ("Negative", -1), ("0,1", (0, 1)), ("1,0", (1, 0)), ("-1,1", (-1, 1)),
                           ("1,-1", (1, -1))])
    def test_exception_raised_for_invalid_rebin_param(self, _, val):
        images = th.generate_images()
        mode = 'reflect'

        npt.assert_raises(ValueError, RebinFilter.filter_func, images, val, mode)

    def test_executed_uniform_par_2(self):
        self.do_execute_uniform(2.0)

    def test_executed_uniform_par_5(self):
        self.do_execute_uniform(5.0)

    def test_executed_uniform_seq_2(self):
        self.do_execute_uniform(2.0)

    def test_executed_uniform_seq_5(self):
        self.do_execute_uniform(5.0)

    def test_executed_uniform_seq_5_int(self):
        self.do_execute_uniform(5.0, np.int32)

    def do_execute_uniform(self, val=2.0, dtype=np.float32):
        images = th.generate_images(dtype=dtype)
        mode = 'reflect'

        expected_x = int(images.data.shape[1] * val)
        expected_y = int(images.data.shape[2] * val)

        result = RebinFilter.filter_func(images, val, mode)

        npt.assert_equal(result.data.shape[1], expected_x)
        npt.assert_equal(result.data.shape[2], expected_y)

        self.assertEqual(images.data.dtype, dtype)
        self.assertEqual(result.data.dtype, dtype)

    def test_executed_xy_par_128_256(self):
        self.do_execute_xy(True, (128, 256))

    def test_executed_xy_par_512_256(self):
        self.do_execute_xy(True, (512, 256))

    def test_executed_xy_seq_128_256(self):
        self.do_execute_xy(False, (128, 256))

    def test_executed_xy_seq_512_256(self):
        self.do_execute_xy(False, (512, 256))

    def do_execute_xy(self, is_parallel: bool, val=(512, 512)):
        if is_parallel:
            images = th.generate_images((15, 8, 10))
        else:
            images = th.generate_images()
        mode = 'reflect'

        expected_x = int(val[0])
        expected_y = int(val[1])

        result = RebinFilter.filter_func(images, rebin_param=val, mode=mode)

        npt.assert_equal(result.data.shape[1], expected_x)
        npt.assert_equal(result.data.shape[2], expected_y)

    def test_failure_to_allocate_output_doesnt_free_input_data(self):
        """
        Tests for a bug fixed in PR#600 that the input data would be freed
        if the output data could not be allocated
        :return:
        """
        images = th.generate_images(shape=(500, 10, 10))
        mode = 'reflect'

        # something very huge that shouldn't fit on ANY computer
        rebin_param = (100000, 100000)
        self.assertRaises(RuntimeError, RebinFilter.filter_func, images, rebin_param=rebin_param, mode=mode)

    def test_execute_wrapper_return_is_runnable(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        rebin_to_dimensions_radio = mock.Mock()
        rebin_to_dimensions_radio.isChecked = mock.Mock(return_value=False)
        rebin_by_factor_radio = mock.Mock()
        rebin_by_factor_radio.isChecked = mock.Mock(return_value=True)
        factor = mock.Mock()
        factor.value = mock.Mock(return_value=0.5)
        mode_field = mock.Mock()
        mode_field.currentText = mock.Mock(return_value='reflect')
        execute_func = RebinFilter.execute_wrapper(rebin_to_dimensions_radio=rebin_to_dimensions_radio,
                                                   rebin_by_factor_radio=rebin_by_factor_radio,
                                                   factor=factor,
                                                   mode_field=mode_field)

        images = th.generate_images()
        execute_func(images)

        self.assertEqual(rebin_to_dimensions_radio.isChecked.call_count, 1)
        self.assertEqual(rebin_by_factor_radio.isChecked.call_count, 1)
        self.assertEqual(factor.value.call_count, 1)
        self.assertEqual(mode_field.currentText.call_count, 1)

    @mock.patch("mantidimaging.core.operations.rebin.rebin.ps")
    def test_execute_argument_order(self, ps_mock):

        images = th.generate_images()
        mode = 'reflect'
        cores = 4
        progress_mock = mock.Mock()
        RebinFilter.filter_func(images=images, mode=mode, cores=cores, progress=progress_mock)

        ps_mock.execute.assert_called_once_with(partial_func=ps_mock.create_partial.return_value,
                                                num_operations=images.data.shape[0],
                                                cores=cores,
                                                msg="Applying Rebin",
                                                progress=progress_mock)


if __name__ == '__main__':
    unittest.main()

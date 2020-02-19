import unittest
from unittest import mock

import numpy as np
import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.filters.rebin import RebinFilter
from mantidimaging.core.utility.memory_usage import get_memory_usage_linux


class RebinTest(unittest.TestCase):
    """
    Test rebin filter.

    Tests return value only.
    """
    def __init__(self, *args, **kwargs):
        super(RebinTest, self).__init__(*args, **kwargs)

    def test_not_executed_rebin_none(self):
        images, control = th.gen_img_shared_array_and_copy()

        val = None
        mode = 'nearest'

        result = RebinFilter.filter_func(images, val, mode)

        npt.assert_equal(result, control)
        npt.assert_equal(images, control)

    def test_not_executed_rebin_negative(self):
        images, control = th.gen_img_shared_array_and_copy()

        mode = 'nearest'
        val = -1

        result = RebinFilter.filter_func(images, val, mode)

        npt.assert_equal(result, control)
        npt.assert_equal(images, control)

    def test_not_executed_rebin_zero(self):
        images, control = th.gen_img_shared_array_and_copy()

        mode = 'nearest'
        val = 0

        result = RebinFilter.filter_func(images, val, mode)

        npt.assert_equal(result, control)
        npt.assert_equal(images, control)

    def test_executed_uniform_par_2(self):
        self.do_execute_uniform(2.0)

    def test_executed_uniform_par_5(self):
        self.do_execute_uniform(5.0)

    def test_executed_uniform_seq_2(self):
        th.switch_mp_off()
        self.do_execute_uniform(2.0)
        th.switch_mp_on()

    def test_executed_uniform_seq_5(self):
        th.switch_mp_off()
        self.do_execute_uniform(5.0)
        th.switch_mp_on()

    def test_executed_uniform_seq_5_int(self):
        th.switch_mp_off()
        self.do_execute_uniform(5.0, np.int32)
        th.switch_mp_on()

    def do_execute_uniform(self, val=2.0, dtype=np.float32):
        images = th.gen_img_shared_array(dtype=dtype)
        mode = 'nearest'

        expected_x = int(images.shape[1] * val)
        expected_y = int(images.shape[2] * val)

        result = RebinFilter.filter_func(images, val, mode)

        npt.assert_equal(result.shape[1], expected_x)
        npt.assert_equal(result.shape[2], expected_y)

        self.assertEquals(images.dtype, dtype)
        self.assertEquals(result.dtype, dtype)

        # TODO: in-place data test
        # npt.assert_equal(images.shape[1], expected_x)
        # npt.assert_equal(images.shape[2], expected_y)

    def test_executed_xy_par_128_256(self):
        self.do_execute_xy((128, 256))

    def test_executed_xy_par_512_256(self):
        self.do_execute_xy((512, 256))

    def test_executed_xy_par_1024_1024(self):
        self.do_execute_xy((1024, 1024))

    def test_executed_xy_seq_128_256(self):
        th.switch_mp_off()
        self.do_execute_xy((128, 256))
        th.switch_mp_on()

    def test_executed_xy_seq_512_256(self):
        th.switch_mp_off()
        self.do_execute_xy((512, 256))
        th.switch_mp_on()

    def test_executed_xy_seq_1024_1024(self):
        th.switch_mp_off()
        self.do_execute_xy((1024, 1024))
        th.switch_mp_on()

    def do_execute_xy(self, val=(512, 512)):
        images = th.gen_img_shared_array()
        mode = 'nearest'

        expected_x = int(val[0])
        expected_y = int(val[1])

        result = RebinFilter.filter_func(images, rebin_param=val, mode=mode)

        npt.assert_equal(result.shape[1], expected_x)
        npt.assert_equal(result.shape[2], expected_y)

        # TODO: in-place data test
        # npt.assert_equal(images.shape[1], expected_x)
        # npt.assert_equal(images.shape[2], expected_y)

    def test_memory_change_acceptable(self):
        """
        This filter will increase the memory usage as it has to allocate memory
        for the new resized shape
        """
        images = th.gen_img_shared_array()

        mode = 'nearest'
        # This about doubles the memory. Value found from running the test
        val = 100.

        expected_x = int(images.shape[1] * val)
        expected_y = int(images.shape[2] * val)

        cached_memory = get_memory_usage_linux(kb=True)[0]

        result = RebinFilter.filter_func(images, val, mode)

        self.assertLess(get_memory_usage_linux(kb=True)[0], cached_memory * 2)

        npt.assert_equal(result.shape[1], expected_x)
        npt.assert_equal(result.shape[2], expected_y)

        # TODO: in-place data test
        # npt.assert_equal(images.shape[1], expected_x)
        # npt.assert_equal(images.shape[2], expected_y)

    def test_execute_wrapper_return_is_runnable(self):
        """
        Test that the partial returned by execute_wrapper can be executed (kwargs are named correctly)
        """
        rebin_to_dimensions_radio = mock.Mock()
        rebin_to_dimensions_radio.isChecked = mock.Mock(return_value=False)
        rebin_by_factor_radio = mock.Mock()
        rebin_by_factor_radio.isChecked = mock.Mock(return_value=True)
        factor = mock.Mock()
        factor.value = mock.Mock(return_value=0)
        mode_field = mock.Mock()
        mode_field.currentText = mock.Mock(return_value=0)
        execute_func = RebinFilter.execute_wrapper(rebin_to_dimensions_radio=rebin_to_dimensions_radio,
                                                   rebin_by_factor_radio=rebin_by_factor_radio,
                                                   factor=factor,
                                                   mode_field=mode_field)

        images, _ = th.gen_img_shared_array_and_copy()
        execute_func(images)

        self.assertEqual(rebin_to_dimensions_radio.isChecked.call_count, 1)
        self.assertEqual(rebin_by_factor_radio.isChecked.call_count, 1)
        self.assertEqual(factor.value.call_count, 1)
        self.assertEqual(mode_field.currentText.call_count, 1)


if __name__ == '__main__':
    unittest.main()

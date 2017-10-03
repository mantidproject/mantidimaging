from __future__ import absolute_import, division, print_function

import unittest

import numpy.testing as npt

from mantidimaging import helper as h
from mantidimaging.tests import test_helper as th

from mantidimaging.core.filters import stripe_removal


class StripeRemovalTest(unittest.TestCase):
    """
    Test stripe removal filter.

    Tests return value and in-place modified data.
    """

    def __init__(self, *args, **kwargs):
        super(StripeRemovalTest, self).__init__(*args, **kwargs)

    def test_not_executed(self):
        images, control = th.gen_img_shared_array_and_copy()

        wf = None
        ti = None
        sf = None

        result = stripe_removal.execute(images, wf, ti, sf)

        npt.assert_equal(result, control)
        npt.assert_equal(images, control)

    def test_executed_wf(self):
        images, control = th.gen_img_shared_array_and_copy()

        wf = ["level=1"]
        ti = None
        sf = None

        result = stripe_removal.execute(images, wf, ti, sf)

        th.assert_not_equals(result, control)
        th.assert_not_equals(images, control)

        npt.assert_equal(result, images)

    def test_executed_wf_dict(self):
        images, control = th.gen_img_shared_array_and_copy()

        wf = {"level": 1}
        ti = None
        sf = None
        result = stripe_removal.execute(images, wf, ti, sf)
        th.assert_not_equals(result, control)

    def test_executed_ti(self):
        images, control = th.gen_img_shared_array_and_copy()

        wf = None
        ti = ['nblock=2']
        sf = None

        result = stripe_removal.execute(images, wf, ti, sf)

        th.assert_not_equals(result, control)
        th.assert_not_equals(images, control)

        npt.assert_equal(result, images)

    def test_executed_ti_dict(self):
        images, control = th.gen_img_shared_array_and_copy()

        wf = None
        ti = {"nblock": 2}
        sf = None
        result = stripe_removal.execute(images, wf, ti, sf)
        th.assert_not_equals(result, control)

    def test_executed_sf(self):
        images, control = th.gen_img_shared_array_and_copy()

        wf = None
        ti = None
        sf = ['size=5']

        result = stripe_removal.execute(images, wf, ti, sf)

        th.assert_not_equals(result, control)
        th.assert_not_equals(images, control)

        npt.assert_equal(result, images)

    def test_executed_sf_dict(self):
        images, control = th.gen_img_shared_array_and_copy()

        wf = None
        ti = None
        sf = {"size": 5}
        result = stripe_removal.execute(images, wf, ti, sf)
        th.assert_not_equals(result, control)

    def test_memory_executed_wf(self):
        images, control = th.gen_img_shared_array_and_copy()

        wf = ["level=1"]
        ti = None
        sf = None

        cached_memory = h.get_memory_usage_linux(kb=True)[0]

        result = stripe_removal.execute(images, wf, ti, sf)

        self.assertLess(
            h.get_memory_usage_linux(kb=True)[0], cached_memory * 1.1)

        th.assert_not_equals(result, control)
        th.assert_not_equals(images, control)

        npt.assert_equal(result, images)

    def test_memory_executed_ti(self):
        images, control = th.gen_img_shared_array_and_copy()

        wf = None
        ti = ['nblock=2']
        sf = None

        cached_memory = h.get_memory_usage_linux(kb=True)[0]

        result = stripe_removal.execute(images, wf, ti, sf)

        self.assertLess(
            h.get_memory_usage_linux(kb=True)[0], cached_memory * 1.1)

        th.assert_not_equals(result, control)
        th.assert_not_equals(images, control)

        npt.assert_equal(result, images)

    def test_memory_executed_sf(self):
        images, control = th.gen_img_shared_array_and_copy()

        wf = None
        ti = None
        sf = ['size=5']

        cached_memory = h.get_memory_usage_linux(kb=True)[0]

        result = stripe_removal.execute(images, wf, ti, sf)

        self.assertLess(
            h.get_memory_usage_linux(kb=True)[0], cached_memory * 1.1)

        th.assert_not_equals(result, control)
        th.assert_not_equals(images, control)

        npt.assert_equal(result, images)


if __name__ == '__main__':
    unittest.main()

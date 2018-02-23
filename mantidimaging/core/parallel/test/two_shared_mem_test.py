import unittest

import numpy.testing as npt

import mantidimaging.core.testing.unit_test_helper as th

from mantidimaging.core.utility.memory_usage import get_memory_usage_linux

from mantidimaging.core.parallel import two_shared_mem as ptsm


def add_inplace(first_shared, second_shared, add_arg):
    # it's not the same as
    # first_shared[:] += second_shared + add_arg
    # as then the check fails versus the expected one
    first_shared[:] = first_shared + second_shared + add_arg


def return_from_func(first_shared, second_shared, add_arg):
    return first_shared[:] + second_shared[:] + add_arg


class TwoSharedMemTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TwoSharedMemTest, self).__init__(*args, **kwargs)

    def test_fwd_func_inplace(self):
        # create data as shared array
        img = th.gen_img_shared_array()
        img2nd, orig_2nd = th.gen_img_shared_array_and_copy()

        # make sure it hasnt changed the original array
        expected = img + img2nd + 5
        assert expected[0, 0, 0] != img[0, 0, 0]
        assert expected[1, 0, 0] != img[1, 0, 0]
        assert expected[0, 4, 0] != img[0, 4, 0]
        assert expected[6, 0, 1] != img[6, 0, 1]

        # create partial
        f = ptsm.create_partial(
            add_inplace, fwd_function=ptsm.inplace, add_arg=5)

        # execute parallel
        ptsm.execute(img, img2nd, f, name="Inplace test")

        # compare results
        npt.assert_equal(img, expected)
        npt.assert_equal(img2nd, orig_2nd)

    def test_fwd_func_second_2d(self):
        # create data as shared array
        img = th.gen_img_shared_array()
        img2nd, orig_2nd = th.gen_img_shared_array_and_copy()

        img2nd = img2nd[0]

        # make sure it hasnt changed the original array
        expected = img + img2nd + 5
        assert expected[0, 0, 0] != img[0, 0, 0]
        assert expected[1, 0, 0] != img[1, 0, 0]
        assert expected[0, 4, 0] != img[0, 4, 0]
        assert expected[6, 0, 1] != img[6, 0, 1]

        # create partial
        f = ptsm.create_partial(
            add_inplace, fwd_function=ptsm.inplace_second_2d, add_arg=5)

        # execute parallel
        ptsm.execute(img, img2nd, f, name="Second 2D test")

        # compare results
        npt.assert_equal(img, expected)
        npt.assert_equal(img2nd, orig_2nd[0])

    def test_return_to_first(self):
        # create data as shared array
        img = th.gen_img_shared_array()
        img2nd, orig_2nd = th.gen_img_shared_array_and_copy()

        # make sure it hasnt changed the original array
        expected = img + img2nd + 5
        assert expected[0, 0, 0] != img[0, 0, 0]
        assert expected[1, 0, 0] != img[1, 0, 0]
        assert expected[0, 4, 0] != img[0, 4, 0]
        assert expected[6, 0, 1] != img[6, 0, 1]

        # create partial
        f = ptsm.create_partial(
            return_from_func, fwd_function=ptsm.return_to_first, add_arg=5)

        # execute parallel
        res1, res2 = ptsm.execute(img, img2nd, f, name="Return to first test")

        # compare results
        npt.assert_equal(res1, expected)
        npt.assert_equal(res2, orig_2nd)

    def test_return_to_second(self):
        # create data as shared array
        img, orig_img = th.gen_img_shared_array_and_copy()
        img2nd = th.gen_img_shared_array()

        # make sure it hasnt changed the original array
        expected = img + img2nd + 5
        assert expected[0, 0, 0] != img[0, 0, 0]
        assert expected[1, 0, 0] != img[1, 0, 0]
        assert expected[0, 4, 0] != img[0, 4, 0]
        assert expected[6, 0, 1] != img[6, 0, 1]

        # create partial
        f = ptsm.create_partial(
            return_from_func, fwd_function=ptsm.return_to_second, add_arg=5)

        # execute parallel
        res1, res2 = ptsm.execute(img, img2nd, f, name="Return to second test")

        # compare results
        npt.assert_equal(res2, expected)
        npt.assert_equal(res1, orig_img)

# ------------------------- FAIL CASES -----------------------

    def test_fail_with_normal_array_fwd_func_inplace(self):
        # create data as normal nd array
        img = th.gen_img_numpy_rand()
        orig_img = th.deepcopy(img)
        img2nd = th.gen_img_numpy_rand()
        orig_img2nd = th.deepcopy(img2nd)

        # get the expected as usual
        expected = img + img2nd

        # make sure it hasnt changed the original array
        assert expected[0, 0, 0] != img[0, 0, 0]
        assert expected[1, 0, 0] != img[1, 0, 0]
        assert expected[0, 4, 0] != img[0, 4, 0]
        assert expected[6, 0, 1] != img[6, 0, 1]

        # create partial
        f = ptsm.create_partial(add_inplace, add_arg=5)

        # execute parallel
        ptsm.execute(img, img2nd, f, name="Fail Inplace test")

        # compare results
        th.assert_not_equals(img, expected)
        th.assert_not_equals(img2nd, expected)
        npt.assert_equal(img, orig_img)
        npt.assert_equal(img2nd, orig_img2nd)

    def test_fail_with_normal_array_fwd_func_second_2d(self):
        # create data as normal nd array
        img = th.gen_img_numpy_rand()
        orig_img = th.deepcopy(img)
        img2nd = th.gen_img_numpy_rand()
        orig_img2nd = th.deepcopy(img2nd)

        img2nd = img2nd[0]

        # get the expected as usual
        expected = img + img2nd

        # make sure it hasnt changed the original array
        assert expected[0, 0, 0] != img[0, 0, 0]
        assert expected[1, 0, 0] != img[1, 0, 0]
        assert expected[0, 4, 0] != img[0, 4, 0]
        assert expected[6, 0, 1] != img[6, 0, 1]

        # create partial
        f = ptsm.create_partial(
            add_inplace, fwd_function=ptsm.inplace_second_2d, add_arg=5)

        # execute parallel
        ptsm.execute(img, img2nd, f, name="Fail Second 2D test")

        # compare results
        th.assert_not_equals(img, expected)
        th.assert_not_equals(img2nd, expected)
        npt.assert_equal(img, orig_img)
        npt.assert_equal(img2nd, orig_img2nd[0])

    def test_fail_with_normal_array_return_to_first(self):
        # create data as normal nd array
        img = th.gen_img_numpy_rand()
        img2nd = th.gen_img_numpy_rand()

        # get the expected as usual
        expected = img + img2nd

        # make sure it hasnt changed the original array
        assert expected[0, 0, 0] != img[0, 0, 0]
        assert expected[1, 0, 0] != img[1, 0, 0]
        assert expected[0, 4, 0] != img[0, 4, 0]
        assert expected[6, 0, 1] != img[6, 0, 1]

        # create partial
        f = ptsm.create_partial(
            return_from_func, fwd_function=ptsm.return_to_first, add_arg=5)

        # execute parallel
        res1, res2 = ptsm.execute(
            img, img2nd, f, name="Fail Return to first test")

        # compare results
        npt.assert_equal(res1, img)
        npt.assert_equal(res2, img2nd)
        th.assert_not_equals(res1, expected)

    def test_fail_with_normal_array_return_to_second(self):
        """
        This test does not use shared arrays and will not change the data.
        This behaviour is intended and is
        """
        # create data as normal nd array
        img = th.gen_img_numpy_rand()
        img2nd = th.gen_img_numpy_rand()

        # get the expected as usual
        expected = img + img2nd

        # make sure it hasnt changed the original array
        assert expected[0, 0, 0] != img[0, 0, 0]
        assert expected[1, 0, 0] != img[1, 0, 0]
        assert expected[0, 4, 0] != img[0, 4, 0]
        assert expected[6, 0, 1] != img[6, 0, 1]

        # create partial
        f = ptsm.create_partial(
            return_from_func, fwd_function=ptsm.return_to_second, add_arg=5)

        # execute parallel
        res1, res2 = ptsm.execute(
            img, img2nd, f, name="Fail Return to second test")

        # compare results
        npt.assert_equal(res1, img)
        npt.assert_equal(res2, img2nd)
        th.assert_not_equals(res2, expected)

# ------------------------- MEMORY TESTS -----------------------

    def test_memory_fwd_func_inplace(self):
        # create data as shared array
        img = th.gen_img_shared_array()
        img2nd, orig_2nd = th.gen_img_shared_array_and_copy()

        # make sure it hasnt changed the original array
        expected = img + img2nd + 5
        assert expected[0, 0, 0] != img[0, 0, 0]
        assert expected[1, 0, 0] != img[1, 0, 0]
        assert expected[0, 4, 0] != img[0, 4, 0]
        assert expected[6, 0, 1] != img[6, 0, 1]

        # create partial
        f = ptsm.create_partial(
            add_inplace, fwd_function=ptsm.inplace, add_arg=5)

        cached_memory = get_memory_usage_linux(kb=True)[0]
        # execute parallel
        ptsm.execute(img, img2nd, f, name="Inplace test")
        self.assertLess(
            get_memory_usage_linux(kb=True)[0], cached_memory * 1.1)
        # compare results
        npt.assert_equal(img, expected)
        npt.assert_equal(img2nd, orig_2nd)

    def test_memory_fwd_func_second_2d(self):
        # create data as shared array
        img = th.gen_img_shared_array()
        img2nd, orig_2nd = th.gen_img_shared_array_and_copy()

        img2nd = img2nd[0]

        # make sure it hasnt changed the original array
        expected = img + img2nd + 5
        assert expected[0, 0, 0] != img[0, 0, 0]
        assert expected[1, 0, 0] != img[1, 0, 0]
        assert expected[0, 4, 0] != img[0, 4, 0]
        assert expected[6, 0, 1] != img[6, 0, 1]

        # create partial
        f = ptsm.create_partial(
            add_inplace, fwd_function=ptsm.inplace_second_2d, add_arg=5)

        # execute parallel
        cached_memory = get_memory_usage_linux(kb=True)[0]
        ptsm.execute(img, img2nd, f, name="Second 2D test")
        self.assertLess(
            get_memory_usage_linux(kb=True)[0], cached_memory * 1.1)
        # compare results
        npt.assert_equal(img, expected)
        npt.assert_equal(img2nd, orig_2nd[0])

    def test_memory_return_to_first(self):
        # create data as shared array
        img = th.gen_img_shared_array()
        img2nd, orig_2nd = th.gen_img_shared_array_and_copy()

        # make sure it hasnt changed the original array
        expected = img + img2nd + 5
        assert expected[0, 0, 0] != img[0, 0, 0]
        assert expected[1, 0, 0] != img[1, 0, 0]
        assert expected[0, 4, 0] != img[0, 4, 0]
        assert expected[6, 0, 1] != img[6, 0, 1]

        # create partial
        f = ptsm.create_partial(
            return_from_func, fwd_function=ptsm.return_to_first, add_arg=5)

        # execute parallel
        cached_memory = get_memory_usage_linux(kb=True)[0]
        res1, res2 = ptsm.execute(img, img2nd, f, name="Return to first test")
        self.assertLess(
            get_memory_usage_linux(kb=True)[0], cached_memory * 1.1)
        # compare results
        npt.assert_equal(res1, expected)
        npt.assert_equal(res2, orig_2nd)

    def test_memory_return_to_second(self):
        # create data as shared array
        img, orig_img = th.gen_img_shared_array_and_copy()
        img2nd = th.gen_img_shared_array()

        # make sure it hasnt changed the original array
        expected = img + img2nd + 5
        assert expected[0, 0, 0] != img[0, 0, 0]
        assert expected[1, 0, 0] != img[1, 0, 0]
        assert expected[0, 4, 0] != img[0, 4, 0]
        assert expected[6, 0, 1] != img[6, 0, 1]

        # create partial
        f = ptsm.create_partial(
            return_from_func, fwd_function=ptsm.return_to_second, add_arg=5)

        # execute parallel
        cached_memory = get_memory_usage_linux(kb=True)[0]
        res1, res2 = ptsm.execute(img, img2nd, f, name="Return to second test")
        self.assertLess(
            get_memory_usage_linux(kb=True)[0], cached_memory * 1.1)
        # compare results
        npt.assert_equal(res2, expected)
        npt.assert_equal(res1, orig_img)


if __name__ == '__main__':
    unittest.main()

import unittest

import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.parallel import shared_mem as psm
from mantidimaging.core.utility.memory_usage import get_memory_usage_linux


def add_inplace(first_shared, add_arg=3):
    first_shared[:] += add_arg


def return_from_func(first_shared, add_arg):
    return first_shared[:] + add_arg


class SharedMemTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(SharedMemTest, self).__init__(*args, **kwargs)

    def test_fwd_func_inplace(self):
        # create data as shared array
        img, _ = th.gen_img_shared_array_and_copy()
        add_arg = 5

        expected = img + add_arg
        assert expected[0, 0, 0] != img[0, 0, 0]
        assert expected[1, 0, 0] != img[1, 0, 0]
        assert expected[0, 4, 0] != img[0, 4, 0]
        assert expected[6, 0, 1] != img[6, 0, 1]

        # create partial
        f = psm.create_partial(add_inplace, fwd_func=psm.inplace, add_arg=add_arg)

        # execute parallel
        img = psm.execute(img, f, name="Inplace test")

        # compare results
        npt.assert_equal(img, expected)

    def test_fwd_func(self):
        # create data as shared array
        img, _ = th.gen_img_shared_array_and_copy()
        add_arg = 5

        expected = img + add_arg
        assert expected[0, 0, 0] != img[0, 0, 0]
        assert expected[1, 0, 0] != img[1, 0, 0]
        assert expected[0, 4, 0] != img[0, 4, 0]
        assert expected[6, 0, 1] != img[6, 0, 1]

        # create partial
        f = psm.create_partial(return_from_func, fwd_func=psm.return_fwd_func, add_arg=add_arg)

        # execute parallel
        img = psm.execute(img, f, name="Fwd func test")

        # compare results
        npt.assert_equal(img, expected)

    def test_fail_with_normal_array_fwd_func_inplace(self):
        # create data as normal nd array
        img = th.gen_img_numpy_rand()
        orig = th.deepcopy(img)
        add_arg = 5

        expected = img + add_arg

        assert expected[0, 0, 0] != img[0, 0, 0]
        assert expected[1, 0, 0] != img[1, 0, 0]
        assert expected[0, 4, 0] != img[0, 4, 0]
        assert expected[6, 0, 1] != img[6, 0, 1]

        # create partial
        f = psm.create_partial(add_inplace, fwd_func=psm.inplace, add_arg=add_arg)

        # execute parallel
        res = psm.execute(img, f, name="Fail Inplace test")

        # compare results
        th.assert_not_equals(res, expected)
        npt.assert_equal(img, orig)

    def test_fail_with_normal_array_fwd_func(self):
        # create data as shared array
        img = th.gen_img_numpy_rand()
        orig = th.deepcopy(img)
        add_arg = 5

        expected = img + add_arg
        assert expected[0, 0, 0] != img[0, 0, 0]
        assert expected[1, 0, 0] != img[1, 0, 0]
        assert expected[0, 4, 0] != img[0, 4, 0]
        assert expected[6, 0, 1] != img[6, 0, 1]

        # create partial
        f = psm.create_partial(return_from_func, fwd_func=psm.return_fwd_func, add_arg=add_arg)

        # execute parallel
        res = psm.execute(img, f, name="Fwd func test")

        # compare results
        th.assert_not_equals(res, expected)
        npt.assert_equal(img, orig)

    def test_memory_fwd_func_inplace(self):
        # create data as shared array
        img, _ = th.gen_img_shared_array_and_copy()
        add_arg = 5

        expected = img + add_arg
        assert expected[0, 0, 0] != img[0, 0, 0]
        assert expected[1, 0, 0] != img[1, 0, 0]
        assert expected[0, 4, 0] != img[0, 4, 0]
        assert expected[6, 0, 1] != img[6, 0, 1]

        # create partial
        f = psm.create_partial(add_inplace, fwd_func=psm.inplace, add_arg=add_arg)

        cached_memory = get_memory_usage_linux(kb=True)[0]
        # execute parallel
        img = psm.execute(img, f, name="Inplace test")

        self.assertLess(get_memory_usage_linux(kb=True)[0], cached_memory * 1.1)

        # compare results
        npt.assert_equal(img, expected)

    def test_memory_fwd_func(self):
        """
        Expected behaviour for the filter is to be done in place
        without using more memory.
        In reality the memory is increased by about 40MB (4 April 2017),
        but this could change in the future.
        The reason why a 10% window is given on the expected size is
        to account for any library imports that may happen.
        This will still capture if the data is doubled, which is the main goal.
        """
        # create data as shared array
        img, _ = th.gen_img_shared_array_and_copy()
        add_arg = 5

        expected = img + add_arg
        assert expected[0, 0, 0] != img[0, 0, 0]
        assert expected[1, 0, 0] != img[1, 0, 0]
        assert expected[0, 4, 0] != img[0, 4, 0]
        assert expected[6, 0, 1] != img[6, 0, 1]

        # create partial
        f = psm.create_partial(return_from_func, fwd_func=psm.return_fwd_func, add_arg=add_arg)

        cached_memory = get_memory_usage_linux(kb=True)[0]
        # execute parallel
        img = psm.execute(img, f, name="Fwd func test")
        self.assertLess(get_memory_usage_linux(kb=True)[0], cached_memory * 1.1)

        # compare results
        npt.assert_equal(img, expected)


if __name__ == '__main__':
    unittest.main()

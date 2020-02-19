import unittest

import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th

from mantidimaging.core.utility.memory_usage import get_memory_usage_linux

from mantidimaging.core.parallel import exclusive_mem as esm


def return_from_func(first_shared, add_arg):
    return first_shared[:] + add_arg


class ExclusiveMemTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(ExclusiveMemTest, self).__init__(*args, **kwargs)

    def test_exec(self):
        # create data as shared array
        img = th.gen_img_numpy_rand()
        add_arg = 5

        expected = img + add_arg
        assert expected[0, 0, 0] != img[0, 0, 0]
        assert expected[1, 0, 0] != img[1, 0, 0]
        assert expected[0, 4, 0] != img[0, 4, 0]
        assert expected[6, 0, 1] != img[6, 0, 1]

        f = esm.create_partial(return_from_func, add_arg=add_arg)
        img = esm.execute(img, f, name="Exclusive mem test")
        npt.assert_equal(img, expected)

    def test_memory_change_acceptable(self):
        img = th.gen_img_numpy_rand()
        add_arg = 5
        expected = img + add_arg

        f = esm.create_partial(return_from_func, add_arg=add_arg)

        cached_memory = get_memory_usage_linux(kb=True)[0]

        img = esm.execute(img, f, name="Exclusive mem test")

        self.assertLess(get_memory_usage_linux(kb=True)[0], cached_memory * 1.1)

        npt.assert_equal(img, expected)


if __name__ == '__main__':
    unittest.main()

from __future__ import absolute_import, division, print_function

import unittest

import numpy.testing as npt

from isis_imaging.tests import test_helper as th


class TestClass(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestClass, self).__init__(*args, **kwargs)

    def test_system_aggregate(self):
        # use unit test code with different data?
        # create config
        # use aggregate on system input data
        # assert files exist with proper names and format
        # load back
        # assert the values are the same as expected data
        self.fail()

    def test_system_imopr_cor(self):
        # TODO add recon slices
        # change cor to return a list of cors
        # compare to hard coded values
        self.fail()

    def test_system_imopr_corwrite(self):
        self.fail()

    def test_system_recon(self):
        self.fail()


if __name__ == '__main__':
    unittest.main()

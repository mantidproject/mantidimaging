from __future__ import (absolute_import, division, print_function)
import unittest
import numpy.testing as npt
from mantidimaging.tests import test_helper as th


class TestClass(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestClass, self).__init__(*args, **kwargs)


if __name__ == '__main__':
    unittest.main()

from __future__ import absolute_import, division, print_function

import unittest

from mantidimaging.core.io import loader


class LoaderTest(unittest.TestCase):

    def test_raise_on_invalid_format(self):
        self.assertRaises(ValueError, loader.load, "/some/path",
                          file_names=["/somefile"], in_format='txt')

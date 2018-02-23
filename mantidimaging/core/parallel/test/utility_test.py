from __future__ import absolute_import, division, print_function

import unittest

import numpy as np
from hazelnut import MemInfo

from mantidimaging.core.parallel import utility as pu


class UtilityTest(unittest.TestCase):

    def test_shared_memory_is_freed(self):
        mapped_before = MemInfo().get('Mapped')

        a = pu.create_shared_array((10, 1024, 1024), np.float32)
        del a

        mapped_after = MemInfo().get('Mapped')

        self.assertLess(mapped_after, mapped_before + 1024)

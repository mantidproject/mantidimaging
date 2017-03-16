from __future__ import (absolute_import, division, print_function)
import unittest
import numpy.testing as npt
from tests import test_helper as th


class TestClass(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestClass, self).__init__(*args, **kwargs)

        # force silent outputs
        from configs.recon_config import ReconstructionConfig
        self.config = ReconstructionConfig.empty_init()
        self.config.func.verbosity = 0

    def test_sample(self):
        pass


if __name__ == '__main__':
    unittest.main()

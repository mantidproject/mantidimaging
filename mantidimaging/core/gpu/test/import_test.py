import sys
import unittest
from unittest import mock


class GPUImportTest(unittest.TestCase):

    def test_gpu_available_returns_false_when_cupy_cant_be_loaded(self):

        sys.modules["cupy"] = None
        from mantidimaging.core.gpu import utility as gpu
        assert not gpu.gpu_available()


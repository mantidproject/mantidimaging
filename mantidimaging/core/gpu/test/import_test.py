import sys
import unittest


class GPUImportTest(unittest.TestCase):
    @unittest.skip("Cupy seems to load successfuly regardless")
    def test_gpu_available_returns_false_when_cupy_cant_be_loaded(self):

        sys.modules["cupy"] = None
        from mantidimaging.core.gpu import utility
        assert not utility.gpu_available()

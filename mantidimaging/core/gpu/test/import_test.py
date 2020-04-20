import sys
import unittest

from unittest import mock


class GPUImportTest(unittest.TestCase):
    @unittest.skip("Cupy seems to load successfuly regardless")
    def test_gpu_available_returns_false_when_cupy_cant_be_loaded(self):

        sys.modules["cupy"] = None
        from mantidimaging.core.gpu import utility
        assert not utility.gpu_available()

    def test_gpu_available_returns_false_when_cupy_isnt_installed_properly(self):

        import cupy
        with mock.patch("mantidimaging.core.gpu.utility.cp.core.core.ndarray.__mul__",
                        side_effect=cupy.cuda.compiler.CompileException):
            from mantidimaging.core.gpu import utility
            assert not utility.gpu_available()

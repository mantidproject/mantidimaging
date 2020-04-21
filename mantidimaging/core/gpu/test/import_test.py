import unittest

from unittest import mock


class GPUImportTest(unittest.TestCase):
    def test_gpu_available_returns_false_when_cupy_cant_be_loaded(self):

        with mock.patch.dict("sys.modules", cupy=None):
            from mantidimaging.core.gpu import utility
            assert not utility.gpu_available()

    def test_gpu_available_returns_false_when_cupy_isnt_installed_properly(self):

        import cupy
        with mock.patch("cupy.add", side_effect=cupy.cuda.compiler.CompileException("", "", "", None)):
            from mantidimaging.core.gpu import utility
            assert not utility.gpu_available()

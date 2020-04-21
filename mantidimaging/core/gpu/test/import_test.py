import unittest

from unittest import mock


class GPUImportTest(unittest.TestCase):
    @unittest.Skip("I don't know how to mock a failed import.")
    def test_gpu_available_returns_false_when_cupy_cant_be_loaded(self):

        with mock.patch("mantidimaging.core.gpu.utility.cp", side_effect=ModuleNotFoundError):
            from mantidimaging.core.gpu import utility
            assert not utility.gpu_available()

    def test_gpu_available_returns_false_when_cupy_isnt_installed_properly(self):

        import cupy
        with mock.patch("cupy.add", side_effect=cupy.cuda.compiler.CompileException("", "", "", None)):
            from mantidimaging.core.gpu import utility
            assert not utility.gpu_available()

# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest

from unittest import mock

from mantidimaging.core.gpu import utility as gpu

GPU_NOT_AVAIL = not gpu.gpu_available()


class GPUImportTest(unittest.TestCase):
    @unittest.skip("I don't know how to mock a failed import.")
    def test_gpu_available_returns_false_when_cupy_cant_be_loaded(self):
        """
        Test that the GPU utility reports the GPU is not available if cupy isn't installed.
        """
        with mock.patch("mantidimaging.core.gpu.utility.cp", side_effect=ModuleNotFoundError):
            from mantidimaging.core.gpu import utility
            assert not utility.gpu_available()

    @unittest.skipIf(GPU_NOT_AVAIL, reason="Can't run GPU tests without cupy installed.")
    def test_gpu_available_returns_false_when_cupy_isnt_installed_properly(self):
        """
        Test that the GPU utility reports the GPU is not available if cupy is installed but not set up properly.
        """
        import cupy
        with mock.patch("cupy.add", side_effect=cupy.cuda.compiler.CompileException("", "", "", None)):
            from mantidimaging.core.gpu import utility
            assert not utility.gpu_available()

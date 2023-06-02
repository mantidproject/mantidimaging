# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import unittest
from unittest import mock
from unittest.mock import patch

from mantidimaging.core.utility import cuda_check


class TestCudaChecker(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cuda_check.CudaChecker.clear_instance()
        cls.cuda_check_patch = mock.patch("mantidimaging.core.utility.cuda_check._cuda_is_present")
        cls.cuda_is_present_mock = cls.cuda_check_patch.start()

    @classmethod
    def tearDownClass(cls):
        cls.cuda_check_patch.stop()
        cuda_check.CudaChecker.clear_instance()

    def test_cuda_checker_object_created_once(self):
        cuda_checkers = [cuda_check.CudaChecker() for _ in range(2)]
        assert cuda_checkers[0] is cuda_checkers[1]
        self.cuda_is_present_mock.assert_called_once()

    def test_cuda_checker_returns_cuda_is_present(self):
        assert cuda_check.CudaChecker().cuda_is_present() == self.cuda_is_present_mock.return_value


class TestCudaCheckHelpers(unittest.TestCase):

    @patch("mantidimaging.core.utility.cuda_check._import_cupy")
    def test_cuda_is_present_returns_true(self, _import_cupy_mock):
        _import_cupy_mock.return_value = None
        assert cuda_check._cuda_is_present()

    @patch("mantidimaging.core.utility.cuda_check._import_cupy")
    def test_cuda_is_present_returns_false_no_cupy(self, _import_cupy_mock):
        _import_cupy_mock.side_effect = ModuleNotFoundError
        cupy_import_error = 'CuPy not installed'

        with self.assertLogs(cuda_check.__name__, level='ERROR') as cuda_check_log:
            assert not cuda_check._cuda_is_present()
        self.assertIn(cupy_import_error, cuda_check_log.output[0])

    @patch("mantidimaging.core.utility.cuda_check._import_cupy")
    def test_cuda_is_present_returns_false_no_CUDA(self, _import_cupy_mock):
        _import_cupy_mock.side_effect = ImportError
        cupy_import_error = 'CuPy installed, but unable to load CUDA'

        with self.assertLogs(cuda_check.__name__, level='ERROR') as cuda_check_log:
            assert not cuda_check._cuda_is_present()
        self.assertIn(cupy_import_error, cuda_check_log.output[0])

    def test_not_found_message(self):
        short_msg, long_msg = cuda_check.not_found_message()
        assert short_msg == "Working CUDA installation not found."
        assert long_msg == "Working CUDA installation not found. Will only use gridrec algorithm for reconstruction."

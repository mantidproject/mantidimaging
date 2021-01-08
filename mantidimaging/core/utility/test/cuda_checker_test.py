# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import unittest
from unittest import mock

from mantidimaging.core.utility import cuda_check


class TestCudaChecker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cuda_check_patch = mock.patch("mantidimaging.core.utility.cuda_check._cuda_is_present")
        cls.cuda_is_present_mock = cls.cuda_check_patch.start()

    @classmethod
    def tearDownClass(cls):
        cls.cuda_check_patch.stop()

    def test_cuda_checker_object_created_once(self):
        cuda_checkers = [cuda_check.CudaChecker() for _ in range(2)]
        assert cuda_checkers[0] is cuda_checkers[1]
        self.cuda_is_present_mock.assert_called_once()

    def test_cuda_checker_returns_cuda_is_present(self):
        assert cuda_check.CudaChecker().cuda_is_present() == self.cuda_is_present_mock.return_value

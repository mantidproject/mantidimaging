# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import unittest
from unittest.mock import Mock, patch

from mantidimaging.core.utility import cuda_check


class TestCudaCheck(unittest.TestCase):
    def test_cuda_is_present(self):
        with patch("mantidimaging.core.utility.cuda_check.os") as os_mock:
            os_mock.popen.return_value.read = Mock(side_effect=["Driver Version", "/path/to/libcuda.so"])
            assert cuda_check.cuda_is_present()

            os_mock.popen.return_value.read = Mock(side_effect=["command not found: nvidia-smi", "/path/to/libcuda.so"])
            assert not cuda_check.cuda_is_present()

            os_mock.popen.return_value.read = Mock(side_effect=["Driver Version", ""])
            assert not cuda_check.cuda_is_present()

    def test_not_found_message(self):
        pass

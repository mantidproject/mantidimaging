# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import subprocess
import unittest
from unittest.mock import patch

from mantidimaging.core.utility import cuda_check


class TestCudaCheck(unittest.TestCase):
    @patch("mantidimaging.core.utility.cuda_check.subprocess.check_output")
    def test_cuda_is_present_returns_true(self, check_output_mock):
        check_output_mock.side_effect = [b"Driver Version", b"/usr/lib/path/to/libcuda.so\n"]
        assert cuda_check.cuda_is_present()

    @patch("mantidimaging.core.utility.cuda_check.subprocess.check_output")
    def test_cuda_is_present_returns_false(self, check_output_mock):
        check_output_mock.side_effect = [
            b"NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA "
            b"driver. Make sure that the latest NVIDIA driver is installed and "
            b"running.\n", b"/path/to/libcuda.so\n"
        ]
        assert not cuda_check.cuda_is_present()

    @patch("mantidimaging.core.utility.cuda_check.subprocess.check_output")
    def test_cuda_is_present_returns_false_when_subprocess_raises_exception(self, check_output_mock):
        check_output_mock.side_effect = PermissionError
        assert not cuda_check.cuda_is_present()

        check_output_mock.side_effect = subprocess.CalledProcessError(returncode=2, cmd=["bad"])
        assert not cuda_check.cuda_is_present()

    def test_not_found_message(self):
        short_msg, long_msg = cuda_check.not_found_message()
        assert short_msg == "Working CUDA installation not found."
        assert long_msg == "Working CUDA installation not found. Will only use gridrec algorithm for reconstruction."

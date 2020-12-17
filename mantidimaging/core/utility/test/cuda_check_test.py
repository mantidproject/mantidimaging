# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import unittest
from unittest.mock import patch

from mantidimaging.core.utility import cuda_check
from mantidimaging.core.utility.cuda_check import NVIDIA_SMI, EXCEPTION_MSG, LOCATE


class TestCudaCheck(unittest.TestCase):
    @patch("mantidimaging.core.utility.cuda_check.subprocess.check_output")
    def test_cuda_is_present_returns_true(self, check_output_mock):
        check_output_mock.side_effect = [b"Driver Version", b"/usr/lib/path/to/libcuda.so\n"]
        assert cuda_check.cuda_is_present()

    @patch("mantidimaging.core.utility.cuda_check.LOG")
    @patch("mantidimaging.core.utility.cuda_check.subprocess.check_output")
    def test_cuda_is_present_returns_false(self, check_output_mock, log_mock):
        nvidia_error = "NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver. Make sure that " \
                       "the latest NVIDIA driver is installed and running.\n "
        check_output_mock.side_effect = [str.encode(nvidia_error), b"/path/to/libcuda.so\n"]
        assert not cuda_check.cuda_is_present()
        log_mock.error.assert_called_once_with(nvidia_error)

    @patch("mantidimaging.core.utility.cuda_check.LOG")
    @patch("mantidimaging.core.utility.cuda_check.subprocess.check_output")
    def test_failed_libcuda_search_is_logged(self, check_output_mock, log_mock):
        check_output_mock.side_effect = [b"Driver Version", b""]
        assert not cuda_check.cuda_is_present()
        log_mock.error.assert_called_once_with("Search for libcuda files returned no results.")

    @patch("mantidimaging.core.utility.cuda_check.LOG")
    @patch("mantidimaging.core.utility.cuda_check.subprocess.check_output")
    def test_cuda_is_present_returns_false_when_subprocess_raises_exception(self, check_output_mock, log_mock):
        check_output_mock.side_effect = PermissionError
        assert not cuda_check.cuda_is_present()

        check_output_mock.side_effect = FileNotFoundError
        assert not cuda_check.cuda_is_present()

        nvidia_exception_msg = f"{EXCEPTION_MSG} {NVIDIA_SMI}"
        locate_exception_msg = f"{EXCEPTION_MSG} {LOCATE}"

        assert nvidia_exception_msg in log_mock.error.call_args_list[0][0][0]
        assert locate_exception_msg in log_mock.error.call_args_list[1][0][0]
        assert nvidia_exception_msg in log_mock.error.call_args_list[2][0][0]
        assert locate_exception_msg in log_mock.error.call_args_list[3][0][0]

    def test_not_found_message(self):
        short_msg, long_msg = cuda_check.not_found_message()
        assert short_msg == "Working CUDA installation not found."
        assert long_msg == "Working CUDA installation not found. Will only use gridrec algorithm for reconstruction."

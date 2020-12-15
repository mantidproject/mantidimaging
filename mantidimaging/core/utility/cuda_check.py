# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import subprocess
from typing import Tuple, List


def _read_from_terminal(command_args: List[str]) -> str:
    """
    Runs a terminal command and returns the result.
    """
    return subprocess.check_output(command_args).decode("ascii")


def cuda_is_present() -> bool:
    """
    Checks if nvidia-smi is on the system + working, and that the libcuda file can be located.
    """
    try:
        return "Driver Version" in _read_from_terminal(
            ["nvidia-smi"]) and _read_from_terminal(["locate", "--regex", "'^/usr/(lib|lib64)/(.*?)/libcuda.so'"]) != ""
    except (subprocess.CalledProcessError, PermissionError, FileNotFoundError):
        return False


def not_found_message() -> Tuple[str, str]:
    """
    Generates a message that can be displayed if a working CUDA installation isn't found.
    """
    cuda_not_found_msg = "Working CUDA installation not found."
    return cuda_not_found_msg, cuda_not_found_msg + " Will only use gridrec algorithm for reconstruction.",

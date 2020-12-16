# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import subprocess
from logging import getLogger
from typing import Tuple, List

LOG = getLogger(__name__)


def _read_from_terminal(command_args: List[str]) -> str:
    """
    Runs a terminal command and returns the result.
    """
    try:
        return subprocess.check_output(command_args, shell=True).decode("ascii")
    except subprocess.CalledProcessError:
        LOG.error(f"{command_args[0]} doesn't appear to be installed on your system.")
        return ""


def cuda_is_present() -> bool:
    """
    Checks if nvidia-smi is on the system + working, and that the libcuda file can be located.
    """
    nvidia_smi_working = libcuda_files_found = True
    try:

        nvidia_smi_output = _read_from_terminal(["nvidia-smi"])
        if "Driver Version" not in nvidia_smi_output:
            nvidia_smi_working = False
            LOG.error(nvidia_smi_output)

        locate_libcuda_output = _read_from_terminal(["locate", "--regex", "'^/usr/(lib|lib64)/(.*?)/libcuda.so'"])
        if locate_libcuda_output == "":
            libcuda_files_found = False
            LOG.error("Search for libcuda files returned no results.")

        return nvidia_smi_working and libcuda_files_found

    except (PermissionError, FileNotFoundError) as e:
        LOG.info(e)
        return False


def not_found_message() -> Tuple[str, str]:
    """
    Generates a message that can be displayed if a working CUDA installation isn't found.
    """
    cuda_not_found_msg = "Working CUDA installation not found."
    return cuda_not_found_msg, cuda_not_found_msg + " Will only use gridrec algorithm for reconstruction.",

# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import subprocess
from logging import getLogger
from typing import Tuple

LOG = getLogger(__name__)


def _read_from_terminal(command: str) -> str:
    """
    Runs a terminal command and returns the result.
    """
    try:
        return subprocess.check_output(command, shell=True).decode("ascii")
    except subprocess.CalledProcessError:
        LOG.error(f"{command.split()[0]} doesn't appear to be installed on your system.")
        return ""


def cuda_is_present() -> bool:
    """
    Checks if nvidia-smi is on the system + working, and that the libcuda files can be located.
    """
    nvidia_smi_working = libcuda_files_found = True
    try:
        nvidia_smi_output = _read_from_terminal("nvidia-smi")
        if "Driver Version" not in nvidia_smi_output:
            nvidia_smi_working = False
            LOG.error(nvidia_smi_output)

    except (PermissionError, FileNotFoundError) as e:
        LOG.error(f"Error when attempting to run nvidia-smi: {e}")
        nvidia_smi_working = False

    try:
        if _read_from_terminal("locate --regex '^/usr/(lib|lib64)/(.*?)/libcuda.so'") == "":
            libcuda_files_found = False
            LOG.error("Search for libcuda files returned no results.")

    except (PermissionError, FileNotFoundError) as e:
        LOG.error(f"Error when attempting to run locate: {e}")
        libcuda_files_found = False

    return nvidia_smi_working and libcuda_files_found


def not_found_message() -> Tuple[str, str]:
    """
    Generates a message that can be displayed if a working CUDA installation isn't found.
    """
    cuda_not_found_msg = "Working CUDA installation not found."
    return cuda_not_found_msg, cuda_not_found_msg + " Will only use gridrec algorithm for reconstruction.",

# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import subprocess
from logging import getLogger
from typing import Tuple

LOG = getLogger(__name__)

NVIDIA_SMI = "nvidia-smi"
LOCATE = "locate"
EXCEPTION_MSG = "Error when attempting to run"


def _read_from_terminal(command: str) -> str:
    """
    Runs a terminal command and returns the output.
    """
    return subprocess.check_output(command + "; exit 0", shell=True, stderr=subprocess.STDOUT).decode("ascii")


def _cuda_is_present() -> bool:
    """
    Checks if nvidia-smi is on the system + working, and that the libcuda files can be located.
    """
    nvidia_smi_working = libcuda_files_found = True
    try:
        nvidia_smi_output = _read_from_terminal(NVIDIA_SMI)
        if "Driver Version" not in nvidia_smi_output:
            nvidia_smi_working = False
            LOG.error(nvidia_smi_output)

    except Exception as e:
        LOG.error(f"{EXCEPTION_MSG} {NVIDIA_SMI}: {e}")
        nvidia_smi_working = False

    try:
        if _read_from_terminal(f"{LOCATE} --regex '^/usr/(lib|lib64)/(.*?)/libcuda.so'") == "":
            libcuda_files_found = False
            LOG.error("Search for libcuda files returned no results.")

    except Exception as e:
        LOG.error(f"{EXCEPTION_MSG} {LOCATE}: {e}")
        libcuda_files_found = False

    return nvidia_smi_working and libcuda_files_found


def not_found_message() -> Tuple[str, str]:
    """
    Generates a message that can be displayed if a working CUDA installation isn't found.
    """
    cuda_not_found_msg = "Working CUDA installation not found."
    return cuda_not_found_msg, cuda_not_found_msg + " Will only use gridrec algorithm for reconstruction.",


class CudaChecker:
    _instance = None
    _cuda_is_present = False

    def __new__(cls):
        """
        Creates a singleton for storing the result of the Cuda check.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._cuda_is_present = _cuda_is_present()
        return cls._instance

    @classmethod
    def cuda_is_present(cls) -> bool:
        """
        Returns the shared cuda check result.
        """
        return cls._cuda_is_present

    @classmethod
    def clear_instance(cls):
        """
        Resets the instance. Used for making sure mocks don't leak in tests.
        """
        cls._instance = None

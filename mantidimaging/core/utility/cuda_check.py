# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import os


def cuda_is_present() -> bool:
    """
    Checks if nvidia-smi is on the system + working, and that the libcuda file can be located.
    """
    return "Driver Version" in os.popen("nvidia-smi").read() and os.popen("locate libcuda.so").read() != ""


def not_found_message() -> str:
    """
    Generates a message that can be displayed if a working CUDA installation isn't found.
    """
    return "Working CUDA installation not found. Will only use gridrec algorithm for reconstruction. Check " \
           "troubleshooting page for assistance. "

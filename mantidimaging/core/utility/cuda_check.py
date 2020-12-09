# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import os
from typing import Tuple


def cuda_is_present() -> bool:
    """
    Checks if nvidia-smi is on the system + working, and that the libcuda file can be located.
    """
    return "Driver Version" in os.popen("nvidia-smi").read() and os.popen("locate libcuda.so").read() != ""


def not_found_message() -> Tuple[str, str]:
    """
    Generates a message that can be displayed if a working CUDA installation isn't found.
    """
    cuda_not_found_msg = "Working CUDA installation not found."
    return cuda_not_found_msg, cuda_not_found_msg + " Will only use gridrec algorithm for reconstruction.",

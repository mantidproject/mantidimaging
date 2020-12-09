# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import os


def is_cuda_present():
    """
    Checks if nvidia-smi is on the system + working, and that the libcuda file can be located.
    """
    return "Driver Version" in os.popen("nvidia-smi").read() and os.popen("locate libcuda.so").read() != ""

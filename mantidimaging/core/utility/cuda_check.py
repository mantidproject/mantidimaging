import os


def check_cuda():
    """
    Checks if nvidia-smi is on the system + working, and that the libcuda file can be located.
    """
    return "Driver Version" in os.popen("nvidia-smi").read() and os.popen("locate libcuda.so").read() is not ""

# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

# Percent memory of the system total to AVOID being allocated by Mantid Imaging shared arrays.
# Our Linux installation steps request 90% of RAM for shared memory and taking up nearly all of that makes it more
# likely to get hit by SIGBUS by the OS. Even if the allocation is permitted, it could slow the
# system down to the point of being unusable
MEMORY_CAP_PERCENTAGE = 0.125


def system_free_memory():

    class Value:

        def __init__(self, bytes):
            self._bytes = bytes

        def kb(self):
            return self._bytes / 1024

        def mb(self):
            return self._bytes / 1024 / 1024

    import psutil

    meminfo = psutil.virtual_memory()
    return Value(meminfo.available - meminfo.total * MEMORY_CAP_PERCENTAGE)


def get_memory_usage_linux() -> float:
    """
    Get the memory usage of the system in bytes
    """
    import psutil

    meminfo = psutil.virtual_memory()
    # meminfo.used gives the size in bytes
    return meminfo.used


def get_memory_usage_linux_str():
    memory_in_kbs = get_memory_usage_linux() / 1024
    memory_in_mbs = memory_in_kbs / 1024
    # handle caching
    memory_string = f"{memory_in_kbs} KB, {memory_in_mbs} MB"

    # use an attribute to this function only, instead a global variable visible
    # outside
    if not hasattr(get_memory_usage_linux_str, 'last_memory_cache'):
        get_memory_usage_linux_str.last_memory_cache = memory_in_kbs
    else:
        # get memory difference in Megabytes
        delta_memory = (
                               memory_in_kbs - get_memory_usage_linux_str.last_memory_cache) \
                       / 1024

        # remove cached memory, del removes the reference so that hasattr will
        # work correctly
        del get_memory_usage_linux_str.last_memory_cache
        memory_string += f". Memory change: {delta_memory} MB"

    return memory_string

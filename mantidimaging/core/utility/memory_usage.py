# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from logging import getLogger

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


def get_memory_usage_linux(kb=False, mb=False):
    """
    :param kb: Return the value in Kilobytes
    :param mb: Return the value in Megabytes
    """
    import psutil

    meminfo = psutil.virtual_memory()
    tuple_to_return = ()  # start with empty tuple
    # meminfo.used gives the size in bytes
    if kb:
        tuple_to_return += (meminfo.used / 1024, )

    if mb:
        tuple_to_return += (meminfo.used / 1024 / 1024, )
    return tuple_to_return


def get_memory_usage_linux_str():
    memory_in_kbs, memory_in_mbs = get_memory_usage_linux(kb=True, mb=True)
    # handle caching
    memory_string = "{0} KB, {1} MB".format(memory_in_kbs, memory_in_mbs)

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
        memory_string += ". Memory change: {0} MB".format(delta_memory)

    return memory_string


def debug_log_memory_usage_linux(message=""):
    try:
        # Windows doesn't seem to have resource package, so this will
        # silently fail
        import resource as res
        log = getLogger(__name__)
        log.info("Memory usage {} KB, {} MB".format(
            res.getrusage(res.RUSAGE_SELF).ru_maxrss,
            int(res.getrusage(res.RUSAGE_SELF).ru_maxrss) / 1024))
        log.info(message)
    except ImportError:
        log.warning('Resource monitoring is not available on Windows')

from logging import getLogger


def get_memory_usage_linux(kb=False, mb=False):
    """
    :param kb: Return the value in Kilobytes
    :param mb: Return the value in Megabytes
    """
    log = getLogger(__name__)

    try:
        # Windows doesn't seem to have resource package, so this will
        # silently fail
        import resource as res
    except ImportError:
        log.warning('Resource monitoring is not available on Windows')

    tuple_to_return = tuple()  # start with empty tuple
    if kb:
        tuple_to_return += (int(res.getrusage(res.RUSAGE_SELF).ru_maxrss),)

    if mb:
        tuple_to_return += (int(res.getrusage(res.RUSAGE_SELF).ru_maxrss) /
                            1024,)
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

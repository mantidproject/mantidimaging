import os


def find_package(module, core_package='isis_imaging'):
    """
    Find the internal ISIS_IMAGING package for the specified module
    :param module: The module whose package we're looking for
    :param core_package: The core package within which we're looking
    """
    s = os.path.dirname(os.path.realpath(module))
    return s[s.find(core_package):]

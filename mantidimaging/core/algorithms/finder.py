from __future__ import (absolute_import, division, print_function)

import os

ROOT_PACKAGE = 'mantidimaging'


def get_external_location(module_file, root_package=ROOT_PACKAGE):
    """
    Find the external ISIS_IMAGING location for the whole package
    :param module_file: The module whose package we're looking for
    :param root_package: The top level package of mantidimaging
    """
    s = os.path.dirname(os.path.realpath(module_file))
    return s[:s.rfind(root_package)]


def get_package(module_file, root_package=ROOT_PACKAGE):
    """
    Find the internal ISIS_IMAGING package for the specified module
    :param module_file: The module whose package we're looking for
    :param root_package: The core package within which the module is expected to be
    """
    s = os.path.dirname(os.path.realpath(module_file))
    internal_core_package = s.find(root_package) + len(root_package) + 1
    return s[internal_core_package:]


def all_modules(package, root_package=ROOT_PACKAGE):
    """
    This function will build the path to the specified package, and then import all of the modules from it,
    and call _cli_register if _cli is specified, or _gui_register if _gui is specified.

    :param package: The internal package from which modules will be imported
    :param root_package: The directory where the ISIS Imaging package is installed.
    """
    # sys path 0 will give us the parent directory of the package, and we
    # append the internal package location
    root_package = os.path.join(root_package, package)

    all_files = os.walk(root_package)

    # replace the / with . to match python package syntax
    for root, dirs, files in all_files:
        # specify the checks to remove specific files
        checks = [
            lambda x: '.py' in x,  # removes all files that DON'T have .py in the name
            lambda x: '.pyc' not in x,  # removes all files that DO have .pyc in the name
            # removes all files that DO have __init__ in the name
            lambda x: '__init__' not in x,
            # removes all files that DO have this module's name
            lambda x: 'registrator.py' not in x
        ]

        # apply all of the above checks
        for check in checks:
            files = filter(check, files)

        # trim the .py in the name to get only the filename
        modules = map(lambda f: f[:-3], files)
        return modules


def all_packages(package, root_package=ROOT_PACKAGE, ignore=[]):
    """
    Finds all packages inside a package. This will only look for folder names.
    For individual modules use all_modules.
    """
    # type: (str) -> [str]
    directory = os.path.join(root_package, package)
    all_files = os.walk(directory)

    for root, dirs, files in all_files:
        return filter(
            lambda current, ignore=ignore: current not in ignore, dirs)

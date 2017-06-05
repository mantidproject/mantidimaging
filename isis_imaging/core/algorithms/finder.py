from __future__ import (absolute_import, division, print_function)

import os
import sys


def get_package_name(module, core_package='core'):
    """
    Find the internal ISIS_IMAGING package for the specified module
    :param module: The module whose package we're looking for
    :param core_package: The core package within which we're looking
    """
    s = os.path.dirname(os.path.realpath(module))
    return s[s.find(core_package):]


def all_modules(package="core/filters", directory=None):
    """
    This function will build the path to the specified package, and then import all of the modules from it,
    and call _cli_register if _cli is specified, or _gui_register if _gui is specified.

    :param obj: the obj into which the modules will be registered,
                this is simply forwarded onto the actual functions that do the dynamic registering
    :param directory: The directory to be walked for python modules.
                      This parameter is currently being added to ease unit testing.
    :param package: The internal package from which modules will be imported
    :param func: Two built in functions are provided, registrator._cli and registrator._gui, for registration into the
                 command line interface (CLI) or the graphical user interface (GUI). A custom function can be passed
                 if the behaviour needs to be extended or overridden
    """
    # sys path 0 will give us the parent directory of the package, and we
    # append the internal package location
    if not directory:
        directory = os.path.join(sys.path[0], package)

    all_files = os.walk(directory)

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


def all_packages(package, ignore=[]):
    # type: (str) -> [str]
    directory = os.path.join(sys.path[0], package)
    all_files = os.walk(directory)

    for root, dirs, files in all_files:
        return filter(
            lambda current, ignore=ignore: current not in ignore, dirs)

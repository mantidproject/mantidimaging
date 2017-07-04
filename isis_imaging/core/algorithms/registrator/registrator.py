from __future__ import absolute_import, division, print_function

import os
import sys

from .cli_registrator import cli_register

def register_into(obj,
                  directory=None,
                  package="core/filters",
                  func=cli_register,
                  ignore_packages=None):
    """
    This function will build the path to the specified package, and then import all of the modules from it,
    and call _cli_register if _cli is specified, or _gui_register if _gui is specified.

    :param ignore_packages:
    :param obj: the obj into which the modules will be registered,
                this is simply forwarded onto the actual functions that do the dynamic registering
    :param directory: The directory to be walked for python modules. If not provided sys.path[0] will be used.
    :param package: The internal package from which modules will be imported
    :param func: Two built in functions are provided, registrator._cli and registrator._gui, for registration into the
                 command line interface (CLI) or the graphical user interface (GUI). A custom function can be passed
                 if the behaviour needs to be extended or overridden
    """
    # use dots because the check is after the conversion of slashes to dots
    all_ignores = ["core.filters", "core.filters.wip"]
    if ignore_packages is not None:
        all_ignores.extend(ignore_packages)

    # sys path 0 will give us the parent directory of the package, and we
    # append the internal package location
    if not directory:
        directory = os.path.join(sys.path[0], package)

    all_files = os.walk(directory)

    # replace the / with . to match python package syntax
    for root, dirs, files in all_files:
        package_dir = root[root.find(package):].replace('/', '.')
        if package_dir in all_ignores:
            continue
        obj = func(obj, package_dir)

    return obj

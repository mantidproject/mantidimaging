from __future__ import (absolute_import, division, print_function)
import importlib
import os
import warnings


def register_into(parser):
    """
    This function will import all the filters, and then call
    cli_register(parser) on them.

    The functionality has been extended to walk the core.filters.* directories automatically and pick up all .py files,
    and try to register them.

    An alternative implementation for the lambda checks is in examples/cli_checks_performance.py
    The current implementation was found to be faster, and more readible
    """
    all_files = os.walk("core/filters")

    for root, dirs, files in all_files:
        # replace the / with . to match python package syntax
        package_dir = root.replace('/', '.')

        # specify the checks to remove specific files
        checks = [
            lambda x: '.py' in x,  # removes all files that DON'T have .py in the name
            lambda x: '.pyc' not in x,  # removes all files that DO have .pyc in the name
            lambda x: '__init__' not in x,  # removes all files that DO have __init__ in the name
            lambda x: 'cli_registrator.py' not in x  # removes all files that have this module's name in the name
        ]

        # apply all of the above checks
        for check in checks:
            files = filter(check, files)

        # trim the .py in the name to get only the filename
        actual_python_modules = map(lambda x: x[:-3], files)

        # this will make the group name equal the package
        # this means the core.filters will be separate from
        # core.filters.wip or any other additional folders
        group = parser.add_argument_group(package_dir)

        # we specify the full absolute path and append the package name
        # the code underneath does import core.filters.package_name
        for module in actual_python_modules:
            full_module = package_dir + '.' + module
            m = importlib.import_module(full_module)

            # warn the user if one of the modules is missing the cli_register method
            try:
                m.cli_register(group)
            except AttributeError:
                cli_register_warning = "The module " + full_module + " does NOT have a cli_register(parser) method!"
                warnings.warn(cli_register_warning)

    return parser

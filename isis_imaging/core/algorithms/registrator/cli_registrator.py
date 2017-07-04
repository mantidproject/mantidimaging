from __future__ import absolute_import, division, print_function

import warnings
import argparse
import importlib


def cli_register(parser, package_dir):
    assert isinstance(
        parser, argparse.ArgumentParser
    ), "The argument parser object was not of the correct type!"

    # we specify the full absolute path and append the package name
    # the code underneath does import core.filters.package_name
    m = importlib.import_module(package_dir)

    # warn the user if one of the modules is missing the _cli_register method
    if getattr(m, '_cli_register', None):
        # this will make the group name equal the package
        # this means the core.filters will be separate from
        # core.filters.wip or any other additional folders
        group = parser.add_argument_group(package_dir)
        m._cli_register(group)
    else:
        _cli_register_warning = "The package " + package_dir + \
            " does NOT have a _cli_register(parser) method!"
        warnings.warn(_cli_register_warning)
    return parser

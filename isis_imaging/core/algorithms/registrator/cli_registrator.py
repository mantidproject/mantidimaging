from __future__ import absolute_import, division, print_function

import argparse

from .registrator import do_importing


def cli_register(parser, package_dir):
    assert isinstance(
        parser, argparse.ArgumentParser
    ), "The argument parser object was not of the correct type!"

    # we specify the full absolute path and append the package name
    # the code underneath does import core.filters.package_name
    do_importing(package_dir, '_cli_register', '_cli', do_registering, parser)

    return parser


def do_registering(module, package_dir, parser):
    group = parser.add_argument_group(package_dir)
    module._cli_register(group)

from __future__ import absolute_import, division, print_function

import argparse

from .registrator import do_importing


def cli_register(parser, module_dir):
    """
    Asserts the state of the execution to make sure we have the correct class.

    :param parser: The parser object into which we are registering.

    :param module_dir: The current module directory

    :return: The parser object
    """
    assert isinstance(
        parser, argparse.ArgumentParser
    ), "The argument parser object was not of the correct type!"

    # we specify the full absolute path and append the package name
    # the code underneath does import core.filters.package_name
    do_importing(module_dir, '_cli_register', '_cli', do_registering, parser)

    return parser


def do_registering(module, module_dir, parser):
    """
    This function is a callback from the registrator. Does the registering into
    the CLI.

    It will add a new group for each filter. If, in the future, we want to
    group the modules better, this is the function that needs to be changed.
    However the grouping doesn't seem to do anything except look differently
    when the `--help` flag is called.

    :param module: The module that we are registering

    :param module_dir: The module's directory, which will be used for the name

    :param parser: The parser into which we're registering.
                   Currently a group will be created using the module_dir
                   parameter, and the module will be registered into that
                   group.
    """
    group = parser.add_argument_group(module_dir)
    module._cli_register(group)

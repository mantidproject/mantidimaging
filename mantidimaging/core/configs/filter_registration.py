from mantidimaging.core.utility.registrator import (get_package_children, import_items, register_into)


def _cli_register_into_parser(parser, module):
    """
    This function is a callback from the registrator. Does the registering into
    the CLI.

    It will add a new group for each filter. If, in the future, we want to
    group the modules better, this is the function that needs to be changed.
    However the grouping doesn't seem to do anything except look differently
    when the `--help` flag is called.

    :param module: The module that we are registering

    :param parser: The parser into which we're registering.
                   Currently a group will be created using the module_dir
                   parameter, and the module will be registered into that
                   group.
    """
    group = parser.add_argument_group(f'{module.FILTER_CLASS.filter_name} options')
    module._cli_register(group)


def register_filters_on_cli(parser,
                            package_name='mantidimaging.core.filters',
                            ignored_packages=['mantidimaging.core.filters.wip']):
    """
    Registers filter modules into the CLI.

    :param parser: The parser instace to register into

    :param package_name: Root package name of modules to register

    :param ignored_packages: Optional list of packages/modules to ignore
    """
    filter_packages = get_package_children(package_name, packages=True, ignore=ignored_packages)
    filter_packages = [p[1] for p in filter_packages]
    loaded_filters = import_items(filter_packages, required_attributes=['FILTER_CLASS'])
    register_into(parser, loaded_filters, _cli_register_into_parser)

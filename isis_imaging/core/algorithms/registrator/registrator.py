from __future__ import absolute_import, division, print_function

import importlib
import os
import sys
import warnings


def register_into(the_object, func=None, directory=None, package="core/filters", ignore_packages=None):
    """
    This function will walk all of the packages in the specified package directory,
    and forward the this_object parameter with the specified func parameter,

    :param the_object: the object into which the modules will be registered,
                        this is forwarded to the actual functions that do the registering

    :param directory: The directory to be walked for python modules. If not provided sys.path[0] will be used.

    :param package: The internal package from which modules will be imported

    :param func: Two built in functions are provided, registrator.cli_register and registrator.gui_register,
                 for registration into the command line interface (CLI) or the graphical user interface (GUI)

    :param ignore_packages: Expected: List, If the package name matches an entry in the list, it will be ignored.
    """

    if not func:
        raise ValueError(
            "The func parameter must be specified! It should be one of either registrator.cli_register or "
            "registrator.gui_register.")

    # use dots because the check is after the conversion of slashes to dots
    all_ignores = ["core.filters", "core.filters.wip"]
    if ignore_packages is not None:
        all_ignores.extend(list(ignore_packages))

    # sys path 0 will give us the parent directory of the package, and we
    # append the internal package location
    if not directory:
        directory = os.path.join(sys.path[0], package)

    all_files = os.walk(directory)

    # sort by filename
    for root, dirs, files in sorted(all_files, key=lambda file_tuple: file_tuple[2]):
        # replace the / with . to match python package syntax
        package_dir = root[root.find(package):].replace('/', '.')
        if package_dir in all_ignores:
            continue
        the_object = func(the_object, package_dir)

    return the_object


def do_importing(package_dir, register_function_name, extended_file_suffix, func_to_do_registering, the_object):
    """
    The interface registering code can be defined in two places:

    - Note: The xxx below can stand for either gui or cli

    - In a _xxx_register function inside the filter module
        -> background_correction has a function _gui_register
    - Or in an external module that has the same name like the filter module, with _xxx appended at the end
        -> background_correction module's GUI file is background_correction_gui

    This is done in order to avoid importing the GUI library on a non-GUI run.

    :param package_dir: The package directory

    :param register_function_name: The function will check if this function is available in the module.
                                   If not it will fallback to looking for a module with the
                                   extended_file_suffix appended at the end.

    :param extended_file_suffix: The suffix for the module in the extended search

    :param func_to_do_registering: The actual function that will do the registering, and will accept the object

    :param the_object: The object that the registering function will use to register the modules in.
    """
    module = importlib.import_module(package_dir)
    # Check if the imported module has the function attribute
    if hasattr(module, register_function_name):
        func_to_do_registering(module, package_dir, the_object)
    # the attribute wasn't found, do the extended search and attempt to import the module with suffix
    else:
        extended_package_dir = package_dir + \
            package_dir[package_dir.rfind('.'):] + extended_file_suffix
        try:
            extended_module = importlib.import_module(extended_package_dir)
            func_to_do_registering(extended_module, package_dir, the_object)
        except AttributeError:
            warnings.warn(
                "Package {0}.{1} function not found!".format(extended_package_dir, register_function_name))
        except ImportError:
            warnings.warn(
                "Package {0}{1} was not found! It is not registered with the GUI and it will not appear.".format(
                    extended_package_dir, extended_file_suffix))

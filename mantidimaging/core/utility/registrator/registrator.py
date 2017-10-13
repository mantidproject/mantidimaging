from __future__ import absolute_import, division, print_function

import importlib
import os
import pkgutil
import sys
import warnings


def find_package_path(package_str):
    """
    Attempts to find the path to a given package provided the root package is
    already on the path.

    :param package_str: Package to search for as a Python path (i.e. "mantidimaging.core.filters")
    :return: Path to package
    """
    package_as_path = os.sep.join(package_str.split('.'))
    for path in sys.path:
        candidate_path = os.path.join(path, package_as_path)
        if os.path.exists(candidate_path):
            return candidate_path

    raise RuntimeError("Cannot find path for package {}".format(package_str))


def register_into(the_object, func=None, package='mantidimaging.core.filters', ignore_packages=None):
    """
    This function will walk all of the packages in the specified package directory,
    and forward the this_object parameter with the specified func parameter,

    :param the_object: the object into which the modules will be registered,
                        this is forwarded to the actual functions that do the registering

    :param package: The internal package from which modules will be imported

    :param func: registrator.cli_register and registrator.gui_register,
                 for registration into the command line interface (CLI) or the graphical user interface (GUI)

    :param ignore_packages: Expected: List, If the package name matches an entry in the list, it will be ignored.
    """

    if not func:
        raise ValueError(
            "The func parameter must be specified! It should be one of either registrator.cli_register or "
            "registrator.gui_register.")

    all_ignores = ["mantidimaging.core.filters.wip"]

    if ignore_packages is not None:
        all_ignores.extend(list(ignore_packages))

    # Walk the children (packages and modules) of the provided root package
    for pkg in pkgutil.walk_packages([find_package_path(package)], prefix=package + '.'):
        # Ignore those that are modules, we want packages
        if not pkg[2]:
            continue

        # Ignore moduels that we want to ignore
        if pkg[1] in all_ignores:
            continue

        the_object = func(the_object, pkg[1])

    return the_object


def do_importing(module_dir,
                 name_of_register_function,
                 extended_search_file_suffix,
                 func_to_do_registering,
                 the_object):
    """
    The interface registering code can be defined in two places:

    - Note: The xxx below can stand for either gui or cli

    - In a _xxx_register function inside the filter module
        -> background_correction has a function _gui_register
    - Or in an external module that has the same name like the filter module, with _xxx appended at the end
        -> background_correction module's GUI file is background_correction_gui

    This is done in order to avoid importing the GUI library on a non-GUI run.

    :param module_dir: The package directory

    :param name_of_register_function: The function will check if this function is available in the module.
                                      If not it will fallback to looking for a module with the
                                      extended_file_suffix appended at the end.

    :param extended_search_file_suffix: The suffix for the module in the extended search

    :param func_to_do_registering: The actual function that will do the registering, and will accept the object

    :param the_object: The object that the registering function will use to register the modules in.
    """

    # import the module inside the provided package_dir,
    # e.g. this will pass the mantidimaging.filters.median_filter package and it will be imported here
    module = importlib.import_module(module_dir)

    # try registering, and if it fails, show warning to the user
    try:
        # If the module has this attribute, it is the function defined in the .py file
        if hasattr(module, name_of_register_function):

            # the function that will do the actual registering, refer to the specialised modules for cli, gui, etc
            func_to_do_registering(module, module_dir, the_object)

        # the attribute wasn't found, do the extended search and attempt to import the module with the provided suffix
        # this will search for a file that has the original filter module name + the suffix appended
        else:
            # build the new module name
            module_dir = module_dir + module_dir[module_dir.rfind('.'):] + extended_search_file_suffix

            extended_module = importlib.import_module(module_dir)

            func_to_do_registering(extended_module, module_dir, the_object)

    except AttributeError:
        warnings.warn(
            "Package {0}.{1} function not found!".format(module_dir, name_of_register_function))
    except ImportError:
        warnings.warn(
            "Package {0}{1} was not found! It is not registered with the GUI and it will not appear.".format(
                module_dir, extended_search_file_suffix))

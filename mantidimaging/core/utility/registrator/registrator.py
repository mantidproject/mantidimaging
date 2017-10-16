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

    :param package_str: Package to search for as a Python path (i.e.
                        "mantidimaging.core.filters")

    :return: Path to package
    """
    package_as_path = os.sep.join(package_str.split('.'))
    for path in sys.path:
        candidate_path = os.path.join(path, package_as_path)
        if os.path.exists(candidate_path):
            return candidate_path

    raise RuntimeError("Cannot find path for package {}".format(package_str))


def get_child_modules(package_name, ignore=None):
    """
    Gets a list of names of modules found under a given package.

    :param package: The package to search within

    :param ignore: List of explicitly matching modules to ignore

    :return: Iterator over matching modules
    """
    # Walk the children (packages and modules) of the provided root package
    pkgs = pkgutil.walk_packages([find_package_path(package_name)],
                                 prefix=package_name + '.')

    # Ignore those that are modules, we want packages
    pkgs = filter(lambda p: p[2], pkgs)

    # Ignore moduels that we want to ignore
    if ignore:
        pkgs = filter(lambda p: not any([m in p[1] for m in ignore]),
                      pkgs)

    return pkgs


def import_modules(module_names, required_attributes=None):
    """
    Imports a list of modules and filters out those that do not have a
    specified required list of attributes.

    :param module_names: List of module names to import

    :param required_attributes: Optional list of attributes that must be
                                present on each individual module

    :return: List of imported modules
    """
    imported_modules = [importlib.import_module(m) for m in module_names]

    # Filter out those that do not contain all the required attributes
    if required_attributes:
        imported_modules = filter(
                lambda m: all([hasattr(m, a) for a in required_attributes]),
                imported_modules)

    return imported_modules


def register_into(the_object,
                  func=None,
                  package='mantidimaging.core.filters',
                  ignore=None):
    """
    This function will walk all of the packages in the specified package
    directory, and forward the this_object parameter with the specified func
    parameter,

    :param the_object: The object into which the modules will be registered,
                       this is forwarded to the actual functions that do the
                       registering

    :param package: The internal package from which modules will be imported

    :param func: Function taking the_object and the module name to be
                 registered

    :param ignore: List of explicitly matching modules to ignore
    """

    if not func:
        raise ValueError(
            "The func parameter must be specified! It should be one of either "
            "registrator.cli_register or registrator.gui_register.")

    all_ignores = ["mantidimaging.core.filters.wip"]

    if ignore is not None:
        all_ignores.extend(list(ignore))

    for pkg in get_child_modules(package, all_ignores):
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
    - Or in an external module that has the same name like the filter module,
      with _xxx appended at the end
        -> background_correction module's GUI file is background_correction_gui

    This is done in order to avoid importing the GUI library on a non-GUI run.

    :param module_dir: The package directory

    :param name_of_register_function: The function will check if this function
                                      is available in the module.
                                      If not it will fallback to looking for a
                                      module with the extended_file_suffix
                                      appended at the end.

    :param extended_search_file_suffix: The suffix for the module in the
                                        extended search

    :param func_to_do_registering: The actual function that will do the
                                   registering, and will accept the object

    :param the_object: The object that the registering function will use to
                       register the modules in.
    """

    # import the module inside the provided package_dir, e.g. this will pass
    # the mantidimaging.filters.median_filter package and it will be imported
    # here
    module = importlib.import_module(module_dir)

    # try registering, and if it fails, show warning to the user
    try:
        # If the module has this attribute, it is the function defined in the
        # .py file
        if hasattr(module, name_of_register_function):

            # the function that will do the actual registering, refer to the
            # specialised modules for cli, gui, etc
            func_to_do_registering(module, module_dir, the_object)

        # the attribute wasn't found, do the extended search and attempt to
        # import the module with the provided suffix this will search for a
        # file that has the original filter module name + the suffix appended
        else:
            # build the new module name
            module_dir = module_dir + module_dir[module_dir.rfind('.'):] \
                    + extended_search_file_suffix

            extended_module = importlib.import_module(module_dir)

            func_to_do_registering(extended_module, module_dir, the_object)

    except AttributeError:
        warnings.warn("Package {0}.{1} function not found!".format(
                module_dir, name_of_register_function))

    except ImportError:
        warnings.warn("Package {0}{1} was not found! It is not registered "
                      "with the GUI and it will not appear.".format(
                            module_dir, extended_search_file_suffix))

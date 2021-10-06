# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import os
import pkgutil
import sys
from typing import List, Iterator, Optional

from mantidimaging.core.operations.base_filter import BaseFilter

_OPERATIONS_DIR = "mantidimaging.core.operations"


def _find_package_path(package_str):
    """
    Attempts to find the path to a given package provided the root package is
    already on the path.

    :param package_str: Package to search for as a Python path (i.e.
                        "mantidimaging.core.operations")

    :return: Path to package
    """
    package_as_path = os.sep.join(package_str.split('.'))
    for path in sys.path:
        candidate_path = os.path.join(path, package_as_path)
        if os.path.exists(candidate_path):
            return candidate_path

    raise RuntimeError("Cannot find path for package {}".format(package_str))


ISPKG_OPERATIONS = {}
MODULES_OPERATIONS = {}
for loader, module_name, is_pkg in pkgutil.walk_packages([os.path.dirname(__file__)]):
    MODULES_OPERATIONS[module_name] = loader.find_module(module_name)
    ISPKG_OPERATIONS[module_name] = is_pkg


def _get_package_children(package_name: str,
                          packages=False,
                          modules=False,
                          ignore=None) -> Iterator[pkgutil.ModuleInfo]:
    """
    Gets a list of names of child packages or modules found under a given
    package.

    :param package_name: The package to search within
    :param packages: Set to True to return packages
    :param modules: Set to True to return modules
    :param ignore: List of explicitly matching modules to ignore

    :return: Iterator over matching modules
    """
    pkgs: Iterator[pkgutil.ModuleInfo] = pkgutil.walk_packages([_find_package_path(package_name)],
                                                               prefix=package_name + '.')

    # Ignore those that do not match the package/module selection criteria
    pkgs = filter(lambda p: p.ispkg and packages or not p.ispkg and modules, pkgs)

    # Ignore modules whose names contain anything from 'ignore'
    if ignore:
        pkgs = filter(lambda p: not any([m in p.name for m in ignore]), pkgs)

    return pkgs


def _import_items(packages: Iterator[pkgutil.ModuleInfo], required_attributes: Optional[List[str]] = None):
    """
    Imports a list of packages/modules and operations out those that do not have a
    specified required list of attributes.

    :param packages: List of packages to import.
    :param required_attributes: Optional list of attributes that must be
                                present on each individual module

    :return: List of imported packages/modules
    """
    imported = map(lambda p: p.module_finder.find_module(p.name).load_module(p.name), packages)
    # Filter out those that do not contain all the required attributes
    if required_attributes:
        imported = filter(  # type: ignore
            lambda i: all([hasattr(i, a) for a in required_attributes]), imported)  # type: ignore

    return imported


def load_filter_packages(ignored_packages=None) -> List[BaseFilter]:
    """
    Imports all subpackages with a FILTER_CLASS attribute, which should be an extension of BaseFilter.

    These classes are then used to provide the names, required inputs, and behaviour to execute
    then named filter on a stack of images.

    :param ignored_packages: List of ignore rules
    """

    filters = {name: MODULES_OPERATIONS[name].load_module(name) for name in MODULES_OPERATIONS.keys()}
    filters = {name: filters[name] for name in filters.keys() if hasattr(filters[name], 'FILTER_CLASS')}
    if not ignored_packages:
        return [f.FILTER_CLASS for f in filters.values()]
    return [
        filters[name].FILTER_CLASS for name in filters.keys()
        if not any([ignore in name for ignore in ignored_packages])
    ]

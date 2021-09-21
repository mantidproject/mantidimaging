# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import os
import pkgutil
import sys
from typing import List, Iterator, Optional

from mantidimaging.core.operations.base_filter import BaseFilter

OPERATIONS_CLASSES = []
OPERATIONS_DIR = "mantidimaging.core.operations"


def find_package_path(package_str):
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


OPERATIONS_ITER = pkgutil.walk_packages([find_package_path(OPERATIONS_DIR)])


def get_package_children(package_name: str, packages=False, modules=False, ignore=None) -> Iterator[pkgutil.ModuleInfo]:
    """
    Gets a list of names of child packages or modules found under a given
    package.

    :param package_name: The package to search within
    :param packages: Set to True to return packages
    :param modules: Set to True to return modules
    :param ignore: List of explicitly matching modules to ignore

    :return: Iterator over matching modules
    """
    if package_name == OPERATIONS_DIR:
        pkgs = OPERATIONS_ITER
    else:
        pkgs: Iterator[pkgutil.ModuleInfo] = pkgutil.walk_packages([find_package_path(package_name)],
                                                                   prefix=package_name + '.')

    # Ignore those that do not match the package/module selection criteria
    pkgs = filter(lambda p: p.ispkg and packages or not p.ispkg and modules, pkgs)

    # Ignore modules whose names contain anything from 'ignore'
    if ignore:
        pkgs = filter(lambda p: not any([m in p.name for m in ignore]), pkgs)

    return pkgs


def import_items(packages: Iterator[pkgutil.ModuleInfo], required_attributes: Optional[List[str]] = None):
    """
    Imports a list of packages/modules and operations out those that do not have a
    specified required list of attributes.

    :param packages: List of packages to import.
    :param required_attributes: Optional list of attributes that must be
                                present on each individual module

    :return: List of imported packages/modules
    """
    imported = []
    for loader, module_name, _ in packages:
        imported.append(loader.find_module(module_name).load_module())

    # Filter out those that do not contain all the required attributes
    if required_attributes:
        imported = filter(  # type: ignore
            lambda i: all([hasattr(i, a) for a in required_attributes]), imported)  # type: ignore

    return imported


def load_filter_packages(package_name="mantidimaging.core.operations", ignored_packages=None) -> List[BaseFilter]:
    """
    Imports all subpackages with a FILTER_CLASS attribute, which should be an extension of BaseFilter.

    These classes are then used to provide the names, required inputs, and behaviour to execute
    then named filter on a stack of images.

    :param package_name: Name of the root package in which to search for
                         operations
    :param ignored_packages: List of ignore rules
    """
    filter_packages = get_package_children(package_name, packages=True, ignore=ignored_packages)

    loaded_filters = import_items(filter_packages, required_attributes=['FILTER_CLASS'])
    loaded_filters = filter(lambda f: f.available() if hasattr(f, 'available') else True, loaded_filters)

    return [f.FILTER_CLASS for f in loaded_filters]

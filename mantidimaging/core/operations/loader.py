# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import os
import pkgutil
import sys
from typing import List, Iterator

from mantidimaging.core.operations.base_filter import BaseFilter

OPERATIONS_CLASSES = []


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


for loader, module_name, is_pkg in pkgutil.walk_packages([find_package_path("mantidimaging.core.operations")]):
    if is_pkg:
        OPERATIONS_CLASSES.append(loader.find_module(module_name))


def get_package_children(pkgs, packages=False, modules=False, ignore=None) -> Iterator[pkgutil.ModuleInfo]:
    """
    Gets a list of names of child packages or modules found under a given
    package.

    :param package_name: The package to search within
    :param packages: Set to True to return packages
    :param modules: Set to True to return modules
    :param ignore: List of explicitly matching modules to ignore

    :return: Iterator over matching modules
    """
    # Ignore those that do not match the package/module selection criteria
    pkgs = filter(lambda p: p.ispkg and packages or not p.ispkg and modules, pkgs)

    # Ignore modules whose names contain anything from 'ignore'
    if ignore:
        pkgs = filter(lambda p: not any([m in p.name for m in ignore]), pkgs)

    return pkgs


def load_filter_packages(package_name="mantidimaging.core.operations", ignored_packages=None) -> List[BaseFilter]:
    """
    Imports all subpackages with a FILTER_CLASS attribute, which should be an extension of BaseFilter.

    These classes are then used to provide the names, required inputs, and behaviour to execute
    then named filter on a stack of images.

    :param package_name: Name of the root package in which to search for
                         operations
    :param ignored_packages: List of ignore rules
    """

    filters = [p.load_module() for p in OPERATIONS_CLASSES]
    filters = [f for f in filters if hasattr(f, "FILTER_CLASS")]

    # filter_packages = get_package_children(package_name, packages=True, ignore=ignored_packages)
    # filter_package_names = [p.name for p in OPERATIONS_CLASSES]
    #
    # loaded_filters = import_items(filter_package_names, required_attributes=['FILTER_CLASS'])
    # loaded_filters = filter(lambda f: f.available() if hasattr(f, 'available') else True, loaded_filters)

    return [f.FILTER_CLASS for f in filters]

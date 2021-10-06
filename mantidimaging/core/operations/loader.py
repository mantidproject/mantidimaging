# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import os
import pkgutil
import sys
from typing import List

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

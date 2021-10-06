# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import os
import pkgutil
from typing import List

from mantidimaging.core.operations.base_filter import BaseFilter

_OPERATIONS_DIR = "mantidimaging.core.operations"

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

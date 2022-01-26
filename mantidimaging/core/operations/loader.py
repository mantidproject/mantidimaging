# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import os
import pkgutil
from typing import List, Protocol, cast
from importlib.machinery import FileFinder, ModuleSpec
from importlib.abc import Loader

from mantidimaging.core.operations.base_filter import BaseFilter

MODULES_OPERATIONS = {}
for finder, module_name, is_pkg in pkgutil.walk_packages([os.path.dirname(__file__)]):
    assert isinstance(finder, FileFinder)
    spec = finder.find_spec(module_name)
    assert isinstance(spec, ModuleSpec)
    assert isinstance(spec.loader, Loader)
    MODULES_OPERATIONS[module_name] = spec.loader


class OperationModule(Protocol):
    FILTER_CLASS: BaseFilter


def load_filter_packages(ignored_packages=None) -> List[BaseFilter]:
    """
    Imports all subpackages with a FILTER_CLASS attribute, which should be an extension of BaseFilter.

    These classes are then used to provide the names, required inputs, and behaviour to execute
    then named filter on a stack of images.

    :param ignored_packages: List of ignore rules
    """

    filters = {name: MODULES_OPERATIONS[name].load_module(name) for name in MODULES_OPERATIONS.keys()}
    filters = {name: filters[name] for name in filters.keys() if hasattr(filters[name], 'FILTER_CLASS')}
    operation_modules = {name: cast(OperationModule, f) for name, f in filters.items()}
    if not ignored_packages:
        return [f.FILTER_CLASS for f in operation_modules.values()]
    return [
        operation_modules[name].FILTER_CLASS for name in operation_modules.keys()
        if not any([ignore in name for ignore in ignored_packages])
    ]

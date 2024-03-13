# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import os
import pkgutil
import sys
from importlib.util import module_from_spec
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mantidimaging.core.operations.base_filter import BaseFilter
    BaseFilterClass = type[BaseFilter]

_OPERATION_MODULES_LIST: list[BaseFilterClass] = []


def _find_operation_modules() -> list[BaseFilterClass]:
    module_list: list[BaseFilterClass] = []
    for finder, module_name, ispkg in pkgutil.walk_packages([os.path.dirname(__file__)]):
        if not ispkg:
            continue

        if getattr(sys, 'frozen', False):
            # If we're running a PyInstaller executable then we need to use a full module path
            module_name = f'mantidimaging.core.operations.{module_name}'

        # near impossible to type check as find can be a pyinstaller specific type that we can't normally import
        spec = finder.find_spec(module_name)  # type: ignore[call-arg]

        assert spec is not None
        assert spec.loader is not None
        module = module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        if hasattr(module, 'FILTER_CLASS'):
            module_list.append(module.FILTER_CLASS)

    return module_list


def load_filter_packages() -> list[BaseFilterClass]:
    """
    Imports all subpackages with a FILTER_CLASS attribute, which should be an extension of BaseFilter.

    These classes are then used to provide the names, required inputs, and behaviour to execute
    then named filter on a stack of images.

    :param ignored_packages: List of ignore rules
    """
    global _OPERATION_MODULES_LIST
    if not _OPERATION_MODULES_LIST:
        _OPERATION_MODULES_LIST = _find_operation_modules()
    return _OPERATION_MODULES_LIST

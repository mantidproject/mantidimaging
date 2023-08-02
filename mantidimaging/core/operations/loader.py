# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import os
import pkgutil
import sys
from importlib.util import module_from_spec
from importlib.machinery import FileFinder, ModuleSpec
from typing import List, TYPE_CHECKING
from importlib.abc import Loader

if TYPE_CHECKING:
    from PyInstaller.loader.pyimod02_importers import FrozenImporter
    from mantidimaging.core.operations.base_filter import BaseFilter

_OPERATION_MODULES_LIST: List[BaseFilter] = []


def _find_operation_modules() -> List[BaseFilter]:
    module_list: List[BaseFilter] = []
    for finder, module_name, ispkg in pkgutil.walk_packages([os.path.dirname(__file__)]):
        if not ispkg:
            continue

        if getattr(sys, 'frozen', False):
            # If we're running a PyInstaller executable then we need to use a full module path
            module_name = f'mantidimaging.core.operations.{module_name}'

        if TYPE_CHECKING:
            assert isinstance(finder, (FileFinder, FrozenImporter))
        spec = finder.find_spec(module_name)

        assert isinstance(spec, ModuleSpec)
        assert isinstance(spec.loader, Loader)
        module = module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        if hasattr(module, 'FILTER_CLASS'):
            module_list.append(module.FILTER_CLASS)

    return module_list


def load_filter_packages(ignored_packages=None) -> List[BaseFilter]:
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

# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import os
import pkgutil
import sys
from typing import List, Protocol, cast, Union, TYPE_CHECKING
from importlib.machinery import FileFinder, ModuleSpec
from importlib.abc import Loader

if TYPE_CHECKING:
    from PyInstaller.loader.pyimod02_importers import FrozenImporter
    from mantidimaging.core.operations.base_filter import BaseFilter

MODULES_OPERATIONS: dict[str, Union['FrozenImporter', Loader]] = {}
if not MODULES_OPERATIONS:
    for finder, module_name, _ in pkgutil.walk_packages([os.path.dirname(__file__)]):
        if getattr(sys, 'frozen', False):
            # If we're running a PyInstaller executable then we will get back a FrozenImporter object instead of a
            # FileFinder. FrozenImporter implements load_module directly, but needs to use the full import name for
            # the module to load it from the PYZ archive.
            assert hasattr(finder, 'load_module')
            MODULES_OPERATIONS[f'mantidimaging.core.operations.{module_name}'] = finder
        else:
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

    operation_modules = []
    for name in MODULES_OPERATIONS.keys():
        if not ignored_packages or not any([ignore in name for ignore in ignored_packages]):
            module = MODULES_OPERATIONS[name].load_module(name)
            if hasattr(module, 'FILTER_CLASS'):
                operation_module = cast("OperationModule", module)
                operation_modules.append(operation_module.FILTER_CLASS)
    return operation_modules

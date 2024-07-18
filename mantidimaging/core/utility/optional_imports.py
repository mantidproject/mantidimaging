# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
"""
A place for availability checking and import logic for optional dependencies to
live.
"""
from __future__ import annotations

import importlib
import traceback
import warnings

from io import StringIO
from logging import getLogger


def safe_import(name):
    """
    Try to import an optional library that may not be present.

    Will fail gracefully by returning None if the library is not available.
    """
    try:
        module = importlib.import_module(name)

    except ImportError:
        warnings.warn(f'Failed to import optional module "{name}"', stacklevel=1)

        o = StringIO()
        traceback.print_stack(file=o)
        getLogger(__name__).debug(f'Module import stack trace: {o.getvalue()}')

        module = None

    return module


def check_availability(name: str) -> bool:
    return safe_import(name) is not None


def tomopy_available() -> bool:
    return check_availability('tomopy')

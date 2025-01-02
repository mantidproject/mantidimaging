# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from PyInstaller.compat import is_pure_conda

if is_pure_conda:
    from PyInstaller.utils.hooks import conda_support

    binaries = conda_support.collect_dynamic_libs('cil')

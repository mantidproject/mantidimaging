# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

__version__ = '2.4.0a1'
"""
The gui package is not imported here, because it will pull in all of PyQt
packages, which we do not want when using only the CLI. This is both a speedup
benefit and we do not have to deal if PyQt is missing (like on SCARF) when not
using the GUI.
"""

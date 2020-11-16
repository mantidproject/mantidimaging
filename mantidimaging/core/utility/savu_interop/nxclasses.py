# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from enum import Enum


class NXClasses(Enum):
    NXcite = b"NXcite"
    NXcollection = b"NXcollection"
    NXprocess = b"NXprocess"
    NXnote = b"NXnote"
    NXentry = b"NXentry"

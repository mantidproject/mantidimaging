from __future__ import absolute_import, division, print_function

import os

from mantidimaging.core.algorithms import finder


def execute(ui_file, qt_obj=None):
    from PyQt5 import uic
    base_path = os.path.join(
        finder.get_external_location(__file__), finder.ROOT_PACKAGE)
    return uic.loadUi(os.path.join(base_path, ui_file), qt_obj)

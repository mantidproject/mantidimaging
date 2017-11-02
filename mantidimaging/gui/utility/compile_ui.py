from __future__ import absolute_import, division, print_function

import os

from PyQt5 import uic

from mantidimaging.core.utility import finder


def compile_ui(ui_file, qt_obj=None):
    base_path = os.path.join(
        finder.get_external_location(__file__), finder.ROOT_PACKAGE)
    return uic.loadUi(os.path.join(base_path, ui_file), qt_obj)

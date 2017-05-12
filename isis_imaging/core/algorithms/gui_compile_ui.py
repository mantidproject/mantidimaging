from __future__ import absolute_import, division, print_function

import os
import sys

from PyQt4 import uic


def execute(ui_file, qt_obj=None):
    base_path = sys.path[0]
    return uic.loadUi(os.path.join(base_path, ui_file), qt_obj)

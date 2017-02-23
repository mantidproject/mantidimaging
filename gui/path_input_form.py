from __future__ import (absolute_import, division, print_function)
from PyQt4 import uic
from PyQt4.QtGui import QWidget


class PathInputForm(QWidget):
    def __init__(self, test=False):
        if not test:
            super(PathInputForm, self).__init__()
            uic.loadUi('./gui/ui/path_input_form.ui', self)

        self._path_sample = None
        self._path_flat = None
        self._path_dark = None

    def set_path_sample(self, new_path):
        self._path_sample = new_path

    def set_path_flat(self, new_path):
        self._path_flat = new_path

    def set_path_dark(self, new_path):
        self._path_dark = new_path

    def get_path_sample(self):
        return self._path_sample

    def get_path_flat(self):
        return self._path_flat

    def get_path_dark(self):
        return self._path_dark

    path_sample = property(get_path_sample, set_path_sample)
    path_flat = property(get_path_flat, set_path_flat)
    path_dark = property(get_path_dark, set_path_dark)

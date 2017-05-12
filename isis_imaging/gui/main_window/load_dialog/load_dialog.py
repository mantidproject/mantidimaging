from __future__ import absolute_import, division, print_function

from PyQt4 import QtGui

from core.algorithms import gui_compile_ui

from core.imgdata.loader import get_file_names

import os


class MWLoadDialog(QtGui.QDialog):
    def __init__(self, parent):
        super(MWLoadDialog, self).__init__(parent)
        gui_compile_ui.execute('gui/ui/load.ui', self)

        # open file path dialogue
        self.sampleButton.clicked.connect(
            lambda: self.update_indices(self.select_file(self.samplePath)))

        self.flatButton.clicked.connect(
            lambda: self.select_file(self.flatPath))

        self.darkButton.clicked.connect(
            lambda: self.select_file(self.darkPath))

        # if accepted load the stack
        self.accepted.connect(parent.load_stack)

    def update_indices(self, select_file_result):
        """
        :param select_file_result: Will be None so discard
        """
        str_path = str(self.samplePath)
        dot_index = str_path.rfind('.')
        file_extension = str_path[dot_index:]
        print(file_extension)
        get_file_names(self.load_path(), file_extension)
        self.index_end = len(get_file_names)

    def select_file(self, field):
        assert isinstance(
            field, QtGui.QLineEdit
        ), "The passed object is of type {0}. This function only works with QLineEdit".format(
            type(field))

        # open file dialogue and set the text if file is selected
        field.setText(QtGui.QFileDialog.getOpenFileName())

    def load_path(self):
        return os.path.basename(str(self.samplePath.text()))

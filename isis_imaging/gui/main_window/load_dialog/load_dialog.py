from __future__ import absolute_import, division, print_function

from PyQt4 import QtGui

from core.algorithms import gui_compile_ui

from core.imgdata.loader import get_file_names, get_file_extension

import os


def select_file(field):
    assert isinstance(
        field, QtGui.QLineEdit
    ), "The passed object is of type {0}. This function only works with QLineEdit".format(
        type(field))

    # open file dialogue and set the text if file is selected
    field.setText(QtGui.QFileDialog.getOpenFileName())


class MWLoadDialog(QtGui.QDialog):

    def __init__(self, parent):
        super(MWLoadDialog, self).__init__(parent)
        gui_compile_ui.execute('gui/ui/load.ui', self)

        # open file path dialogue
        self.sampleButton.clicked.connect(
            lambda: self.update_indices(select_file(self.samplePath)))

        self.flatButton.clicked.connect(lambda: select_file(self.flatPath))

        self.darkButton.clicked.connect(lambda: select_file(self.darkPath))

        # if accepted load the stack
        self.accepted.connect(parent.execute_load)
        self.image_format = ''

    def update_indices(self, select_file_result):
        """
        :param select_file_result: Will be None, because it contains the return of the nested function select_file
        """
        self.image_format = get_file_extension(str(self.samplePath.text()))
        image_files = get_file_names(self.sample_path(), self.image_format)

        # cap the end value FIRST, otherwise setValue might fail if the
        # previous max val is smaller
        self.index_end.setMaximum(len(image_files))
        self.index_end.setValue(len(image_files))

        # cap the start value to be end - 1
        self.index_start.setMaximum(len(image_files) - 1)

        # enforce the maximum step
        self.index_step.setMaximum(len(image_files))

    def load_path(self):
        return os.path.basename(str(self.samplePath.text()))

    def sample_path(self):
        """
        :return: The directory of the path as a Python string
        """
        return os.path.dirname(str(self.samplePath.text()))

    def flat_path(self):
        """
        :return: The directory of the path as a Python string
        """
        return os.path.dirname(str(self.flatPath.text()))

    def dark_path(self):
        """
        :return: The directory of the path as a Python string
        """
        return os.path.dirname(str(self.darkPath.text()))

    def parallel_load(self):
        """
        :return: True if load should be in parallel, else False
        """
        return self.parallelLoad.isChecked()

    def indices(self):
        return self.index_start.value(), self.index_end.value(
        ), self.index_step.value()

from __future__ import absolute_import, division, print_function

from PyQt4 import QtGui

from core.algorithms import gui_compile_ui

from core.imgdata.loader import get_file_names

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
        self.accepted.connect(parent.load_stack)

    def update_indices(self, select_file_result):
        """
<<<<<<< Updated upstream
        :param select_file_result: Will be None so discard
||||||| merged common ancestors
        :param select_file_result: Will be None, because it contains the return of the nested function self.select_file
=======
        :param select_file_result: Will be None, because it contains the return of the nested function select_file
>>>>>>> Stashed changes
        """
        str_path = str(self.samplePath)
        dot_index = str_path.rfind('.')
        file_extension = str_path[dot_index:]
        print(file_extension)
        get_file_names(self.load_path(), file_extension)
        self.index_end = len(get_file_names)

<<<<<<< Updated upstream
    def select_file(self, field):
        assert isinstance(
            field, QtGui.QLineEdit
        ), "The passed object is of type {0}. This function only works with QLineEdit".format(
            type(field))

        # open file dialogue and set the text if file is selected
        field.setText(QtGui.QFileDialog.getOpenFileName())

    def load_path(self):
        return os.path.basename(str(self.samplePath.text()))
||||||| merged common ancestors
    def select_file(self, field):
        assert isinstance(
            field, QtGui.QLineEdit
        ), "The passed object is of type {0}. This function only works with QLineEdit".format(
            type(field))

        # open file dialogue and set the text if file is selected
        field.setText(QtGui.QFileDialog.getOpenFileName())

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
=======
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
|
>>>>>>> Stashed changes

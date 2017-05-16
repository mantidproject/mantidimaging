from __future__ import absolute_import, division, print_function

import os

from PyQt4 import QtGui

from core.algorithms import gui_compile_ui


class MWSaveDialog(QtGui.QDialog):
    def __init__(self, parent, stack_list):
        super(MWSaveDialog, self).__init__(parent)
        gui_compile_ui.execute('gui/ui/save.ui', self)

        self.browseButton.clicked.connect(
            lambda: self.select_directory(self.savePath))

        self.saveSingle.clicked.connect(self.save_single)

        self.buttonBox.button(QtGui.QDialogButtonBox.SaveAll).clicked.connect(
            self.save_all)

        if stack_list:  # we will just show an empty drop down if no stacks
            self.stackNames.addItems(zip(*stack_list)[1])

    def save_single(self):
        print("Save single clicked")
        # force the end indice to be start + 1
        self.index_end.setValue(self.index_start.value() + 1)
        # force close the dialogue, the other buttons do it automatically
        self.close()
        self.parent().execute_save()

    def save_all(self):
        print("Save all clicked")

    def select_directory(self, field):
        assert isinstance(
            field, QtGui.QLineEdit
        ), "The passed object is of type {0}. This function only works with QLineEdit".format(
            type(field))

        # open file dialogue and set the text if file is selected
        field.setText(QtGui.QFileDialog.getExistingDirectory())

    def indices(self):
        return self.index_start.value(), self.index_end.value(
        ), self.index_step.value()

    def save_path(self):
        """
            :return: The directory of the path as a Python string
        """
        return os.path.dirname(str(self.savePath.text()))

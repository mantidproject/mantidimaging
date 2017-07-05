from __future__ import absolute_import, division, print_function

from PyQt5 import Qt

from isis_imaging.core.algorithms import gui_compile_ui

from isis_imaging.core.io.utility import get_file_names, get_file_extension

import os


def select_file(field, caption):
    """
    :param field: The field in which the result will be saved
    :param caption: Title of the file browser window that will be opened
    :return: True: If a file has been selected, False otherwise
    """
    assert isinstance(
        field, Qt.QLineEdit
    ), "The passed object is of type {0}. This function only works with QLineEdit".format(
        type(field))

    selected_file = Qt.QFileDialog.getOpenFileName(caption=caption)[0]
    # open file dialogue and set the text if file is selected
    if selected_file:
        field.setText(selected_file)
        return True

    # no file has been selected
    return False


class MWLoadDialog(Qt.QDialog):
    def __init__(self, parent):
        super(MWLoadDialog, self).__init__(parent)
        gui_compile_ui.execute('gui/ui/load_dialog.ui', self)

        # TODO is there a way to do this only when ACCEPTED
        # open file path dialogue
        self.sampleButton.clicked.connect(
            lambda: self.update_indices(select_file(self.samplePath, "Sample")))

        self.flatButton.clicked.connect(
            lambda: select_file(self.flatPath, "Flat"))

        self.darkButton.clicked.connect(
            lambda: select_file(self.darkPath, "Dark"))

        # if accepted load the stack
        self.accepted.connect(parent.execute_load)
        self.image_format = ''

    def update_indices(self, select_file_successful):
        """
        :param select_file_successful: The result from the select_file function
        """
        if not select_file_successful:
            return False

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
        self.index_step.setValue(len(image_files) / 10)

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

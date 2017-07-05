from __future__ import absolute_import, division, print_function

import os

from PyQt5 import Qt

from isis_imaging.core.algorithms import gui_compile_ui, size_calculator
from isis_imaging.core.io.loader import read_in_shape
from isis_imaging.core.io.utility import get_file_extension


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

        self.sampleButton.clicked.connect(
            lambda: self.update_dialogue(select_file(self.samplePath, "Sample")))

        # connect the calculation of expected memory to spinboxes
        self.index_start.valueChanged.connect(self.update_expected_memory)
        self.index_end.valueChanged.connect(self.update_expected_memory)
        self.index_step.valueChanged.connect(self.update_expected_memory)

        # if accepted load the stack
        self.accepted.connect(parent.execute_load)
        self.image_format = ''
        self.single_mem = 0

    def update_dialogue(self, select_file_successful):
        if not select_file_successful:
            return False

        self.image_format = get_file_extension(str(self.samplePath.text()))
        shape = read_in_shape(self.sample_path(), self.image_format)
        self.single_mem = size_calculator.to_MB(
            size_calculator.single_size(shape, axis=0), dtype='32')
        self.update_indices(shape[0])
        self.update_expected_memory()

    def update_indices(self, number_of_images):
        """
        :param number_of_images: Number of images that will be loaded in from the current selection
        """
        # cap the end value FIRST, otherwise setValue might fail if the previous max val is smaller
        self.index_end.setMaximum(number_of_images)
        self.index_end.setValue(number_of_images)

        # cap the start value to be end - 1
        self.index_start.setMaximum(number_of_images - 1)

        # enforce the maximum step
        self.index_step.setMaximum(number_of_images)
        self.index_step.setValue(number_of_images / 10)

    def update_expected_memory(self):
        # TODO maybe refactor the number of images calculation to size_calculator if it's needed elsewhere
        exp_mem = self.single_mem * \
            ((self.index_end.value() - self.index_start.value()) / self.index_step.value())
        # we also need to account for the step
        self.expectedMemoryLabel.setText("{} MB".format(round(exp_mem, 1)))

    def load_path(self):
        return os.path.basename(str(self.samplePath.text()))

    def sample_path(self):
        """
        :return: The directory of the path as a Python string
        """
        return os.path.dirname(str(self.samplePath.text()))

    def parallel_load(self):
        """
        :return: True if load should be in parallel, else False
        """
        return self.parallelLoad.isChecked()

    def indices(self):
        return self.index_start.value(), self.index_end.value(
        ), self.index_step.value()

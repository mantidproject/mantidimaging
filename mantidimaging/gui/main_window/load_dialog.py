from __future__ import absolute_import, division, print_function

import os
from logging import getLogger

from PyQt5 import Qt

from mantidimaging.core.algorithms import gui_compile_ui, size_calculator
from mantidimaging.core.io.loader import read_in_shape
from mantidimaging.core.io.utility import get_file_extension


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

        self.parent_view = parent

        self.sampleButton.clicked.connect(
            lambda: self.update_dialogue(select_file(self.samplePath, "Sample")))

        # connect the calculation of expected memory to spinboxes
        self.index_start.valueChanged.connect(self.update_expected)
        self.index_end.valueChanged.connect(self.update_expected)
        self.index_step.valueChanged.connect(self.update_expected)
        self.pixelBitDepth.currentIndexChanged.connect(self.update_expected)

        # if accepted load the stack
        self.accepted.connect(parent.execute_load)
        self.image_format = ''
        self.single_mem = 0
        self.last_shape = (0, 0, 0)

        # remove the placeholder text from QtCreator
        self.expectedResourcesLabel.setText("")

        self.dtype = '32'

        # Populate the size calculator result with initial values (zeros)
        self.update_expected()

    def update_dialogue(self, select_file_successful):
        if not select_file_successful:
            return False

        sample_filename = str(self.samplePath.text())
        self.image_format = get_file_extension(sample_filename)

        try:
            self.last_shape = read_in_shape(self.sample_path(),
                                            in_format=self.image_format)
        except Exception as e:
            getLogger(__name__).error("Failed to read file %s (%s)", sample_filename, e)
            self.parent_view.presenter.show_error("Failed to read this file. See log for details.")
            self.last_shape = (0, 0, 0)

        self.update_indices(self.last_shape[0])
        self.update_expected()

    def update_indices(self, number_of_images):
        """
        :param number_of_images: Number of images that will be loaded in from
                                 the current selection
        """
        # cap the end value FIRST, otherwise setValue might fail if the
        # previous max val is smaller
        self.index_end.setMaximum(number_of_images)
        self.index_end.setValue(number_of_images)

        # cap the start value to be end - 1
        self.index_start.setMaximum(number_of_images - 1)

        # enforce the maximum step
        self.index_step.setMaximum(number_of_images)
        self.index_step.setValue(number_of_images / 10)

    def update_expected(self):
        self.dtype = self.pixelBitDepth.currentText()

        num_images = size_calculator.number_of_images_from_indices(
            self.index_start.value(),
            self.index_end.value(),
            self.index_step.value())

        single_mem = size_calculator.to_MB(
            size_calculator.single_size(self.last_shape, axis=0),
            dtype=self.dtype)

        exp_mem = round(single_mem * num_images, 2)
        self.expectedResourcesLabel.setText(
            "{0}x{1}x{2}: {3} MB".format(num_images, self.last_shape[1],
                                         self.last_shape[2], exp_mem))

    def sample_file(self):
        """
        :return: The file that the use has selected
        """
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
        return (self.index_start.value(),
                self.index_end.value(),
                self.index_step.value())

    def window_title(self):
        user_text = self.stackName.text()
        return user_text if len(user_text) > 0 else None

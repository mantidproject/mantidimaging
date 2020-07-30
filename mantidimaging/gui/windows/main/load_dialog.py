import os
import traceback
from collections import namedtuple
from logging import getLogger
from pathlib import Path
from typing import Dict, Optional, Any

from PyQt5 import Qt
from PyQt5.QtWidgets import QLineEdit, QPushButton, QVBoxLayout, QWidget, QComboBox, QCheckBox

from mantidimaging.core.io.loader import read_in_shape
from mantidimaging.core.io.utility import get_file_extension, get_prefix, get_file_names
from mantidimaging.core.utility import size_calculator
from mantidimaging.gui.utility import (compile_ui, select_file)

ImageLoadIndices = namedtuple('ImageLoadIndices', ['start', 'end', 'step'])


class MWLoadDialog(Qt.QDialog):
    data_fields_layout: QVBoxLayout

    sample_button: QPushButton
    flat_button: QPushButton
    dark_button: QPushButton

    sample_path: QLineEdit
    flat_path: QLineEdit
    dark_path: QLineEdit

    dark_flat_button: QPushButton
    dark_widget: QWidget
    flat_widget: QWidget

    pixel_bit_depth: QComboBox
    images_are_sinograms: QCheckBox

    def __init__(self, parent):
        super(MWLoadDialog, self).__init__(parent)
        compile_ui('gui/ui/load_dialog.ui', self)

        self.parent_view = parent

        self.sample_button.clicked.connect(lambda: self.update_dialogue(select_file(self.sample_path, "Sample")))
        self.dark_button.clicked.connect(lambda: select_file(self.dark_path, "Dark"))
        self.flat_button.clicked.connect(lambda: select_file(self.flat_path, "Flat"))

        # connect the calculation of expected memory to spinboxes
        self.index_start.valueChanged.connect(self.update_expected_mem_usage)
        self.index_end.valueChanged.connect(self.update_expected_mem_usage)
        self.index_step.valueChanged.connect(self.update_expected_mem_usage)
        self.pixel_bit_depth.currentIndexChanged.connect(self.update_expected_mem_usage)

        self.step_all.clicked.connect(self._set_all_step)
        self.step_preview.clicked.connect(self._set_preview_step)
        # if accepted load the stack
        self.accepted.connect(parent.execute_load)
        self.image_format = ''
        self.single_mem = 0
        self.last_shape = (0, 0, 0)

        # remove the placeholder text from QtCreator
        self.expectedResourcesLabel.setText("")

        self.dtype = '32'

        # Populate the size calculator result with initial values (zeros)
        self.update_expected_mem_usage()

    def update_dialogue(self, select_file_successful):
        """
        Updates the memory usage and the indices in the dialog.
        :param select_file_successful: Whether the user selected a file or closed the dialog.
        """
        if not select_file_successful:
            return False

        sample_filename = self.sample_file()
        self.image_format = get_file_extension(sample_filename)

        filename = self.sample_path_text()
        dirname = self.sample_path_directory()
        try:
            self.last_shape, sinograms = read_in_shape(dirname, in_prefix=get_prefix(filename),
                                                       in_format=self.image_format)
        except Exception as e:
            getLogger(__name__).error("Failed to read file %s (%s)", sample_filename, e)
            self.parent_view.presenter.show_error("Failed to read this file. See log for details.",
                                                  traceback.format_exc())
            self.last_shape = (0, 0, 0)
            sinograms = False

        sample_dirname = Path(dirname)
        self.flat_path.setText(self._find_images(sample_dirname, "Flat"))
        self.dark_path.setText(self._find_images(sample_dirname, "Dark"))

        self.images_are_sinograms.setChecked(sinograms)

        self.update_indices(self.last_shape[0])
        self.update_expected_mem_usage()

    def _find_images(self, sample_dirname: Path, type: str) -> str:
        expected_path = sample_dirname / ".." / f"{type}_After"
        logger = getLogger(__name__)
        try:
            path_filenames = get_file_names(expected_path.absolute(), self.image_format)
            return path_filenames[0]
        except RuntimeError:
            logger.info(f"Could not find {type} files in {expected_path.absolute()}")
            expected_path = sample_dirname / ".." / f"{type}_Before"
            try:
                path_filenames = get_file_names(expected_path.absolute(), self.image_format)
                return path_filenames[0]
            except RuntimeError:
                logger.info(f"Could not find {type} files in {expected_path.absolute()}")
        # look for files in the same directory
        try:
            path_filenames = get_file_names(sample_dirname.absolute(), self.image_format, prefix=f"*{type}")
            return path_filenames[0]
        except RuntimeError:
            logger.info(f"Could not find {type} files in {sample_dirname.absolute()}")

        return ""

    def update_indices(self, number_of_images):
        """
        :param number_of_images: Number of images that will be loaded in from
                                 the current selection
        """
        # Cap the end value FIRST, otherwise setValue might fail if the
        # previous max val is smaller
        self.index_end.setMaximum(number_of_images)
        self.index_end.setValue(number_of_images)

        # Cap the start value to be end - 1 (ensure no negative value can be
        # set in case of loading failure)
        self.index_start.setMaximum(max(number_of_images - 1, 0))

        # Enforce the maximum step (ensure a minimum of 1)
        self.index_step.setMaximum(max(number_of_images, 1))

    def update_expected_mem_usage(self):
        self.dtype = self.pixel_bit_depth.currentText()

        num_images = size_calculator.number_of_images_from_indices(self.index_start.value(), self.index_end.value(),
                                                                   self.index_step.value())

        single_mem = size_calculator.to_MB(size_calculator.single_size(self.last_shape, axis=0), dtype=self.dtype)

        exp_mem = round(single_mem * num_images, 2)
        self.expectedResourcesLabel.setText(
            "{0}x{1}x{2}: {3} MB".format(num_images, self.last_shape[1], self.last_shape[2], exp_mem))

    def sample_file(self) -> str:
        """
        :return: The file that the use has selected
        """
        return os.path.basename(str(self.sample_path.text()))

    def _get_path_directory(self, field) -> str:
        """
        :return: The directory of the path as a Python string
        """
        return os.path.dirname(str(field.text()))

    def sample_path_directory(self) -> str:
        """
        :return: The directory of the path as a Python string
        """
        return self._get_path_directory(self.sample_path)

    @staticmethod
    def _get_text(widget):
        return str(widget.text())

    def sample_path_text(self) -> str:
        """
        :return: The directory of the path as a Python string
        """
        return self._get_text(self.sample_path)

    def flat_path_text(self) -> str:
        """
        :return: The directory of the path as a Python string
        """
        return self._get_text(self.flat_path)

    def dark_path_text(self) -> str:
        """
        :return: The directory of the path as a Python string
        """
        return self._get_text(self.dark_path)

    @property
    def indices(self) -> ImageLoadIndices:
        return ImageLoadIndices(self.index_start.value(), self.index_end.value(), self.index_step.value())

    def window_title(self) -> Optional[str]:
        user_text = self.stackName.text()
        return user_text if len(user_text) > 0 else None

    def _set_all_step(self):
        self.index_step.setValue(1)

    def _set_preview_step(self):
        self.index_step.setValue(self.last_shape[0] / 10)

    def get_kwargs(self) -> Dict[str, Any]:
        return {
            'selected_file': self.sample_file(),
            'sample_path': self.sample_path_directory(),
            'flat_path': self.flat_path_text(),
            'dark_path': self.dark_path_text(),
            'in_prefix': get_prefix(self.sample_path_text()),
            'image_format': self.image_format,
            'indices': self.indices,
            'custom_name': self.window_title(),
            'dtype': self.pixel_bit_depth.currentText(),
            'sinograms': self.images_are_sinograms.isChecked()
        }

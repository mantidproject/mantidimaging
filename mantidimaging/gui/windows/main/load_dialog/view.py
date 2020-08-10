import os
from collections import namedtuple
from typing import Dict, Optional, Any, Tuple

from PyQt5 import Qt
from PyQt5.QtWidgets import QLineEdit, QPushButton, QVBoxLayout, QWidget, QComboBox, QCheckBox, QTreeView, QTreeWidget

from mantidimaging.core.io.utility import get_prefix
from mantidimaging.gui.utility import (compile_ui)
from mantidimaging.gui.windows.main.load_dialog.presenter import LoadPresenter, Notification

ImageLoadIndices = namedtuple('ImageLoadIndices', ['start', 'end', 'step'])


class MWLoadDialog(Qt.QDialog):
    tree:QTreeWidget
    pixel_bit_depth: QComboBox
    images_are_sinograms: QCheckBox

    def __init__(self, parent):
        super(MWLoadDialog, self).__init__(parent)
        compile_ui('gui/ui/load_dialog.ui', self)

        self.

        self.parent_view = parent
        self.presenter = LoadPresenter(self)

        self.sample_button.clicked.connect(lambda: self.presenter.notify(Notification.UPDATE))
        self.dark_button.clicked.connect(lambda: self.select_file(self.dark_path, "Dark"))
        self.flat_button.clicked.connect(lambda: self.select_file(self.flat_path, "Flat"))

        # connect the calculation of expected memory to spinboxes
        self.index_start.valueChanged.connect(self.update_expected_mem_usage)
        self.index_end.valueChanged.connect(self.update_expected_mem_usage)
        self.index_step.valueChanged.connect(self.update_expected_mem_usage)
        self.pixel_bit_depth.currentIndexChanged.connect(self.update_expected_mem_usage)

        self.step_all.clicked.connect(self._set_all_step)
        self.step_preview.clicked.connect(self._set_preview_step)
        # if accepted load the stack
        self.accepted.connect(self.parent_view.execute_load)

        # remove the placeholder text from QtCreator
        self.expectedResourcesLabel.setText("")

    @staticmethod
    def select_file(field: QWidget, caption: str) -> bool:
        """
        :param field: The field in which the result will be saved
        :param caption: Title of the file browser window that will be opened
        :return: True: If a file has been selected, False otherwise
        """
        assert isinstance(field, Qt.QLineEdit), ("The passed object is of type {0}. This function only works with "
                                                 "QLineEdit".format(type(field)))
        images_filter = "Images (*.png *.jpg *.tif *.tiff *.fit *.fits)"
        selected_file = Qt.QFileDialog.getOpenFileName(caption=caption,
                                                       filter=f"{images_filter};;All (*.*)",
                                                       initialFilter=images_filter)[0]
        # open file dialogue and set the text if file is selected
        if selected_file:
            field.setText(selected_file)
            return True

        # no file has been selected
        return False

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

    def update_expected_mem_usage(self, num_images: int, shape: Tuple[int, int, int], exp_mem: int):
        self.expectedResourcesLabel.setText(f"{num_images}x{shape[1]}x{shape[2]}: {exp_mem} MB")

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

    def show_error(self, msg, traceback):
        self.parent_view.presenter.show_error(msg, traceback)

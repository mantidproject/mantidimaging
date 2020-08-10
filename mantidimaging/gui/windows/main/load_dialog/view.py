import os
from collections import namedtuple
from typing import Dict, Optional, Any, Tuple

from PyQt5 import Qt
from PyQt5.QtWidgets import QComboBox, QCheckBox, QTreeWidget, QTreeWidgetItem, QPushButton, QSizePolicy, \
    QHeaderView

from mantidimaging.core.io.utility import get_prefix
from mantidimaging.gui.utility import (compile_ui)
from mantidimaging.gui.windows.main.load_dialog.field import Field
from mantidimaging.gui.windows.main.load_dialog.presenter import LoadPresenter, Notification

Indices = namedtuple('Indices', ['start', 'end', 'step'])


class MWLoadDialog(Qt.QDialog):
    tree: QTreeWidget
    pixel_bit_depth: QComboBox
    images_are_sinograms: QCheckBox

    _sample_path: Optional[QTreeWidgetItem] = None
    _flat_path: Optional[QTreeWidgetItem] = None
    _dark_path: Optional[QTreeWidgetItem] = None
    _proj_180deg_path: Optional[QTreeWidgetItem] = None
    _sample_log_path: Optional[QTreeWidgetItem] = None
    _flat_log_path: Optional[QTreeWidgetItem] = None

    def __init__(self, parent):
        super(MWLoadDialog, self).__init__(parent)
        compile_ui('gui/ui/load_dialog.ui', self)

        self.parent_view = parent
        self.presenter = LoadPresenter(self)

        self.tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tree.header().setStretchLastSection(False)
        self.tree.setTabKeyNavigation(True)

        self.sample, self.select_sample = self.create_file_input(0)
        self.select_sample.clicked.connect(lambda: self.presenter.notify(Notification.UPDATE))

        self.flat, self.select_flat = self.create_file_input(1)
        self.dark, self.select_dark = self.create_file_input(2)

        self.proj_180deg, self.select_proj_180deg = self.create_file_input(3)
        self.sample_log, self.select_sample_log = self.create_file_input(4)
        self.flat_log, self.select_flat_log = self.create_file_input(5)

        self.step_all.clicked.connect(self._set_all_step)
        self.step_preview.clicked.connect(self._set_preview_step)
        # if accepted load the stack
        self.accepted.connect(self.parent_view.execute_load)

        # remove the placeholder text from QtCreator
        self.expectedResourcesLabel.setText("")

    def create_file_input(self, position: int) -> Tuple[Field, QPushButton]:
        section: QTreeWidgetItem = self.tree.topLevelItem(position)

        select_button = QPushButton(f"Select")
        select_button.setMaximumWidth(100)
        select_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.tree.setItemWidget(section, 2, select_button)

        return Field(self, self.tree, section), select_button

    @staticmethod
    def select_file(field: Field, caption: str) -> bool:
        """
        :param field: The field in which the result will be saved
        :param caption: Title of the file browser window that will be opened
        :return: True: If a file has been selected, False otherwise
        """
        images_filter = "Images (*.png *.jpg *.tif *.tiff *.fit *.fits)"
        selected_file, accepted = Qt.QFileDialog.getOpenFileName(caption=caption,
                                                                 filter=f"{images_filter};;All (*.*)",
                                                                 initialFilter=images_filter)

        if accepted:
            field.path.setText(1, selected_file)
            return True
        else:
            return False

    def update_indices(self, field: Field, number_of_images):
        """
        :param number_of_images: Number of images that will be loaded in from
                                 the current selection
        """
        # Cap the end value FIRST, otherwise setValue might fail if the
        # previous max val is smaller
        field.stop.setMaximum(number_of_images)
        field.stop.setValue(number_of_images)

        # Cap the start value to be end - 1 (ensure no negative value can be
        # set in case of loading failure)
        field.start.setMaximum(max(number_of_images - 1, 0))

        # Enforce the maximum step (ensure a minimum of 1)
        field.increment.setMaximum(max(number_of_images, 1))

    def update_expected_mem_usage(self, num_images: int, shape: Tuple[int, int, int], exp_mem: int):
        self.expectedResourcesLabel.setText(f"{num_images}x{shape[1]}x{shape[2]}: {exp_mem} MB")

    @property
    def indices(self) -> Indices:
        return Indices(self.index_start.value(), self.index_end.value(), self.index_step.value())

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

    # def add_indices(self, parent: QTreeWidgetItem):
    #     start = QTreeWidgetItem(parent)
    #     start_spinbox = QSpinBox(self)
    #     self.tree.setItemWidget(start, 1, start_spinbox)

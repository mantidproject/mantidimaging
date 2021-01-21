# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from typing import Optional, Tuple

from PyQt5 import Qt
from PyQt5.QtWidgets import QComboBox, QCheckBox, QTreeWidget, QTreeWidgetItem, QPushButton, QSizePolicy, \
    QHeaderView, QSpinBox

from mantidimaging.core.io.loader.loader import DEFAULT_PIXEL_SIZE, DEFAULT_IS_SINOGRAM, DEFAULT_PIXEL_DEPTH
from mantidimaging.core.utility.data_containers import LoadingParameters
from mantidimaging.gui.utility import (compile_ui)
from mantidimaging.gui.windows.load_dialog.field import Field
from .presenter import LoadPresenter, Notification


class MWLoadDialog(Qt.QDialog):
    tree: QTreeWidget
    pixel_bit_depth: QComboBox
    images_are_sinograms: QCheckBox

    pixelSize: QSpinBox

    step_preview: QPushButton
    step_all: QPushButton

    _sample_path: Optional[QTreeWidgetItem] = None
    _flat_before_path: Optional[QTreeWidgetItem] = None
    _flat_after_path: Optional[QTreeWidgetItem] = None
    _dark_before_path: Optional[QTreeWidgetItem] = None
    _dark_after_path: Optional[QTreeWidgetItem] = None
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
        self.select_sample.clicked.connect(lambda: self.presenter.notify(Notification.UPDATE_ALL_FIELDS))

        self.flat_before, self.select_flat_before = self.create_file_input(1)
        self.select_flat_before.clicked.connect(lambda: self.presenter.notify(
            Notification.UPDATE_FLAT_OR_DARK, field=self.flat_before, name="Flat", suffix="Before"))

        self.flat_after, self.select_flat_after = self.create_file_input(2)
        self.select_flat_after.clicked.connect(lambda: self.presenter.notify(
            Notification.UPDATE_FLAT_OR_DARK, field=self.flat_after, name="Flat", suffix="After"))

        self.dark_before, self.select_dark_before = self.create_file_input(3)
        self.select_dark_before.clicked.connect(lambda: self.presenter.notify(
            Notification.UPDATE_FLAT_OR_DARK, field=self.dark_before, name="Dark", suffix="Before"))

        self.dark_after, self.select_dark_after = self.create_file_input(4)
        self.select_dark_after.clicked.connect(lambda: self.presenter.notify(
            Notification.UPDATE_FLAT_OR_DARK, field=self.dark_after, name="Dark", suffix="After"))

        self.proj_180deg, self.select_proj_180deg = self.create_file_input(5)
        self.select_proj_180deg.clicked.connect(lambda: self.presenter.notify(
            Notification.UPDATE_SINGLE_FILE, field=self.proj_180deg, name="180 degree", is_image_file=True))

        self.sample_log, self.select_sample_log = self.create_file_input(6)
        self.select_sample_log.clicked.connect(lambda: self.presenter.notify(
            Notification.UPDATE_SAMPLE_LOG, field=self.sample_log, name="Sample Log", is_image_file=False))

        self.flat_before_log, self.select_flat_before_log = self.create_file_input(7)
        self.select_flat_before_log.clicked.connect(lambda: self.presenter.notify(
            Notification.UPDATE_SINGLE_FILE, field=self.flat_before_log, name="Flat Before Log", image_file=False))

        self.flat_after_log, self.select_flat_after_log = self.create_file_input(8)
        self.select_flat_after_log.clicked.connect(lambda: self.presenter.notify(
            Notification.UPDATE_SINGLE_FILE, field=self.flat_after_log, name="Flat After Log", image_file=False))

        self.step_all.clicked.connect(self._set_all_step)
        self.step_preview.clicked.connect(self._set_preview_step)
        # if accepted load the stack
        self.accepted.connect(self.parent_view.execute_load)

        # remove the placeholder text from QtCreator
        self.expectedResourcesLabel.setText("")

        # Ensure defaults are set
        self.images_are_sinograms.setChecked(DEFAULT_IS_SINOGRAM)
        self.pixelSize.setValue(DEFAULT_PIXEL_SIZE)
        self.pixel_bit_depth.setCurrentText(DEFAULT_PIXEL_DEPTH)

    def create_file_input(self, position: int) -> Tuple[Field, QPushButton]:
        section: QTreeWidgetItem = self.tree.topLevelItem(position)

        use = QCheckBox(self)
        if position == 0:
            use.setEnabled(False)
        self.tree.setItemWidget(section, 2, use)

        select_button = QPushButton("Select", self)
        select_button.setMaximumWidth(100)
        select_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.tree.setItemWidget(section, 3, select_button)
        field = Field(self, self.tree, section, use)

        return field, select_button

    @staticmethod
    def select_file(caption: str, image_file=True) -> Optional[str]:
        """
        :param caption: Title of the file browser window that will be opened
        :param image_file: Whether or not the file being looked for is an image
        :return: True: If a file has been selected, False otherwise
        """
        if image_file:
            file_filter = "Images (*.png *.jpg *.tif *.tiff *.fit *.fits)"
        else:
            # Assume text file
            file_filter = "Log File (*.txt *.log *.csv)"
        selected_file, _ = Qt.QFileDialog.getOpenFileName(caption=caption,
                                                          filter=f"{file_filter};;All (*.*)",
                                                          initialFilter=file_filter)

        if len(selected_file) > 0:
            return selected_file
        else:
            return None

    def _set_all_step(self):
        self.sample.set_step(1)

    def _set_preview_step(self):
        # FIXME direct attribute access
        self.sample.set_step(self.presenter.last_file_info.shape[0] // 10)

    def get_parameters(self) -> LoadingParameters:
        return self.presenter.get_parameters()

    def show_error(self, msg, traceback):
        self.parent_view.presenter.show_error(msg, traceback)

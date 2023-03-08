# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import Optional, Dict

from PyQt5.QtWidgets import QComboBox, QCheckBox, QTreeWidget, QTreeWidgetItem, QPushButton, QSizePolicy, \
    QHeaderView, QSpinBox, QFileDialog, QDialogButtonBox, QWidget

from mantidimaging.core.io.loader.loader import DEFAULT_PIXEL_SIZE, DEFAULT_IS_SINOGRAM, DEFAULT_PIXEL_DEPTH, \
    LoadingParameters
from mantidimaging.core.utility.data_containers import FILE_TYPES
from mantidimaging.gui.windows.image_load_dialog.field import Field
from .presenter import LoadPresenter
from ...mvp_base import BaseDialogView


class ImageLoadDialog(BaseDialogView):
    tree: QTreeWidget
    pixel_bit_depth: QComboBox
    images_are_sinograms: QCheckBox

    pixelSize: QSpinBox

    step_preview: QPushButton
    step_all: QPushButton

    fields: Dict[str, Field]

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent, 'gui/ui/image_load_dialog.ui')

        self.parent_view = parent
        self.presenter = LoadPresenter(self)
        self.fields = {}

        self.tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tree.header().setStretchLastSection(False)
        self.tree.setTabKeyNavigation(True)

        for n, file_info in enumerate(FILE_TYPES):
            self.fields[file_info.fname] = self.create_file_input(n, file_info)

        self.sample = self.fields["Sample"]

        self.step_all.clicked.connect(self._set_all_step)
        self.step_preview.clicked.connect(self._set_preview_step)
        # if accepted load the stack
        self.accepted.connect(self.parent_view.execute_image_file_load)
        self.ok_button = self.buttonBox.button(QDialogButtonBox.Ok)
        self.ok_button.setEnabled(False)

        # remove the placeholder text from QtCreator
        self.expectedResourcesLabel.setText("")

        # Ensure defaults are set
        self.images_are_sinograms.setChecked(DEFAULT_IS_SINOGRAM)
        self.pixelSize.setValue(DEFAULT_PIXEL_SIZE)
        self.pixel_bit_depth.setCurrentText(DEFAULT_PIXEL_DEPTH)

    def create_file_input(self, position: int, file_info: FILE_TYPES) -> Field:
        section: QTreeWidgetItem = self.tree.topLevelItem(position)

        use = QCheckBox(self)
        if position == 0:
            use.setEnabled(False)
        self.tree.setItemWidget(section, 2, use)

        select_button = QPushButton("Select", self)
        select_button.setMaximumWidth(100)
        select_button.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)

        self.tree.setItemWidget(section, 3, select_button)
        field = Field(self.tree, section, use, select_button, file_info)

        select_button.clicked.connect(lambda: self.presenter.do_update_field(field=field))

        return field

    @staticmethod
    def select_file(caption: str, image_file=True) -> Optional[str]:
        """
        :param caption: Title of the file browser window that will be opened
        :param image_file: Whether or not the file being looked for is an image
        :return: Selected file name or None if canceled
        """
        if image_file:
            file_filter = "Images (*.png *.jpg *.tif *.tiff *.fit *.fits)"
        else:
            # Assume text file
            file_filter = "Log File (*.txt *.log *.csv)"
        selected_file, _ = QFileDialog.getOpenFileName(caption=caption,
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

    def enable_preview_all_buttons(self):
        self.step_preview.setEnabled(True)
        self.step_all.setEnabled(True)

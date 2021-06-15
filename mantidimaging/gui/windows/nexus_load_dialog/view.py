# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from typing import Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QDialog, QPushButton, QFileDialog, QLineEdit, QTreeWidget, QTreeWidgetItem, \
    QHeaderView, QCheckBox, QDialogButtonBox

from mantidimaging.gui.utility import compile_ui
from mantidimaging.gui.windows.nexus_load_dialog.presenter import NexusLoadPresenter, Notification

NEXUS_CAPTION = "NeXus"
NEXUS_FILTER = "NeXus (*.nxs *.hd5)"

FOUND_PALETTE = QPalette()

FOUND_TEXT = {True: "✓", False: "✕"}

FOUND_COLUMN = 1
PATH_COLUMN = 2
SHAPE_COLUMN = 3
CHECKBOX_COLUMN = 4


class NexusLoadDialog(QDialog):
    tree: QTreeWidget
    chooseFileButton: QPushButton
    filePathLineEdit: QLineEdit
    buttonBox: QDialogButtonBox

    def __init__(self, parent):
        super(NexusLoadDialog, self).__init__(parent)
        compile_ui("gui/ui/nexus_load_dialog.ui", self)

        self.parent_view = parent
        self.presenter = NexusLoadPresenter(self)
        self.tree.expandItem(self.tree.topLevelItem(1))

        self.tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.Stretch)

        self.chooseFileButton.clicked.connect(self.choose_nexus_file)
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

    def choose_nexus_file(self):
        selected_file, _ = QFileDialog.getOpenFileName(caption=NEXUS_CAPTION,
                                                       filter=f"{NEXUS_FILTER};;All (*.*)",
                                                       initialFilter=NEXUS_FILTER)

        if selected_file:
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)
            self.filePathLineEdit.setText(selected_file)
            self.presenter.notify(Notification.NEXUS_FILE_SELECTED)

    def set_data_found(self, position: int, found: bool, path: str, shape: Tuple[int, ...]):
        section: QTreeWidgetItem = self.tree.topLevelItem(position)
        self.set_found_status(section, found)

        if not found:
            return

        section.setText(PATH_COLUMN, path)
        section.setText(SHAPE_COLUMN, str(shape))

    def set_images_found(self, position: int, found: bool, shape: Tuple[int, int, int], checkbox_enabled: bool = True):
        section: QTreeWidgetItem = self.tree.topLevelItem(1)
        child = section.child(position)
        self.set_found_status(child, found)

        if not found:
            return

        child.setText(SHAPE_COLUMN, str(shape))
        checkbox = QCheckBox()
        if not checkbox_enabled:
            checkbox.setEnabled(False)
            checkbox.setChecked(True)
        self.tree.setItemWidget(child, CHECKBOX_COLUMN, checkbox)

    def show_error(self, msg, traceback):
        self.parent_view.presenter.show_error(msg, traceback)

    def invalid_file_opened(self):
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

    @staticmethod
    def set_found_status(tree_widget_item: QTreeWidgetItem, found: bool):
        tree_widget_item.setText(FOUND_COLUMN, FOUND_TEXT[found])
        tree_widget_item.setTextAlignment(FOUND_COLUMN, Qt.AlignHCenter)

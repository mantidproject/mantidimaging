# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from typing import Tuple

from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QDialog, QPushButton, QFileDialog, QLineEdit, QTreeWidget, QTreeWidgetItem, \
    QHeaderView, QCheckBox

from mantidimaging.gui.utility import compile_ui
from mantidimaging.gui.windows.nexus_load_dialog.presenter import NexusLoadPresenter, Notification

NEXUS_CAPTION = "NeXus"
NEXUS_FILTER = "NeXus (*.nxs *.hd5)"

FOUND_PALETTE = QPalette()

FOUND_TEXT = {True: "✓", False: "✕"}


class NexusLoadDialog(QDialog):
    tree: QTreeWidget
    chooseFileButton: QPushButton
    filePathLineEdit: QLineEdit

    def __init__(self, parent):
        super(NexusLoadDialog, self).__init__(parent)
        compile_ui("gui/ui/nexus_load_dialog.ui", self)

        self.parent_view = parent
        self.presenter = NexusLoadPresenter(self)
        self.tree.expandItem(self.tree.topLevelItem(1))

        self.tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.Stretch)

        self.chooseFileButton.clicked.connect(self.choose_nexus_file)

    def choose_nexus_file(self):
        selected_file, _ = QFileDialog.getOpenFileName(caption=NEXUS_CAPTION,
                                                       filter=f"{NEXUS_FILTER};;All (*.*)",
                                                       initialFilter=NEXUS_FILTER)

        if selected_file:
            self.filePathLineEdit.setText(selected_file)
            self.presenter.notify(Notification.NEXUS_FILE_SELECTED)

    def set_data_found(self, position: int, found: bool, path: str, shape: Tuple[int, ...]):
        section: QTreeWidgetItem = self.tree.topLevelItem(position)
        section.setText(1, FOUND_TEXT[found])

        if not found:
            return

        section.setText(2, path)
        section.setText(3, str(shape))

    def set_images_found(self, position: int, found: bool, shape: Tuple[int, int, int], checkbox_enabled: bool = True):
        section: QTreeWidgetItem = self.tree.topLevelItem(1)
        child = section.child(position)
        child.setText(1, FOUND_TEXT[found])

        if not found:
            return

        child.setText(3, str(shape))
        checkbox = QCheckBox()
        if not checkbox_enabled:
            checkbox.setEnabled(False)
            checkbox.setChecked(True)
        self.tree.setItemWidget(child, 4, checkbox)

    def show_error(self, msg, traceback):
        self.parent_view.presenter.show_error(msg, traceback)

    def invalid_file_opened(self):
        # disable OK button in this case
        pass

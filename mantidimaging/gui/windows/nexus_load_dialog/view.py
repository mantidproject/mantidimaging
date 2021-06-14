# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from typing import Tuple

from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QDialog, QPushButton, QFileDialog, QLineEdit, QTreeWidget, QTreeWidgetItem, QLabel, \
    QHeaderView, QCheckBox

from mantidimaging.gui.utility import compile_ui
from mantidimaging.gui.windows.nexus_load_dialog.presenter import NexusLoadPresenter, Notification

NEXUS_CAPTION = "NeXus"
NEXUS_FILTER = "NeXus (*.nxs *.hd5)"

FOUND_PALETTE = QPalette()


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

    def set_data_found(self, position: int, found: bool, path: str, size: Tuple[int, ...]):
        section: QTreeWidgetItem = self.tree.topLevelItem(position)

        if not found:
            self.tree.setItemWidget(section, 1, QLabel("✕"))
            return

        self.tree.setItemWidget(section, 1, QLabel("✓"))
        self.tree.setItemWidget(section, 2, QLabel(path))
        self.tree.setItemWidget(section, 3, QLabel(str(size)))

    def set_images_found(self, position: int, found: bool, shape: Tuple[int, int, int], checkbox_enabled: bool = True):
        section: QTreeWidgetItem = self.tree.topLevelItem(1)
        child = section.child(position)

        if not found:
            self.tree.setItemWidget(child, 1, QLabel("✕"))
            return

        self.tree.setItemWidget(child, 1, QLabel("✓"))
        self.tree.setItemWidget(child, 3, QLabel(str(shape)))
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

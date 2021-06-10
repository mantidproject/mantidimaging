# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from PyQt5.QtWidgets import QDialog, QPushButton, QFileDialog, QLineEdit, QTreeWidget, QTreeWidgetItem, QLabel

from mantidimaging.gui.utility import compile_ui
from mantidimaging.gui.windows.nexus_load_dialog.presenter import NexusLoadPresenter, Notification

NEXUS_CAPTION = "NeXus"
NEXUS_FILTER = "NeXus (*.nxs *.hd5)"


class NexusLoadDialog(QDialog):

    tree: QTreeWidget
    chooseFileButton: QPushButton
    filePathLineEdit: QLineEdit

    def __init__(self, parent):
        super(NexusLoadDialog, self).__init__(parent)
        compile_ui("gui/ui/nexus_load_dialog.ui", self)

        self.parent_view = parent
        self.presenter = NexusLoadPresenter(self)

        self.chooseFileButton.clicked.connect(self.choose_nexus_file)
        # self.filePathLineEdit.textChanged.connect(self.presenter.notify(Notification.NEXUS_FILE_SELECTED))

    def choose_nexus_file(self):
        selected_file, _ = QFileDialog.getOpenFileName(caption=NEXUS_CAPTION,
                                                       filter=f"{NEXUS_FILTER};;All (*.*)",
                                                       initialFilter=NEXUS_FILTER)

        if selected_file:
            self.filePathLineEdit.setText(selected_file)
            self.presenter.notify(Notification.NEXUS_FILE_SELECTED)

    def set_data_found(self, position: int, found: bool, path: str):
        if not found:
            pass

        section: QTreeWidgetItem = self.tree.topLevelItem(position)
        found_text = QLabel("True")
        path_text = QLabel(path)

        self.tree.setItemWidget(section, 2, found_text)
        self.tree.setItemWidget(section, 3, path_text)

    def show_error(self, msg, traceback):
        self.parent_view.presenter.show_error(msg, traceback)

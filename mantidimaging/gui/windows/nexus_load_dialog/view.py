# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from PyQt5.QtWidgets import QDialog, QPushButton, QFileDialog, QLineEdit

from mantidimaging.gui.utility import compile_ui
from mantidimaging.gui.windows.nexus_load_dialog.presenter import NexusLoadPresenter

NEXUS_CAPTION = "NeXus"
NEXUS_FILTER = "NeXus (*.nxs *.hd5)"


class NexusLoadDialog(QDialog):

    chooseFileButton: QPushButton
    filePathLineEdit: QLineEdit

    def __init__(self, parent):
        super(NexusLoadDialog, self).__init__(parent)
        compile_ui("gui/ui/nexus_load_dialog.ui", self)

        self.parent_view = parent
        self.presenter = NexusLoadPresenter(self)

        self.chooseFileButton.clicked.connect(self.choose_nexus_file)
        self.filePathLineEdit.textChanged.connect(self.scan_nexus_file)

    def choose_nexus_file(self):
        selected_file, _ = QFileDialog.getOpenFileName(caption=NEXUS_CAPTION,
                                                       filter=f"{NEXUS_FILTER};;All (*.*)",
                                                       initialFilter=NEXUS_FILTER)

        if selected_file:
            self.filePathLineEdit.setText(selected_file)

    def scan_nexus_file(self, file_path: str):
        print(file_path)

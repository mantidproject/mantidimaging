# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from logging import getLogger

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QDialog

from mantidimaging.gui.utility import compile_ui

LOG = getLogger(__name__)


class BaseMainWindowView(QMainWindow):

    def __init__(self, parent, ui_file=None):
        super().__init__(parent)

        if ui_file is not None:
            compile_ui(ui_file, self)

    def closeEvent(self, e):
        LOG.debug('UI window closed')
        self.cleanup()
        super().closeEvent(e)

    def cleanup(self):
        """
        Runs when the window is closed.
        """
        pass

    def show_error_dialog(self, msg: str):
        LOG.error(f"show_error_dialog(): {msg}")
        QMessageBox.critical(self, "Error", str(msg))

    def show_info_dialog(self, msg: str):
        LOG.info(f"show_info_dialog(): {msg}")
        QMessageBox.information(self, "Information", str(msg))

    def show_warning_dialog(self, msg: str):
        LOG.warning(f"show_warning_dialog(): {msg}")
        QMessageBox.warning(self, "Warning", str(msg))


class BaseDialogView(QDialog):

    def __init__(self, parent, ui_file=None):
        super().__init__(parent)

        # Prevents the context help button appearing in the dialog title bar on Windows
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        if ui_file is not None:
            compile_ui(ui_file, self)

    def show_error_dialog(self, msg=""):
        """
        Shows an error message.

        :param msg: Error message string
        """
        QMessageBox.critical(self, "Error", str(msg))

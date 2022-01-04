# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from logging import getLogger

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

    def show_error_dialog(self, msg=""):
        """
        Shows an error message.

        :param msg: Error message string
        """
        QMessageBox.critical(self, "Error", str(msg))

    def show_info_dialog(self, msg=""):
        """
        Shows an information message.

        :param msg: Information message string.
        """
        QMessageBox.information(self, "Information", str(msg))


class BaseDialogView(QDialog):
    def __init__(self, parent, ui_file=None):
        super().__init__(parent)

        if ui_file is not None:
            compile_ui(ui_file, self)

    def show_error_dialog(self, msg=""):
        """
        Shows an error message.

        :param msg: Error message string
        """
        QMessageBox.critical(self, "Error", str(msg))

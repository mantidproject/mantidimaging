# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from logging import getLogger

from PyQt5 import Qt, QtWidgets

from mantidimaging.gui.utility import compile_ui

LOG = getLogger(__name__)


class BaseMainWindowView(Qt.QMainWindow):
    def __init__(self, parent, ui_file=None):
        super(BaseMainWindowView, self).__init__(parent)

        if ui_file is not None:
            compile_ui(ui_file, self)

    def closeEvent(self, e):
        LOG.debug('UI window closed')
        self.cleanup()
        super(BaseMainWindowView, self).closeEvent(e)

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
        QtWidgets.QMessageBox.critical(self, "Error", str(msg))


class BaseDialogView(Qt.QDialog):
    def __init__(self, parent, ui_file=None):
        super(BaseDialogView, self).__init__(parent)

        if ui_file is not None:
            compile_ui(ui_file, self)

    def show_error_dialog(self, msg=""):
        """
        Shows an error message.

        :param msg: Error message string
        """
        QtWidgets.QMessageBox.critical(self, "Error", str(msg))

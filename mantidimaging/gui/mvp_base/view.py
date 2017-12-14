from __future__ import absolute_import, division, print_function

from PyQt5 import Qt, QtWidgets

from mantidimaging.gui.utility import compile_ui


class BaseMainWindowView(Qt.QMainWindow):

    def __init__(self, parent, ui_file=None):
        super(BaseMainWindowView, self).__init__(parent)

        if ui_file is not None:
            compile_ui(ui_file, self)

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

        self.setAttribute(Qt.Qt.WA_DeleteOnClose)

    def show_error_dialog(self, msg=""):
        """
        Shows an error message.

        :param msg: Error message string
        """
        QtWidgets.QMessageBox.critical(self, "Error", str(msg))

# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import time
from logging import getLogger

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QDialog, QApplication

from mantidimaging.gui.utility import compile_ui

LOG = getLogger(__name__)
perf_logger = getLogger("perf." + __name__)
settings = QtCore.QSettings('mantidproject', 'Mantid Imaging')

if not settings.contains("theme_selection") or settings.value("theme_selection") is None:
    settings.setValue('theme_selection', 'Fusion')


class BaseMainWindowView(QMainWindow):

    def __init__(self, parent, ui_file=None):
        self._t0 = time.monotonic()
        super().__init__(parent)

        self._has_shown = False
        QApplication.instance().setStyle(settings.value('theme_selection'))

        if ui_file is not None:
            compile_ui(ui_file, self)

    def closeEvent(self, e) -> None:
        LOG.debug('UI window closed')
        self.cleanup()
        super().closeEvent(e)

    def cleanup(self) -> None:
        """
        Runs when the window is closed.
        """
        pass

    def show_error_dialog(self, msg: str) -> None:
        LOG.error(f"show_error_dialog(): {msg}")
        QMessageBox.critical(self, "Error", str(msg))

    def show_info_dialog(self, msg: str) -> None:
        LOG.info(f"show_info_dialog(): {msg}")
        QMessageBox.information(self, "Information", str(msg))

    def show_warning_dialog(self, msg: str) -> None:
        LOG.warning(f"show_warning_dialog(): {msg}")
        QMessageBox.warning(self, "Warning", str(msg))

    def showEvent(self, ev) -> None:
        super().showEvent(ev)
        if not self._has_shown:
            self._has_shown = True
            QTimer.singleShot(0, self._window_ready)

    def _window_ready(self) -> None:
        if perf_logger.isEnabledFor(1):
            perf_logger.info(f"{type(self).__name__} shown in {time.monotonic() - self._t0}")


class BaseDialogView(QDialog):

    def __init__(self, parent, ui_file=None):
        super().__init__(parent)

        # Prevents the context help button appearing in the dialog title bar on Windows
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        if ui_file is not None:
            compile_ui(ui_file, self)

    def show_error_dialog(self, msg="") -> None:
        """
        Shows an error message.

        :param msg: Error message string
        """
        QMessageBox.critical(self, "Error", str(msg))

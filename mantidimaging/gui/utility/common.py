# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from contextlib import contextmanager

from PyQt5.QtWidgets import QMessageBox


@contextmanager
def operation_in_progress(title, message, parent=None):
    msgbox = QMessageBox(parent)
    msgbox.setIcon(QMessageBox.Information)
    msgbox.setWindowTitle(title)
    msgbox.setText(message)
    try:
        msgbox.show()
        yield
    finally:
        msgbox.close()

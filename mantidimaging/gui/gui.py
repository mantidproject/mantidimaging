# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import logging
import os
import sys
import traceback

from PyQt5.QtWidgets import QMessageBox
import pyqtgraph

from mantidimaging.gui.windows.main import MainWindowView
from mantidimaging.core.parallel import manager as pm


def execute() -> None:
    # all data will be row-major, so this needs to be specified as the default is col-major
    pyqtgraph.setConfigOptions(imageAxisOrder="row-major")

    # create the GUI event loop
    application_window = MainWindowView()

    sys.excepthook = lambda exc_type, exc_value, exc_traceback: application_window.uncaught_exception(
        "".join(traceback.format_exception_only(exc_type, exc_value)), "".join(
            traceback.format_exception(exc_type, exc_value, exc_traceback)))

    def dont_let_qt_shutdown_while_debugging(type, value, tback) -> None:
        # log the exception here
        logging.getLogger(__name__).error(
            f"Exception {type} encountered:\n{traceback.format_exception(type, value, tback)}")
        # then call the default handler
        sys.__excepthook__(type, value, tback)

    if os.environ.get("PYDEVD_LOAD_VALUES_ASYNC", False):
        sys.excepthook = dont_let_qt_shutdown_while_debugging

    application_window.show()

    def clean_up_old_memory() -> None:
        if sys.platform == 'linux':
            memory_to_clean = pm.find_memory_from_previous_process_linux()
            if memory_to_clean:
                # Show confirmation box asking if the user wants to clear the shared memory
                msg_box = QMessageBox.question(application_window,
                                               "Clean Up Shared Memory",
                                               "Mantid Imaging has found shared memory objects that appear to be from "
                                               "a previous instance of the application. This is likely either because"
                                               " Mantid Imaging did not close properly, or due to a bug."
                                               "\n\nDo you want these to be automatically cleaned now?",
                                               defaultButton=QMessageBox.No)
                if msg_box == QMessageBox.Yes:
                    pm.free_shared_memory_linux(memory_to_clean)
                    done = QMessageBox(application_window)
                    done.setWindowTitle("Clean Up Shared Memory")
                    done.setIcon(QMessageBox.Information)
                    done.setText("Clean up process complete")
                    done.exec()

    clean_up_old_memory()

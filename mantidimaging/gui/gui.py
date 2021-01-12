# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import logging
import os
import sys
import traceback

import pyqtgraph
from PyQt5.Qt import QApplication

from mantidimaging.gui.windows.main import MainWindowView


def execute():
    # all data will be row-major, so this needs to be specified as the default is col-major
    pyqtgraph.setConfigOptions(imageAxisOrder="row-major")

    # create the GUI event loop
    q_application = QApplication(sys.argv)
    q_application.setApplicationName("Mantid Imaging")
    q_application.setOrganizationName("mantidproject")
    q_application.setOrganizationDomain("mantidproject.org")
    application_window = MainWindowView()

    sys.excepthook = lambda exc_type, exc_value, exc_traceback: application_window.uncaught_exception(
        "".join(traceback.format_exception_only(exc_type, exc_value)), "".join(
            traceback.format_exception(exc_type, exc_value, exc_traceback)))

    def dont_let_qt_shutdown_while_debugging(type, value, tback):
        # log the exception here
        logging.getLogger(__name__).error(
            f"Exception {type} encountered:\n{traceback.format_exception(type, value, tback)}")
        # then call the default handler
        sys.__excepthook__(type, value, tback)

    if os.environ.get("PYDEVD_LOAD_VALUES_ASYNC", False):
        sys.excepthook = dont_let_qt_shutdown_while_debugging
    application_window.show()

    return sys.exit(q_application.exec_())

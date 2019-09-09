import sys
import traceback

import pyqtgraph
from PyQt5.Qt import QApplication

from mantidimaging.gui.windows.main import MainWindowView
from mantidimaging.gui.windows.savu_filters.preparation import BackgroundService


def execute(process: BackgroundService):
    # all data will be row-major, so this needs to be specified as the default is col-major
    pyqtgraph.setConfigOptions(imageAxisOrder="row-major")

    # create the GUI event loop
    q_application = QApplication(sys.argv)
    application_window = MainWindowView()
    application_window.set_background_service(process)

    sys.excepthook = lambda exc_type, exc_value, exc_traceback: application_window.uncaught_exception(
        "".join(traceback.format_exception_only(exc_type, exc_value)),
        "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))

    application_window.show()

    return sys.exit(q_application.exec_())

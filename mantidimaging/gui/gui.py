import sys
import traceback

from PyQt5.Qt import QApplication

from mantidimaging.gui.windows.main import MainWindowView


def execute():
    # create the GUI event loop
    q_application = QApplication(sys.argv)
    application_window = MainWindowView()

    sys.excepthook = lambda exc_type, exc_value, exc_traceback: application_window.uncaught_exception(
        "".join(traceback.format_exception_only(exc_type, exc_value)),
        "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))

    application_window.show()

    return sys.exit(q_application.exec_())

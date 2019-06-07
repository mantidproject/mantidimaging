import sys

from PyQt5.Qt import QApplication

from mantidimaging.gui.windows.main import MainWindowView
from mantidimaging.gui.windows.savu_filters.preparation import prepare_data


def run_preparations():
    prepare_data()


def execute():
    # create the GUI event loop
    q_application = QApplication(sys.argv)
    application_window = MainWindowView()

    application_window.show()

    return sys.exit(q_application.exec_())

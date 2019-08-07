import sys

import pyqtgraph
from PyQt5.Qt import QApplication

from mantidimaging.gui.windows.main import MainWindowView


def execute():
    # all data will be row-major, so this needs to be specified as the default is col-major
    pyqtgraph.setConfigOptions(imageAxisOrder="row-major")

    # create the GUI event loop
    q_application = QApplication(sys.argv)
    application_window = MainWindowView()

    application_window.show()

    return sys.exit(q_application.exec_())

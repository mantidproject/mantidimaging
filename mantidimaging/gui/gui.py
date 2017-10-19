from __future__ import absolute_import, division, print_function

import sys

from PyQt5.Qt import QApplication

from mantidimaging.gui.main_window import MainWindowView


def execute(config):
    # create the GUI event loop
    q_application = QApplication(sys.argv)
    application_window = MainWindowView(config)

    application_window.show()

    return sys.exit(q_application.exec_())

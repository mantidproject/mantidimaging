from __future__ import absolute_import, division, print_function

import sys

from PyQt4.QtGui import QApplication

from gui.main_window.mw_view import ImgpyMainWindowView


def execute(config):

    # create the GUI event loop
    qApp = QApplication(sys.argv)
    aw = ImgpyMainWindowView(config)
    aw.show()

    return sys.exit(qApp.exec_())

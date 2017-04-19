from __future__ import (absolute_import, division, print_function)
from PyQt4 import uic, QtCore
from PyQt4.QtGui import QApplication


def execute(config):
    import sys

    # create the GUI event loop
    qApp = QApplication(sys.argv)
    from gui.main_view.mw_view import ImgpyMainWindowView
    aw = ImgpyMainWindowView(config)
    aw.show()

    return sys.exit(qApp.exec_())
